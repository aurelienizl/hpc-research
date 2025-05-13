#!/usr/bin/env bash
# test_all.sh
# Comprehensive tests for the two-step init/launch benchmark API.
# Requires 'jq'.

SERVER_URL="http://localhost:5000"
VALID_SECRET="mySecret123"
INVALID_SECRET="wrongSecret"
COMMAND="sysbench cpu run"
# Fake UUID for negative tests
FAKE_ID="00000000-0000-0000-0000-000000000000"

# Poll until status is not 'initializing' or 'running'.
poll_status() {
    local task_id="$1"
    echo -n "Polling status for task_id: $task_id ... "
    while true; do
        resp=$(curl -s "$SERVER_URL/api/benchmark/status/$task_id")
        status=$(echo "$resp" | jq -r '.status')
        # If jq fails, show raw response and exit
        if [[ $? -ne 0 ]]; then
            echo "\nInvalid JSON response: $resp"
            return 1
        fi
        echo -n "$status "
        if [[ "$status" != "initializing" && "$status" != "running" ]]; then
            break
        fi
        sleep 1
    done
    echo
    return 0
}

# Test 1: Valid init + launch + results
test_valid() {
    echo "=== Test 1: Valid init → launch → results ==="
    # INIT
    init_resp=$(curl -s -X POST "$SERVER_URL/api/benchmark/init" \
        -H 'Content-Type: application/json' \
        -d '{"secret_key":"'"$VALID_SECRET"'","pre_cmd_exec":"echo pre-cmd > pre.txt"}')
    echo "Init response: $init_resp"
    task_id=$(echo "$init_resp" | jq -r '.task_id')
    if [[ -z "$task_id" || "$task_id" == "null" ]]; then
        echo "FAIL: No task_id from init"
        return 1
    fi

    # WAIT for init to complete (status → ready)
    if ! poll_status "$task_id"; then
        echo "FAIL: Status polling error"
        return 1
    fi
    status=$(curl -s "$SERVER_URL/api/benchmark/status/$task_id" | jq -r '.status')
    if [[ "$status" != "ready" ]]; then
        echo "FAIL: Expected 'ready', got '$status'"
        return 1
    fi

    # LAUNCH
    launch_resp=$(curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
        -H 'Content-Type: application/json' \
        -d '{"secret_key":"'"$VALID_SECRET"'","task_id":"'"$task_id"'","command":"'"$COMMAND"'"}')
    echo "Launch response: $launch_resp"

    # WAIT for benchmark to finish
    if ! poll_status "$task_id"; then
        echo "FAIL: Status polling error"
        return 1
    fi
    status=$(curl -s "$SERVER_URL/api/benchmark/status/$task_id" | jq -r '.status')
    if [[ "$status" != "finished" ]]; then
        echo "FAIL: Expected 'finished', got '$status'"
        return 1
    fi

    # RESULTS
    results=$(curl -s "$SERVER_URL/api/benchmark/results/$task_id")
    echo "Results:"
    echo "$results" | jq .
    echo "=== Test 1 completed ==="
    echo
    return 0
}

# Test 2: Error scenarios
test_errors() {
    echo "=== Test 2: Error Scenarios ==="

    # Invalid secret on init
    echo "-- Invalid init secret --"
    curl -s -X POST "$SERVER_URL/api/benchmark/init" \
        -H 'Content-Type: application/json' \
        -d '{"secret_key":"'"$INVALID_SECRET"'","pre_cmd_exec":"echo"}' | jq .

    # Launch with missing task_id or command
    echo "-- Launch missing params --"
    curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
        -H 'Content-Type: application/json' \
        -d '{"secret_key":"'"$VALID_SECRET"'"}' | jq .

    # Launch with non-existent task_id
    echo "-- Launch with non-existent task_id --"
    curl -s -X POST "$SERVER_URL/api/benchmark/launch" \
        -H 'Content-Type: application/json' \
        -d '{"secret_key":"'"$VALID_SECRET"'","task_id":"'"$FAKE_ID"'","command":"'"$COMMAND"'"}' | jq .

    # Status for non-existent task
    echo "-- Status non-existent --"
    curl -s "$SERVER_URL/api/benchmark/status/$FAKE_ID" | jq .

    # Results for task not finished
    echo "-- Results before finish --"
    init2=$(curl -s -X POST "$SERVER_URL/api/benchmark/init" \
        -H 'Content-Type: application/json' \
        -d '{"secret_key":"'"$VALID_SECRET"'","pre_cmd_exec":"sleep 3"}')
    tid2=$(echo "$init2" | jq -r '.task_id')
    echo "New task: $tid2"
    curl -s "$SERVER_URL/api/benchmark/results/$tid2" | jq .

    echo "=== Test 2 completed ==="
    echo
}

# Main

echo "Running tests against $SERVER_URL"
if ! command -v jq &> /dev/null; then
    echo "ERROR: 'jq' is required but not installed."
    exit 1
fi

test_valid

test_errors

echo "All tests done."
