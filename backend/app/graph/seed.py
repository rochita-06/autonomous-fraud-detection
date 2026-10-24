"""Seed Neo4j with the synthetic dataset.

Run after `docker compose up -d neo4j`:
    cd backend && python -m app.graph.seed
"""

import csv

from neo4j import GraphDatabase

from ..config import settings


def main():
    driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    driver.verify_connectivity()

    with open(settings.data_dir / "users.csv", newline="", encoding="utf-8") as f:
        users = list(csv.DictReader(f))
    with open(settings.data_dir / "user_devices.csv", newline="", encoding="utf-8") as f:
        devices = list(csv.DictReader(f))
    with open(settings.data_dir / "transactions.csv", newline="", encoding="utf-8") as f:
        txs = list(csv.DictReader(f))

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        session.run(
            "CREATE CONSTRAINT user_id IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.user_id IS UNIQUE"
        )
        session.run(
            "CREATE CONSTRAINT device_id IF NOT EXISTS "
            "FOR (d:Device) REQUIRE d.device_id IS UNIQUE"
        )

        session.run(
            """
            UNWIND $rows AS row
            MERGE (u:User {user_id: row.user_id})
            SET u.name = row.name,
                u.country = row.country,
                u.is_flagged = row.is_flagged = '1'
            """,
            rows=users,
        )
        session.run(
            """
            UNWIND $rows AS row
            MERGE (d:Device {device_id: row.device_id})
            WITH d, row
            MATCH (u:User {user_id: row.user_id})
            MERGE (u)-[:USED_DEVICE]->(d)
            """,
            rows=devices,
        )
        session.run(
            """
            UNWIND $rows AS row
            MATCH (s:User {user_id: row.sender_id})
            MATCH (r:User {user_id: row.receiver_id})
            MERGE (s)-[t:TRANSFERRED_TO]->(r)
            ON CREATE SET t.count = 1, t.total = toFloat(row.amount)
            ON MATCH SET t.count = t.count + 1, t.total = t.total + toFloat(row.amount)
            """,
            rows=txs,
        )

    counts = driver.session().run(
        "MATCH (u:User) WITH count(u) AS users "
        "MATCH (d:Device) WITH users, count(d) AS devices "
        "MATCH ()-[t:TRANSFERRED_TO]->() RETURN users, devices, count(t) AS transfers"
    ).single()
    print(f"Seeded Neo4j: {counts['users']} users, {counts['devices']} devices, "
          f"{counts['transfers']} transfer edges")
    driver.close()


if __name__ == "__main__":
    main()
