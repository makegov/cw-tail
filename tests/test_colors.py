import pytest
from rich.text import Text

from cw_tail.utils import color_funcs


class TestColorFuncs:
    """Test the color_funcs utility function."""
    
    def test_color_funcs_returns_dict(self):
        """Test that color_funcs returns a dictionary."""
        colors = color_funcs()
        assert isinstance(colors, dict)
        assert len(colors) > 0
    
    def test_color_funcs_expected_colors(self):
        """Test that expected color functions are present."""
        colors = color_funcs()
        expected_colors = [
            "blue", "cyan", "green", "dark_green", "purple", 
            "red", "white", "yellow", "black", "black_on_yellow"
        ]
        
        for color in expected_colors:
            assert color in colors, f"Color {color} not found in color_funcs"
    
    def test_color_functions_return_text_objects(self):
        """Test that color functions return Text objects."""
        colors = color_funcs()
        
        for color_name, color_func in colors.items():
            result = color_func("test text")
            assert isinstance(result, Text), f"Color function {color_name} should return Text object"
            assert str(result) == "test text", f"Color function {color_name} should preserve text content"
    
    def test_color_functions_are_callable(self):
        """Test that all color functions are callable."""
        colors = color_funcs()
        
        for color_name, color_func in colors.items():
            assert callable(color_func), f"Color function {color_name} should be callable"
    
    def test_color_functions_with_different_inputs(self):
        """Test color functions with various input types."""
        colors = color_funcs()
        red_func = colors["red"]
        
        # Test with string
        result = red_func("hello")
        assert str(result) == "hello"
        
        # Test with empty string
        result = red_func("")
        assert str(result) == ""
        
        # Test with numbers (converted to string)
        result = red_func("123")
        assert str(result) == "123"
    
    def test_color_functions_unique(self):
        """Test that color functions are unique instances."""
        colors = color_funcs()
        
        # Call the same color function twice
        red1 = colors["red"]("text1")
        red2 = colors["red"]("text2")
        
        # Should be different Text objects but same style
        assert red1 is not red2
        assert str(red1) == "text1"
        assert str(red2) == "text2" 