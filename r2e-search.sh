#!/bin/bash
# r2e-search.sh - Simple keyword search script for R2E repositories
# Usage: ./r2e-search.sh [exp_id] [query]
#
# Examples:
#   ./r2e-search.sh talkhier_exp "graph visualization"
#   ./r2e-search.sh PAE_exp "control flow"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./r2e-search.sh [exp_id] [query]"
    echo "Example: ./r2e-search.sh talkhier_exp \"graph visualization\""
    exit 1
fi

EXP_ID="$1"
QUERY="$2"
SHOW_CODE=""

# Check if show-code flag is provided
if [ "$3" == "--show-code" ]; then
    SHOW_CODE="--show-code"
fi

# Run the query with environment variables to disable API usage
OPENAI_API_KEY="" OPENROUTER_API_KEY="" python r2e_query_engine.py --exp_id "$EXP_ID" --query "$QUERY" --no-document $SHOW_CODE

# Check if we should update the visualization
if [ "$4" == "--visualize" ]; then
    echo "Generating visualization..."
    ./test_prototype.py --exp_id "$EXP_ID" --query "$QUERY" --depth 2
    echo "Visualization saved to docs/graphs/${EXP_ID}_${QUERY// /_}.png"
fi
