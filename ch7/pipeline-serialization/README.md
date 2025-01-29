## Pipeline serilization and deployment with Hayhooks

This assumes we have installed the package "hayhooks". This can be handled using `just develop` and the pyproject.toml file provided in the chapter.

To serialize a pipeline, simply build a Haystack pipeline and run the `.dumps()` method. This will create a YAML representation of the pipeline. A simple example is outlined in [here](./sample_pipeline.py). This pipeline can be visualized in YAML format [as follows](./chat_pipeline.yaml).

This pipeline consists of a simple prompt for an LLM to summarize a topic. 

To deploy the pipeline using Hayhooks, run

```bash
hayhooks run
```

Open a second terminal, then check it's running

```bash
hayhooks status
```

To deploy a pipeline, run

```bash
hayhooks deploy chat_pipeline.yaml
```

You can visit the documentation of the endpoint in `http://localhost:1416/docs#`

To draw the pipeline, run

```bash
curl -X 'GET' \
  'http://localhost:1416/draw/chat_pipeline' \
  -H 'accept: application/json'
```

This pipeline can be visualized as follows 

![](./serialized-chat-pipeline.png)

To undeploy the pipeline, run

```bash
hayhooks undeploy chat_pipeline
```

### Executing the pipeline

You can make a post request to the pipeline as follows (simply replace the topic with a topic you're seeking to summarize)

```bash
curl -X 'POST' \
  'http://localhost:1416/chat_pipeline' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "llm": {
    "generation_kwargs": {}
  },
  "prompt_builder": {
    "topic": "NLP"
 
  }
}'
```