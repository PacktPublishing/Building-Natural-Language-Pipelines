# Technical requirements

To follow along and successfully implement the concepts discussed in this chapter, you need to set up a proper development environment. The main technical requirement is Python, which will be used to manage the dependencies and run the necessary code for the project. Specifically, you need: 

Python 3.12 or Higher 

The project is designed to work with Python 3.12, so ensure you have this version installed. If not, consider using a tool like pyenv to manage and install the correct Python version. 

## Dependency Management 

We will use just scripts and uv for managing dependencies efficiently. These tools allow us to handle virtual environments and package installation seamlessly. For more information, visit https://github.com/casey/just and https://astral.sh/blog/uv  to perform installation. Installation guide for just can be found here https://github.com/casey/just?tab=readme-ov-file#installation 

It is also suggested to use pyenv to manage Python versions https://github.com/pyenv/pyenv, installation instructions can be found here https://github.com/pyenv/pyenv?tab=readme-ov-file#installation  

You can set Python 3.12 globally as follows: 

```bash
$ pyenv global system 3.12 
```

Virtual Environment: We recommend creating a virtual environment to isolate the project dependencies and avoid conflicts with other Python installations. 

pipx: While optional, using pipx for managing command-line tools like uv can simplify dependency installation and management. 

Docker desktop installed: We will be using a Docker image for Elastic Search to populate our vector database. https://www.docker.com/products/docker-desktop/. 

## Libraries and Packages 

The project requires several Python libraries, which will be installed through the provided justfile. The main libraries include: 

* Haystack for building the Q&A pipeline 
* OpenAI for embedding generation 
* Additional utilities like BeautifulSoup, dotenv, and more for pre-processing and environment management. 
* Bonus: Bytewax for real time processing 

We will add these as part of a `pyproject.toml` file found [here](./pyproject.toml). 

By ensuring these requirements are met, you'll be able to set up a reproducible and scalable environment for the Q&A pipeline project. 