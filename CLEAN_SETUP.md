# Clean MCP Logging Setup

## Essential Files to Keep (6 files)

### Core System
- `openrouter_agent.py` - Main OpenRouter agent runner
- `simple_structured_logger.py` - Logging logic
- `system_prompt_template.py` - Prompt templates
- `web_search_evaluator.py` - Anti-cheating evaluation

### Configuration
- `.env` - API keys (OPENROUTER_API_KEY)
- `requirements.txt` - Dependencies

## Setup Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variable
echo "OPENROUTER_API_KEY=your_key_here" > .env

# 3. Run with different questions
python openrouter_agent.py
```

## Quick Usage

### Change Questions
Edit `openrouter_agent.py` line 273-279:
```python
questions = [
    "Calculate the pKa for acetic acid",
    "Generate conformers of ibuprofen, optimize the lowest energy conformer, then calculate its logP and pKa values",
    # Add more questions here
]
```

### Disable Web Search
```python
asyncio.run(test_with_simple_logging(questions[0], enable_web_search=False))
```

### Evaluate Results
```python
from web_search_evaluator import evaluate_with_web_search_detection
evaluate_with_web_search_detection('simple_logs_YYYYMMDD_HHMMSS.json')
```

## Output Files
- `simple_logs_YYYYMMDD_HHMMSS.json` - Execution logs
- Console output shows progress

## Files You Can Delete
- All other `.py` files
- All other `.json` files
- All `.md` files except this one
- `__pycache__/` directory
- Old log files