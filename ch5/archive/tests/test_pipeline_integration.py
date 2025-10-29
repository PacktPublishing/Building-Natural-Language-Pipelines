import pytest
from haystack import Pipeline
from textlength import TextLengthCalculator, TextInputComponent, ResultLoggerComponent

def test_pipeline_integration():
    # Construct the pipeline
    pipeline = Pipeline()
    pipeline.add_component(instance=TextInputComponent(), name="TextInput")
    pipeline.add_component(instance=TextLengthCalculator(), name="TextLengthCalc")
    pipeline.add_component(instance=ResultLoggerComponent(), name="ResultLogger")

    pipeline.connect("TextInput.text", "TextLengthCalc.text")
    pipeline.connect("TextLengthCalc.length", "ResultLogger.length")
    pipeline.connect("TextLengthCalc.category", "ResultLogger.category")


    # Execute the pipeline
    output = pipeline.run({})

    # Asserts to verify integration success
    assert "ResultLogger" in output
    assert "log" in output["ResultLogger"]
    assert "Text length:" in output["ResultLogger"]["log"]
    assert "Category:" in output["ResultLogger"]["log"]
