## Dockerization of indexing and query pipelines 

Redis instance

```bash
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

```bash
python -m bytewax.run ./api-dockerization/indexing_dataflow:flow
```