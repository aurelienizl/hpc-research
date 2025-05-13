#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess
import uuid
import threading
import os

app = Flask(__name__)
SECRET_KEY = "mySecret123"
tasks = {}
# task.status ∈ {initializing, ready, running, finished, error}

def run_command(cmd, workdir, prefix=""):
    proc = subprocess.run(cmd, shell=True, cwd=workdir,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for stream, suffix in (("stdout", "output"), ("stderr", "error")):
        data = getattr(proc, stream).decode("utf-8")
        fname = f"{prefix + '_' if prefix else ''}{suffix}.log"
        with open(os.path.join(workdir, fname), "w") as f:
            f.write(data)
    return proc

def run_init(task_id, pre_cmd, workdir):
    try:
        run_command(pre_cmd, workdir, prefix="pre_cmd_exec")
        tasks[task_id]["status"] = "ready"
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

def run_benchmark(task_id, cmd, workdir):
    try:
        run_command(cmd, workdir)
        tasks[task_id]["status"] = "finished"
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

@app.route("/api/benchmark/init", methods=["POST"])
def init_benchmark():
    data = request.get_json() or {}
    key = data.get("secret_key")
    pre_cmd = data.get("pre_cmd_exec", "") or ""

    if key != SECRET_KEY:
        return jsonify(status="error", message="Invalid key"), 403

    task_id = str(uuid.uuid4())
    task_dir = os.path.join("/tmp", task_id)
    try:
        os.makedirs(task_dir)
    except Exception as e:
        return jsonify(status="error", message=f"Could not create dir: {e}"), 500

    # No pre-cmd → immediate 'ready'
    if not pre_cmd.strip():
        tasks[task_id] = {"status": "ready", "dir": task_dir}
        return jsonify(status="accepted", task_id=task_id), 202

    # Otherwise spawn background init
    tasks[task_id] = {"status": "initializing", "dir": task_dir}
    threading.Thread(target=run_init, args=(task_id, pre_cmd, task_dir)).start()
    return jsonify(status="accepted", task_id=task_id), 202

@app.route("/api/benchmark/launch", methods=["POST"])
def launch_benchmark():
    data = request.get_json() or {}
    key = data.get("secret_key")
    task_id = data.get("task_id")
    cmd = data.get("command")

    if key != SECRET_KEY:
        return jsonify(status="error", message="Invalid key"), 403
    if not task_id or not cmd:
        return jsonify(status="error", message="Missing task_id or command"), 400

    task = tasks.get(task_id)
    if not task:
        return jsonify(status="error", message="Task ID not found"), 404
    if task["status"] != "ready":
        return jsonify(status="error", message=f"Not ready ({task['status']})"), 400

    tasks[task_id].update(status="running", command=cmd)
    threading.Thread(target=run_benchmark, args=(task_id, cmd, task["dir"])).start()
    return jsonify(status="accepted", task_id=task_id), 202

@app.route("/api/benchmark/status/<tid>", methods=["GET"])
def status(tid):
    t = tasks.get(tid)
    if not t:
        return jsonify(status="not found", message="Task ID not found"), 404
    return jsonify(task_id=tid, status=t["status"])

@app.route("/api/benchmark/results/<tid>", methods=["GET"])
def results(tid):
    t = tasks.get(tid)
    if not t:
        return jsonify(status="not found", message="Task ID not found"), 404
    if t["status"] != "finished":
        return jsonify(status="error", message="Benchmark not finished"), 400

    out = []
    for fn in sorted(os.listdir(t["dir"])):
        path = os.path.join(t["dir"], fn)
        if os.path.isfile(path):
            with open(path) as f:
                out.append({"filename": fn, "content": f.read()})
    return jsonify(task_id=tid, status="finished", results=out)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
