# Integration Guide: Using GATE and PAE Together

This guide explains how to use the core functions from GATE (Graph Analysis Tool for Exploration) and PAE (Program Analysis and Execution) repositories together for advanced code analysis.

## Core Workflow

1. **Parse Code to AST**
   ```python
   from python_graphs import program_utils
   
   # Convert Python code to AST
   code = """
   def example():
       x = 1
       if x > 0:
           return True
       return False
   """
   ast_node = program_utils.program_to_ast(code)
   ```

2. **Build Control Flow Graph**
   ```python
   from python_graphs import control_flow
   
   # Generate control flow graph
   cfg = control_flow.get_control_flow_graph(ast_node)
   ```

3. **Create Program Graph**
   ```python
   from python_graphs import program_graph
   
   # Create nodes from instructions
   nodes = []
   for block in cfg.blocks:
       for cf_node in block.control_flow_nodes:
           instruction = cf_node.instruction
           node = program_graph.make_node_from_instruction(instruction)
           nodes.append(node)
   ```

4. **Analyze Graph Metrics**
   ```python
   from python_graphs import program_graph_analysis
   
   # Calculate complexity
   complexity = cyclomatic_complexity(cfg)
   
   # Convert to NetworkX for advanced analysis
   nx_graph = _program_graph_to_nx(graph, directed=True)
   
   # Get graph diameter
   graph_diameter = diameter(graph)
   
   # Get betweenness centrality
   max_between = max_betweenness(graph)
   ```

5. **Visualize Results**
   ```python
   from python_graphs import program_graph_graphviz
   
   # Create GraphViz representation
   graphviz_graph = program_graph_graphviz.to_graphviz(graph)
   
   # Save visualization
   graphviz_graph.draw('program_graph.png', prog='dot')
   ```

6. **Comprehensive Analysis**
   ```python
   # Get complete analysis results
   results = analyze_graph(graph, "my_analysis")
   
   # Access metrics
   num_nodes = results[1]['num_nodes']
   num_edges = results[1]['num_edges']
   ast_height = results[1]['ast_height']
   ```

## Integration Example

```python
import ast
from python_graphs import program_utils, control_flow, program_graph, program_graph_analysis

def analyze_code(code_string):
    """Analyze Python code using GATE and PAE tools."""
    # Parse code to AST
    ast_node = program_utils.program_to_ast(code_string)
    
    # Build control flow graph
    cfg = control_flow.get_control_flow_graph(ast_node)
    
    # Calculate complexity metrics
    cc1 = cyclomatic_complexity(cfg)
    cc2 = cyclomatic_complexity2(cfg)
    cc3 = cyclomatic_complexity3(cfg)
    
    # Create program graph
    # (This is a simplified version, actual implementation would build a full graph)
    graph = build_program_graph(cfg)
    
    # Analyze graph structure
    nx_graph = _program_graph_to_nx(graph, directed=True)
    try:
        diam = diameter(graph)
    except:
        diam = "N/A (disconnected graph)"
    
    # Generate comprehensive analysis
    _, results = analyze_graph(graph, "analysis")
    
    return {
        "complexity": {
            "cc1": cc1,
            "cc2": cc2,
            "cc3": cc3
        },
        "structure": {
            "nodes": results['num_nodes'],
            "edges": results['num_edges'],
            "diameter": diam,
            "ast_height": results['ast_height']
        }
    }
```

## Key Functions Reference

| Function | Source | Purpose |
|----------|--------|---------|
| `program_to_ast` | PAE | Converts Python code to AST |
| `get_control_flow_graph` | GATE | Builds control flow graph from AST |
| `make_node_from_instruction` | Both | Creates graph nodes from instructions |
| `_program_graph_to_nx` | PAE | Converts to NetworkX for analysis |
| `cyclomatic_complexity` | Both | Calculates code complexity |
| `diameter` | PAE | Finds maximum distance in graph |
| `to_graphviz` | Both | Creates visualization |
| `analyze_graph` | PAE | Performs comprehensive analysis |

## Using with the Query Engine

```python
# Search across both repos for control flow functions
./multi_repo_search.py --query "control flow analysis" --experiments PAE_exp gate_exp

# Generate research trajectories combining both toolsets
python r2e_query_engine.py --exp_id PAE_exp --research "combining control flow analysis with graph metrics" --use_openrouter
```