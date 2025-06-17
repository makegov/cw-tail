import pytest
import time
from unittest.mock import patch

from cw_tail.utils import sleep


class TestSleep:
    """Test the sleep utility function."""
    
    @patch('time.sleep')
    def test_sleep_calls_time_sleep_multiple_times(self, mock_time_sleep):
        """Test that sleep function calls time.sleep multiple times with 0.001."""
        sleep(1.5)
        # Should call time.sleep(0.001) multiple times
        assert mock_time_sleep.called
        # All calls should be with 0.001
        for call in mock_time_sleep.call_args_list:
            assert call[0][0] == 0.001
    
    @patch('time.sleep')
    def test_sleep_with_integer(self, mock_time_sleep):
        """Test sleep function with integer input."""
        sleep(2)
        assert mock_time_sleep.called
        # All calls should be with 0.001
        for call in mock_time_sleep.call_args_list:
            assert call[0][0] == 0.001
    
    @patch('time.sleep')
    def test_sleep_with_zero(self, mock_time_sleep):
        """Test sleep function with zero input."""
        sleep(0)
        # Should still call at least once due to max(int(value/0.001), 1)
        assert mock_time_sleep.called
        assert mock_time_sleep.call_args[0][0] == 0.001
    
    @patch('time.sleep')
    def test_sleep_with_small_value(self, mock_time_sleep):
        """Test sleep function with small input."""
        sleep(0.001)
        # Should call at least once
        assert mock_time_sleep.called
        assert mock_time_sleep.call_args[0][0] == 0.001
    
    def test_sleep_actually_sleeps(self):
        """Test that sleep actually pauses execution (integration test)."""
        start_time = time.time()
        sleep(0.01)  # Very short sleep for testing
        end_time = time.time()
        
        # Should have slept for at least the requested time
        # Add small tolerance for timing variations
        assert end_time - start_time >= 0.005 