# Specification: Production Grade Enhancements & Hardening

## Overview
This track focuses on elevating the Pantheon project from an advanced prototype to a production-grade application. The enhancements aim to secure the API, improve system scalability and response times through asynchronous processing and caching, and establish robust observability for monitoring LLM interactions and system health. The target deployment environment is a single VPS utilizing Docker Compose.

## Functional Requirements
1. **Security & Authentication:**
   - Implement JWT (JSON Web Token) based authentication for the FastAPI backend.
   - Restrict CORS (Cross-Origin Resource Sharing) to specific, allowed origins rather than `*`.
   - Implement API rate limiting to prevent abuse and manage LLM API costs.
2. **Async Queues & Caching (Redis):**
   - Integrate Redis as the primary caching layer for API responses, LLM extractions, and market data to reduce latency and external API calls.
   - Implement an asynchronous task queue (e.g., using Celery or ARQ with Redis) to handle long-running background tasks such as LLM news extraction and daily MMCI scoring, decoupling them from the synchronous HTTP request-response cycle.
3. **Observability & Tracing:**
   - Integrate OpenTelemetry for distributed tracing across FastAPI routes and background tasks.
   - Implement LLM-specific tracing (e.g., using LangSmith or a similar tool) to monitor prompt inputs, token usage, latency, and outputs.
   - Set up Prometheus and Grafana (or integrate with existing tools) for monitoring system metrics, API performance, and background task queue health.

## Non-Functional Requirements
- **Performance:** Caching should significantly reduce the time-to-first-byte (TTFB) for repeated queries.
- **Reliability:** Background tasks must have robust retry mechanisms (building on the existing Tenacity logic) and dead-letter queues for failed jobs.
- **Maintainability:** Code modifications must adhere to the existing Python and project style guides.
- **Deployment:** All new infrastructure components (Redis, worker processes) must be easily deployable via the target Docker Compose setup.

## Acceptance Criteria
- [ ] Users must authenticate via JWT to access protected FastAPI endpoints.
- [ ] CORS policies are properly restricted.
- [ ] Redis is successfully integrated; repeated identical LLM or market data requests are served from the cache.
- [ ] Long-running data ingestion and LLM tasks are executed asynchronously via a task queue without blocking the main API thread.
- [ ] System traces and LLM execution logs are successfully captured and visible in the chosen observability platform.

## Out of Scope
- Complete migration to a Kubernetes (K8s) or managed cloud orchestrator (sticking to Docker Compose).
- Development of new trading strategies or core MMCI logic changes.
- Complex CI/CD pipeline automation (deferred).