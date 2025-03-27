# R2E Query Engine

A semantic code query tool for extracting insights, generating research trajectories, and visualizing code relationships from repositories analyzed with R2E.

## Features

- **Semantic Code Search**: Find functions across repositories based on natural language queries
- **Research Trajectory Generation**: Generate novel research directions by combining code from multiple repositories
- **Prototype Generation**: Create code prototypes implementing the generated research ideas
- **Code Relationship Visualization**: Generate graph visualizations showing relationships between functions
- **Pattern Detection**: Automatically identify common patterns in code (AST processing, control flow, etc.)
- **Self-installing Wrapper**: Uses uv (or falls back to venv) for a seamless setup experience

## Quick Start

1. Add a repository to the system using the provided script:
   ```bash
   # Add a new repository
   ./add_repo.sh https://github.com/example/repo my_experiment
   
   # The script will:
   # - Clone the repository to the correct location
   # - Extract functions and methods
   # - Set up the experiment ID
   # - Add it to the living documentation
   ```

2. Run the self-installing query engine wrapper:
   ```bash
   ./r2e_query_wrapper.py --exp_id my_experiment
   ```
   
   The wrapper will:
   - Use your existing 'env' environment if available, or set up a new one if necessary
   - Prompt for an OpenAI API key if not already set in the environment
   - Start the query engine in interactive mode
   
   You can also run in non-interactive mode:
   ```bash
   ./r2e_query_wrapper.py --non-interactive --query "search term"
   ```

3. Use the interactive prompt to explore your code repositories:
   ```
   Command (search/research/prototype/help/exit): search functions that process image data
   ```

## Command Reference

### Interactive Commands

Once in the interactive mode, you can use the following commands:

- `search <query>`: Search for relevant functions across repositories
- `research <query>`: Generate research trajectories based on a query
- `prototype <index>`: Generate a prototype implementation for a research trajectory
- `help`: Show available commands
- `exit`: Exit the interactive mode

### Quick Search Scripts

For simple keyword-based searching without requiring API keys:

```bash
# Search in a single repository
./r2e-search.sh gate_test "extract" --show-code

# Search across all repositories
./search-all.sh "graph" --show-code

# Search and visualize relationships
./r2e-search.sh syncmind_test "agent" --show-code --visualize
```

These scripts bypass the API key requirements and perform pure keyword searches.

### Command Line Arguments

You can also run the wrapper with specific arguments:

```bash
# Run in interactive mode with a specific experiment ID
./r2e_query_wrapper.py --exp_id my_experiment --interactive

# Run a specific query directly
./r2e_query_wrapper.py --exp_id my_experiment --query "functions for image processing"

# Run in non-interactive mode
./r2e_query_wrapper.py --non-interactive --query "algorithm complexity"

# Generate research trajectories for a topic
./r2e_query_wrapper.py --exp_id my_experiment --research "combining graph algorithms with machine learning"

# Show full code for search results
./r2e_query_wrapper.py --exp_id my_experiment --query "graph" --show-code
```

## Requirements

- Python 3.8+
- R2E installed and set up
- API key (either OpenAI or OpenRouter)
  - OpenAI API key (for standard operation)
  - OpenRouter API key (optional, for using alternative models)
- uv (optional, will fall back to venv if not available)

## Using OpenRouter

