# Rate Limiter

A small FastAPI server with middleware that allows at most **N requests per user per minute** (default: 5). Requests over the limit get `429 Too Many Requests`.

## Running it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload
```

In a second terminal, send 6 requests as the same user. The 6th one should be blocked:

```bash
for i in {1..6}; do curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-ID: alice" localhost:8000/hello; done
# 200 200 200 200 200 429
```

Run the tests with:

```bash
pytest -v
```

## How it works

- **Identifying users:** the middleware reads the `X-User-ID` header. If it's missing, it falls back to the client's IP address.
- **Counting:** a dictionary maps each user to `[window_start, count]`. The window starts on a user's first request. Each allowed request increments the count until it reaches `LIMIT`, and after that requests are rejected. Once `WINDOW` (60) seconds have passed since `window_start`, the next request starts a fresh window.
- **Middleware:** `@app.middleware("http")` runs before every route, so individual endpoints don't need any rate limiting code.

## Tradeoffs

I chose a **fixed window counter** because it is the simplest approach that meets the requirement, and it only needs two numbers per user.

| Approach | Accuracy | Memory per user | Notes |
|---|---|---|---|
| **Fixed window (this)** | Allows bursts at window edges | O(1) | Simplest |
| Sliding window log | Exact | O(N) timestamps | Never more than N in *any* 60s span |
| Sliding window counter | Close approximation | O(1) | Weights the previous window's count |
| Token bucket | Allows controlled bursts | O(1) | Common in real APIs |

What I gave up by keeping it simple:

- **Burst at window boundaries.** A user can send 5 requests at second 59 of their window and 5 more right after it resets, which is 10 requests in about 2 seconds. A sliding window log would prevent this, at the cost of storing every timestamp.
- **In-memory state.** All counts are lost when the server restarts.
- **Memory grows forever.** Users are never removed from the dictionary. A real version would evict users whose window has expired, or let Redis expire keys automatically.
- **No lock.** This is safe in this app because the middleware is async and `is_allowed` never awaits, so it runs uninterrupted on a single event loop. It would not be safe if called from multiple threads.
- **`time.time()` can jump** if the system clock changes. `time.monotonic()` would be safer.
- **`X-User-ID` can be spoofed.** Anyone can send any user ID. In production the user should come from a verified auth token. Falling back to IP also means users behind the same NAT or proxy share one limit.

## What would change with multiple servers

Right now each server has its own `requests_by_user` dictionary. Behind a load balancer with 3 servers, a user could get up to **3 × N** requests per minute, because each server counts separately.

**Fix: move the counts into a shared store like Redis.**

- Use a key per user per minute, for example `ratelimit:alice:<current_minute>`.
- On each request, `INCR` the key, and `EXPIRE` it after 60 seconds the first time it's created. If the count is over N, reject the request.
- `INCR` is atomic, so two servers can't both let the 5th request through. That replaces the "no lock needed" assumption from the single-server version.
- `EXPIRE` also fixes the memory growth problem, since Redis deletes old keys automatically.

**New problems this creates:**

- **Latency:** every request now makes a network call to Redis.
- **Single point of failure:** if Redis goes down, I need to decide whether to *fail open* (allow all requests and risk overload) or *fail closed* (block all requests and risk an outage).
- **Clock differences:** servers might disagree on the current minute. Using Redis's clock, or keys that expire on their own, avoids this.

Alternatives include sticky sessions (always send a user to the same server, which is simple but breaks when a server goes down) or rate limiting at an API gateway like nginx before requests reach the app.

## AI Use

I used **Claude Code (Claude Opus 5.5)** as a coding assistant. 


**Time spent:** 45 Minutes


