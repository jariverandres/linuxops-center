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
import socket
import platform
import shutil
import psutil

@app.get("/server-info")
def server_info():
    total, used, free = shutil.disk_usage("/")

    return {
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "cpu_cores": psutil.cpu_count(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": round((used / total) * 100, 2),
        "disk_total_gb": round(total / (1024**3), 2),
        "disk_free_gb": round(free / (1024**3), 2)
    }
