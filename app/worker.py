import redis
import json
import time
from groq import Groq

# Initialize clients
r = redis.Redis(host='localhost', port=6379, db=0)
client = Groq(api_key="YOUR_GROQ_API_KEY")

def process_event(event_data):
    print(f"Analyzing payload: {event_data}")
    # Here is where the AI magic happens
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Analyze this for security threats: {event_data}"}],
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