#!/bin/bash

# -----------------------------------------------------------------------------
# Test Suite for CollectlManager.sh and CollectlInterface.py
# -----------------------------------------------------------------------------

# Paths to the scripts
COLLECTL_MANAGER="./CollectlManager.sh"
COLLECTL_INTERFACE="./CollectlInterface.py"

# Test directories and files
TEST_PID_DIR="/tmp/collectl_pids"
TEST_OUTPUT_DIR="/tmp/collectl_tests"
TEST_OUTPUT_FILE="${TEST_OUTPUT_DIR}/test_output.lexpr"
TEST_ID="test_id"

# Setup test environment
setup_environment() {
    echo "Setting up test environment..."
    rm -rf "$TEST_PID_DIR" "$TEST_OUTPUT_DIR"
    mkdir -p "$TEST_PID_DIR" "$TEST_OUTPUT_DIR"
}

# Cleanup test environment
cleanup_environment() {
    echo "Cleaning up test environment..."
    rm -rf "$TEST_PID_DIR" "$TEST_OUTPUT_DIR"
}

# Test: Install Collectl using CollectlManager.sh
test_collectl_install() {
    echo "Test: CollectlManager.sh - Install"
    bash "$COLLECTL_MANAGER" install || {
        echo "Error: Installation failed."
        exit 1
    }
    command -v collectl &> /dev/null || {
        echo "Error: Collectl binary not found after installation."
        exit 1
    }
    echo "Collectl installation passed."
}

# Test: Start Collectl with CollectlManager.sh
test_collectl_start() {
    echo "Test: CollectlManager.sh - Start"
    bash "$COLLECTL_MANAGER" start -id "$TEST_ID" -o "$TEST_OUTPUT_FILE" || {
        echo "Error: Failed to start Collectl."
        exit 1
    }
    PID_FILE="$TEST_PID_DIR/${TEST_ID}.pid"
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Error: PID file not created."
        exit 1
    fi
    echo "Collectl started successfully."
}

# Test: Check if Collectl is running
test_collectl_running() {
    echo "Test: CollectlManager.sh - Check if running"
    PID_FILE="$TEST_PID_DIR/${TEST_ID}.pid"
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo "Collectl is running with PID $PID."
        else
            echo "Error: Collectl is not running but PID file exists."
            exit 1
        fi
    else
        echo "Error: PID file not found."
        exit 1
    fi
}

# Test: Stop Collectl with CollectlManager.sh
test_collectl_stop() {
    echo "Test: CollectlManager.sh - Stop"
    bash "$COLLECTL_MANAGER" stop -id "$TEST_ID" || {
        echo "Error: Failed to stop Collectl."
        exit 1
    }
    PID_FILE="$TEST_PID_DIR/${TEST_ID}.pid"
    if [[ -f "$PID_FILE" ]]; then
        echo "Error: PID file still exists after stopping Collectl."
        exit 1
    fi
    echo "Collectl stopped successfully."
}

# Test: CollectlInterface.py - Import and Basic Functionality
test_collectl_interface_import() {
    echo "Test: CollectlInterface.py - Import"
    python3 -c "from CollectlInterface import CollectlManager; print('CollectlInterface imported successfully.')" || {
        echo "Error: Failed to import CollectlInterface."
        exit 1
    }
    echo "CollectlInterface imported successfully."
}

# Test: CollectlInterface.py - Start and Stop
test_collectl_interface_start_stop() {
    echo "Test: CollectlInterface.py - Start and Stop"
    python3 - <<EOF
from CollectlInterface import CollectlManager

manager = CollectlManager()
try:
    print("Starting Collectl...")
    manager.start_collectl(id="$TEST_ID", output_file="$TEST_OUTPUT_FILE")
    print("Collectl started.")
    if not manager.is_collectl_running(id="$TEST_ID"):
        raise Exception("Collectl is not running.")
    print("Stopping Collectl...")
    manager.stop_collectl(id="$TEST_ID")
    print("Collectl stopped successfully.")
except Exception as e:
    print(f"Error during CollectlInterface.py test: {e}")
    exit(1)
EOF
    echo "CollectlInterface.py Start and Stop tests passed."
}

# Main Test Execution
run_tests() {
    setup_environment

    test_collectl_install
    test_collectl_start
    test_collectl_running
    test_collectl_stop
    test_collectl_interface_import
    test_collectl_interface_start_stop

    cleanup_environment
    echo "All tests passed."
}

# Run the tests
run_tests
