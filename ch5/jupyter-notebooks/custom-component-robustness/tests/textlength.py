from haystack import component

@component
class TextLengthCalculator():

    @component.output_types(length=int, category=str)
    def run(self, text: str) -> dict:
        length = len(text)
        if length < 50:
            category = 'Short'
        elif length < 100:
            category = 'Medium'
        else:
            category = 'Long'
        
        return {"length": length, "category": category}
    
@component
class TextInputComponent():
    @component.output_types(text=str)
    def run(self) -> dict:
        return {"text": "This is a sample text for integration testing."}

@component
class ResultLoggerComponent():
    @component.output_types(log=str)
    def run(self, length: int, category: str) -> dict:
        log_message = f"Text length: {length}, Category: {category}"
        print(log_message)  # For simplicity, we're just printing. In practice, you might log to a file or system.
        return {"log": log_message}
    
    