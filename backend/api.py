from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Import the enqueue_jobs function from the producer shim
from backend.producer import enqueue_jobs

app = FastAPI(title="Scraper API")


class Target(BaseModel):
    url: str
    requires_js: Optional[bool] = False


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/enqueue")
async def enqueue(targets: List[Target]):
    """Enqueue one or more scraping targets into the Redis queue.

    Example body: [{"url": "https://example.com", "requires_js": false}]
    """
    try:
        # enqueue_jobs expects a list[dict]
        enqueued = await enqueue_jobs([t.dict() for t in targets])
        return {"enqueued": enqueued}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
