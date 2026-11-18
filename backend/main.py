from fastapi import FastAPI


app = FastAPI(
    title="Quote-to-Provision Assistant API",
    description="Backend API for the Quote-to-Provision hackathon solution",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "quote-to-provision-backend",
    }