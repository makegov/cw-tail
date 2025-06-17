import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from argparse import Namespace

from cw_tail.utils import (
    chunk_list,
    load_config,
    parse_command_line_arguments,
    parse_qs,
    parse_time_string,
)


class TestChunkList:
    """Test the chunk_list utility function."""
    
    def test_chunk_list_basic(self):
        """Test basic chunking functionality."""
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunks = list(chunk_list(lst, 3))
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
        assert chunks == expected
    
    def test_chunk_list_exact_division(self):
        """Test chunking when list length is exactly divisible by chunk size."""
        lst = [1, 2, 3, 4, 5, 6]
        chunks = list(chunk_list(lst, 2))
        expected = [[1, 2], [3, 4], [5, 6]]
        assert chunks == expected
    
    def test_chunk_list_empty(self):
        """Test chunking an empty list."""
        lst = []
        chunks = list(chunk_list(lst, 3))
        assert chunks == []
    
    def test_chunk_list_single_element(self):
        """Test chunking a single element list."""
        lst = [1]
        chunks = list(chunk_list(lst, 3))
        expected = [[1]]
        assert chunks == expected


class TestParseTimeString:
    """Test the parse_time_string utility function."""
    
    def test_parse_hours(self):
        """Test parsing hour strings."""
        assert parse_time_string("1h") == 3600
        assert parse_time_string("2h") == 7200
        assert parse_time_string("24h") == 86400
    
    def test_parse_minutes(self):
        """Test parsing minute strings."""
        assert parse_time_string("1m") == 60
        assert parse_time_string("30m") == 1800
        assert parse_time_string("60m") == 3600
    
    def test_parse_seconds(self):
        """Test parsing second strings."""
        assert parse_time_string("1s") == 1
        assert parse_time_string("30s") == 30
        assert parse_time_string("120s") == 120
    
    def test_parse_case_insensitive(self):
        """Test case insensitive parsing."""
        assert parse_time_string("1H") == 3600
        assert parse_time_string("30M") == 1800
        assert parse_time_string("45S") == 45
    
    def test_parse_invalid_format(self):
        """Test invalid format returns default."""
        assert parse_time_string("invalid") == 3600
        assert parse_time_string("1") == 3600
        assert parse_time_string("h1") == 3600
        assert parse_time_string("1x") == 3600
    
    def test_parse_with_whitespace(self):
        """Test parsing with whitespace."""
        assert parse_time_string(" 1h ") == 3600
        assert parse_time_string("  30m  ") == 1800


class TestParseQs:
    """Test the parse_qs utility function."""
    
    def test_parse_basic(self):
        """Test basic querystring parsing."""
        result = parse_qs("a=1&b=2&c=3")
        expected = {"a": "1", "b": "2", "c": "3"}
        assert result == expected
    
    def test_parse_with_spaces(self):
        """Test parsing with spaces around values."""
        result = parse_qs("a = 1 & b = 2 & c = 3")
        expected = {"a ": " 1", "b ": " 2", "c ": " 3"}
        assert result == expected
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_qs("")
        assert result == {}
    
    def test_parse_single_pair(self):
        """Test parsing single key-value pair."""
        result = parse_qs("key=value")
        assert result == {"key": "value"}
    
    def test_parse_with_equals_in_value(self):
        """Test parsing when value contains equals sign."""
        result = parse_qs("key=value=with=equals")
        assert result == {"key": "value=with=equals"}
    
    def test_parse_skip_invalid_pairs(self):
        """Test that invalid pairs are skipped."""
        result = parse_qs("a=1&invalid&b=2")
        assert result == {"a": "1", "b": "2"}


class TestParseCommandLineArguments:
    """Test the parse_command_line_arguments utility function."""
    
    def test_parse_basic_args(self):
        """Test parsing basic arguments."""
        args = Namespace(
            log_group="test-logs",
            region="us-east-1",
            since="1h",
            colorize=True
        )
        result = parse_command_line_arguments(args)
        expected = {
            "log_group": "test-logs",
            "region": "us-east-1", 
            "since": "1h",
            "colorize": True
        }
        assert result == expected
    
    def test_parse_list_arguments(self):
        """Test parsing list-type arguments."""
        args = Namespace(
            highlight_tokens="error,warning,critical",
            exclude_tokens="debug,info",
            filter_tokens="ERROR,WARN",  # Note: filter_tokens not filter_pattern
            exclude_streams="stream1,stream2"
        )
        result = parse_command_line_arguments(args)
        expected = {
            "highlight_tokens": ["error", "warning", "critical"],
            "exclude_tokens": ["debug", "info"],
            "filter_tokens": ["ERROR", "WARN"],
            "exclude_streams": ["stream1", "stream2"]
        }
        assert result == expected
    
    def test_parse_dict_arguments(self):
        """Test parsing dictionary-type arguments."""
        args = Namespace(
            format_options="key1=value1&key2=value2"
        )
        result = parse_command_line_arguments(args)
        expected = {
            "format_options": {"key1": "value1", "key2": "value2"}
        }
        assert result == expected
    
    def test_parse_none_values_skipped(self):
        """Test that None values are skipped."""
        args = Namespace(
            log_group="test-logs",
            region=None,
            since=None
        )
        result = parse_command_line_arguments(args)
        expected = {"log_group": "test-logs"}
        assert result == expected


