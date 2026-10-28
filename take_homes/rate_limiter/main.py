# Rate limiter: at most N request per user per minute
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

LIMIT = 5 # requests allowed
WINDOW = 60 # per this many seconds

app = FastAPI()
requests_by_user = {} # user_id -> [window_start, count]

def is_allowed(user_id):
    now = time.time()
    window_start, count = requests_by_user.get(user_id, [now, 0])

    # A minute has passed, so start a fresh window
    if now - window_start >= WINDOW: 
        window_start, count = now, 0

    if count >= LIMIT:
        return False

    requests_by_user[user_id] = [window_start, count + 1]
    return True

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    user_id = request.headers.get("X-User-ID") or request.client.host

    if not is_allowed(user_id):
        return JSONResponse({"detail": "Too many requests"}, status_code=429)

    return await call_next(request)

@app.get("/hello")
def hello():
    return {"message": "hello"}
            