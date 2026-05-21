from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import redis
import json

app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 1. Root Endpoint
@app.get("/")
def read_root():
    return {"status": "SixGuard API is online"}

# 2. Security Scan Endpoint
@app.post("/scan")
def scan_payload(payload: dict):
    ip = payload.get("ip")
    # Check blocklist first
    if ip and r.sismember('block_list', ip):
        raise HTTPException(status_code=403, detail="IP Blocked by AI Security")

    # Queue for analysis
    r.rpush('security_queue', json.dumps(payload))
    return {"status": "queued", "message": "Payload is being analyzed"}

# 3. Dashboard Endpoint
@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    blocked_ips = r.smembers('block_list')
    ips_list = "".join([f"<li class='p-2 bg-red-100 border-l-4 border-red-500 my-2 rounded'>{ip}</li>" for ip in blocked_ips])
    
    return f"""
    <html>
        <head>
            <script src="https://cdn.tailwindcss.com"></script>
            <title>SixGuard Dashboard</title>
        </head>
        <body class='bg-gray-100 p-8'>
            <div class='max-w-4xl mx-auto'>
                <h1 class='text-3xl font-bold mb-6 text-gray-800'>SixGuard Security Dashboard</h1>
                <div class='bg-white p-6 rounded shadow'>
                    <h2 class='text-xl font-semibold mb-4'>Blocked IP Addresses</h2>
                    <ul>{ips_list if ips_list else '<li class="text-gray-500">No threats detected yet.</li>'}</ul>
                    <button onclick='location.reload()' class='mt-4 bg-blue-500 text-white px-4 py-2 rounded'>Refresh List</button>
                </div>
            </div>
        </body>
    </html>
    """