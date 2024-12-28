import unittest
import os
import time
from typing import Dict, Any, Optional
import requests
import json

class NodeTester:
    """Base class for node testing operations"""
    
    def __init__(self, host: str = None, port: str = None, api_key: str = None):
        self.host = host or os.getenv('API_HOST', '127.0.0.1')
        self.port = port or os.getenv('API_PORT', '5000')
        
    def _send_request(self, endpoint: str, method: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to an endpoint"""
        url = f"http://{self.host}:{self.port}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url)
            else:  # POST
                response = requests.post(url, json=data)
                
            return {
                "status_code": response.status_code,
                "response": response.json() if response.text else {}
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 500,
                "response": {"error": f"Connection error: {str(e)}"}
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "response": {"message": response.text}
            }

    def send_ping(self) -> bool:
        """Send ping request and verify response"""
        result = self._send_request("ping", "POST")
        return result["status_code"] == 200 and result["response"].get("message") == "pong"

    def submit_task(self, ps: int, qs: int, n_value: int, nb: int, 
                   instances_num: int, expect_success: bool = True) -> Optional[str]:
        """Submit a task and return task_id if successful"""
        data = {
            "ps": ps,
            "qs": qs,
            "n_value": n_value,
            "nb": nb,
            "instances_num": instances_num
        }
        result = self._send_request("submit_custom_task", "POST", data)
        
        if expect_success:
            if result["status_code"] != 200 or "task_id" not in result["response"]:
                return None
            return result["response"]["task_id"]
        else:
            return result["status_code"] != 200

    def check_task_status(self, task_id: str, expected_status: str = None) -> bool:
        """Check task status against expected status"""
        result = self._send_request(f"task_status/{task_id}", "GET")
        
        if result["status_code"] != 200:
            return False
            
        actual_status = result["response"].get("status", "").lower()
        return actual_status == expected_status.lower() if expected_status else True

    def get_results(self, task_id: str, expect_failure: bool = False) -> bool:
        """Get task results and verify expectations"""
        result = self._send_request(f"get_results/{task_id}", "GET")
        
        if expect_failure:
            return result["status_code"] != 200
        return result["status_code"] == 200 and "results" in result["response"]

class TestNode(unittest.TestCase):
    """Test cases for node functionality"""
    
    @classmethod
    def setUpClass(cls):
        cls.node = NodeTester()
        # Ensure node is available before running tests
        retry_count = 3
        for i in range(retry_count):
            if cls.node.send_ping():
                break
            if i < retry_count - 1:
                time.sleep(2)
        else:
            raise Exception("Node is not available")

    def test_ping(self):
        """Test ping endpoint"""
        self.assertTrue(self.node.send_ping(), "Ping should return pong")

    def test_submit_valid_task(self):
        """Test submitting a valid task"""
        task_id = self.node.submit_task(1, 1, 2000, 192, 1)
        self.assertIsNotNone(task_id, "Should get valid task_id")
        
        # Monitor task status
        max_checks = 10
        task_completed = False
        for _ in range(max_checks):
            if self.node.check_task_status(task_id, "completed"):
                task_completed = True
                break
            time.sleep(5)
            
        self.assertTrue(task_completed, "Task should complete successfully")
        self.assertTrue(self.node.get_results(task_id), "Should get valid results")

    def test_submit_invalid_task(self):
        """Test submitting an invalid task"""
        self.assertTrue(
            self.node.submit_task(-1, -1, -1, -1, -1, expect_success=False),
            "Should reject invalid parameters"
        )

    def test_nonexistent_task_status(self):
        """Test getting status of non-existent task"""
        self.assertFalse(
            self.node.check_task_status("nonexistent_task_id"),
            "Should fail for non-existent task"
        )

    def test_nonexistent_task_results(self):
        """Test getting results of non-existent task"""
        self.assertTrue(
            self.node.get_results("nonexistent_task_id", expect_failure=True),
            "Should fail for non-existent task"
        )

def run_tests(host: str = None, port: str = None, api_key: str = None):
    """Run all tests with optional configuration"""
    if host:
        os.environ['API_HOST'] = host
    if port:
        os.environ['API_PORT'] = port
    if api_key:
        os.environ['API_KEY'] = api_key
        
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNode)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == '__main__':
    # Example usage
    run_tests()