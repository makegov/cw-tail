import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, Mock
from argparse import ArgumentParser

from cw_tail.cw_tail import main


class TestMain:
    """Integration tests for the main function."""
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('cw_tail.utils.load_config')
    @patch('sys.argv', ['cw-tail', '--log-group', 'test-logs', '--region', 'us-east-1'])
    def test_main_basic_args(self, mock_load_config, mock_tailer_class):
        """Test main function with basic command-line arguments."""
        mock_load_config.return_value = {}
        mock_tailer = Mock()
        mock_tailer_class.return_value = mock_tailer
        
        main()
        
        # Should create tailer with merged config
        mock_tailer_class.assert_called_once()
        call_args = mock_tailer_class.call_args[1]
        assert call_args['log_group'] == 'test-logs'
        assert call_args['region'] == 'us-east-1'
        assert call_args['since'] == 3600  # Default 1h converted to seconds
        
        # Should start tailing
        mock_tailer.tail.assert_called_once()
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('sys.argv', ['cw-tail', '--config', 'prod'])
    def test_main_with_config(self, mock_tailer_class):
        """Test main function loading from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                'default': {'region': 'us-east-1', 'since': '1h'},
                'prod': {
                    'log_group': 'prod-logs',
                    'region': 'us-west-2',
                    'since': '30m',
                    'highlight_tokens': ['error', 'warning']
                }
            }
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                mock_tailer = Mock()
                mock_tailer_class.return_value = mock_tailer
                
                main()
                
                # Should create tailer with config values
                mock_tailer_class.assert_called_once()
                call_args = mock_tailer_class.call_args[1]
                assert call_args['log_group'] == 'prod-logs'
                assert call_args['region'] == 'us-west-2'
                assert call_args['since'] == 1800  # 30m converted to seconds
                assert call_args['highlight_tokens'] == ['error', 'warning']
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('sys.argv', ['cw-tail', '--config', 'dev', '--log-group', 'override-logs', '--since', '2h'])
    def test_main_config_override(self, mock_tailer_class):
        """Test that command-line args override config values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                'default': {'region': 'us-east-1', 'since': '1h'},
                'dev': {
                    'log_group': 'dev-logs',
                    'region': 'us-east-1',
                    'since': '1h'
                }
            }
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                mock_tailer = Mock()
                mock_tailer_class.return_value = mock_tailer
                
                main()
                
                # Should merge config with command-line overrides
                mock_tailer_class.assert_called_once()
                call_args = mock_tailer_class.call_args[1]
                assert call_args['log_group'] == 'override-logs'  # Overridden
                assert call_args['region'] == 'us-east-1'  # From config
                assert call_args['since'] == 7200  # 2h converted to seconds, overridden
    
    @patch('sys.argv', ['cw-tail'])
    def test_main_missing_log_group(self):
        """Test main function exits when log group is missing."""
        with patch('cw_tail.utils.load_config', return_value={}):
            with pytest.raises(SystemExit):
                main()
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('cw_tail.utils.load_config')
    @patch('sys.argv', ['cw-tail', '--log-group', 'test-logs', '--filter-tokens', 'error,warning', 
                        '--exclude-tokens', 'debug,info', '--highlight-tokens', 'critical,fatal'])
    def test_main_list_arguments(self, mock_load_config, mock_tailer_class):
        """Test main function with list-type arguments."""
        mock_load_config.return_value = {}
        mock_tailer = Mock()
        mock_tailer_class.return_value = mock_tailer
        
        main()
        
        mock_tailer_class.assert_called_once()
        call_args = mock_tailer_class.call_args[1]
        assert call_args['filter_tokens'] == ['error', 'warning']
        assert call_args['exclude_tokens'] == ['debug', 'info']
        assert call_args['highlight_tokens'] == ['critical', 'fatal']
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('cw_tail.utils.load_config')
    @patch('sys.argv', ['cw-tail', '--log-group', 'test-logs', '--format-options', 'key1=value1&key2=value2'])
    def test_main_dict_arguments(self, mock_load_config, mock_tailer_class):
        """Test main function with dictionary-type arguments."""
        mock_load_config.return_value = {}
        mock_tailer = Mock()
        mock_tailer_class.return_value = mock_tailer
        
        main()
        
        mock_tailer_class.assert_called_once()
        call_args = mock_tailer_class.call_args[1]
        assert call_args['format_options'] == {'key1': 'value1', 'key2': 'value2'}
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('cw_tail.utils.load_config')
    @patch('sys.argv', ['cw-tail', '--log-group', 'test-logs', '--since', '45m'])
    def test_main_time_string_conversion(self, mock_load_config, mock_tailer_class):
        """Test that time strings are properly converted to seconds."""
        mock_load_config.return_value = {}
        mock_tailer = Mock()
        mock_tailer_class.return_value = mock_tailer
        
        main()
        
        mock_tailer_class.assert_called_once()
        call_args = mock_tailer_class.call_args[1]
        assert call_args['since'] == 2700  # 45 minutes in seconds
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('cw_tail.utils.load_config')
    @patch('sys.argv', ['cw-tail', '--log-group', 'test-logs', '--colorize'])
    def test_main_boolean_flags(self, mock_load_config, mock_tailer_class):
        """Test main function with boolean flags."""
        mock_load_config.return_value = {}
        mock_tailer = Mock()
        mock_tailer_class.return_value = mock_tailer
        
        main()
        
        mock_tailer_class.assert_called_once()
        call_args = mock_tailer_class.call_args[1]
        assert call_args['colorize'] is True
    
    @patch('cw_tail.cw_tail.CloudWatchTailer')
    @patch('cw_tail.utils.load_config')
    @patch('sys.argv', ['cw-tail', '--help'])
    def test_main_help(self, mock_load_config, mock_tailer_class):
        """Test main function displays help."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Help should exit with code 0
        assert exc_info.value.code == 0
    
    def test_argument_parser_setup(self):
        """Test that argument parser is set up correctly."""
        # Import and test the parser directly
        from cw_tail.cw_tail import main
        
        # Use a mock to capture the parser configuration
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_parser_class.return_value = mock_parser
            mock_parser.parse_args.side_effect = SystemExit(0)  # Simulate early exit
            
            try:
                main()
            except SystemExit:
                pass
            
            # Check that parser was configured correctly
            mock_parser_class.assert_called_once()
            
            # Check that all expected arguments were added
            expected_args = [
                '--config', '--log-group', '--region', '--filter-tokens',
                '--highlight-tokens', '--exclude-tokens', '--exclude-streams',
                '--since', '--colorize', '--formatter', '--format-options'
            ]
            
            for expected_arg in expected_args:
                # Check that add_argument was called with this argument
                assert any(
                    call[0][0] == expected_arg 
                    for call in mock_parser.add_argument.call_args_list
                ), f"Expected argument {expected_arg} not found"


class TestMainIntegration:
    """Integration tests with real configuration files."""
    
    def test_main_with_project_config(self):
        """Test main function with a real project configuration file."""
        config_data = {
            "default": {"region": "us-east-1", "since": "1h"},
            "test": {
                "log_group": "test-integration-logs",
                "region": "us-west-2",
                "since": "30m",
                "highlight_tokens": ["error", "warning"]
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yml"
            config_path.write_text(yaml.dump(config_data))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                with patch('sys.argv', ['cw-tail', '--config', 'test']):
                    with patch('cw_tail.cw_tail.CloudWatchTailer') as mock_tailer_class:
                        mock_tailer = Mock()
                        mock_tailer_class.return_value = mock_tailer
                        
                        main()
                        
                        # Should load from project config
                        mock_tailer_class.assert_called_once()
                        call_args = mock_tailer_class.call_args[1]
                        assert call_args['log_group'] == 'test-integration-logs'
                        assert call_args['region'] == 'us-west-2'
                        assert call_args['since'] == 1800  # 30m in seconds
                        assert call_args['highlight_tokens'] == ['error', 'warning']
    
    def test_main_config_priority(self):
        """Test that project config takes priority over global config."""
        project_config = {
            "default": {"region": "us-east-1"},
            "test": {"log_group": "project-logs"}
        }
        
        global_config = {
            "default": {"region": "us-west-1"},
            "test": {"log_group": "global-logs"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project config
            project_path = Path(temp_dir) / "config.yml"
            project_path.write_text(yaml.dump(project_config))
            
            # Create global config directory
            global_dir = Path(temp_dir) / "home" / ".config" / "cw-tail"
            global_dir.mkdir(parents=True)
            global_path = global_dir / "config.yml"
            global_path.write_text(yaml.dump(global_config))
            
            with patch("cw_tail.utils.Path.cwd", return_value=Path(temp_dir)):
                with patch("cw_tail.utils.Path.home", return_value=Path(temp_dir) / "home"):
                    with patch('sys.argv', ['cw-tail', '--config', 'test']):
                        with patch('cw_tail.cw_tail.CloudWatchTailer') as mock_tailer_class:
                            mock_tailer = Mock()
                            mock_tailer_class.return_value = mock_tailer
                            
                            main()
                            
                            # Should use project config (not global)
                            mock_tailer_class.assert_called_once()
                            call_args = mock_tailer_class.call_args[1]
                            assert call_args['log_group'] == 'project-logs'
                            assert call_args['region'] == 'us-east-1' 