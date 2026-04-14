"""
DATA/generate_data.py
Synthetic AML transaction dataset generator using Faker
Run: python DATA/generate_data.py
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from faker import Faker
import os

fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

CHANNELS = ["ATM", "Online", "Branch", "Mobile", "Wire Transfer", "RTGS", "NEFT", "UPI"]
LOCATIONS = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
    "Dubai", "Singapore", "Cayman Islands", "Panama", "Switzerland",
    "Ahmedabad", "Pune", "Jaipur", "Lucknow"
]
HIGH_RISK_LOCATIONS = ["Cayman Islands", "Panama", "Switzerland", "Dubai"]
HIGH_RISK_CHANNELS = ["Wire Transfer", "RTGS"]


def generate_normal_transaction(account_id: str, base_ts: datetime) -> dict:
    amount = round(random.lognormvariate(9.5, 1.2), 2)  # log-normal distribution
    amount = min(amount, 500000)
    return {
        "transaction_id": fake.uuid4(),
        "account_id": account_id,
        "amount": amount,
        "timestamp": (base_ts + timedelta(seconds=random.randint(0, 86400))).isoformat(),
        "location": random.choice(LOCATIONS[:-4]),  # domestic
        "channel": random.choice(CHANNELS[:-2]),
        "counterparty_account": fake.bban(),
        "transaction_type": random.choice(["debit", "credit"]),
        "currency": "INR",
        "ip_address": fake.ipv4(),
        "device_id": fake.md5()[:12],
        "is_suspicious": 0,
        "fraud_type": "none"
    }


def generate_structuring_transactions(account_id: str, base_ts: datetime) -> list:
    """Structuring: multiple transactions just below reporting threshold (10 lakh)"""
    txns = []
    threshold = 1000000  # 10 lakh INR
    for i in range(random.randint(3, 8)):
        amount = round(random.uniform(threshold * 0.85, threshold * 0.98), 2)
        txn = {
            "transaction_id": fake.uuid4(),
            "account_id": account_id,
            "amount": amount,
            "timestamp": (base_ts + timedelta(hours=i * random.uniform(0.5, 3))).isoformat(),
            "location": random.choice(LOCATIONS),
            "channel": random.choice(CHANNELS),
            "counterparty_account": fake.bban(),
            "transaction_type": "debit",
            "currency": "INR",
            "ip_address": fake.ipv4(),
            "device_id": fake.md5()[:12],
            "is_suspicious": 1,
            "fraud_type": "structuring"
        }
        txns.append(txn)
    return txns


def generate_layering_transaction(account_id: str, base_ts: datetime) -> dict:
    """Layering: high-value international wire transfer to high-risk jurisdiction"""
    return {
        "transaction_id": fake.uuid4(),
        "account_id": account_id,
        "amount": round(random.uniform(500000, 5000000), 2),
        "timestamp": base_ts.isoformat(),
        "location": random.choice(HIGH_RISK_LOCATIONS),
        "channel": random.choice(HIGH_RISK_CHANNELS),
        "counterparty_account": fake.bban(),
        "transaction_type": "debit",
        "currency": random.choice(["USD", "EUR", "CHF", "AED"]),
        "ip_address": fake.ipv4(),
        "device_id": fake.md5()[:12],
        "is_suspicious": 1,
        "fraud_type": "layering"
    }


def generate_smurfing_transactions(account_id: str, base_ts: datetime) -> list:
    """Smurfing: many small deposits from multiple sources then one large withdrawal"""
    txns = []
    # Many small credits
    for i in range(random.randint(10, 20)):
        txn = {
            "transaction_id": fake.uuid4(),
            "account_id": account_id,
            "amount": round(random.uniform(5000, 50000), 2),
            "timestamp": (base_ts + timedelta(minutes=i * random.randint(5, 30))).isoformat(),
            "location": random.choice(LOCATIONS),
            "channel": random.choice(["ATM", "Branch", "Online"]),
            "counterparty_account": fake.bban(),
            "transaction_type": "credit",
            "currency": "INR",
            "ip_address": fake.ipv4(),
            "device_id": fake.md5()[:12],
            "is_suspicious": 1,
            "fraud_type": "smurfing"
        }
        txns.append(txn)
    # One large withdrawal
    txns.append({
        "transaction_id": fake.uuid4(),
        "account_id": account_id,
        "amount": round(sum(t["amount"] for t in txns) * 0.95, 2),
        "timestamp": (base_ts + timedelta(hours=random.uniform(4, 12))).isoformat(),
        "location": random.choice(HIGH_RISK_LOCATIONS),
        "channel": "Wire Transfer",
        "counterparty_account": fake.bban(),
        "transaction_type": "debit",
        "currency": "INR",
        "ip_address": fake.ipv4(),
        "device_id": fake.md5()[:12],
        "is_suspicious": 1,
        "fraud_type": "smurfing"
    })
    return txns


def generate_dataset(n_accounts: int = 300, fraud_ratio: float = 0.04) -> pd.DataFrame:
    all_txns = []
    accounts = [fake.bban()[:10] for _ in range(n_accounts)]
    base_date = datetime(2024, 1, 1)

    for acc in accounts:
        # Each account has 10–50 transactions over a year
        n_txns = random.randint(10, 50)
        for _ in range(n_txns):
            ts = base_date + timedelta(days=random.randint(0, 365))
            all_txns.append(generate_normal_transaction(acc, ts))

    # Inject fraud patterns
    n_fraud_accounts = max(1, int(n_accounts * fraud_ratio))
    fraud_accounts = random.sample(accounts, n_fraud_accounts)

    for acc in fraud_accounts:
        ts = base_date + timedelta(days=random.randint(0, 300))
        fraud_type = random.choice(["structuring", "layering", "smurfing"])
        if fraud_type == "structuring":
            all_txns.extend(generate_structuring_transactions(acc, ts))
        elif fraud_type == "layering":
            all_txns.append(generate_layering_transaction(acc, ts))
        else:
            all_txns.extend(generate_smurfing_transactions(acc, ts))

    df = pd.DataFrame(all_txns)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered features for ML."""
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_high_risk_location"] = df["location"].isin(HIGH_RISK_LOCATIONS).astype(int)
    df["is_high_risk_channel"] = df["channel"].isin(HIGH_RISK_CHANNELS).astype(int)
    df["is_international"] = (df["currency"] != "INR").astype(int)
    df["amount_log"] = np.log1p(df["amount"])
    df["near_threshold"] = ((df["amount"] > 850000) & (df["amount"] < 1000000)).astype(int)
    # Account-level features
    acc_stats = df.groupby("account_id")["amount"].agg(
        acc_mean_amount="mean",
        acc_std_amount="std",
        acc_txn_count="count",
        acc_max_amount="max"
    ).reset_index()
    acc_stats["acc_std_amount"] = acc_stats["acc_std_amount"].fillna(0)
    df = df.merge(acc_stats, on="account_id", how="left")
    df["amount_vs_mean"] = df["amount"] / (df["acc_mean_amount"] + 1)
    df["amount_zscore"] = (df["amount"] - df["acc_mean_amount"]) / (df["acc_std_amount"] + 1)
    return df


if __name__ == "__main__":
    os.makedirs("DATA", exist_ok=True)
    print("Generating synthetic AML dataset...")
    df = generate_dataset(n_accounts=500, fraud_ratio=0.05)
    df = add_features(df)
    print(f"Total transactions: {len(df)}")
    print(f"Suspicious: {df['is_suspicious'].sum()} ({df['is_suspicious'].mean()*100:.2f}%)")
    # Save full dataset
    df.to_csv("DATA/transactions.csv", index=False)
    print("Saved DATA/transactions.csv")
    # Save test subset (10%)
    test_df = df.sample(frac=0.1, random_state=42)
    test_df.to_csv("DATA/transactions_test.csv", index=False)
    print("Saved DATA/transactions_test.csv")
    print("\nColumn summary:")
    print(df.dtypes)
    print("\nClass distribution:")
    print(df["is_suspicious"].value_counts())
