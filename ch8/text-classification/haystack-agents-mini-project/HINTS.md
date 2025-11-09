# Exercise Solutions Guide

> **Note**: This file provides hints and guidance for each section. Try to complete each section on your own first before consulting these hints.

## Section 2: EntityExtractor Implementation

### Hint 1: Initializing the NER Model
```python
# Initialize before the class definition
ner_model = NamedEntityExtractor(
    backend="hugging_face",
    model="dslim/bert-base-NER"
)
ner_model.warm_up()
```

### Hint 2: Running NER Extraction
```python
# Inside the run() method
ner_result = ner_model.run(documents=[document])
# The result adds 'named_entities' to document.meta
```

### Hint 3: Processing Entities
```python
# Get named entities from metadata
named_entities = document.meta.get('named_entities', [])

# Loop through and filter
for entity in named_entities:
    if entity.score >= self.confidence_threshold:
        word = content[entity.start:entity.end]
        entities_by_type[entity.entity].add(word)
```

### Hint 4: Storing Results
```python
# Convert sets to lists
document.meta['entities'] = {
    "PER": list(entities_by_type["PER"]),
    "ORG": list(entities_by_type["ORG"]),
    "LOC": list(entities_by_type["LOC"]),
    "MISC": list(entities_by_type["MISC"])
}
```

## Section 3: Classification Pipeline

### Hint 1: Component Initialization
```python
web_search = SearchApiWebSearch(
    top_k=5,
    api_key=Secret.from_env_var("SEARCH_API_KEY"),
    allowed_domains=["https://www.britannica.com/"]
)

link_content = LinkContentFetcher(
    retry_attempts=3,
    timeout=10
)

# ... initialize remaining components
```

### Hint 2: Pipeline Connections
The flow should be:
```
search.links → fetcher.urls
fetcher → htmldocument
htmldocument → cleaner
cleaner → classifier
```

## Section 4: Combined Pipeline

### Key Insight
Connect the classifier output to the entity extractor input:
```python
pipeline.connect("cleaner", "classifier")
pipeline.connect("classifier", "entity_extractor")
```

## Section 5: SuperComponents

### Input/Output Mapping Pattern
```python
SuperComponent(
    pipeline=your_pipeline,
    input_mapping={
        "query": ["search.query"]  # External param → Internal param
    },
    output_mapping={
        "last_component.documents": "documents"  # Internal → External
    }
)
```

### Remember
- Input mapping: Maps external parameters to internal component inputs
- Output mapping: Exposes internal outputs as external outputs
- Use the correct final component name (classifier, entity_extractor, etc.)

## Section 6: Tool Descriptions

### Good Tool Description Template
```
Purpose: [What does this tool do?]
Input: [What parameters does it need?]
Output: [What does it return?]
Use cases: [When should this tool be used?]
Example: [Sample usage scenario]
```

### Classification Tool Example Structure
```
"Use this tool to classify web articles into categories.
Categories: Politics, Sport, Technology, Entertainment, Business
Input: query (string) - topic to search for
Output: Documents with 'labels' in metadata containing category
Use when: User asks to classify articles or categorize content"
```

## Section 7: Agent System Prompt

### Key Elements to Include
1. **Agent Role**: What is the agent's purpose?
2. **Available Tools**: List each tool with brief description
3. **Decision Logic**: When to use each tool
4. **Response Format**: How to present results
5. **Examples**: Sample queries for each tool

### Structure Example
```
You are a [role] assistant with access to [tools].

Available tools:
1. [tool_name]: [when to use]
2. [tool_name]: [when to use]
3. [tool_name]: [when to use]

When a user asks to:
- [scenario] → use [tool]
- [scenario] → use [tool]

Always:
- [guideline 1]
- [guideline 2]
```

## Section 8: Serialization

### Basic Pattern
```python
yaml_content = pipeline.dumps()

with open("pipelines/pipeline_name.yaml", "w") as f:
    f.write(yaml_content)
```

### Verification
```python
# Load and test
test_pipeline = Pipeline.loads(yaml_content)
result = test_pipeline.run(...)
```

## Section 9: Hayhooks Deployment

### Ensure you rebuild the pipelines when you change components to get the latest YAML file

```bash
./build_pipelines.sh

```
### Starting the Server
```bash
hayhooks run --pipelines-dir pipelines/
```

### Testing with Python
```python
response = requests.post(
    "http://localhost:1416/pipelines/pipeline_name",
    json={"search": {"query": "test"}}
)
result = response.json()
```

### Testing with curl
```bash
curl -X POST http://localhost:1416/pipelines/pipeline_name \
  -H "Content-Type: application/json" \
  -d '{"search": {"query": "test"}}'
```

## Common Debugging Scenarios

### Issue: "Component not found"
**Check**: Component names in pipeline.connect() match the names used in add_component()

### Issue: "Output type mismatch"
**Check**: The output type of one component matches the input type of the next

### Issue: "No named_entities in metadata"
**Check**: NER extractor was properly initialized and warm_up() was called

### Issue: "Agent not using correct tool"
**Check**: Tool descriptions are clear and specific about when to use each tool

### Issue: "YAML serialization fails"
**Check**: All components can be serialized (custom components need proper decorators)

