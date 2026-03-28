# Implementation Plan: Production Grade Enhancements & Hardening

## Phase 1: Security & Authentication Hardening [checkpoint: bb2e69f]
- [x] Task: Implement JWT Authentication Middleware c279821
    - [x] Write unit tests for JWT token generation and validation.
    - [x] Create `pantheon/auth/jwt_handler.py` with encoding/decoding logic.
    - [x] Create FastAPI dependency (`Depends`) to secure endpoints.

- [x] Task: Configure CORS and API Rate Limiting 097f592
    - [x] Write tests for rate limiting logic.
    - [x] Update `pantheon/api/main.py` to restrict `allow_origins`.
    - [x] Implement a basic sliding window or token bucket rate limiter in memory (to be replaced by Redis later).

- [x] Task: Conductor - User Manual Verification 'Phase 1: Security & Authentication Hardening' (Protocol in workflow.md) bb2e69f

## Phase 2: Redis Caching Layer
- [x] Task: Integrate Redis Connection Manager 35b7bc
    - [x] Update `tech-stack.md` to include Redis.
    - [x] Add `redis` to `requirements.txt`.
    - [x] Create `pantheon/db/redis_client.py` for connection pooling.

- [x] Task: Implement LLM Response and Data Caching
    - [x] Write unit tests for cache decorator/service.
    - [x] Update `pantheon/extractors/` to check Redis before hitting external LLM APIs.
    - [x] Update `pantheon/data/upstox_client.py` to cache high-frequency market data queries.
    
- [x] Task: Migrate API Rate Limiting to Redis
    - [x] Update the rate-limiting middleware created in Phase 1 to utilize the Redis backend.
    - [x] Implement distributed lock for weight updates using Redis.
    
- [x] Task: Conductor - User Manual Verification 'Phase 2: Redis Caching Layer' (Protocol in workflow.md)

**Note:** Redis is REQUIRED for production deployments. Without Redis:
- Weight updates may have race conditions (multiple instances updating simultaneously)
- Rate limiting only works within a single process (not across workers)
- Caching falls back to local SQLite (less efficient)

The system degrades gracefully without Redis but should NOT be deployed to production without it.

## Phase 3: Asynchronous Task Queues
- [ ] Task: Implement Task Queue Framework (e.g., Celery/ARQ)
    - [ ] Update `tech-stack.md` to include the chosen task queue.
    - [ ] Configure the queue worker to use Redis as the message broker.
    - [ ] Create basic worker entry point.
- [ ] Task: Migrate Scheduled Jobs to Task Queue
    - [ ] Refactor `pantheon/scripts/run_analysis.py` and `run_scheduler.py` (APScheduler) to trigger background tasks via the new queue.
    - [ ] Ensure MMCI scoring and news extraction can run asynchronously.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Asynchronous Task Queues' (Protocol in workflow.md)

## Phase 4: Observability & Tracing
- [ ] Task: Implement OpenTelemetry / LangSmith Tracing
    - [ ] Add necessary OpenTelemetry/LangSmith packages to `requirements.txt`.
    - [ ] Instrument `pantheon/api/main.py` for API route tracing.
    - [ ] Instrument `pantheon/extractors/` to trace LLM calls (tokens, latency, prompts).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Observability & Tracing' (Protocol in workflow.md)

## Phase 5: Containerization (Docker Compose)
- [ ] Task: Create Docker Artifacts
    - [ ] Create `Dockerfile` for the FastAPI backend and worker processes.
    - [ ] Create `docker-compose.yml` defining services: `api`, `worker`, `redis`, and optionally `db` (Postgres).
- [ ] Task: Environment Configuration Updates
    - [ ] Update `.env.example` to reflect new required variables (Redis URL, JWT Secret, Tracing Keys).
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Containerization' (Protocol in workflow.md)