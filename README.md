
# JobQueue API

An event-driven background job processing platform built with FastAPI.
Users submit jobs over a REST API; workers process them asynchronously
via Redis (arq) with retries, an audit trail, and real-time status polling.

## Architecture
(ASCII diagram — draw the API → Redis → Worker flow)

## Why these decisions
- **arq over Celery** — async-native, fits the asyncio stack...
- **Job event log** — state vs. history; debuggability...
- **JWT over sessions** — stateless, scales horizontally...
- **timestamptz everywhere** — naive/aware datetime bugs...

## Features
- JWT auth (bcrypt, enumeration-safe errors)
- Async job processing with retries (max 3 attempts)
- Full audit trail per job (job_events)
- Pagination, rate limiting (20 req/min/user), object-level authorization
- 8 passing tests including end-to-end worker integration

## Quickstart
(commands to run API, worker, tests)

## Known limitations / next steps
- Fixed-window rate limiter (sliding window would be more precise)
- No refresh tokens yet
- Worker integration tests use the dev database
- API keys (designed, deferred)