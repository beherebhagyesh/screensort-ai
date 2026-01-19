import unittest
import subprocess
import os
import time
import signal

class TestStartupScript(unittest.TestCase):
    def setUp(self):
        self.script_name = "sort_screenshots.py"
        self.startup_script = "./start_bg_service.sh"
        # Ensure cleanup before start
        subprocess.run(["pkill", "-f", self.script_name])
        time.sleep(1)

    def tearDown(self):
        # Cleanup
        subprocess.run(["pkill", "-f", self.script_name])

    def test_startup_script(self):
        # 1. Run startup script
        result = subprocess.run([self.startup_script], capture_output=True, text=True)
        # print(result.stdout)
        
        # 2. Verify running
        # Give it a moment to start
        time.sleep(2)
        
        proc_check = subprocess.run(["pgrep", "-f", f"python3 .*{self.script_name}"], capture_output=True, text=True)
        
        self.assertEqual(proc_check.returncode, 0, "Process did not start")
        pid = int(proc_check.stdout.strip().split('\n')[0])
        # print(f"Process running with PID: {pid}")
        
        # 3. Verify idempotency (running again shouldn't start new one)
        result_2 = subprocess.run([self.startup_script], capture_output=True, text=True)
        # print(result_2.stdout)
        self.assertIn("already running", result_2.stdout)

if __name__ == "__main__":
    unittest.main()
