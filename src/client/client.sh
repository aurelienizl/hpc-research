#!/bin/bash
# test_all.sh
# Comprehensive tests for the benchmark client API endpoints.
# Requires 'jq' for JSON parsing.

SERVER_URL="http://localhost:5000"
VALID_SECRET="mySecret123"
INVALID_SECRET="wrongSecret"
# Using sysbench for a valid test; adjust as needed.
COMMAND="sysbench cpu run"
# For a long-running test, we use a simple sleep command.
LONG_COMMAND="sleep 10"

# Function: Poll until task is no longer running.
function poll_status() {
    local task_id=$1
    local status="running"
    echo "Polling status for task_id: $task_id ..."
    while [ "$status" == "running" ]; do
        sleep 2
        status_response=$(curl -s "$SERVER_URL/api/benchmark/status/$task_id")
        status=$(echo "$status_response" | jq -r '.status')
        echo "Current status: $status"
        if [ "$status" == "error" ]; then
            echo "Task $task_id ended with error."
            return 1
        fi
    done
    return 0
}

# Test 1: Valid benchmark launch (with pre and post commands), status polling, and results retrieval.
function test_valid() {
    echo "=== Test 1: Valid Launch with pre_cmd_exec and post_cmd_exec ==="
    response=$(curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
      -H "Content-Type: application/json" \
      -d "{\"command\": \"$COMMAND\", \"secret_key\": \"$VALID_SECRET\", \"pre_cmd_exec\": \"echo pre-cmd executed\", \"post_cmd_exec\": \"echo post-cmd executed\"}")
    echo "Launch response: $response"
    task_id=$(echo "$response" | jq -r '.task_id')
    if [ -z "$task_id" ] || [ "$task_id" == "null" ]; then
        echo "Test 1 FAILED: No valid task_id returned."
        return 1
    fi
    echo "Task ID: $task_id"
    
    if ! poll_status "$task_id"; then
        echo "Test 1 FAILED: Task encountered error."
        return 1
    fi

    echo "Benchmark finished. Retrieving results..."
    results=$(curl -s "$SERVER_URL/api/benchmark/results/$task_id")
    echo "Results:"
    echo "$results" | jq .
    echo "=== Test 1 Completed ==="
    echo ""
}

# Test 2: Launch with invalid secret.
function test_invalid_secret() {
    echo "=== Test 2: Invalid Secret ==="
    response=$(curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
      -H "Content-Type: application/json" \
      -d "{\"command\": \"$COMMAND\", \"secret_key\": \"$INVALID_SECRET\"}")
    echo "Response:"
    echo "$response" | jq .
    echo "=== Test 2 Completed ==="
    echo ""
}

# Test 3: Launch with missing command.
function test_missing_command() {
    echo "=== Test 3: Missing Command ==="
    response=$(curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
      -H "Content-Type: application/json" \
      -d "{\"secret_key\": \"$VALID_SECRET\"}")
    echo "Response:"
    echo "$response" | jq .
    echo "=== Test 3 Completed ==="
    echo ""
}

# Test 4: Launch with missing secret key.
function test_missing_secret() {
    echo "=== Test 4: Missing Secret Key ==="
    response=$(curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
      -H "Content-Type: application/json" \
      -d "{\"command\": \"$COMMAND\"}")
    echo "Response:"
    echo "$response" | jq .
    echo "=== Test 4 Completed ==="
    echo ""
}

# Test 5: Query status for a non-existent task.
function test_nonexistent_status() {
    echo "=== Test 5: Non-existent Task Status ==="
    fake_id="non-existent-task-id"
    response=$(curl -s "$SERVER_URL/api/benchmark/status/$fake_id")
    echo "Response:"
    echo "$response" | jq .
    echo "=== Test 5 Completed ==="
    echo ""
}

# Test 6: Query results for a non-existent task.
function test_nonexistent_results() {
    echo "=== Test 6: Non-existent Task Results ==="
    fake_id="non-existent-task-id"
    response=$(curl -s "$SERVER_URL/api/benchmark/results/$fake_id")
    echo "Response:"
    echo "$response" | jq .
    echo "=== Test 6 Completed ==="
    echo ""
}

# Test 7: Retrieve results for a running task (should return error).
function test_running_results() {
    echo "=== Test 7: Results for Running Task ==="
    response=$(curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
      -H "Content-Type: application/json" \
      -d "{\"command\": \"$LONG_COMMAND\", \"secret_key\": \"$VALID_SECRET\"}")
    echo "Launch response: $response"
    task_id=$(echo "$response" | jq -r '.task_id')
    if [ -z "$task_id" ] || [ "$task_id" == "null" ]; then
        echo "Test 7 FAILED: No valid task_id returned."
        return 1
    fi
    echo "Task ID: $task_id"
    
    # Immediately query results; expected to be an error because the task is still running.
    results=$(curl -s "$SERVER_URL/api/benchmark/results/$task_id")
    echo "Immediate Results Response (expected error):"
    echo "$results" | jq .
    
    # Wait for the task to finish.
    echo "Waiting for task to finish..."
    poll_status "$task_id"
    echo "=== Test 7 Completed ==="
    echo ""
}

# Run all tests.
echo "Running all tests..."
test_valid
test_invalid_secret
test_missing_command
test_missing_secret
test_nonexistent_status
test_nonexistent_results
test_running_results
echo "All tests completed."
