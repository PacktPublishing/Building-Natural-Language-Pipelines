# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup (2 minutes)

Complete the setup [in the readme](../README.md#setup-instructions)

### 2. Start the Exercise (2 minutes)

Open the Jupyter notebook [classification-ner-agent-exercise.ipynb](./classification-ner-agent-exercise.ipynb)


### 3. Refactor your code and populate the `pipelines/` 

* Migrate your final custom components to the appropriate folder. For the classification pipeline, they will be migrated to [pipelines/classification/components](./pipelines/classification/components.py)
* Build the pipeline with your custom components and serialize it. For the same example [pipelines/classification/build_pipeline](./pipelines/classification/build_pipeline.py)
* Load the pipeline and get ready to expose as Endpoints with Hayhooks. For the same example [pipelines/classification/pipeline_wrapper](./pipelines/classification/pipeline_wrapper.py)

### 4. Run Hayhooks server

```bash
hayhooks run --pipelines-dir pipelines
```

5. Open and test endpoints on `http://localhost:1416/docs#/`


## 📋 What to Expect

### Time Estimates
- **Section 1 (Setup)**: 5 minutes
- **Section 2 (NER Component)**: 30 minutes
- **Section 3 (Classification Pipeline)**: 20 minutes
- **Section 4 (Combined Pipeline)**: 20 minutes
- **Section 5 (SuperComponents)**: 20 minutes
- **Section 6 (Tools)**: 15 minutes
- **Section 7 (Agent)**: 30 minutes
- **Section 8 (Serialization)**: 10 minutes
- **Section 9 (Deployment)**: 20 minutes
- **Section 10 (Testing)**: 20 minutes

**Total**: ~3 hours (can be done in multiple sessions)

### Key Tasks Summary

1. **Implement EntityExtractor** (components.py)
   - Extract entities from text
   - Filter by confidence (>0.8)
   - Organize by type (PER, ORG, LOC, MISC)

2. **Build 3 Pipelines** 
   - Classification: Search → Fetch → Clean → Classify (pipelines/classification/build_pipeline.py)
   - NER: Search → Fetch → Clean → Extract (pipelines/ner-extraction/build_pipeline.py)
   - Combined: Search → Fetch → Clean → Classify → Extract (create folder structure)

3. **Create SuperComponents** (pipeline_wrapper.py)
   - Wrap each pipeline with simplified interface
   - Map query → search.query

4. **Build Agent** (pipeline_wrapper.py)
   - Create 3 tools from SuperComponents
   - Write system prompt
   - Enable natural language queries

5. **Deploy with Hayhooks** 
   - Serialize pipelines to YAML  
   - Start Hayhooks server 
   - Test REST endpoints


## 💡 Pro Tips

### While Coding
- ✅ Test after each component (don't wait until the end!)
- ✅ Print intermediate results to debug
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

## 🎓 Learning Path

### If You're New to Haystack
1. Start with Section 1 (Setup)
2. Work through Section 2 slowly (this is the foundation)
3. Test everything in Section 2 before moving on
4. Reference the tutorial notebooks frequently

### If You're Experienced with Haystack
1. Skim Sections 1-2 (you might already know this)
2. Focus on Sections 5-7 (SuperComponents and Agents)
3. Section 9 (Hayhooks deployment) is the most advanced

### If You Want to Go Fast
- Implement all TODOs in order
- Run tests after each section
- Skip optional testing cells
- Can complete in ~2 hours

### If You Want to Go Deep
- Experiment with different parameters
- Try additional test cases
- Implement the extension ideas
- Can spend 5+ hours exploring

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

**Need help?** Check the main README.md for troubleshooting and resources.
