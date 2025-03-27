#!/bin/bash
# search-all.sh - Search across all experiments using keywords
# Usage: ./search-all.sh [query]
#
# Example:
#   ./search-all.sh "graph visualization"

if [ -z "$1" ]; then
    echo "Usage: ./search-all.sh [query]"
    echo "Example: ./search-all.sh \"graph visualization\""
    exit 1
fi

QUERY="$1"
SHOW_CODE=""

# Check if show-code flag is provided
if [ "$2" == "--show-code" ]; then
    SHOW_CODE="--show-code"
fi

# Get list of experiments
EXPERIMENTS=$(ls -1 ~/buckets/r2e_bucket/extracted_data/ | grep "_extracted.json" | sed 's/_extracted.json//')

echo "Searching for \"$QUERY\" across all experiments..."
echo "======================================================"

for EXP in $EXPERIMENTS; do
    echo -e "\n\033[1;34m** Experiment: $EXP **\033[0m"
    OPENAI_API_KEY="" OPENROUTER_API_KEY="" python r2e_query_engine.py --exp_id "$EXP" --query "$QUERY" --no-document $SHOW_CODE | grep -v "Warning:" | grep -v "Loaded" | grep -v "No API key"
    
    # Add separator
    echo "------------------------------------------------------"
done

# Visualize if requested
if [ "$3" == "--visualize" ]; then
    echo -e "\n\033[1;32mGenerating visualizations for each experiment...\033[0m"
    for EXP in $EXPERIMENTS; do
        echo "Visualizing $EXP..."
        ./test_prototype.py --exp_id "$EXP" --query "$QUERY" --depth 2
    done
    echo -e "\033[1;32mVisualizations saved to docs/graphs/ directory\033[0m"
fi