The R2E Query Engine now supports using [OpenRouter](https://openrouter.ai/) as an alternative to the OpenAI API. This allows you to:

1. Choose from a variety of LLM models (Claude, OpenAI, etc.)
2. Potentially reduce costs by selecting more efficient models
3. Avoid API quota limitations on individual providers

To use OpenRouter:

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY="your-api-key-here"

# Run with OpenRouter
./r2e_query_wrapper.py --use_openrouter --query "graph algorithms"

# Specify a particular model (planned feature)
./r2e_query_wrapper.py --use_openrouter --model "anthropic/claude-3-haiku" --query "graph algorithms"

# Generate research trajectories with OpenRouter
./r2e_query_wrapper.py --use_openrouter --research "optimizing graph algorithms"
```

The current implementation uses Google's Gemini Pro model via OpenRouter when available, with a fallback to OpenAI's GPT-3.5-Turbo. Gemini is particularly strong at code generation tasks, producing cleaner and more efficient implementations.

### How OpenRouter is used in this tool

1. **Search**: When searching for functions, OpenRouter is used to provide semantic understanding of code beyond simple keyword matching.
2. **Research**: For generating research trajectories, the service analyzes available components and suggests novel directions.
3. **Prototype**: When generating code prototypes, OpenRouter helps create working implementations based on the research trajectories.

All these features work with the standard OpenAI API as well, but using OpenRouter can help avoid quota limitations.

## How It Works

The R2E Query Engine combines the power of R2E's code extraction capabilities with large language models to provide semantic understanding of code repositories:

1. **Data Loading**: Loads functions extracted by R2E from repositories
2. **Semantic Search**: Uses LLMs to find functions relevant to natural language queries
3. **Research Generation**: Analyzes available code components to suggest novel research directions
4. **Prototype Creation**: Generates executable prototype code implementing research ideas

This approach helps you quickly understand multiple repositories and identify new opportunities to combine and extend their capabilities.

## Common Workflows

### Cross-Repository Code Understanding

```
Command: search implementations of graph algorithms
```

### Finding Functional Patterns

```
Command: search error handling patterns in asynchronous code
```

### Generating Research Ideas

```
Command: research how to combine reinforcement learning with graph neural networks
```

### Building Prototypes

```
Command: prototype 1
```

## Extending

The R2E Query Engine is designed to be extensible. You can modify `r2e_query_engine.py` to add new capabilities or improve existing ones, such as:

- Adding different LLM providers beyond OpenAI
- Implementing more sophisticated code analysis techniques
- Enhancing the research trajectory generation with domain-specific knowledge
- Integrating with other tools in your development workflow

## Code Relationship Visualization

The R2E Query Engine now includes tools for visualizing relationships between functions in the repositories.

### Visualize from Documentation

Process all queries from the research documentation and generate visualizations:

```bash
./test_prototype.py --from_docs --depth 2
```

This will:
1. Extract all queries and results from the research documentation
2. Build relationship graphs for each query
3. Detect patterns in the functions
4. Generate visualizations in the `docs/graphs/` directory

### Visualize a Specific Query

You can also visualize relationships for a specific query:

```bash
./test_prototype.py --exp_id talkhier_exp --query "graph traversal" --depth 2
```

Parameters:
- `--exp_id`: The experiment ID to analyze
- `--query`: The search query (optional, all functions if not provided)
- `--depth`: Relationship depth to include (default 1)
- `--output`: Output file path for the visualization (default: docs/graphs/{exp_id}_{query}.png)

### Pattern Detection

The visualization tools also detect common patterns in the code:

- AST processing
- Graph operations
- Control flow
- Data flow
- Visualization

This helps understand the purpose and functionality of the code without having to read through all the implementation details.

## Future Vision: Research Paper Integration

A powerful expansion of the R2E Query Engine would be integrating research papers with extracted code, creating a system that enables both reproducibility and innovation:

### Research Reproducibility

1. **Paper-to-Code Mapping**
   - Direct links between paper formulations and code implementations
   - Automatic identification of core algorithms and matching to code components
   - Execution graphs showing how paper concepts flow through implementation

2. **Environment Reconstruction**
   - Complete environment specifications based on papers' methods
   - Docker containers or virtual environments for exact reproduction
   - Resolution of dependency conflicts affecting results

3. **Experiment Verification**
   - Automated test suites validating reproduction of key results
   - Synthetic datasets matching paper descriptions
   - Statistical validation to verify results match reported metrics

### New Research Direction Generation

1. **Gap Analysis**
   - Identification of limitations mentioned in papers
   - Comparison of methods across papers to find unexplored combinations
   - Citation network analysis to discover complementary approaches

2. **Technique Fusion**
   - Prototypes combining methods from multiple papers
   - Adapter components to make incompatible methods work together
   - Auto-tuning of hyperparameters when combining approaches

3. **Scaling and Optimization**
   - Application of contemporary optimization techniques to older algorithms
   - Parallelization strategies for sequential algorithms
   - Hardware-specific optimizations (GPU, TPU, etc.)

This expanded system would create a powerful tool for researchers to confidently reproduce results from papers, create novel research directions by combining existing work, validate hypotheses about improvements, and accelerate the research cycle by automating implementation details.