# JobQueueApi
A REST API where authenticated users submit background jobs (data processing tasks). Jobs are queued, processed asynchronously by workers, and users track status in real time. Includes retries, rate limiting, caching, and full observability

# architecture diagram
Client → FastAPI (REST) → PostgreSQL
                ↓
           Redis (job queue + cache)
                ↓
        Worker (arq/Celery) — processes jobs, writes results
                ↓
        Updates job status → Client polls /jobs/{id} or WebSocket