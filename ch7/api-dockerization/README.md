## Dockerization of indexing and query pipelines 

Redis instance

```bash
gunicorn -b 127.0.0.1:8000 myapp:app -k uvicorn.workers.UvicornWorker
pip-compile requirements.in --output-file requirements.txt
docker run --restart always -p 8000:8000 fastapi-bytewax-app

```

