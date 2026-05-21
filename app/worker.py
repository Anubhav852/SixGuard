import redis
import json
import os  # <--- THIS WAS MISSING
from groq import Groq

# Initialize clients
# Added decode_responses=True so Redis returns strings, not bytes
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def process_event(event_data):
    print(f"Analyzing payload: {event_data}")
    # We ask for a strict YES/NO to make the logic easier
    prompt = f"Analyze this payload for malicious intent (e.g. SQL Injection). Reply ONLY with 'YES' if it is malicious, or 'NO' if it is safe. Payload: {event_data}"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

print("Worker started. Waiting for security events...")

while True:
    # Pop an event from the 'security_queue'
    _, message = r.blpop('security_queue')
    data = json.loads(message)
    
    result = process_event(data)
    print(f"Threat Analysis Result: {result}")
    
    # If the AI says YES, block the IP
    if "YES" in result.upper():
        ip = data.get("ip")
        if ip:
            r.sadd('block_list', ip)
            print(f"[!!!] ALERT: Blocked {ip} based on AI decision.")