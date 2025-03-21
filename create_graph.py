from neo4j import GraphDatabase
import numpy as np
from data_loader import load_and_clean_data, detect_outliers
from analysis import compute_guideline_deviation

# ---------------------------
# Neo4j Connection Setup
# ---------------------------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")  # Replace 'password' with your actual Neo4j credentials.
driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

# ---------------------------
# Load and Preprocess Data
# ---------------------------
CSV_PATH = "assets/EURUSD.csv"
df = load_and_clean_data(CSV_PATH)
df = detect_outliers(df)
df = compute_guideline_deviation(df)

# ---------------------------
# 1. Create Trade Nodes
# ---------------------------
def create_trade_node(tx, trade_data):
    """
    Inserts a trade as a node in the Neo4j database.
    """
    query = """
    CREATE (t:Trade {
        trade_id: $trade_id,
        timestamp: $timestamp,
        open_price: $open,
        high_price: $high,
        low_price: $low,
        close_price: $close,
        volume: $volume,
        is_outlier: $is_outlier,
        deviates_guideline: $deviates_guideline
    })
    """
    tx.run(query, **trade_data)


with driver.session() as session:
    for _, row in df.iterrows():
        trade_time = row["Gmt time"].isoformat()
        trade_data = {
            "trade_id": trade_time,
            "timestamp": trade_time,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
            "is_outlier": bool(row["is_outlier"]),
            "deviates_guideline": bool(row["deviates_guideline"])
        }
        session.execute_write(create_trade_node, trade_data)

print("✔ Trade nodes successfully created.")

# ---------------------------
# 2. Create Consecutive Trade Relationships
# ---------------------------
def create_next_relationship(tx, trade_id1, trade_id2):
    """
    Creates a NEXT relationship between two consecutive trades.
    """
    query = """
    MATCH (a:Trade {trade_id: $trade_id1}), (b:Trade {trade_id: $trade_id2})
    CREATE (a)-[:NEXT]->(b)
    """
    tx.run(query, trade_id1=trade_id1, trade_id2=trade_id2)


trade_ids = [row["Gmt time"].isoformat() for _, row in df.sort_values(by="Gmt time").iterrows()]

with driver.session() as session:
    for i in range(len(trade_ids) - 1):
        session.execute_write(create_next_relationship, trade_ids[i], trade_ids[i + 1])

print("✔ Consecutive trade relationships successfully created.")

# ---------------------------
# 3. Create Similarity-Based Relationships
# ---------------------------
SIMILAR_THRESHOLD = 0.0005  # Adjust for similarity sensitivity

def create_similar_relationship(tx, trade_id1, trade_id2, similarity_score):
    """
    Creates a SIMILAR relationship between trades based on price similarity.
    """
    query = """
    MATCH (a:Trade {trade_id: $trade_id1}), (b:Trade {trade_id: $trade_id2})
    CREATE (a)-[:SIMILAR {similarity: $similarity_score}]->(b)
    """
    tx.run(query, trade_id1=trade_id1, trade_id2=trade_id2, similarity_score=similarity_score)


trade_list = [(row["Gmt time"].isoformat(), float(row["Open"])) for _, row in df.iterrows()]

with driver.session() as session:
    for i in range(len(trade_list)):
        for j in range(i + 1, len(trade_list)):
            price_diff = abs(trade_list[i][1] - trade_list[j][1])
            if price_diff < SIMILAR_THRESHOLD:
                similarity_score = 1.0 / (price_diff + 1e-6)  # Avoid division by zero
                session.execute_write(create_similar_relationship, trade_list[i][0], trade_list[j][0], similarity_score)

print("✔ Similarity-based trade relationships successfully created.")

# ---------------------------
# 4. Outlier Connection Graph
# ---------------------------
def create_outlier_links(tx, trade_id1, trade_id2):
    """
    Creates a DIRECT_OUTLIER relationship between two outlier trades.
    """
    query = """
    MATCH (a:Trade {trade_id: $trade_id1}), (b:Trade {trade_id: $trade_id2})
    CREATE (a)-[:DIRECT_OUTLIER]->(b)
    """
    tx.run(query, trade_id1=trade_id1, trade_id2=trade_id2)


outlier_trades = [row["Gmt time"].isoformat() for _, row in df[df["is_outlier"]].iterrows()]

if len(outlier_trades) > 1:
    with driver.session() as session:
        for i in range(len(outlier_trades) - 1):
            session.execute_write(create_outlier_links, outlier_trades[i], outlier_trades[i + 1])
    print("✔ Outlier connection graph created.")

# ---------------------------
# Close Neo4j Connection
# ---------------------------
driver.close()
print("✔ Neo4j connection closed successfully.")
