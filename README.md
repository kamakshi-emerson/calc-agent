# Mathematical Operations Assistant

## Overview
Mathematical Operations Assistant is a None general agent designed for multimodal interactions.

## Features


## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the agent:
```bash
python agent.py
```

## Configuration

The agent uses the following environment variables:
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key (if using Anthropic)
- `GOOGLE_API_KEY`: Google API key (if using Google)

## Usage

```python
from agent import Mathematical Operations AssistantAgent

agent = Mathematical Operations AssistantAgent()
response = await agent.process_message("Hello!")
```

## Domain: general
## Personality: None
## Modality: multimodal