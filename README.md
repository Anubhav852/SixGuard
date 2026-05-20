# SixGuard

SixGuard is an enterprise-grade, event-driven security monitoring platform.

## System Architecture

The following diagram illustrates the decoupled, asynchronous data flow:

```mermaid
graph LR
    User((Client)) --> API[FastAPI Gateway]
    API --> Redis[(Redis Queue)]
    Redis --> Worker[AI Worker]
    Worker --> Groq[Groq Llama 3.3]
    Worker --> DB[(SQLite DB)]
    DB --> Dash[Dashboard]
```


## Key Technical Features

Asynchronous Processing: Decoupled design ensures AI analysis does not block the user.

Low-Latency AI: Hardware-accelerated Llama 3.3 for sub-second threat detection.

Scalable Queue: Redis-backed workers allow for horizontal scaling.