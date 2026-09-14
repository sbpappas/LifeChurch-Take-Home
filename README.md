Life Church Take Home Assignment README:

1. **Setup & run instructions**

Run these instructions in the terminal to get this project running on your machine:

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste the provided app key into YOUVERSION_APP_KEY
python run.py                   # serves on http://127.0.0.1:5000
```

Try it:
```bash
curl "http://127.0.0.1:5000/votd?day=195&version=206"
```

Run tests:
```bash
pytest
```


2. **Decisions & Assumptions**

- If the day param was completely omitted from the votd call, I chose the current UTC time (today, now) since that is fairly standard to do in the computing world.
- If version was omitted, I defaulted to version 206 ssince it is in the public domain.
- I chose Flask over FastAPI because I was more familar with it, and I hear Flask is more explicit.
- Any non 200s response from YouVersion (including licensed-version 403s) collapses to a single 502 UPSTREAM_ERROR — the spec only defines 400/502 for this API, so no separate code was added for "access denied" vs. "actually down"

3. **What I'd do next**

- Implement tests for the 'GET /versions' add on. Didn't have time, but I did test it with curl.
- Look into FastAPI instead of Flask. I went with Flask because I've used it before, but some research reveals that FastAPI is quicker, has built in data validation, and has native async support. Some of that is just "nice to have" but I'd definitely check that out if buildng a major, high traffic app like the Bible app.

These last two are more "for fun":

- Allow for using multiple instances behind a load balancer, which would mean in-memory cache would need to move to something shared like a db
- Build an automated notifier that uses this API. I would love to receive a text with the verse of the day at a certain time each day to my phone, maybe about the time I arrive at work.
