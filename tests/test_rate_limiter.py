import pytest
import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from pantheon.auth.dependencies import get_current_user
from pantheon.api.rate_limiter import RateLimiter

# Mock app for testing rate limiter
app = FastAPI()
limiter = RateLimiter(requests_limit=2, window_seconds=5)

@app.get("/test")
async def test_route(limiter_status: bool = Depends(limiter)):
    return {"message": "success"}

client = TestClient(app)

def test_rate_limiter_allows_requests():
    # First 2 requests should pass
    response = client.get("/test")
    assert response.status_code == 200
    
    response = client.get("/test")
    assert response.status_code == 200

def test_rate_limiter_blocks_excessive_requests():
    # Limiter is set to 2 requests per 5 seconds
    # These are the 3rd and 4th requests in a short time
    # (Assuming the previous test ran just before)
    
    # We might need to reset or use a fresh limiter if tests are not isolated
    # But let's assume they run sequentially for now or use a new one
    
    local_app = FastAPI()
    local_limiter = RateLimiter(requests_limit=1, window_seconds=2)
    
    @local_app.get("/local-test")
    async def local_test(limiter_status: bool = Depends(local_limiter)):
        return {"message": "success"}
    
    local_client = TestClient(local_app)
    
    # 1st request passes
    assert local_client.get("/local-test").status_code == 200
    
    # 2nd request fails
    response = local_client.get("/local-test")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests"

def test_rate_limiter_resets_after_window():
    local_app = FastAPI()
    local_limiter = RateLimiter(requests_limit=1, window_seconds=1)
    
    @local_app.get("/reset-test")
    async def reset_test(limiter_status: bool = Depends(local_limiter)):
        return {"message": "success"}
    
    local_client = TestClient(local_app)
    
    assert local_client.get("/reset-test").status_code == 200
    assert local_client.get("/reset-test").status_code == 429
    
    # Wait for window to pass
    time.sleep(1.1)
    
    assert local_client.get("/reset-test").status_code == 200
