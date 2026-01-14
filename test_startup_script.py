import subprocess
import os
import time
import signal

def test_startup_script():
    script_name = "sort_screenshots.py"
    startup_script = "./start_bg_service.sh"
    
    # 1. Ensure not running
    subprocess.run(["pkill", "-f", script_name])
    time.sleep(1)
    
    # 2. Run startup script
    result = subprocess.run([startup_script], capture_output=True, text=True)
    print(result.stdout)
    
    # 3. Verify running
    # Give it a moment to start
    time.sleep(2)
    
    proc_check = subprocess.run(["pgrep", "-f", script_name], capture_output=True, text=True)
    
    try:
        assert proc_check.returncode == 0, "Process did not start"
        pid = int(proc_check.stdout.strip().split('\n')[0])
        print(f"Process running with PID: {pid}")
        
        # 4. Verify idempotency (running again shouldn't start new one)
        result_2 = subprocess.run([startup_script], capture_output=True, text=True)
        print(result_2.stdout)
        assert "already running" in result_2.stdout
        
    finally:
        # Cleanup
        subprocess.run(["pkill", "-f", script_name])

if __name__ == "__main__":
    test_startup_script()
