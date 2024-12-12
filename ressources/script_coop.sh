#!/bin/bash

# Global variable for n_value
n_value=5000

# Function to submit a task
submit_task() {
  local ps=$1
  local qs=$2
  curl -X POST http://127.0.0.1:5000/submit_custom_task \
       -H "Content-Type: application/json" \
       -d "{ \"ps\": $ps, \"qs\": $qs, \"n_value\": $n_value, \"nb\": 128, \"comp\": false }"
}

# Main loop to run tasks 5 times
for ((i=1; i<=5; i++)); do
  echo "Iteration $i:"
  submit_task 1 1

  echo "---"
done

# Main loop to run tasks 5 times
for ((i=1; i<=5; i++)); do
  echo "Iteration $i:"
  submit_task 1 2
  echo "---"
done

for ((i=1; i<=5; i++)); do
  echo "Iteration $i:"
  submit_task 2 2
  echo "---"
done

for ((i=1; i<=5; i++)); do
  echo "Iteration $i:"
  submit_task 2 4
  echo "---"
done



