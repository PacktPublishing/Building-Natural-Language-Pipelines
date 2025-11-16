# Token Usage Measurement Guide

This guide explains how to measure actual token usage between Yelp Navigator V1 and V2 to validate the architectural improvements.

## Quick Start

### 1. Install Dependencies

```bash

```

### 2. Run a Single Test

```bash
# Test with default query (Italian restaurants in Boston, general detail)
uv run python measure_token_usage.py

# Test with custom query
uv run python measure_token_usage.py --test-query "sushi restaurants" --test-location "Tokyo, Japan"

# Test with different detail levels
uv run python measure_token_usage.py --test-query "coffee shops" --test-location "Seattle, WA" --detail-level reviews
```

### 3. Run Comprehensive Test Suite

```bash
# Run all predefined test cases
uv run python measure_token_usage.py --run-all-tests
```

This will test:
- Italian restaurants in Boston (general, detailed, reviews)
- Coffee shops in San Francisco (general)
- Sushi restaurants in New York (reviews)

### 4. View Results

The script generates a markdown report: `token_usage_report.md`

```bash
# View the report
cat token_usage_report.md

# Or open in your editor
code token_usage_report.md
```

## Understanding the Output

### Console Output

```
================================================================================
Testing: Italian restaurants in Boston (detail_level: general)
================================================================================

🏗️  Running V1 workflow...
🏗️  Running V2 workflow...

📊 V1 Breakdown:
  clarification              800 tokens
  search                    1200 tokens
  summary_generation        3500 tokens
  supervisor_approval       2500 tokens
  TOTAL                     8000 tokens

📊 V2 Breakdown:
  clarification              400 tokens
  supervisor_decision_1      300 tokens
  supervisor_decision_2      350 tokens
  summary_generation        2000 tokens
  TOTAL                     3050 tokens

✨ Reduction: 4950 tokens (61.9%)
```

### Report Contents

The generated report includes:

1. **Summary Statistics**
   - Total tokens for V1 vs V2
   - Overall reduction percentage
   - Average reduction per query

2. **Cost Impact**
   - Cost per workflow (GPT-4 pricing)
   - Savings per query
   - Projected monthly savings at scale

3. **Detailed Results Table**
   - Per-query breakdown
   - Token counts for each architecture
   - Reduction metrics

### Measured Operations

**V1 Operations:**
- Clarification agent
- Search agent
- Details agent (if detailed/reviews)
- Sentiment agent (if reviews)
- Summary generation (with full context)
- Supervisor approval (with full summary)

**V2 Operations:**
- Clarification (structured output)
- Supervisor decision 1 (initial routing)
- Tool execution (minimal context)
- Supervisor decision 2+ (incremental context)
- Summary generation (from accumulated results)

## Cost Analysis

### Token Cost (GPT-4)

Current pricing (as of 2024):
- **Input tokens**: $0.03 per 1K tokens
- **Output tokens**: $0.06 per 1K tokens


## Additional Resources

- [OpenAI Tokenizer Documentation](https://github.com/openai/tiktoken)
- [LangSmith Tracing Guide](https://docs.smith.langchain.com/)
- [Token Optimization Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
