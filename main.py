from fastapi import FastAPI

app = FastAPI(
    title="LinuxOps Center",
    version="0.1"
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "name": "LinuxOps Center",
        "version": "0.1"
    }
