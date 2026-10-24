"""Graph intelligence layer.

Primary backend is Neo4j (User / Device nodes, USED_DEVICE / TRANSFERRED_TO
edges). When Neo4j is unreachable the same queries run against an in-memory
graph built from the CSVs, so the system works without Docker.
"""

from __future__ import annotations

import csv
from collections import defaultdict

from ..config import settings


class MemoryGraph:
    """In-memory fallback graph loaded straight from the CSV datasets."""

    backend = "memory"

    def __init__(self):
        self.user_flagged: dict[str, bool] = {}
        self.devices_of: dict[str, set[str]] = defaultdict(set)
        self.users_of_device: dict[str, set[str]] = defaultdict(set)
        self.transfer_partners: dict[str, set[str]] = defaultdict(set)
        self._load()

    def _load(self):
        with open(settings.data_dir / "users.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.user_flagged[row["user_id"]] = row["is_flagged"] == "1"

        with open(settings.data_dir / "user_devices.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.devices_of[row["user_id"]].add(row["device_id"])
                self.users_of_device[row["device_id"]].add(row["user_id"])

        with open(settings.data_dir / "transactions.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.transfer_partners[row["sender_id"]].add(row["receiver_id"])
                self.transfer_partners[row["receiver_id"]].add(row["sender_id"])

    def is_flagged(self, user_id: str) -> bool:
        return self.user_flagged.get(user_id, False)

    def record_transaction(
        self, user_id: str, receiver_id: str = "", device_id: str = "",
        amount: float = 0.0, flagged: bool = False,
    ) -> None:
        """Merge a live transaction into the graph so newly investigated
        users/devices/partners show up immediately in the identity graph —
        mirrors what Neo4jGraph.record_transaction does against Neo4j."""
        if not user_id:
            return
        self.user_flagged.setdefault(user_id, False)
        if flagged:
            self.user_flagged[user_id] = True
        if device_id:
            self.devices_of[user_id].add(device_id)
            self.users_of_device[device_id].add(user_id)
        if receiver_id:
            self.user_flagged.setdefault(receiver_id, False)
            self.transfer_partners[user_id].add(receiver_id)
            self.transfer_partners[receiver_id].add(user_id)

    def linked_accounts(self, user_id: str) -> dict:
        shared_devices = []
        linked_users: set[str] = set()
        for device in sorted(self.devices_of.get(user_id, ())):
            others = sorted(self.users_of_device[device] - {user_id})
            if others:
                shared_devices.append({"device_id": device, "shared_with": others})
                linked_users.update(others)

        partners = sorted(self.transfer_partners.get(user_id, ()))
        flagged_links = sorted(
            u for u in (linked_users | set(partners)) if self.user_flagged.get(u)
        )
        return {
            "user_id": user_id,
            "is_flagged": self.is_flagged(user_id),
            "shared_devices": shared_devices,
            "device_linked_users": sorted(linked_users),
            "transfer_partners": partners[:20],
            "flagged_connections": flagged_links,
            "flagged_connection_count": len(flagged_links),
        }

    def subgraph(self, user_id: str) -> dict:
        """Small neighborhood for dashboard visualization."""
        nodes = {user_id: {"id": user_id, "type": "user", "flagged": self.is_flagged(user_id)}}
        links = []
        for device in sorted(self.devices_of.get(user_id, ())):
            nodes[device] = {"id": device, "type": "device", "flagged": False}
            links.append({"source": user_id, "target": device, "rel": "USED_DEVICE"})
            for other in sorted(self.users_of_device[device] - {user_id}):
                nodes[other] = {"id": other, "type": "user", "flagged": self.is_flagged(other)}
                links.append({"source": other, "target": device, "rel": "USED_DEVICE"})
        for partner in sorted(self.transfer_partners.get(user_id, ()))[:8]:
            if partner not in nodes:
                nodes[partner] = {"id": partner, "type": "user", "flagged": self.is_flagged(partner)}
            links.append({"source": user_id, "target": partner, "rel": "TRANSFERRED_TO"})
        return {"nodes": list(nodes.values()), "links": links}


class Neo4jGraph:
    backend = "neo4j"

    def __init__(self):
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=5,
        )
        self._driver.verify_connectivity()

    def _run(self, query: str, **params) -> list[dict]:
        with self._driver.session() as session:
            return [dict(record) for record in session.run(query, **params)]

    def is_flagged(self, user_id: str) -> bool:
        rows = self._run(
            "MATCH (u:User {user_id: $uid}) RETURN u.is_flagged AS flagged", uid=user_id
        )
        return bool(rows and rows[0]["flagged"])

    def record_transaction(
        self, user_id: str, receiver_id: str = "", device_id: str = "",
        amount: float = 0.0, flagged: bool = False,
    ) -> None:
        """MERGE a live transaction into Neo4j as it's investigated, so the
        identity graph reflects new users/devices/transfers immediately
        instead of only ever showing whatever `seed.py` loaded at boot.
        Without this, any user_id not present in the seeded CSVs is a
        graph orphan — a single disconnected node — even though the
        transaction was just processed successfully."""
        if not user_id:
            return
        self._run(
            """
            MERGE (u:User {user_id: $uid})
            ON CREATE SET u.is_flagged = $flagged
            ON MATCH SET u.is_flagged = u.is_flagged OR $flagged
            """,
            uid=user_id, flagged=bool(flagged),
        )
        if device_id:
            self._run(
                """
                MERGE (d:Device {device_id: $did})
                WITH d
                MATCH (u:User {user_id: $uid})
                MERGE (u)-[:USED_DEVICE]->(d)
                """,
                uid=user_id, did=device_id,
            )
        if receiver_id:
            self._run(
                "MERGE (r:User {user_id: $rid}) ON CREATE SET r.is_flagged = false",
                rid=receiver_id,
            )
            self._run(
                """
                MATCH (s:User {user_id: $uid})
                MATCH (r:User {user_id: $rid})
                MERGE (s)-[t:TRANSFERRED_TO]->(r)
                ON CREATE SET t.count = 1, t.total = $amount
                ON MATCH SET t.count = t.count + 1, t.total = t.total + $amount
                """,
                uid=user_id, rid=receiver_id, amount=float(amount or 0),
            )

    def linked_accounts(self, user_id: str) -> dict:
        shared = self._run(
            """
            MATCH (u:User {user_id: $uid})-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(o:User)
            RETURN d.device_id AS device_id, collect(DISTINCT o.user_id) AS shared_with
            """,
            uid=user_id,
        )
        partners = self._run(
            """
            MATCH (u:User {user_id: $uid})-[:TRANSFERRED_TO]-(p:User)
            RETURN DISTINCT p.user_id AS user_id LIMIT 20
            """,
            uid=user_id,
        )
        flagged = self._run(
            """
            MATCH (u:User {user_id: $uid})-[:USED_DEVICE|TRANSFERRED_TO*1..2]-(o:User)
            WHERE o.is_flagged AND o.user_id <> $uid
            RETURN DISTINCT o.user_id AS user_id
            """,
            uid=user_id,
        )
        linked_users = sorted({u for row in shared for u in row["shared_with"]})
        flagged_ids = sorted(row["user_id"] for row in flagged)
        return {
            "user_id": user_id,
            "is_flagged": self.is_flagged(user_id),
            "shared_devices": [
                {"device_id": r["device_id"], "shared_with": sorted(r["shared_with"])}
                for r in shared
            ],
            "device_linked_users": linked_users,
            "transfer_partners": sorted(r["user_id"] for r in partners),
            "flagged_connections": flagged_ids,
            "flagged_connection_count": len(flagged_ids),
        }

    def subgraph(self, user_id: str) -> dict:
        rows = self._run(
            """
            MATCH (u:User {user_id: $uid})-[r:USED_DEVICE|TRANSFERRED_TO]-(n)
            RETURN u, type(r) AS rel, n, labels(n) AS labels
            LIMIT 40
            """,
            uid=user_id,
        )
        nodes: dict[str, dict] = {}
        links = []
        nodes[user_id] = {"id": user_id, "type": "user", "flagged": self.is_flagged(user_id)}
        for row in rows:
            n = row["n"]
            if "Device" in row["labels"]:
                nid, ntype, flagged = n["device_id"], "device", False
            else:
                nid, ntype, flagged = n["user_id"], "user", bool(n.get("is_flagged"))
            nodes[nid] = {"id": nid, "type": ntype, "flagged": flagged}
            links.append({"source": user_id, "target": nid, "rel": row["rel"]})
        return {"nodes": list(nodes.values()), "links": links}


import time

_graph = None
_last_reconnect_attempt = 0.0
_RECONNECT_INTERVAL_SECONDS = 30


def _connect_neo4j_with_retry(attempts: int = 5, delay_seconds: float = 2.0):
    """Neo4j's HTTP port (used by the docker-compose healthcheck) can report
    healthy slightly before the bolt port finishes accepting connections.
    Retrying a few times at boot avoids permanently falling back to the
    in-memory graph over what is really just a startup race."""
    last_err: Exception | None = None
    for attempt in range(attempts):
        try:
            return Neo4jGraph()
        except Exception as exc:  # noqa: BLE001 - want any driver/connection error
            last_err = exc
            if attempt < attempts - 1:
                time.sleep(delay_seconds)
    raise last_err  # type: ignore[misc]


def get_graph():
    """Returns the process-wide graph backend. If we're currently on the
    in-memory fallback, periodically retries Neo4j in the background so the
    app self-heals once Neo4j becomes reachable, instead of staying on the
    fallback for the container's entire lifetime."""
    global _graph, _last_reconnect_attempt
    if _graph is None:
        try:
            _graph = _connect_neo4j_with_retry()
            print("[graph] connected to Neo4j")
        except Exception as exc:
            _graph = MemoryGraph()
            print(f"[graph] Neo4j unreachable ({exc}) — using in-memory graph")
    elif _graph.backend == "memory":
        now = time.time()
        if now - _last_reconnect_attempt > _RECONNECT_INTERVAL_SECONDS:
            _last_reconnect_attempt = now
            try:
                _graph = Neo4jGraph()
                print("[graph] reconnected to Neo4j — switching off the in-memory fallback")
            except Exception:
                pass  # still unreachable, keep serving from memory
    return _graph
