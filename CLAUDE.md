# R2E Query Engine - Quick Reference

## Overview
This system provides a semantic search engine for code repositories extracted with R2E. It enables research trajectory generation and prototype implementation.

## Adding New Repositories

```bash
# Add a new repository (auto-names based on repo name)
./add_repo.sh https://github.com/amazon-science/PAE

# Add with custom experiment name
./add_repo.sh https://github.com/ayanami2003/GATE gate_experiment

# Repositories to try:
# - https://github.com/amazon-science/PAE
# - https://github.com/ayanami2003/GATE
# - https://github.com/foundation-interface/graphologue
# - https://github.com/sony/talkhier
```

## Key Commands

```bash
# Basic Search (uses local environment)
python r2e_query_engine.py --exp_id quickstart --query "graph algorithm"

# Using OpenRouter (better model access)
python r2e_query_engine.py --exp_id quickstart --query "graph algorithm" --use_openrouter

# Research Trajectory Generation
python r2e_query_engine.py --exp_id quickstart --research "optimizing graph algorithms" --use_openrouter

# Show full code instead of snippets
python r2e_query_engine.py --exp_id quickstart --query "graph" --show-code
```

## API Keys
- Set once in environment: `export OPENROUTER_API_KEY="your-key-here"`
- Add to shell config: `echo 'export OPENROUTER_API_KEY="your-key-here"' >> ~/.zshrc`

## Workflow Guidelines
1. **KEEP IT SIMPLE**: One command, one purpose - avoid over-explaining
2. **NO EXCESSIVE TESTING**: Only test key functionality when needed
3. **FOCUS ON RESULTS**: Prioritize useful output over process explanation
4. **USE EXISTING ENV**: Work with the current environment setup
5. **BE CONCISE**: Keep documentation and explanations brief

## Cross-Repository Search

```bash
# Search across all repositories with a single query
./multi_repo_search.py --query "graph traversal" 

# Search only specific repositories
./multi_repo_search.py --query "neural networks" --experiments PAE_exp GATE_experiment

# Use OpenRouter with Google Gemini for semantic search
./multi_repo_search.py --query "transform data" --use_openrouter
```

## LOTUS Bridge UI

The LOTUS Bridge provides a graphical interface and LOTUS-compatible operators:

```bash
# Launch the LOTUS Bridge UI
./lotus_bridge.py --ui

# Run semantic search with LOTUS operators
./lotus_bridge.py --exp_id quickstart --query "graph algorithm"

# Use OpenRouter with the LOTUS Bridge
./lotus_bridge.py --exp_id PAE_exp --use_openrouter --query "control flow"

# Generate LOTUS documentation for a repository
./lotus_bridge.py --exp_id PAE_exp --generate-docs

# Generate documentation for all repositories
./lotus_bridge.py --all-experiments --generate-docs
```

LOTUS operators used:
- `sem_filter`: Filter code semantically with natural language
- `sem_join`: Join code components based on natural language relationships
- `sem_map`: Transform each item based on natural language instructions
- `sem_group_by`: Group items by semantic similarity

## Living Documentation

The system automatically documents your research journey:

```bash
# Generate HTML documentation from all previous searches
./living_doc.py --generate_html

# Document a new repository manually
./living_doc.py --document_repo --repo_url https://github.com/example/repo --exp_id example_exp

# Document a specific query
./living_doc.py --exp_id quickstart --query "graph algorithms"
```

The documentation is automatically updated when you:
- Add new repositories
- Run queries with `--document` flag (or by default)
- Generate research trajectories

View the documentation by opening `docs/research_doc.html` in your browser.

## Future Development
- Paper-to-Code mapping for research reproducibility
- Expanded multi-repository analysis capabilities
- Knowledge graph construction for code relationships
- Visualization of cross-repository connections