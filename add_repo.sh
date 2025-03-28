#!/bin/bash
# Script to add new repositories to R2E and make them available for querying

# Activate the environment
source env/bin/activate

# Check if repository URL is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <repository_url> [experiment_name]"
  echo "Example: $0 https://github.com/amazon-science/PAE my_experiment"
  exit 1
fi

# Repository URL
REPO_URL=$1

# Experiment name (default to repo name if not provided)
if [ -z "$2" ]; then
  REPO_NAME=$(basename $REPO_URL .git)
  EXP_NAME="${REPO_NAME}_exp"
else
  EXP_NAME=$2
fi

# Extract organization and repo name from URL
ORG_REPO=$(echo $REPO_URL | sed -E 's/https:\/\/github.com\/([^\/]+)\/([^\/]+)(\/.*)?/\1___\2/')

# Set paths
REPOS_DIR=~/buckets/local_repoeval_bucket/repos
DEST_DIR="$REPOS_DIR/$ORG_REPO"

echo "==== Adding repository: $REPO_URL ===="
echo "==== Using experiment name: $EXP_NAME ===="

# 0. Make sure repos directory exists
mkdir -p $REPOS_DIR

# 1. Clone the repository
echo "Cloning repository to $DEST_DIR..."
if [ -d "$DEST_DIR" ]; then
  echo "Directory already exists. Removing old repository..."
  rm -rf "$DEST_DIR"
fi
git clone --depth=1 $REPO_URL "$DEST_DIR"

# 2. Extract functions from the repository
echo "Extracting functions from repository..."
r2e extract -e $EXP_NAME --overwrite_extracted

# 3. List the extracted functions
echo "Listing extracted functions..."
r2e list-functions -e $EXP_NAME | head -n 10

# 4. Run a sample query using the new experiment
echo "Testing a simple query on the new repository..."
python r2e_query_engine.py --exp_id $EXP_NAME --query "sample test query" --show-code

# 5. Add to living documentation
echo "Adding repository to living documentation..."
python living_doc.py --document_repo --repo_url $REPO_URL --exp_id $EXP_NAME --generate_html

echo "==== Repository added successfully! ===="
echo "To search the new repository, use:"
echo "python r2e_query_engine.py --exp_id $EXP_NAME --query \"your query\""
echo "To view the documentation, open docs/research_doc.html in your browser."