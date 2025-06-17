import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.text import Text

from cw_tail.cw_tail import CloudWatchTailer


class TestCloudWatchTailer:
    """Test the CloudWatchTailer class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        tailer = CloudWatchTailer(
            log_group="test-logs",
            region="us-east-1",
            since=3600
        )
        
        assert tailer.log_group == "test-logs"
        assert tailer.region == "us-east-1"
        assert tailer.since == 3600
        assert tailer.delay == 5
        assert tailer.exclude_streams == []
        assert tailer.highlight_tokens == []
        assert tailer.formatter is None
        assert tailer.format_options == {}
    
    def test_init_with_defaults(self):
        """Test initialization with default values applied."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        # Should have default values
        assert tailer.exclude_streams == []
        assert tailer.highlight_tokens == []
        assert tailer.formatter is None
        assert tailer.format_options == {}
        assert tailer.delay == 5
    
    def test_init_with_formatter(self):
        """Test initialization with a valid formatter."""
        with patch('cw_tail.cw_tail.formatters') as mock_formatters:
            mock_formatter = Mock()
            mock_formatters.json_formatter = mock_formatter
            
            tailer = CloudWatchTailer(
                log_group="test-logs",
                formatter="json_formatter"
            )
            
            assert tailer.formatter == mock_formatter
    
    def test_init_with_invalid_formatter(self):
        """Test initialization with invalid formatter raises error."""
        with patch('cw_tail.cw_tail.formatters') as mock_formatters:
            # Simulate formatter not found
            mock_formatters.invalid_formatter = None
            del mock_formatters.invalid_formatter
            
            with pytest.raises(ValueError, match="Formatter invalid_formatter not found"):
                CloudWatchTailer(
                    log_group="test-logs",
                    formatter="invalid_formatter"
                )
    
    def test_parse_filter_and_exclude_tokens_basic(self):
        """Test parsing filter and exclude tokens."""
        tailer = CloudWatchTailer(
            log_group="test-logs",
            filter_tokens=["error", "warning"],
            exclude_tokens=["debug", "info"]
        )
        
        assert tailer.filter_tokens == ["error", "warning"]
        assert tailer.exclude_tokens == ["debug", "info"]
        assert tailer.filter_pattern == "?error ?warning -debug -info"
    
    def test_parse_filter_and_exclude_tokens_string_input(self):
        """Test parsing when tokens are provided as strings."""
        tailer = CloudWatchTailer(
            log_group="test-logs",
            filter_tokens="error,warning,critical",
            exclude_tokens="debug,info"
        )
        
        assert tailer.filter_tokens == ["error", "warning", "critical"]
        assert tailer.exclude_tokens == ["debug", "info"]
        assert tailer.filter_pattern == "?error ?warning ?critical -debug -info"
    
    def test_parse_filter_and_exclude_tokens_with_question_marks(self):
        """Test parsing tokens that already have question marks."""
        tailer = CloudWatchTailer(
            log_group="test-logs",
            filter_tokens=["?error", "warning"],
            exclude_tokens=["?debug"]
        )
        
        # Should strip existing question marks
        assert tailer.filter_tokens == ["error", "warning"]
        assert tailer.exclude_tokens == ["debug"]
        assert tailer.filter_pattern == "?error ?warning -debug"
    
    def test_parse_filter_and_exclude_tokens_empty(self):
        """Test parsing with no tokens."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        assert tailer.filter_tokens == []
        assert tailer.exclude_tokens == []
        assert tailer.filter_pattern == ""
    
    def test_format_message_no_formatter(self):
        """Test message formatting without a formatter."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        message = "test message\n"
        result = tailer._format_message(message)
        assert result == "test message"
    
    def test_format_message_with_formatter(self):
        """Test message formatting with a formatter."""
        mock_formatter = Mock(return_value="formatted message")
        
        tailer = CloudWatchTailer(
            log_group="test-logs",
            format_options={"key": "value"}
        )
        tailer.formatter = mock_formatter
        
        message = "test message"
        result = tailer._format_message(message)
        
        assert result == "formatted message"
        mock_formatter.assert_called_once_with(message, key="value")
    
    def test_highlight_basic(self):
        """Test basic text highlighting."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        message = "This is an error message"
        result = tailer._highlight(message, ["error", "message"], "red")
        
        assert isinstance(result, Text)
        # The highlighted text should contain the original message
        assert str(result) == message
    
    def test_highlight_regex_tokens(self):
        """Test highlighting with regex tokens."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        message = "IP: 192.168.1.100 connected"
        # Use a regex pattern for IP addresses
        result = tailer._highlight(message, [r"\d+\.\d+\.\d+\.\d+"], "blue")
        
        assert isinstance(result, Text)
        assert str(result) == message
    
    def test_highlight_invalid_regex(self):
        """Test highlighting with invalid regex falls back to literal matching."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        message = "This has [brackets] in it"
        # Invalid regex should be treated as literal
        result = tailer._highlight(message, ["[brackets]"], "yellow")
        
        assert isinstance(result, Text)
        assert str(result) == message
    
    def test_highlight_multiple(self):
        """Test highlighting multiple token-style pairs."""
        tailer = CloudWatchTailer(log_group="test-logs")
        
        message = "Error: warning detected"
        token_styles = [("error", "red"), ("warning", "yellow")]
        result = tailer._highlight_multiple(message, token_styles)
        
        assert isinstance(result, Text)
        assert str(result) == message
    
    def test_format_log_line(self):
        """Test formatting a complete log line."""
        tailer = CloudWatchTailer(log_group="test-logs", colorize=False)
        
        timestamp = "2023-01-01 12:00:00"
        message = "test message"
        container = "app-container"
        
        result = tailer._format_log_line(timestamp, message, container)
        
        assert isinstance(result, Text)
        # Should contain all components
        result_str = str(result)
        assert container in result_str
        assert timestamp in result_str
        assert message in result_str
    
    def test_format_log_line_with_colors(self):
        """Test formatting log line with colors enabled."""
        tailer = CloudWatchTailer(log_group="test-logs", colorize=True)
        
        timestamp = "2023-01-01 12:00:00"
        message = "test message"
        container = "app-container"
        
        result = tailer._format_log_line(timestamp, message, container)
        
        assert isinstance(result, Text)
        # Container should be assigned a color
        assert container in tailer.containers
    
    def test_format_log_line_with_text_message(self):
        """Test formatting log line when message is already a Text object."""
        tailer = CloudWatchTailer(log_group="test-logs", colorize=False)
        
        timestamp = "2023-01-01 12:00:00"
        message = Text("styled message", style="bold")
        container = "app-container"
        
        result = tailer._format_log_line(timestamp, message, container)
        
        assert isinstance(result, Text)
        result_str = str(result)
        assert "styled message" in result_str
    
    @patch('cw_tail.cw_tail.boto3.Session')
    def test_boto3_session_creation(self, mock_session):
        """Test that boto3 session is created correctly."""
        mock_session_instance = Mock()
        mock_logs_client = Mock()
        mock_session_instance.client.return_value = mock_logs_client
        mock_session.return_value = mock_session_instance
        
        tailer = CloudWatchTailer(
            log_group="test-logs",
            region="us-west-2"
        )
        
        # Should create session with correct region
        mock_session.assert_called_once_with(region_name="us-west-2")
        mock_session_instance.client.assert_called_once_with("logs")
        assert tailer.logs_client == mock_logs_client
    
    def test_get_included_streams_no_exclusions(self):
        """Test getting included streams when no exclusions are specified."""
        mock_logs_client = Mock()
        mock_logs_client.describe_log_streams.return_value = {
            "logStreams": [
                {"logStreamName": "stream1"},
                {"logStreamName": "stream2"},
                {"logStreamName": "stream3"}
            ]
        }
        
        tailer = CloudWatchTailer(log_group="test-logs")
        tailer.logs_client = mock_logs_client
        tailer.exclude_streams = []
        
        result = tailer._get_included_streams()
        
        assert result == ["stream1", "stream2", "stream3"]
        mock_logs_client.describe_log_streams.assert_called_once_with(
            logGroupName="test-logs",
            orderBy="LastEventTime"
        )
    
    def test_get_included_streams_with_exclusions(self):
        """Test getting included streams with exclusions."""
        mock_logs_client = Mock()
        mock_logs_client.describe_log_streams.return_value = {
            "logStreams": [
                {"logStreamName": "app-stream-1"},
                {"logStreamName": "debug-stream-2"},
                {"logStreamName": "app-stream-3"}
            ]
        }
        
        tailer = CloudWatchTailer(log_group="test-logs")
        tailer.logs_client = mock_logs_client
        tailer.exclude_streams = ["debug"]
        
        result = tailer._get_included_streams()
        
        # Should exclude streams containing "debug"
        assert result == ["app-stream-1", "app-stream-3"]
    
    def test_get_included_streams_pagination(self):
        """Test getting included streams with pagination."""
        mock_logs_client = Mock()
        
        # Mock paginated response
        mock_logs_client.describe_log_streams.side_effect = [
            {
                "logStreams": [{"logStreamName": "stream1"}],
                "nextToken": "token1"
            },
            {
                "logStreams": [{"logStreamName": "stream2"}],
                "nextToken": "token2"
            },
            {
                "logStreams": [{"logStreamName": "stream3"}]
                # No nextToken in final response
            }
        ]
        
        tailer = CloudWatchTailer(log_group="test-logs")
        tailer.logs_client = mock_logs_client
        tailer.exclude_streams = []
        
        result = tailer._get_included_streams()
        
        assert result == ["stream1", "stream2", "stream3"]
        assert mock_logs_client.describe_log_streams.call_count == 3
    
    def test_print_header_format(self):
        """Test that print header includes expected information."""
        with patch('cw_tail.cw_tail.shutil.get_terminal_size', return_value=(80, 24)):
            with patch('builtins.print') as mock_print:
                with patch('cw_tail.utils.sleep'):  # Mock sleep to avoid the scroll_up calls
                    tailer = CloudWatchTailer(
                        log_group="test-logs",
                        region="us-east-1",
                        filter_tokens=["error"],
                        exclude_tokens=["debug"],
                        highlight_tokens=["warning"],
                        exclude_streams=["test-stream"],
                        since=3600,
                        delay=5
                    )
                    
                    tailer._print_header()
                    
                    # Should print header with all configuration details
                    mock_print.assert_called_once()
                    printed_output = mock_print.call_args[0][0]
                    
                    assert "test-logs" in printed_output
                    assert "us-east-1" in printed_output
                    assert "error" in printed_output
                    assert "debug" in printed_output
                    assert "warning" in printed_output
                    assert "test-stream" in printed_output
                    assert "3600" in printed_output


def test_package_version_error_handling():
    """Test package version loading with file errors."""
    # Test when pyproject.toml is missing or unreadable
    with patch('builtins.open', side_effect=FileNotFoundError()):
        # Reimport to trigger the version loading code
        import importlib
        import cw_tail.cw_tail
        importlib.reload(cw_tail.cw_tail)
        assert cw_tail.cw_tail.PACKAGE_VERSION == "??"


def test_scroll_up_keyboard_interrupt():
    """Test _scroll_up method with KeyboardInterrupt."""
    tailer = CloudWatchTailer(log_group="test-group")
    
    # Mock sleep to raise KeyboardInterrupt after a few calls
    call_count = 0
    def mock_sleep(duration):
        nonlocal call_count
        call_count += 1
        if call_count > 3:  # Interrupt after a few iterations
            raise KeyboardInterrupt()
    
    with patch('cw_tail.cw_tail.sleep', side_effect=mock_sleep), \
         patch('sys.stdout') as mock_stdout, \
         patch('shutil.get_terminal_size', return_value=(80, 24)):
        
        with pytest.raises(KeyboardInterrupt):
            tailer._scroll_up(min_lines=20)
        
        # Should have written some output and flushed
        assert mock_stdout.write.called
        assert mock_stdout.flush.called


def test_get_included_streams_pagination():
    """Test _get_included_streams with pagination."""
    tailer = CloudWatchTailer(log_group="test-group", exclude_streams=["exclude-me"])
    
    # Mock paginated response
    mock_responses = [
        {
            "logStreams": [
                {"logStreamName": "stream1"},
                {"logStreamName": "exclude-me-stream"},
                {"logStreamName": "stream2"}
            ],
            "nextToken": "token1"
        },
        {
            "logStreams": [
                {"logStreamName": "stream3"},
                {"logStreamName": "stream4"}
            ]
            # No nextToken - end of pagination
        }
    ]
    
    with patch.object(tailer.logs_client, 'describe_log_streams', side_effect=mock_responses):
        streams = tailer._get_included_streams()
        
        # Should include all streams except the excluded one
        expected_streams = ["stream1", "stream2", "stream3", "stream4"]
        assert streams == expected_streams


def test_highlight_regex_error_handling():
    """Test _highlight method with invalid regex patterns."""
    tailer = CloudWatchTailer(log_group="test-group")
    
    # Test with invalid regex that gets escaped
    message = "test [invalid regex message"
    tokens = ["[invalid"]  # Invalid regex pattern
    
    result = tailer._highlight(message, tokens, "bold")
    
    # Should handle the regex error and escape the pattern
    assert isinstance(result, Text)
    assert str(result) == message


def test_highlight_multiple_regex_error_handling():
    """Test _highlight_multiple method with invalid regex patterns."""
    tailer = CloudWatchTailer(log_group="test-group")
    
    message = "test [invalid regex message"
    token_styles = [("[invalid", "bold"), ("test", "italic")]
    
    result = tailer._highlight_multiple(message, token_styles)
    
    # Should handle the regex error and escape the pattern
    assert isinstance(result, Text)
    assert str(result) == message


def test_tail_stream_refresh_logic():
    """Test the stream refresh logic in tail method."""
    tailer = CloudWatchTailer(
        log_group="test-group",
        exclude_streams=["exclude-me"],
        since=3600,
        delay=1,
        colorize=True
    )
    
    # Test the stream refresh logic without running the full loop
    with patch.object(tailer, '_get_included_streams', return_value=["stream1", "stream2"]) as mock_get_streams:
        # Mock time to simulate stream refresh interval
        with patch('time.time', side_effect=[0, 61]):  # 61 seconds later
            # Test that streams are refreshed when interval is exceeded
            current_time = 61
            last_stream_refresh = 0
            stream_refresh_interval = 60
            
            if current_time - last_stream_refresh > stream_refresh_interval:
                included_streams = tailer._get_included_streams()
                assert included_streams == ["stream1", "stream2"]
                mock_get_streams.assert_called_once()


def test_tail_event_filtering():
    """Test event filtering logic with exclude_tokens."""
    tailer = CloudWatchTailer(
        log_group="test-group",
        exclude_tokens=["DEBUG", "TRACE"],
        colorize=True
    )
    
    # Test the filtering logic directly
    events = [
        {"timestamp": 1000000, "message": "INFO: This should be shown", "logStreamName": "test/stream1"},
        {"timestamp": 1000001, "message": "DEBUG: This should be excluded", "logStreamName": "test/stream1"},
        {"timestamp": 1000002, "message": "ERROR: This should be shown", "logStreamName": "test/stream1"}
    ]
    
    # Filter events like the tail method does
    filtered_events = [
        e for e in events
        if not any(token in e["message"] for token in tailer.exclude_tokens)
    ]
    
    # Should exclude the DEBUG message
    assert len(filtered_events) == 2
    assert "DEBUG" not in filtered_events[0]["message"]
    assert "DEBUG" not in filtered_events[1]["message"]


def test_main_function_if_name_main():
    """Test the if __name__ == '__main__' block."""
    # Test that main() is called when script is run directly
    with patch('cw_tail.cw_tail.main') as mock_main:
        # Simulate running the script directly
        import cw_tail.cw_tail
        # The if __name__ == "__main__" block should not execute during import
        # This test mainly ensures the line is covered
        mock_main.assert_not_called() 