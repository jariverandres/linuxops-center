from fastapi import FastAPI
import json
from datetime import datetime

app = FastAPI(
    title="LinuxOps Center",
    version="0.1"
)
def write_remediation_log(data):
    logfile = "/opt/linuxops/logs/remediation.log"

    with open(logfile, "a") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": datetime.now().isoformat(),
                    **data
                }
            ) + "\n"
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
import subprocess
import time

CRITICAL_PROCESSES = [
    "systemd",
    "sshd",
    "nginx",
    "uvicorn",
    "python",
    "postgres",
    "mysql",
    "docker"
]

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
import time

@app.get("/memory")
def memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_percent": mem.percent
    }

@app.get("/disk")
def disk_info():
    total, used, free = shutil.disk_usage("/")
    return {
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
        "used_percent": round((used / total) * 100, 2)
    }

@app.get("/uptime")
def uptime_info():
    uptime_seconds = int(time.time() - psutil.boot_time())
    return {
        "uptime_seconds": uptime_seconds,
        "uptime_hours": round(uptime_seconds / 3600, 2)
    }
@app.get("/diagnostics/cpu")
def cpu_diagnostics():
    processes = []

    for proc in psutil.process_iter():
         try:
            proc.cpu_percent()
         except:
            pass

    time.sleep(1)

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "user": info["username"],
                "cpu_percent": info["cpu_percent"],
                "memory_percent": round(info["memory_percent"], 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(
        processes,
        key=lambda x: x["cpu_percent"],
        reverse=True
    )[:10]

    return {
        "status": "ok",
        "message": "Top CPU consuming processes",
        "top_processes": top_processes
    }
import subprocess

@app.post("/actions/process/renice/{pid}")
def renice_process(pid: int):

    try:
        result = subprocess.run(
            ["renice", "+10", "-p", str(pid)],
            capture_output=True,
            text=True
        )

        return {
            "status": "ok",
            "pid": pid,
            "action": "renice",
            "output": result.stdout
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
@app.post("/deploy")
def deploy():

    report = []

    try:

        git_pull = subprocess.run(
            ["git", "-C", "/opt/linuxops/app", "pull"],
            capture_output=True,
            text=True
        )

        report.append({
            "step": "git_pull",
            "output": git_pull.stdout
        })

        restart = subprocess.run(
            ["systemctl", "restart", "linuxops"],
            capture_output=True,
            text=True
        )

        report.append({
            "step": "restart_service",
            "output": restart.stdout
        })

        return {
            "status": "success",
            "report": report
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }
    CRITICAL_PROCESSES = [
    "systemd",
    "sshd",
    "nginx",
    "uvicorn",
    "python3",
    "mysql",
    "postgres",
    "docker",
    "dockerd"
]

@app.post("/playbooks/cpu-high")
def cpu_high_playbook():


    before_cpu = psutil.cpu_percent(interval=2)

    for proc in psutil.process_iter():
        try:
            proc.cpu_percent()
        except:
            pass

    time.sleep(1)

    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
         try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "user": info["username"],
                "cpu_percent": info["cpu_percent"],
                "memory_percent": round(info["memory_percent"], 2)
            })
         except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(
        processes,
        key=lambda x: x["cpu_percent"],
        reverse=True
    )[:5]

    selected_process = None
    action_taken = "none"

    for process in top_processes:
        if process["name"] not in CRITICAL_PROCESSES and process["cpu_percent"] > 0:
            selected_process = process

            result = subprocess.run(
                ["renice", "+10", "-p", str(process["pid"])],
                capture_output=True,
                text=True
            )

            action_taken = {
                "action": "renice",
                "pid": process["pid"],
                "process": process["name"],
                "output": result.stdout,
                "error": result.stderr
            }
            write_remediation_log({
                "playbook": "cpu-high-remediate",
                "action": "renice",
                "pid": process["pid"],
                "process": process["name"]
            })  
            break

    after_cpu = psutil.cpu_percent(interval=2)

    return {
        "status": "completed",
        "playbook": "cpu-high",
        "cpu_before": before_cpu,
        "cpu_after": after_cpu,
        "top_processes": top_processes,
        "selected_process": selected_process,
        "action_taken": action_taken
    }
@app.post("/playbooks/cpu-high/remediate")
def cpu_high_remediate():
    before_cpu = psutil.cpu_percent(interval=2)

    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "user": info["username"],
                "cpu_percent": info.get("cpu_percent") or 0,
                "memory_percent": round(info.get("memory_percent") or 0, 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_processes = sorted(
        processes,
        key=lambda x: x["cpu_percent"],
        reverse=True
    )[:10]

    selected_process = None
    action_result = None

    for process in top_processes:
        process_name = process["name"]

        if process_name not in CRITICAL_PROCESSES and process["cpu_percent"] >= 0:
            selected_process = process

            result = subprocess.run(
                ["renice", "+10", "-p", str(process["pid"])],
                capture_output=True,
                text=True
            )

            action_result = {
                "action": "renice",
                "pid": process["pid"],
                "process": process_name,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            write_remediation_log({
                "playbook": "cpu-high-remediate",
                "action": "renice",
                "pid": process["pid"],
                "process": process_name
            })


            break

    after_cpu = psutil.cpu_percent(interval=2)

    return {
        "status": "completed",
        "playbook": "cpu-high-remediate",
        "cpu_before": before_cpu,
        "cpu_after": after_cpu,
        "top_processes": top_processes,
        "selected_process": selected_process,
        "action_taken": action_result
    }
