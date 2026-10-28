import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(override=True)  # reads .env; override so stale terminal values don't win

client = MongoClient(
    os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
    serverSelectionTimeoutMS=8000,
)
db = client[os.environ.get("MONGODB_DB", "sixguard")]

events = db.events          # queue + results: one document per scan
blocklist = db.blocklist    # _id = blocked IP
rate_limits = db.rate_limits


def init_indexes():
    events.create_index([("status", 1), ("ts", 1)])
    events.create_index("created_at", expireAfterSeconds=7 * 86400)  # auto-delete old audit logs
    rate_limits.create_index("expire_at", expireAfterSeconds=0)