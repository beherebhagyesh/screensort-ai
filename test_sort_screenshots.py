import unittest
from unittest.mock import patch, MagicMock
import sort_screenshots
import time

class TestSortScreenshots(unittest.TestCase):
    
    @patch('sort_screenshots.time.sleep')
    @patch('sort_screenshots.process_files')
    def test_run_continuous_loop(self, mock_process, mock_sleep):
        # We want to verify that run_continuous calls process_files and sleeps
        # We'll throw an exception to break the infinite loop for testing
        mock_sleep.side_effect = InterruptedError("Break loop")
        
        try:
            sort_screenshots.run_continuous(interval=5)
        except InterruptedError:
            pass
            
        # Verify process_files was called
        mock_process.assert_called()
        # Verify sleep was called with correct interval
        mock_sleep.assert_called_with(5)

if __name__ == '__main__':
    unittest.main()
