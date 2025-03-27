#!/bin/bash

# Set your API keys here
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# Check if we have API keys set
if [ "$OPENAI_API_KEY" = "your_openai_api_key" ]; then
  echo "Please replace 'your_openai_api_key' with your actual OpenAI API key in set_env.sh"
  exit 1
fi

if [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key" ]; then
  echo "Please replace 'your_anthropic_api_key' with your actual Anthropic API key in set_env.sh"
  exit 1
fi

echo "Environment variables set successfully!"