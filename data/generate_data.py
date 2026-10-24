"""Generate synthetic datasets for the fraud investigation system.

Produces four CSVs in this directory:
  - users.csv          : account holders, a few flagged as known fraudsters
  - user_devices.csv   : which devices each user has logged in from (some shared)
  - transactions.csv   : 90 days of historical transactions with fraud labels
  - fraud_cases.csv    : a knowledge base of known fraud patterns (for RAG)

Run:  python generate_data.py
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
HERE = Path(__file__).parent

COUNTRIES = ["IN", "US", "GB", "SG", "AE"]
MERCHANT_CATEGORIES = [
    "groceries", "electronics", "travel", "dining", "utilities",
    "entertainment", "fashion", "fuel", "crypto_exchange", "gift_cards",
]

# Users flagged as known fraudsters (a "fraud ring" plus two loners)
FLAGGED_USERS = {"U050", "U051", "U052", "U053", "U020", "U033"}
RING_USERS = ["U050", "U051", "U052", "U053", "U054", "U055"]
SHARED_RING_DEVICES = ["D666", "D667"]


def generate_users():
    users = []
    base = datetime(2024, 1, 1)
    for i in range(1, 61):
        uid = f"U{i:03d}"
        users.append({
            "user_id": uid,
            "name": f"User {i}",
            "country": random.choice(COUNTRIES),
            "signup_date": (base + timedelta(days=random.randint(0, 500))).date().isoformat(),
            "avg_tx_amount": round(random.uniform(20, 400), 2),
            "is_flagged": 1 if uid in FLAGGED_USERS else 0,
        })
    return users


def generate_devices(users):
    rows = []
    device_counter = 1
    for u in users:
        for _ in range(random.randint(1, 2)):
            rows.append({"user_id": u["user_id"], "device_id": f"D{device_counter:03d}"})
            device_counter += 1
    # Fraud ring shares two devices
    for uid in RING_USERS:
        for dev in SHARED_RING_DEVICES:
            rows.append({"user_id": uid, "device_id": dev})
    # A few innocent-looking shared devices (family members etc.)
    for a, b in [("U001", "U002"), ("U010", "U011"), ("U030", "U031")]:
        shared = f"D{device_counter:03d}"
        device_counter += 1
        rows.append({"user_id": a, "device_id": shared})
        rows.append({"user_id": b, "device_id": shared})
    return rows


def generate_transactions(users, device_rows):
    user_by_id = {u["user_id"]: u for u in users}
    devices_of = {}
    for row in device_rows:
        devices_of.setdefault(row["user_id"], []).append(row["device_id"])

    txs = []
    start = datetime.now() - timedelta(days=90)
    tx_counter = 1
    user_ids = [u["user_id"] for u in users]

    for _ in range(1200):
        sender = random.choice(users)
        is_fraud = random.random() < 0.05
        ts = start + timedelta(minutes=random.randint(0, 90 * 24 * 60))

        if is_fraud:
            amount = round(sender["avg_tx_amount"] * random.uniform(4, 15), 2)
            receiver = random.choice(RING_USERS)
            country = random.choice([c for c in COUNTRIES if c != sender["country"]])
            hour = random.choice([0, 1, 2, 3, 4, 23])
            ts = ts.replace(hour=hour)
            category = random.choice(["crypto_exchange", "gift_cards", "electronics"])
            device = random.choice(SHARED_RING_DEVICES + devices_of[sender["user_id"]])
        else:
            amount = round(max(2.0, random.gauss(sender["avg_tx_amount"], sender["avg_tx_amount"] * 0.3)), 2)
            receiver = random.choice([u for u in user_ids if u != sender["user_id"]])
            country = sender["country"]
            category = random.choice(MERCHANT_CATEGORIES[:8])
            device = random.choice(devices_of[sender["user_id"]])

        txs.append({
            "tx_id": f"T{tx_counter:05d}",
            "timestamp": ts.isoformat(timespec="seconds"),
            "sender_id": sender["user_id"],
            "receiver_id": receiver,
            "amount": amount,
            "currency": "USD",
            "country": country,
            "device_id": device,
            "merchant_category": category,
            "label": 1 if is_fraud else 0,
        })
        tx_counter += 1

    txs.sort(key=lambda t: t["timestamp"])
    return txs


FRAUD_CASES = [
    ("card_cloning", "large purchase from new device in foreign country",
     "Cardholder's details were skimmed and cloned. Fraudster made a large electronics purchase from a device never seen before, in a country the victim had never transacted from. Amount was 6x the victim's average spend."),
    ("card_cloning", "rapid small purchases followed by large purchase",
     "Cloned card tested with several small transactions under $5 within minutes, then a single large purchase at an electronics retailer. Classic card testing followed by cash-out."),
    ("account_takeover", "password reset then immediate high-value transfer",
     "Attacker gained access via credential stuffing, changed the password, added a new payee and transferred nearly the full balance within 20 minutes, at 3 AM local time."),
    ("account_takeover", "login from new device and new geography",
     "Account accessed from a device and IP geolocation never associated with the user. Attacker changed notification settings before initiating transfers to mule accounts."),
    ("money_mule", "many small incoming transfers then single large outgoing",
     "Account received dozens of small transfers from unrelated senders over two days, then forwarded the aggregate sum to an overseas account. Typical mule layering behaviour."),
    ("money_mule", "dormant account suddenly routing funds",
     "A dormant account with no activity for 8 months suddenly began receiving and immediately forwarding transfers. Device used was shared with three other flagged accounts."),
    ("synthetic_identity", "new account fast ramp-up to credit limit",
     "Account opened with a synthetic identity (real SSN fragment, fake name). Small normal purchases for two weeks to build trust, then maxed out available credit on gift cards."),
    ("synthetic_identity", "multiple accounts sharing one device",
     "Five newly created accounts with different identities all operated from the same physical device. Each account transacted just below reporting thresholds."),
    ("phishing_scam", "victim-initiated transfer to fraudster account",
     "Victim was socially engineered by a fake bank support call and personally authorised a transfer to a 'safe account' controlled by the fraudster. Transfer was 10x the victim's usual amount."),
    ("phishing_scam", "OTP interception and instant drain",
     "Fraudster phished the victim's one-time passcode and drained the account via three consecutive maximum-value transfers within five minutes."),
    ("card_testing", "burst of tiny online transactions",
     "Stolen card numbers validated through a burst of 15 sub-dollar transactions at an online donation page within two minutes, from a single device cycling through many cards."),
    ("refund_fraud", "purchase, refund to different instrument",
     "Fraudster purchased high-value goods and manipulated support into refunding onto a different card. Repeated across several accounts sharing the same device fingerprint."),
    ("crypto_offramp", "large transfer to crypto exchange at odd hours",
     "Compromised account transferred a large sum to a crypto exchange at 2 AM, far exceeding the user's typical spend, immediately after a login from a new device."),
    ("crypto_offramp", "structured transfers below limits to exchange",
     "Series of transfers each just under the daily limit sent to a crypto exchange over consecutive nights, emptying the account while evading per-transaction alerts."),
    ("gift_card_fraud", "bulk gift card purchases after account access",
     "Attacker converted stolen balance into retailer gift cards — several maximum-denomination purchases in a row, a pattern almost never seen in legitimate use."),
    ("velocity_abuse", "many transactions in short window",
     "Account executed 12 transactions in under ten minutes across different merchants, inconsistent with any prior behaviour. Indicates scripted/automated cash-out."),
    ("ring_activity", "cluster of accounts transacting with each other",
     "A cluster of six accounts, several already flagged, transacted almost exclusively with each other and shared two devices. Funds cycled to obscure origin before off-ramp."),
    ("ring_activity", "new account funnelling to flagged receivers",
     "Newly opened account began sending funds exclusively to accounts previously flagged for fraud. Shared device fingerprint with two of the receivers."),
    ("first_party_fraud", "customer disputes own legitimate purchases",
     "Customer made purchases then filed chargebacks claiming non-receipt. Pattern repeated across billing cycles; delivery confirmations contradicted every claim."),
    ("triangulation_fraud", "seller uses stolen cards to fulfil orders",
     "Marketplace seller took orders and fulfilled them using stolen card numbers, pocketing the buyer payments. Detected via mismatched shipping and card billing identities."),
    ("salary_scam", "fake employer overpayment and refund request",
     "Victim received a fraudulent 'salary overpayment' and was pressured to refund the difference to a third account before the original credit bounced."),
    ("romance_scam", "escalating transfers to single overseas beneficiary",
     "Victim sent escalating amounts to a single overseas beneficiary over weeks, each transfer larger than the last, depleting savings. No prior relationship to the receiver."),
    ("invoice_fraud", "supplier bank details changed before payment",
     "Business email compromise: attacker altered a supplier's bank details on a pending invoice. Payment went to an account with no transaction history."),
    ("atm_skimming", "card present withdrawals in two distant cities",
     "Physical card used for ATM withdrawals in two cities 800km apart within one hour — impossible travel indicating a cloned card in parallel use."),
    ("subscription_abuse", "trial abuse across linked accounts",
     "Dozens of trial subscriptions opened from linked accounts sharing payment instruments and devices, each cancelled just before billing."),
    ("insider_collusion", "employee-linked account receiving waived fees",
     "Account linked to an employee device received systematic fee reversals and manual credit adjustments outside policy."),
    ("smurfing", "structured deposits under reporting threshold",
     "Cash deposits structured at just under the reporting threshold across multiple branches on the same day, then consolidated and wired abroad."),
    ("chargeback_fraud", "high-value purchase from flagged receiver network",
     "Purchase routed to a merchant account connected to a known fraud ring; buyer account had prior chargebacks and shared a device with a flagged user."),
    ("impossible_travel", "logins from two continents within an hour",
     "Sessions initiated from IPs on two continents within 40 minutes, followed by a transfer 8x the account average to a first-time receiver."),
    ("dormant_activation", "long-dormant account making max transfers",
     "Account inactive for a year suddenly made three maximum-limit transfers at 4 AM to receivers with no prior relationship, from a newly enrolled device."),
]


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    users = generate_users()
    devices = generate_devices(users)
    txs = generate_transactions(users, devices)
    cases = [
        {"case_id": f"C{i:03d}", "fraud_type": ft, "pattern": pat, "description": desc}
        for i, (ft, pat, desc) in enumerate(FRAUD_CASES, start=1)
    ]

    write_csv(HERE / "users.csv", users, list(users[0].keys()))
    write_csv(HERE / "user_devices.csv", devices, ["user_id", "device_id"])
    write_csv(HERE / "transactions.csv", txs, list(txs[0].keys()))
    write_csv(HERE / "fraud_cases.csv", cases, ["case_id", "fraud_type", "pattern", "description"])

    print(f"users:        {len(users)}")
    print(f"device links: {len(devices)}")
    print(f"transactions: {len(txs)} ({sum(t['label'] for t in txs)} fraud)")
    print(f"fraud cases:  {len(cases)}")


if __name__ == "__main__":
    main()
