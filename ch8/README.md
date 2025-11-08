# Description

Exercises for Chapter 8. "Hands-on projects"

## Setup Instructions

1. **Install [uv](https://github.com/astral-sh/uv):**
	```sh
	pip install uv
	```
2. **Install dependencies:**
	```sh
	uv sync
	```
3. **Activate the virtual environment:**
	```sh
	source .venv/bin/activate
	```
4. **(Recommended) Open this `ch8` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Set up API keys:**

Create a `.env` file in the root directory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
RAPID_API_KEY=your_rapid_api_key_here
SEARCH_API_KEY=your_search_api_key_here
```

To obtain the API key:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)
- Search API key: Sign ut at [Search API](https://www.searchapi.io/)

This notebook uses the Yelp Business Reviews API through RapidAPI:
- Sign up at: https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews
- Store your API key in a `.env` file as `RAPID_API_KEY`


---



## Mini projects

1. [Perform Named Entity Recognition (NER)](./named-entity-recognition/) - this folder contains two sample applications for NER:
    * [Extracting entities from a dataset containing articles - stand alone component](./named-entity-recognition/ner-with-haystack-search-pipeline.ipynb)
    * [Extracting entities after a web search - pipeline with custom component](./named-entity-recognition/ner-with-haystack-search-pipeline.ipynb)
2. [Perform text classification and sentiment analysis](./text-classification/) - this folder contains three sample applications of text classification:
    * [Evaluating Haystack's text classification component on a labelled dataset with categorized news](./text-classification/text-classification.ipynb)
    * [Building a custom component to classify news articles retrieved from web search](./text-classification/classification-with-haystack-search-pipeline.ipynb)
    * [Building a custom component to perform sentiment analysis on Yelp reviews](./text-classification/sentiment_analysis.ipynbß)
3. [Build a chatbot or virtual assistant](./chatbot-virtual-assistant/)
