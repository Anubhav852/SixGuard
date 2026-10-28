import json
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pymongo import ReturnDocument

from app.db import blocklist, events, init_indexes, rate_limits
from app.worker import run_worker

PER_MIN_LIMIT = 15
DAILY_LIMIT = 1000
INDEX = Path(__file__).parent / "static" / "index.html"


@asynccontextmanager
async def lifespan(app):
    init_indexes()
    if os.environ.get("RUN_WORKER", "1") == "1":
        threading.Thread(target=run_worker, daemon=True).start()
    yield


app = FastAPI(title="SixGuard", lifespan=lifespan)


def bump(key: str, ttl_seconds: int) -> int:
    doc = rate_limits.find_one_and_update(
        {"_id": key},
        {"$inc": {"n": 1}, "$setOnInsert": {"expire_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    return doc["n"]


def rate_limit(request: Request):
    visitor = (request.headers.get("x-forwarded-for") or request.client.host).split(",")[0].strip()
    if bump(f"{visitor}:{int(time.time() // 60)}", 90) > PER_MIN_LIMIT:
        raise HTTPException(429, "Rate limit: max 15 scans/minute on the public demo")
    if bump(f"daily:{time.strftime('%Y%m%d')}", 172800) > DAILY_LIMIT:
        raise HTTPException(429, "Daily demo quota reached, try again tomorrow")


def public(d: dict) -> dict:
    d = dict(d)
    d["id"] = d.pop("_id")
    d.pop("created_at", None)
    d.pop("status", None)
    return d


@app.get("/")
def console():
    return FileResponse(INDEX)


@app.get("/dashboard")
def dashboard():
    return FileResponse(INDEX)


@app.get("/health")
def health():
    return {"status": "SixGuard API is online"}


@app.post("/scan")
def scan_payload(payload: dict, request: Request):
    rate_limit(request)
    ip = str(payload.get("ip") or "").strip()[:45]
    body = payload.get("payload")
    text = body if isinstance(body, str) else json.dumps(payload)
    if len(text) > 2000:
        raise HTTPException(413, "Payload too large (max 2000 chars)")
    if ip and blocklist.find_one({"_id": ip}):
        raise HTTPException(403, "IP Blocked by AI Security")
    event_id = uuid.uuid4().hex[:12]
    events.insert_one({"_id": event_id, "ip": ip, "payload": text, "ts": time.time(),
                       "created_at": datetime.now(timezone.utc), "status": "pending"})
    return {"status": "queued", "id": event_id}


@app.get("/api/result/{event_id}")
def result(event_id: str):
    d = events.find_one({"_id": event_id, "status": "done"})
    return public(d) if d else {"status": "pending"}


@app.get("/api/events")
def list_events():
    return [public(d) for d in events.find({"status": "done"}).sort("ts", -1).limit(20)]


@app.get("/api/blocklist")
def list_blocklist():
    return [{"ip": d["_id"], "category": d.get("category", "")} for d in blocklist.find()]


@app.post("/api/reset")
def reset():
    blocklist.delete_many({})
    events.delete_many({})
    return {"status": "reset"}