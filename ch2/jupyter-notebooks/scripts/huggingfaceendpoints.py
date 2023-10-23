import os
import requests
import json
from haystack.preview import component
from typing import Any, Dict, List

@component
class InferenceEndpointAPI:
    
    def __init__(self, api_url:str,  api_key: str, parameters:dict):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"}
        self.parameters = parameters

    @component.output_types(replies=List[str])
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
        response_json = response.json()
        
        if response.status_code == 200:
            if isinstance(response_json, list) and isinstance(response_json[0], dict) and 'generated_text' in response_json[0]:
                # if the response is as expected
                generated_text = [item['generated_text'] for item in response_json]
                return {"replies": generated_text}
            else:
                # if the response is not as expected, just return the raw response
                return {"replies": [str(response_json)]}
        else:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")