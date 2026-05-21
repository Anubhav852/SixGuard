from fastapi import FastAPI
import redis
import json

app = FastAPI()

# Connect to Redis
# If you are using Docker, use host='redis'
# If you are running locally, use host='localhost'
r = redis.Redis(host='localhost', port=6379, db=0)

@app.post("/scan")
def scan_payload(payload: dict):
    """
    Accepts a security event, pushes it to Redis, 
    and returns immediately without waiting for AI analysis.
    """
    # Push the payload to Redis queue named 'security_queue'
    r.rpush('security_queue', json.dumps(payload))
    
    return {
        "status": "queued", 
        "message": "Payload is being analyzed by AI worker"
    }

@app.get("/")
def read_root():
    return {"status": "SixGuard API is online"}