class TestLoadConfig:
    """Test the load_config utility function with project-specific support."""
    
    def test_load_config_from_current_directory(self):
        """Test loading config from current directory."""
        config_data = {
            "default": {"region": "us-east-1", "since": "1h"},
            "prod": {"log_group": "prod-logs", "region": "us-west-2"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                result = load_config("prod")
                expected = {
                    "region": "us-west-2",  # prod overrides default
                    "since": "1h",         # inherited from default
                    "log_group": "prod-logs"
                }
                assert result == expected
    
    def test_load_config_from_hidden_file(self):
        """Test loading config from hidden .cw-tail.yml file."""
        config_data = {
            "default": {"region": "us-east-1"},
            "dev": {"log_group": "dev-logs"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".cw-tail.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                result = load_config("dev")
                expected = {
                    "region": "us-east-1",
                    "log_group": "dev-logs"
                }
                assert result == expected
    
    def test_load_config_priority_order(self):
        """Test that config files are loaded in correct priority order."""
        config_data1 = {
            "default": {"region": "us-east-1"},
            "test": {"log_group": "config-yml-logs"}
        }
        config_data2 = {
            "default": {"region": "us-west-1"},
            "test": {"log_group": "cw-tail-yml-logs"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create both config files
            (Path(temp_dir) / "config.yml").write_text(yaml.dump(config_data1))
            (Path(temp_dir) / ".cw-tail.yml").write_text(yaml.dump(config_data2))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                # config.yml should take precedence over .cw-tail.yml
                result = load_config("test")
                assert result["log_group"] == "config-yml-logs"
    
    def test_load_config_default_creation(self):
        """Test that default config is created when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir) / "home"
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)), \
                 patch("cw_tail.utils.Path.home", return_value=home_dir):
                
                result = load_config()
                
                # Should create default config
                config_file = home_dir / ".config" / "cw-tail" / "config.yml"
                assert config_file.exists()
                
                # Should return default config values
                assert result["region"] == "us-east-1"
                assert result["since"] == "1h"
                assert result["colorize"] is True
    
    def test_load_config_default_section(self):
        """Test loading the default section when no config name specified."""
        config_data = {
            "default": {"region": "us-east-1", "since": "2h"},
            "prod": {"log_group": "prod-logs"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                result = load_config()
                expected = {"region": "us-east-1", "since": "2h"}
                assert result == expected
    
    def test_load_config_nonexistent_section(self):
        """Test loading a nonexistent config section."""
        config_data = {
            "default": {"region": "us-east-1"},
            "prod": {"log_group": "prod-logs"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                result = load_config("nonexistent")
                assert result == {}
    
    def test_load_config_invalid_yaml(self):
        """Test handling of invalid YAML content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text("invalid: yaml: content: [")
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                result = load_config()
                assert result == {}
    
    def test_load_config_merge_with_default(self):
        """Test that specified config merges with default section."""
        config_data = {
            "default": {
                "region": "us-east-1",
                "since": "1h",
                "colorize": True
            },
            "prod": {
                "log_group": "prod-logs",
                "region": "us-west-2"  # This should override default
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                result = load_config("prod")
                expected = {
                    "region": "us-west-2",    # overridden
                    "since": "1h",           # inherited
                    "colorize": True,        # inherited
                    "log_group": "prod-logs" # new
                }
                assert result == expected

    def test_load_config_file_read_error(self):
        """Test load_config when there's an error reading the config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            
            # Create a config file
            config_path.write_text("default:\n  region: us-west-2")
            
            # Mock yaml.safe_load to raise an exception
            with patch('cw_tail.utils.yaml.safe_load', side_effect=Exception("YAML parse error")), \
                 patch('builtins.print') as mock_print, \
                 patch('cw_tail.utils.Path.cwd', return_value=Path(temp_dir)):
                
                result = load_config()
                
                # Should return empty dict on error
                assert result == {}
                
                # Should print error message
                mock_print.assert_called()
                error_call = mock_print.call_args_list[0]
                assert "Error loading config file" in str(error_call) 