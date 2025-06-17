import pytest
import json
from cw_tail.formatters import json_formatter


class TestJsonFormatter:
    """Test the json_formatter function."""
    
    def test_format_valid_json(self):
        """Test formatting valid JSON."""
        input_json = '{"level": "info", "message": "test message", "timestamp": 1234567890}'
        result = json_formatter(input_json)
        
        # Should return valid JSON
        parsed = json.loads(result)
        assert parsed["level"] == "info"
        assert parsed["message"] == "test message"
        assert parsed["timestamp"] == 1234567890
    
    def test_format_invalid_json(self):
        """Test formatting invalid JSON returns original string."""
        invalid_json = "not valid json"
        result = json_formatter(invalid_json)
        assert result == invalid_json
    
    def test_format_remove_keys(self):
        """Test formatting with remove_keys option."""
        input_json = '{"level": "info", "logger": "test.logger", "message": "test", "timestamp": 123}'
        result = json_formatter(input_json, remove_keys="logger,timestamp")
        
        parsed = json.loads(result)
        assert "logger" not in parsed
        assert "timestamp" not in parsed
        assert parsed["level"] == "info"
        assert parsed["message"] == "test"
    
    def test_format_remove_keys_with_spaces(self):
        """Test formatting with remove_keys option containing spaces."""
        input_json = '{"level": "info", "logger": "test.logger", "message": "test"}'
        result = json_formatter(input_json, remove_keys=" logger , level ")
        
        parsed = json.loads(result)
        assert "logger" not in parsed
        assert "level" not in parsed
        assert parsed["message"] == "test"
    
    def test_format_key_value_pairs(self):
        """Test formatting with key_value_pairs option."""
        input_json = '{"level": "info", "status": "success", "message": "test", "user": "admin"}'
        result = json_formatter(input_json, key_value_pairs="level:info,status:success")
        
        parsed = json.loads(result)
        assert "level" not in parsed
        assert "status" not in parsed
        assert parsed["message"] == "test"
        assert parsed["user"] == "admin"
    
    def test_format_key_value_pairs_no_match(self):
        """Test formatting with key_value_pairs that don't match."""
        input_json = '{"level": "error", "status": "failed", "message": "test"}'
        result = json_formatter(input_json, key_value_pairs="level:info,status:success")
        
        parsed = json.loads(result)
        # Should keep all keys since values don't match
        assert parsed["level"] == "error"
        assert parsed["status"] == "failed"
        assert parsed["message"] == "test"
    
    def test_format_combined_options(self):
        """Test formatting with both remove_keys and key_value_pairs."""
        input_json = '{"level": "info", "logger": "test", "status": "success", "message": "test", "extra": "data"}'
        result = json_formatter(
            input_json, 
            remove_keys="logger,extra", 
            key_value_pairs="level:info"
        )
        
        parsed = json.loads(result)
        assert "logger" not in parsed
        assert "extra" not in parsed
        assert "level" not in parsed  # removed by key_value_pairs
        assert parsed["status"] == "success"
        assert parsed["message"] == "test"
    
    def test_format_nested_json(self):
        """Test formatting nested JSON objects."""
        input_json = '{"outer": {"inner": {"deep": "value", "logger": "test"}}, "level": "info"}'
        result = json_formatter(input_json, remove_keys="logger")
        
        parsed = json.loads(result)
        assert "logger" not in parsed
        assert parsed["outer"]["inner"]["deep"] == "value"
        # Note: Current implementation doesn't recursively remove nested keys
        # This is expected behavior for this formatter
        assert parsed["level"] == "info"
    
    def test_format_nested_json_with_lists(self):
        """Test formatting nested JSON with lists."""
        input_json = '''
        {
            "items": [
                {"name": "item1", "logger": "test1"},
                {"name": "item2", "logger": "test2"}
            ],
            "logger": "main"
        }
        '''
        result = json_formatter(input_json, remove_keys="logger")
        
        parsed = json.loads(result)
        assert "logger" not in parsed
        assert len(parsed["items"]) == 2
        # Note: Current implementation does NOT recursively remove keys from nested objects in lists
        # Only removes keys from the top level
        assert "logger" in parsed["items"][0]  # logger key remains in nested objects
        assert "logger" in parsed["items"][1]  # logger key remains in nested objects
        assert parsed["items"][0]["name"] == "item1"
        assert parsed["items"][1]["name"] == "item2"
    
    def test_format_clean_string_values(self):
        """Test formatting cleans string values (strips and removes newlines)."""
        input_json = '{"message": "  test message with\\nnewlines  ", "level": "info"}'
        result = json_formatter(input_json)
        
        parsed = json.loads(result)
        assert parsed["message"] == "test message with newlines"
        assert parsed["level"] == "info"
    
    def test_format_sort_option(self):
        """Test formatting with sort option."""
        input_json = '{"z": "last", "a": "first", "m": "middle"}'
        result = json_formatter(input_json, sort=True)
        
        # Check that keys are sorted alphabetically
        result_keys = list(json.loads(result).keys())
        assert result_keys == ["a", "m", "z"]
    
    def test_format_sort_nested_dict(self):
        """Test formatting with sort option on nested dictionaries."""
        input_json = '{"outer": {"z": "last", "a": "first"}, "b": "second"}'
        result = json_formatter(input_json, sort=True)
        
        parsed = json.loads(result)
        # Outer keys should be sorted
        outer_keys = list(parsed.keys())
        assert outer_keys == ["b", "outer"]
        
        # Inner keys should be sorted
        inner_keys = list(parsed["outer"].keys())
        assert inner_keys == ["a", "z"]
    
    def test_format_sort_list(self):
        """Test formatting with sort option on lists."""
        input_json = '{"items": ["zebra", "apple", "banana"]}'
        result = json_formatter(input_json, sort=True)
        
        parsed = json.loads(result)
        # Note: The current implementation doesn't sort lists inside objects when sort=True
        # This is because sort is only applied at the level being processed
        assert parsed["items"] == ["zebra", "apple", "banana"]
    
    def test_format_ensure_ascii_false(self):
        """Test formatting preserves unicode characters."""
        input_json = '{"message": "测试消息", "emoji": "🚀"}'
        result = json_formatter(input_json)
        
        parsed = json.loads(result)
        assert parsed["message"] == "测试消息"
        assert parsed["emoji"] == "🚀"
        
        # Should contain actual unicode characters, not escaped
        assert "测试消息" in result
        assert "🚀" in result
    
    def test_format_non_dict_json(self):
        """Test formatting non-dictionary JSON (arrays, primitives)."""
        # Test with array
        input_json = '["item1", "item2", "item3"]'
        result = json_formatter(input_json)
        assert json.loads(result) == ["item1", "item2", "item3"]
        
        # Test with primitive
        input_json = '"just a string"'
        result = json_formatter(input_json)
        assert json.loads(result) == "just a string"
        
        # Test with number
        input_json = '42'
        result = json_formatter(input_json)
        assert json.loads(result) == 42
    
    def test_format_empty_options(self):
        """Test formatting with empty string options."""
        input_json = '{"level": "info", "message": "test"}'
        result = json_formatter(input_json, remove_keys="", key_value_pairs="")
        
        parsed = json.loads(result)
        assert parsed["level"] == "info"
        assert parsed["message"] == "test"

    def test_json_formatter_sort_non_dict(self):
        """Test json_formatter with sort option on non-dict data."""
        # Test with a top-level list to trigger the else clause in clean_dict
        message = '["zebra", "apple", "banana"]'
        result = json_formatter(message, sort=True)
        
        # The current implementation doesn't actually sort top-level lists
        # This test covers the else clause but tests the actual behavior
        assert result == '["zebra", "apple", "banana"]' 