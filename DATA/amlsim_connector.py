"""
DATA/amlsim_connector.py
Connector and mapper for AMLSim datasets and graph-based synthetic generation.
Supports mapping external IBM AMLSim schema to ProofSAR internal schema.
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from loguru import logger

# Default AMLSim mappings (Source: IBM AMLSim standard output)
AMLSIM_SCHEMA = {
    "TRAN_ID": "transaction_id",
    "SENDER_ACCOUNT_ID": "account_id",
    "RECEIVER_ACCOUNT_ID": "counterparty_account",
    "TX_AMOUNT": "amount",
    "TX_TYPE": "channel",
    "TIMESTAMP": "timestamp",
    "IS_FRAUD": "is_suspicious"
}

def map_amlsim_to_proofsar(amlsim_df: pd.DataFrame) -> pd.DataFrame:
    """Maps a typical AMLSim CSV to ProofSAR internal format."""
    df = amlsim_df.copy()
    
    # Rename known columns
    rename_map = {k: v for k, v in AMLSIM_SCHEMA.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    
    # Fill missing required fields with realistic defaults
    if 'location' not in df.columns:
        df['location'] = random.choice(["Mumbai", "Delhi", "Dubai", "Singapore"])
    if 'currency' not in df.columns:
        df['currency'] = "INR"
    if 'fraud_type' not in df.columns:
        df['fraud_type'] = df.apply(lambda x: "smurfing" if x.get('is_suspicious') else "none", axis=1)
        
    logger.info(f"Mapped AMLSim dataset: {len(df)} rows")
    return df

def generate_network_pattern(n_nodes=10, n_hops=3, base_amount=1000000):
    """
    Simulates a 'Laundering Network' (Graph Pattern).
    Example: 1 Source -> 5 Intermediate Nodes -> 1 Sink.
    """
    txns = []
    source_acc = f"SRC-{random.randint(1000, 9999)}"
    intermediate_accs = [f"INT-{random.randint(10000, 99999)}" for _ in range(n_nodes)]
    sink_acc = f"SNK-{random.randint(1000, 9999)}"
    
    base_ts = datetime.now()
    
    # Layer 1: Source to Intermediate (Layering)
    for i, acc in enumerate(intermediate_accs):
        amount = (base_amount / n_nodes) * random.uniform(0.95, 1.05)
        txns.append({
            "transaction_id": f"L1-{i}-{random.randint(100,999)}",
            "account_id": source_acc,
            "counterparty_account": acc,
            "amount": round(amount, 2),
            "timestamp": (base_ts + timedelta(minutes=i*10)).isoformat(),
            "location": "Cayman Islands",
            "channel": "Wire Transfer",
            "currency": "USD",
            "is_suspicious": 1,
            "fraud_type": "layering_network"
        })
        
    # Layer 2: Intermediate to Sink (Integration)
    for i, acc in enumerate(intermediate_accs):
        amount = (base_amount / n_nodes) * random.uniform(0.9, 0.95) # deducting 'fee'
        txns.append({
            "transaction_id": f"L2-{i}-{random.randint(100,999)}",
            "account_id": acc,
            "counterparty_account": sink_acc,
            "amount": round(amount, 2),
            "timestamp": (base_ts + timedelta(hours=24 + i*5)).isoformat(),
            "location": "Mumbai",
            "channel": "RTGS",
            "currency": "INR",
            "is_suspicious": 1,
            "fraud_type": "integration_network"
        })
        
    return pd.DataFrame(txns)

if __name__ == "__main__":
    # Test generation
    df_network = generate_network_pattern(n_nodes=5, base_amount=5000000)
    print("Simulated Laundering Network Pattern (AMLSim-style):")
    print(df_network[['account_id', 'counterparty_account', 'amount', 'fraud_type']])
