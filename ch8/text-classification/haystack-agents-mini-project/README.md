# Quick Start Guide

## 🚀 Get Started 

### 1. Setup 

Complete the setup [in the readme](../../README.md#setup-instructions)

### 2. Complete the Exercise (2-4 hours)

Open the Jupyter notebook [classification-ner-agent-exercise.ipynb](./classification-ner-agent-exercise.ipynb)

Build custom componets for NER and text classification from URL websites.

### 3. Refactor your code and populate the `pipelines/`  (2-4 hours)

* Migrate your final custom components to the appropriate folder. For the classification pipeline, they will be migrated to [pipelines/classification/components](./pipelines/classification/components.py)
* Build the pipeline with your custom components and serialize it. For the same example [pipelines/classification/build_pipeline](./pipelines/classification/build_pipeline.py)
* Load the pipeline and get ready to expose as Endpoints with Hayhooks. For the same example [pipelines/classification/pipeline_wrapper](./pipelines/classification/pipeline_wrapper.py)

### 4. Serialize your pipelines

```bash
./build_pipelines.sh
```

[Review it](./build_pipelines.sh)

### 5. Run Hayhooks server (2 hours,debug)

```bash
hayhooks run --pipelines-dir pipelines
```

Open and test endpoints on `http://localhost:1416/docs#/`


### Key Tasks Summary

1. **Implement EntityExtractor and NewsClassifier** 
- [EntityExtractor](./pipelines/ner_extraction/components.py)
- [NewsClassifier](./pipelines/ner_extraction/components.py)

2. **Build 3 Pipelines** 
   - Classification: Search → Fetch → Clean → Classify (pipelines/classification/build_pipeline.py)
   - NER: Search → Fetch → Clean → Extract (pipelines/ner-extraction/build_pipeline.py)
   - Combined: Search → Fetch → Clean → Classify → Extract (create folder structure)

3. **Deploy with Hayhooks** 
   - Serialize pipelines to YAML  
   - Expose the YAML pipeline through the pipeline wrapper
   - Start Hayhooks server 
   - Test REST endpoints

Advanced

4. **Create SuperComponents** 
   - Wrap each pipeline with simplified interface
   - Map query → search.query

5. **Build Agent** 
   - Create 3 tools from SuperComponents
   - Write system prompt
   - Enable natural language queries

6. **Deploy Agent**

## 💡 Pro Tips

### While Coding
- ✅ Test after each component (don't wait until the end!)
- ✅ Incorporate logging in your custom components to debug
- ✅ Read error messages carefully
- ✅ Use the reference notebooks when stuck

### Common Mistakes to Avoid
- ❌ Skipping the warm_up() call on models
- ❌ Wrong component names in pipeline.connect()
- ❌ Vague tool descriptions (agent won't know when to use them)
- ❌ Hardcoding API keys (always use .env)

### Testing Shortcuts
```python
# Quick test for EntityExtractor
test_doc = Document(content="Elon Musk founded Tesla in California.")
result = extractor.run(documents=[test_doc])
print(result['documents'][0].meta.get('entities'))

# Quick test for pipeline
result = pipeline.run(data={"search": {"query": "AI"}})

# Quick test for agent
agent.run(messages=[ChatMessage.from_user("Classify articles about AI")])
```

## 🆘 If You Get Stuck

[Review the Hints provided](HINTS.md)

### First Steps
1. Check the TODO comments in the code
2. Look at the hints in the notebook
3. Review the reference notebooks:
   - `ner-with-haystack-search-pipeline.ipynb`
   - `classification-with-haystack-search-pipeline.ipynb`

### Debugging Checklist
- [ ] Are all imports working? (try running first cell)
- [ ] Is .env file in the right location?
- [ ] Did you call warm_up() on models?
- [ ] Do pipeline connections match component names?
- [ ] Are you testing with simple queries first?

### Still Stuck?
Look at the error type:
- **ImportError**: Install missing package
- **KeyError**: Check component names in pipeline
- **AttributeError**: Verify method names and parameters
- **APIError**: Check API keys in .env


## 🔥 Bonus Challenges

Once you complete the basic exercise:

1. **Easy**: Modify the confidence threshold and see how it affects results
2. **Medium**: Add a new category to classification
3. **Hard**: Create a 4th pipeline that includes sentiment analysis
4. **Expert**: Deploy to a cloud platform (AWS, GCP, Azure)

## 📊 Success Criteria

You've successfully completed the exercise when:

✅ All notebook cells execute without errors  
✅ EntityExtractor correctly identifies entities  
✅ All three pipelines return expected results  
✅ Agent correctly chooses tools based on queries  
✅ Hayhooks server deploys and serves pipelines  
✅ REST API endpoints return valid responses  

## 🎉 You're Ready!

Open the notebook and start with Section 1. Good luck! 🚀

---
