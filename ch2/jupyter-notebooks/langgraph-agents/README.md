# LangGraph Agent Tutorials

This directory contains tutorials for building agents with LangGraph.

## Notebooks

### 1. `connecting-state-graph.ipynb`
**Introduction to LangGraph: Learning about State**

Learn the fundamentals of LangGraph:
- How to define state schemas using `MessagesState`
- Creating nodes and edges
- Building and compiling graphs
- Basic state management with reducers

**Prerequisites:**
- Python 3.8+
- Basic Python knowledge
- Understanding of type hints

### 2. `building-agent-with-tools.ipynb`
**Building a Simple Agent with Tools using Ollama**

Build a complete agent that uses external tools, running entirely locally with Ollama:
- Using Qwen2-0.5B model via Ollama (no OpenAI API needed!)
- Integrating search tools (Tavily or Serper)
- Implementing conditional routing
- Creating agent loops for multi-step reasoning
- Complete privacy with local LLM inference

**Prerequisites:**
- Completed the first notebook (state basics)
- Ollama installed: https://ollama.com
- Qwen2 model: `ollama pull qwen2:0.5b`
- API key for Tavily (https://tavily.com) or Serper (https://serper.dev)

## Quick Start

### Setup Ollama

1. **Install Ollama:**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Or download from: https://ollama.com
   ```

2. **Pull the Qwen2 model:**
   ```bash
   ollama pull qwen2:0.5b
   ```

3. **Verify installation:**
   ```bash
   ollama list
   ```

### Install Python Dependencies

```bash
pip install langgraph langchain-ollama langchain-community tavily-python python-dotenv
```

### Set up API Keys (for search tools)

Create a `.env` file in this directory:
```bash
TAVILY_API_KEY=your-tavily-api-key-here
# OR
SERPER_API_KEY=your-serper-api-key-here
```

Get API keys:
- Tavily: https://tavily.com (recommended for AI applications)
- Serper: https://serper.dev (Google Search wrapper)

## Why Ollama + Qwen2?

### Benefits
- **Privacy**: All LLM inference runs locally on your machine
- **Cost-Effective**: No API costs for the language model
- **Fast**: Qwen2-0.5B is lightweight (352MB) and runs quickly
- **Capable**: Despite its small size, supports tool calling and reasoning
- **Offline**: Works without internet (except for search API calls)

### Model Options
You can use different Qwen2 sizes based on your needs:

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `qwen2:0.5b` | 352MB | Very Fast | Simple tasks, learning, quick prototyping |
| `qwen2:1.5b` | ~1GB | Fast | Better reasoning, more complex tasks |
| `qwen2:7b` | ~4.7GB | Moderate | Production agents, complex reasoning |

Pull other sizes:
```bash
ollama pull qwen2:1.5b
ollama pull qwen2:7b
```

## Troubleshooting

### Ollama Issues

**Problem: "Ollama not found"**
```bash
# Check if installed
which ollama

# If not installed, install from https://ollama.com
```

**Problem: "Connection refused"**
```bash
# Make sure Ollama service is running
ollama serve

# Or check if it's already running
ps aux | grep ollama
```

**Problem: "Model not found"**
```bash
# List available models
ollama list

# Pull the required model
ollama pull qwen2:0.5b
```

### Python Package Issues

**Problem: Import errors**
```bash
# Ensure you're in the correct environment
pip list | grep langchain

# Reinstall if needed
pip install --upgrade langgraph langchain-ollama langchain-community
```

### API Key Issues

**Problem: "Tavily API key not set"**
- Create a `.env` file in the notebook directory
- Add: `TAVILY_API_KEY=your-key-here`
- Restart the notebook kernel

## Learning Path

1. **Start with `connecting-state-graph.ipynb`**
   - Understand state management
   - Learn graph basics
   - Practice with simple examples

2. **Progress to `building-agent-with-tools.ipynb`**
   - Build on state concepts
   - Add tool integration
   - Create complete agents

3. **Experiment and Extend**
   - Try different models (`qwen2:7b`, `llama3.2`, `mistral`)
   - Add custom tools (calculator, database, APIs)
   - Build multi-agent systems

## Additional Resources

### Documentation
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Ollama Integration](https://python.langchain.com/docs/integrations/chat/ollama/)
- [Ollama Documentation](https://ollama.com/docs)
- [Qwen2 Model Card](https://huggingface.co/Qwen/Qwen2-0.5B)

### Community
- [LangChain Discord](https://discord.gg/langchain)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)

### Related Models
Try other Ollama models for different capabilities:
- **Llama 3.2**: `llama3.2:1b`, `llama3.2:3b` (Meta's models)
- **Mistral**: `mistral:7b` (strong reasoning)
- **Phi-3**: `phi3:mini` (Microsoft's efficient model)
- **DeepSeek**: `deepseek-coder:6.7b` (coding specialist)

## Contributing

Found an issue or want to improve these tutorials? Feel free to:
1. Open an issue
2. Submit a pull request
3. Share your extensions and improvements

## License

These notebooks are part of the "Building Natural Language Pipelines" book project.
