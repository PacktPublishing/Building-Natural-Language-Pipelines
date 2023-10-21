import os
import requests
import json
from haystack.preview import component

@component
class HuggingFaceModelQuery:
    
    def __init__(self, api_url:str,  api_key: str, parameters:dict):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"}
        self.parameters = parameters

    def run(self, prompt:str) -> dict:
        """
        Query the model with a prompt and optional parameters.

        :param prompt: A string containing the input prompt for the query.
        :param parameters: Optional dictionary containing additional parameters for the query.
        :return: A dictionary containing the model's response.
        """
        
        data = {
            "inputs": prompt  # directly using the string prompt
        }
        
        
        data['parameters'] = self.parameters
            
        response = requests.post(self.api_url, headers=self.headers, json=data)
        generated_text = [item['generated_text'] for item in response.json()]
        
        if response.status_code == 200:
            return {"replies": generated_text}  # ensuring output is a dict
        else:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")