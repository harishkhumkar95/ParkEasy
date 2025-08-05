import pandas as pd
import random
import time
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# ✅ Load variables from your .env file
load_dotenv()


# ✅ Get the Mongo URI from the environment
MONGO_URI = os.getenv("MONGO_URI")
# ✅ Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["ParkEasy"]
collection = db["parking_spots"]

# Load your CSV
df = pd.read_csv("Cleaned_Parking_Dublin_V2.csv")

# Loop forever to simulate real-time changes
while True:
    for index, row in df.iterrows():
        record = {
            "spot_id": f"Spot_{index}",
            "location": row["spot_name"],
            "latitude": row["lat"],
            "longitude": row["lon"],
            "status": random.choice(["free", "occupied"]),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Upsert into MongoDB
        collection.update_one(
            {"spot_id": record["spot_id"]},
            {"$set": record},
            upsert=True
        )

    print("✅ MongoDB updated with new spot statuses.")
    time.sleep(10)  # Wait 10 seconds before updating again