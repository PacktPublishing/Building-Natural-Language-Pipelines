import os
import requests
import json
from haystack.preview import component

@component
class HuggingFaceModelQuery:
    
    def __init__(self, api_url:str,  api_key: str):
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"}

        
    def run(self, inputs: dict, parameters: dict = None) -> dict:
        """
        Query the model with inputs and optional parameters.

        :param inputs: A dictionary containing the input data for the query.
        :param parameters: Optional dictionary containing additional parameters for the query.
        :return: A dictionary containing the model's response.
        """
        data = {
            "inputs": inputs
        }
        
        if parameters:
            data['parameters'] = parameters
            
        response = requests.post(self.api_url, headers=self.headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

