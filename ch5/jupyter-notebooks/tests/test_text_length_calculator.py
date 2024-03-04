import pytest
from textlength import TextLengthCalculator

# Example of a unit test for the TextLengthCalculator component
def test_text_length_calculator():
    component = TextLengthCalculator()

    # Test with a short text
    result = component.run(text="Hello")
    assert result["length"] == 5
    assert result["category"] == "Short"

    # Test with a medium text
    medium_text = "Hello " * 10  # Replicate "Hello " 10 times
    result = component.run(text=medium_text)
    assert result["length"] == 60
    assert result["category"] == "Medium"

    # Test with a long text
    long_text = "Hello " * 20  # Replicate "Hello " 20 times
    result = component.run(text=long_text)
    assert result["length"] == 120
    assert result["category"] == "Long"

# Example of using parametrized tests to cover a range of inputs
@pytest.mark.parametrize("text, expected_length, expected_category", [
    ("Hi", 2, "Short"),
    ("Hello " * 10, 60, "Medium"),
    ("Hello " * 20, 120, "Long"),
])
def test_text_length_calculator_parametrized(text, expected_length, expected_category):
    component = TextLengthCalculator()
    result = component.run(text=text)
    assert result["length"] == expected_length
    assert result["category"] == expected_category
