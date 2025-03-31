#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess
import uuid
import threading
import os

app = Flask(__name__)

# In-memory storage for tasks.
tasks = {}
# Secret key for validating benchmark requests.
SECRET_KEY = "mySecret123"

def run_command(command, working_dir, prefix=""):
    """Helper function to run a command and save its output"""
    process = subprocess.run(command, shell=True, cwd=working_dir,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Save stdout and stderr to files
    for stream, suffix in [('stdout', 'output'), ('stderr', 'error')]:
        content = getattr(process, stream).decode('utf-8')
        filename = f"{prefix}{'_' if prefix else ''}{suffix}.log"
        with open(os.path.join(working_dir, filename), "w") as f:
            f.write(content)
    
    return process

def run_benchmark(task_id, command, working_dir, pre_cmd_exec=None, post_cmd_exec=None):
    """
    Launches the benchmark command in a subprocess with the working directory set to working_dir.
    Optionally executes a pre-command before running the benchmark and a post-command afterward.
    Writes stdout and stderr of each step to separate log files in working_dir and updates the task status.
    """
    try:
        # Execute commands in sequence if provided
        if pre_cmd_exec:
            run_command(pre_cmd_exec, working_dir, "pre_cmd_exec")
            
        # Run main benchmark command
        run_command(command, working_dir)
            
        if post_cmd_exec:
            run_command(post_cmd_exec, working_dir, "post_cmd_exec")
        
        tasks[task_id]['status'] = "finished"
        
    except Exception as e:
        tasks[task_id]['status'] = "error"
        tasks[task_id]['error'] = str(e)

@app.route('/api/benchmark/launch', methods=['POST'])
def launch_benchmark():
    """
    Launches a benchmark task.
    Expects a JSON payload with:
      - "command": the command line to execute.
      - "secret_key": the secret for authentication.
      - Optionally, "pre_cmd_exec": a command to execute before the benchmark.
      - Optionally, "post_cmd_exec": a command to execute after the benchmark.
    
    If valid, creates a unique task directory in /tmp, launches the command,
    and returns a generated task_id.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
    
    command = data.get("command")
    secret_key = data.get("secret_key")
    pre_cmd_exec = data.get("pre_cmd_exec")
    post_cmd_exec = data.get("post_cmd_exec")
    
    if not command or not secret_key:
        return jsonify({"status": "error", "message": "Missing command or secret_key"}), 400
    
    if secret_key != SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid key"}), 403
    
    # Generate a random task_id.
    task_id = str(uuid.uuid4())
    
    # Create a directory for this task in /tmp.
    task_dir = os.path.join("/tmp", task_id)
    try:
        os.makedirs(task_dir, exist_ok=False)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to create task directory: {str(e)}"}), 500
    
    # Store task details including optional pre and post commands.
    tasks[task_id] = {
        "status": "running",
        "command": command,
        "dir": task_dir,
        "pre_cmd_exec": pre_cmd_exec,
        "post_cmd_exec": post_cmd_exec
    }
    
    # Launch the benchmark in a separate thread.
    thread = threading.Thread(target=run_benchmark, args=(task_id, command, task_dir, pre_cmd_exec, post_cmd_exec))
    thread.start()
    
    return jsonify({"status": "accepted", "task_id": task_id}), 202

@app.route('/api/benchmark/status/<task_id>', methods=['GET'])
def benchmark_status(task_id):
    """
    Returns the status of a benchmark task.
    Possible statuses:
      - "not found": if the task_id does not exist.
      - "error": if an error occurred.
      - "running": if the benchmark is still executing.
      - "finished": if the benchmark has completed.
    """
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "not found", "message": "Task ID not found"}), 404
    return jsonify({"task_id": task_id, "status": task["status"]})

@app.route('/api/benchmark/results/<task_id>', methods=['GET'])
def benchmark_results(task_id):
    """
    Retrieves benchmark results.
    Returns an array of objects each containing:
      - "filename": the file name.
      - "content": the file content.
    
    If the task is not found or not yet finished, returns an appropriate error.
    """
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "not found", "message": "Task ID not found"}), 404
    if task["status"] != "finished":
        return jsonify({"status": "error", "message": "Benchmark not finished yet"}), 400
    
    task_dir = task["dir"]
    results = []
    try:
        for filename in os.listdir(task_dir):
            file_path = os.path.join(task_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                results.append({"filename": filename, "content": content})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error reading result files: {str(e)}"}), 500
    
    return jsonify({"task_id": task_id, "status": task["status"], "results": results})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
