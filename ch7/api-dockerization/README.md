## Dockerization of indexing and query pipelines 

Redis instance

```bash
gunicorn -b 127.0.0.1:8000 app:app -k uvicorn.workers.UvicornWorker
pip-compile requirements.in --output-file requirements.txt
docker build -t nlp-api .
docker run -p 8000:8000 nlp-api

```

