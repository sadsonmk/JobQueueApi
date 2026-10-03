# JobQueueApi
A REST API where authenticated users submit background jobs for processing by workers.

# architecture diagram
Client → FastAPI (REST) → PostgreSQL
                ↓
           Redis (job queue + cache)
                ↓
        Worker (arq/Celery) — processes jobs, writes results
                ↓
        Updates job status → Client polls /jobs/{id} or WebSocket