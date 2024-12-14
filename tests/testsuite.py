# test_server.py

import unittest
import requests
import uuid
import time

API_HOST = "127.0.0.1"
API_PORT = 5000
BASE_URL = f"http://{API_HOST}:{API_PORT}"

class TestHPLBenchmarkAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Set up resources before any tests are run.
        """
        cls.session = requests.Session()
        cls.task_id = None

    @classmethod
    def tearDownClass(cls):
        """
        Clean up resources after all tests are run.
        """
        cls.session.close()

    def test_1_submit_task_success(self):
        """
        Test submitting a task when no other task is running.
        Expect a successful response with a task_id.
        """
        payload = {
            "ps": 2,
            "qs": 2,
            "n_value": 1000,  # Small N for quick testing
            "nb": 256,
            "comp": False
        }
        response = self.session.post(f"{BASE_URL}/submit_custom_task", json=payload)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}")
        data = response.json()
        self.assertIn("task_id", data, "Response JSON should contain 'task_id'")
        self.task_id = data["task_id"]
        print(f"Submitted task successfully with task_id: {self.task_id}")

    def test_2_submit_task_conflict(self):
        """
        Test submitting a task while another task is already running.
        Expect a 409 Conflict response.
        """
        if not self.task_id:
            self.skipTest("No task_id from previous test to check conflict.")
        
        # Attempt to submit another task
        payload = {
            "ps": 2,
            "qs": 2,
            "n_value": 1000,
            "nb": 256,
            "comp": False
        }
        response = self.session.post(f"{BASE_URL}/submit_custom_task", json=payload)
        self.assertEqual(response.status_code, 409, f"Expected 409 Conflict, got {response.status_code}")
        data = response.json()
        self.assertIn("error", data, "Response JSON should contain 'error'")
        print(f"Conflict correctly raised when submitting a second task: {data['error']}")

    def test_3_task_status(self):
        """
        Test checking the status of the submitted task.
        Expect status to transition from 'Running' to 'Completed'.
        """
        if not self.task_id:
            self.skipTest("No task_id from previous test to check status.")
        
        status = None
        max_retries = 10
        for attempt in range(max_retries):
            response = self.session.get(f"{BASE_URL}/task_status/{self.task_id}")
            self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}")
            data = response.json()
            self.assertIn("status", data, "Response JSON should contain 'status'")
            status = data["status"]
            print(f"Attempt {attempt + 1}: Task status is '{status}'")
            if status == "Completed" or status in ["Configuration Error", "Execution Error"]:
                break
            time.sleep(2)  # Wait before next status check
        else:
            self.fail("Task did not complete within the expected time.")

        self.assertIn(status, ["Completed", "Configuration Error", "Execution Error"],
                      f"Unexpected task status: {status}")

    def test_4_get_results(self):
        """
        Test retrieving the results of the completed task.
        Expect to receive the contents of result files.
        """
        if not self.task_id:
            self.skipTest("No task_id from previous test to retrieve results.")
        
        # First, ensure that the task is completed
        response = self.session.get(f"{BASE_URL}/task_status/{self.task_id}")
        self.assertEqual(response.status_code, 200, f"Expected 200 OK for status check, got {response.status_code}")
        data = response.json()
        status = data.get("status")
        self.assertEqual(status, "Completed", f"Task status should be 'Completed', got '{status}'")

        # Now, retrieve the results
        response = self.session.get(f"{BASE_URL}/get_results/{self.task_id}")
        self.assertEqual(response.status_code, 200, f"Expected 200 OK for get_results, got {response.status_code}")
        data = response.json()
        self.assertIn("results", data, "Response JSON should contain 'results'")
        self.assertIsInstance(data["results"], list, "'results' should be a list")

        # Verify the presence of expected files
        expected_files = ["hpl_custom_4", "collectl.log"]
        filenames = [file["filename"] for file in data["results"]]
        for expected_file in expected_files:
            self.assertTrue(any(expected_file in filename for filename in filenames),
                            f"Expected file '{expected_file}' not found in results.")
        
        # Optionally, verify content (e.g., non-empty)
        for file in data["results"]:
            self.assertTrue(len(file["content"]) > 0, f"File '{file['filename']}' should not be empty.")
            print(f"Retrieved file '{file['filename']}' with {len(file['content'])} characters.")

    def test_5_submit_task_after_completion(self):
        """
        Test submitting a new task after the previous one has completed.
        Expect a successful response.
        """
        if not self.task_id:
            self.skipTest("No task_id from previous test to proceed.")

        # Submit a new task
        payload = {
            "ps": 2,
            "qs": 2,
            "n_value": 1000,  # Small N for quick testing
            "nb": 256,
            "comp": False
        }
        response = self.session.post(f"{BASE_URL}/submit_custom_task", json=payload)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}")
        data = response.json()
        self.assertIn("task_id", data, "Response JSON should contain 'task_id'")
        new_task_id = data["task_id"]
        print(f"Submitted a new task successfully with task_id: {new_task_id}")

        # Clean up by waiting for the new task to complete
        status = None
        max_retries = 10
        for attempt in range(max_retries):
            response = self.session.get(f"{BASE_URL}/task_status/{new_task_id}")
            self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}")
            data = response.json()
            self.assertIn("status", data, "Response JSON should contain 'status'")
            status = data["status"]
            print(f"Attempt {attempt + 1}: New task status is '{status}'")
            if status == "Completed" or status in ["Configuration Error", "Execution Error"]:
                break
            time.sleep(2)  # Wait before next status check
        else:
            self.fail("New task did not complete within the expected time.")

        self.assertIn(status, ["Completed", "Configuration Error", "Execution Error"],
                      f"Unexpected new task status: {status}")

        # Optionally, retrieve results for the new task
        response = self.session.get(f"{BASE_URL}/get_results/{new_task_id}")
        self.assertEqual(response.status_code, 200, f"Expected 200 OK for get_results, got {response.status_code}")
        data = response.json()
        self.assertIn("results", data, "Response JSON should contain 'results'")
        self.assertIsInstance(data["results"], list, "'results' should be a list")
        print(f"Retrieved results for new task_id: {new_task_id}")

if __name__ == '__main__':
    unittest.main()
