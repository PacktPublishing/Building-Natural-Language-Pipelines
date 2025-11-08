# Troubleshooting: No Search Results

## Problem
The Yelp search is returning 0 results because the RapidAPI key is invalid or not subscribed to the Yelp Business Reviews API.

## Root Cause
```
HTTP/2 401 
{"message":"Invalid API key. Go to https://docs.rapidapi.com/docs/keys for more info."}
```

## Solutions

### Solution 1: Get a Valid RapidAPI Key (Recommended for Production)

1. **Sign up for RapidAPI**:
   - Visit https://rapidapi.com/
   - Create an account or log in

2. **Subscribe to Yelp Business Reviews API**:
   - Search for "Yelp Business Reviews"
   - Choose a subscription plan (free tier available)
   - Subscribe to the API

3. **Get your API key**:
   - Go to your RapidAPI dashboard
   - Copy your API key

4. **Update your `.env` file**:
   ```bash
   RAPID_API_KEY=your_new_valid_key_here
   ```

5. **Restart hayhooks server**:
   ```bash
   # Stop the current server (Ctrl+C in the terminal)
   # Then restart:
   uv run hayhooks run --pipelines-dir pipelines
   ```

### Solution 2: Use Mock Data for Testing (Immediate Testing)

If you want to test the LangGraph workflow immediately without waiting for API access:

1. **Modify `build_pipeline.py`** to use the mock component:

   ```python
   # In pipelines/business_search/build_pipeline.py
   
   # Change this import:
   from .components import YelpBusinessSearch
   
   # To this:
   from .components_mock import YelpBusinessSearchMock as YelpBusinessSearch
   ```

2. **Rebuild the pipeline**:
   ```bash
   cd /Users/laurafunderburk/Documents/GitHub/Building-Natural-Language-Pipelines/ch8/yelp-navigator
   uv run python pipelines/business_search/build_pipeline.py
   ```

3. **Restart hayhooks** (if it's running):
   ```bash
   uv run hayhooks run --pipelines-dir pipelines
   ```

4. **Test again** - You should now see mock results with 5 sample Mexican restaurants in Austin

## Verification

Test the endpoint directly:
```bash
curl -X POST http://localhost:1416/business_search/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Mexican restaurants in Austin, Texas"}' | jq .
```

You should see `"result_count": 5` with mock business data.

## Note on Mock Data

The mock data includes realistic looking businesses but is not real-time data from Yelp. It's sufficient for:
- Testing the LangGraph workflow
- Demonstrating the multi-agent system
- Development and debugging

For production use, you'll need a valid RapidAPI key to get real business data.
