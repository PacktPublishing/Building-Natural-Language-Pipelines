# Building RAG Applications with Haystack 2.0
Supplementary material for the book "Building Natural Language Pipelines published by Packt"

Author: Laura Funderburk

## Chapter breakdown

* [ch2](./ch2/) - "Diving deep into Large Language Models (LLMs)"
* [ch3](./ch3/) - "Introduction to Haystack by deepset"
* [ch4](./ch4/) - "Bringing components together: Haystack pipelines for different use cases"
* [ch5](./ch5/) - "Haystack pipeline development with custom components"
* [ch6](./ch6/) - "Setting up a reproducible project: question and answer pipeline"

## Setting up

Set up a virtual environment and install the required packages:

### Set up - for Jupyter notebook usage

If you have completed the following, you may discard this information. Otherwise, as a reminder and to ease installation, you can follow the instructions below.  

Throughout this book we will be using `pip`, `conda` and `just` for package management. We will also create an isolated `conda` environment with Python 3.10.  

We recommend that you install Miniconda and VSCode. We also recommend that you install GitHub (GitBash for Windows or Git for Linux and Mac) to make the process of accessing the material locally easier.   

* Install Miniconda: https://docs.conda.io/projects/miniconda/en/latest/  

* Install VSCode: https://code.visualstudio.com/docs/setup/setup-overview  

To obtain the code and exercises, clone the repository: 

Open VSCode, Click File-> New Window, then Terminal ->New Terminal. Ensure your terminal is of type “Bash” or “Command line”.  

Within the terminal, type each of the commands (a command is identified by the $ sign) below, one by one. Then press enter.  

```bash

$ git clone https://github.com/PacktPublishing/Building-Natural-Language-Pipelines.git 

$ cd building-RAG-applications/ 

$ conda create –-name llm-pipelines python==3.12

$ conda activate llm-pipelines 

$ pip install poetry, haystack-ai, ipykernel, ipytthon
```

Enable the Jupyter Notebook extension on VSCode through the extension marketplace. When you open a notebook, press on ‘Select Kernel’ and click on `llm-pipeline` as our environment. 

### Advanced set up - for chapters 6 and higher

Please refer to the instructions in this [README](./ch6/README.md) for how to set up for advanced chapters



