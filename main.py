from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}
from fastapi import FastAPI
from app.routers import crypto, news, signal

app = FastAPI()

app.include_router(crypto.router)
app.include_router(news.router)
app.include_router(signal.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
