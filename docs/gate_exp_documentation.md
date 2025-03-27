# Documentation for gate_exp

## Overview

This documentation was automatically generated for the gate_exp experiment. It contains 71 functions from the extracted repositories.

## Functions by Repository

### Repository: python-graphs

Contains 71 functions.

#### make_node_from_instruction

File: `python_graphs.program_graph`

```python
def make_node_from_instruction(instruction):
    """Creates a ProgramGraphNode corresponding to an existing Instruction.

  Args:
    instruction: An Instruction object.

  Returns:
    A ProgramGraphNode corresponding to that instruction.
  """
    ast_node = instruction.node
    node = make_node_from_ast_node(ast_node)
    node.instruction = instruction
    return node
```

#### make_node_from_ast_node

File: `python_graphs.program_graph`

```python
def make_node_from_ast_node(ast_node):
    """Creates a program graph node for the provided AST node.

  This is only called when the AST node doesn't already correspond to an
  Instruction in the program's control flow graph.

  Args:
    ast_node: An AST node from the program being analyzed.

  Returns:
    A node in the program graph corresponding to the AST node.
  """
    node = ProgramGraphNode()
    node.node_type = pb.NodeType.AST_NODE
    node.id = program_utils.unique_id()
    node.ast_node = ast_node
    node.ast_type = type(ast_node).__name__
    return node
```

#### make_node_from_ast_value

File: `python_graphs.program_graph`

```python
def make_node_from_ast_value(value):
    """Creates a ProgramGraphNode for the provided value.

  `value` is a primitive value appearing in a Python AST.

  For example, the number 1 in Python has AST Num(n=1). In this, the value '1'
  is a primitive appearing in the AST. It gets its own ProgramGraphNode with
  node_type AST_VALUE.

  Args:
    value: A primitive value appearing in an AST.

  Returns:
    A ProgramGraphNode corresponding to the provided value.
  """
    node = ProgramGraphNode()
    node.node_type = pb.NodeType.AST_VALUE
    node.id = program_utils.unique_id()
    node.ast_value = value
    return node
```

#### to_graphviz

File: `python_graphs.program_graph_graphviz`

```python
def to_graphviz(graph):
    """Creates a graphviz representation of a ProgramGraph.

  Args:
    graph: A ProgramGraph object to visualize.
  Returns:
    A pygraphviz object representing the ProgramGraph.
  """
    g = pygraphviz.AGraph(strict=False, directed=True)
    for unused_key, node in graph.nodes.items():
        node_attrs = {}
        if node.ast_type:
            node_attrs['label'] = six.ensure_str(node.ast_type, 'utf-8')
        else:
            node_attrs['shape'] = 'point'
        node_type_colors = {}
        if node.node_type in node_type_colors:
            node_attrs['color'] = node_type_colors[node.node_type]
            node_attrs['colorscheme'] = 'svg'
        g.add_node(node.id, **node_attrs)
    for edge in graph.edges:
        edge_attrs = {}
        edge_attrs['label'] = edge.type.name
        edge_colors = {pb.EdgeType.LAST_READ: 'red', pb.EdgeType.LAST_WRITE: 'red'}
        if edge.type in edge_colors:
            edge_attrs['color'] = edge_colors[edge.type]
            edge_attrs['colorscheme'] = 'svg'
        g.add_edge(edge.id1, edge.id2, **edge_attrs)
    return g
```

#### get_control_flow_graph

File: `python_graphs.control_flow`

```python
def get_control_flow_graph(program):
    """Get a ControlFlowGraph for the provided AST node.

  Args:
    program: Either an AST node, source string, or a function.
  Returns:
    A ControlFlowGraph.
  """
    control_flow_visitor = ControlFlowVisitor()
    node = program_utils.program_to_ast(program)
    control_flow_visitor.run(node)
    return control_flow_visitor.graph
```

#### getsource

File: `python_graphs.program_utils`

```python
def getsource(obj):
    """Gets the source for the given object.

  Args:
    obj: A module, class, method, function, traceback, frame, or code object.
  Returns:
    The source of the object, if available.
  """
    if inspect.ismethod(obj):
        func = obj.__func__
    else:
        func = obj
    source = inspect.getsource(func)
    return textwrap.dedent(source)
```

#### program_to_ast

File: `python_graphs.program_utils`

```python
def program_to_ast(program):
    """Convert a program to its AST.

  Args:
    program: Either an AST node, source string, or a function.
  Returns:
    The root AST node of the AST representing the program.
  """
    if isinstance(program, ast.AST):
        return program
    if isinstance(program, six.string_types):
        source = program
    else:
        source = getsource(program)
    module_node = ast.parse(source, mode='exec')
    return module_node
```

#### get_accesses_from_ast_node

File: `python_graphs.instruction`

```python
def get_accesses_from_ast_node(node):
    """Get all accesses for an AST node, in depth-first AST field order."""
    visitor = AccessVisitor()
    visitor.visit(node)
    return visitor.accesses
```

#### cyclomatic_complexity

File: `python_graphs.cyclomatic_complexity`

```python
def cyclomatic_complexity(control_flow_graph):
    """Computes the cyclomatic complexity of a function from its cfg."""
    enter_block = next(control_flow_graph.get_enter_blocks())
    new_blocks = []
    seen_block_ids = set()
    new_blocks.append(enter_block)
    seen_block_ids.add(id(enter_block))
    num_edges = 0
    while new_blocks:
        block = new_blocks.pop()
        for next_block in block.exits_from_end:
            num_edges += 1
            if id(next_block) not in seen_block_ids:
                new_blocks.append(next_block)
                seen_block_ids.add(id(next_block))
    num_nodes = len(seen_block_ids)
    p = 1
    e = num_edges
    n = num_nodes
    return e - n + 2 * p
```

#### cyclomatic_complexity2

File: `python_graphs.cyclomatic_complexity`

```python
def cyclomatic_complexity2(control_flow_graph):
    """Computes the cyclomatic complexity of a program from its cfg."""
    p = 1
    e = sum((len(block.exits_from_end) for block in control_flow_graph.blocks))
    n = len(control_flow_graph.blocks)
    return e - n + 2 * p
```

#### cyclomatic_complexity3

File: `python_graphs.cyclomatic_complexity`

```python
def cyclomatic_complexity3(control_flow_graph):
    """Computes the cyclomatic complexity of a program from its cfg."""
    start_block = control_flow_graph.start_block
    enter_blocks = control_flow_graph.get_enter_blocks()
    new_blocks = [start_block]
    seen_block_ids = {id(start_block)}
    num_connected_components = 1
    num_edges = 0
    for enter_block in enter_blocks:
        new_blocks.append(enter_block)
        seen_block_ids.add(id(enter_block))
        num_connected_components += 1
    while new_blocks:
        block = new_blocks.pop()
        for next_block in block.exits_from_end:
            num_edges += 1
            if id(next_block) not in seen_block_ids:
                new_blocks.append(next_block)
                seen_block_ids.add(id(next_block))
    num_nodes = len(seen_block_ids)
    p = num_connected_components
    e = num_edges
    n = num_nodes
    return e - n + 2 * p
```

#### get_label

File: `python_graphs.control_flow_graphviz`

```python
def get_label(block):
    """Gets the source code for a control flow basic block."""
    lines = []
    for control_flow_node in block.control_flow_nodes:
        instruction = control_flow_node.instruction
        line = get_label_for_instruction(instruction)
        if line.strip():
            lines.append(line)
    return LEFT_ALIGN.join(lines) + LEFT_ALIGN
```

#### ast_height

File: `python_graphs.analysis.program_graph_analysis`

```python
def ast_height(ast_node):
    """Computes the height of an AST from the given node.

  Args:
    ast_node: An AST node.

  Returns:
    The height of the AST starting at ast_node. A leaf node or single-node AST
    has a height of 1.
  """
    max_child_height = 0
    for child_node in ast.iter_child_nodes(ast_node):
        max_child_height = max(max_child_height, ast_height(child_node))
    return 1 + max_child_height
```

#### _program_graph_to_nx

File: `python_graphs.analysis.program_graph_analysis`

```python
def _program_graph_to_nx(program_graph, directed=False):
    """Converts a ProgramGraph to a NetworkX graph.

  Args:
    program_graph: A ProgramGraph.
    directed: Whether the graph should be treated as a directed graph.

  Returns:
    A NetworkX graph that can be analyzed by the networkx module.
  """
    dict_of_lists = {}
    for node in program_graph.all_nodes():
        neighbor_ids = [neighbor.id for neighbor in program_graph.outgoing_neighbors(node)]
        dict_of_lists[node.id] = neighbor_ids
    return nx.DiGraph(dict_of_lists) if directed else nx.Graph(dict_of_lists)
```

#### diameter

File: `python_graphs.analysis.program_graph_analysis`

```python
def diameter(graph):
    """Returns the diameter of a ProgramGraph.

  Note: this is very slow for large graphs.

  Args:
    graph: A ProgramGraph.

  Returns:
    The diameter of the graph. A single-node graph has diameter 0. The graph is
    treated as an undirected graph.

  Raises:
    networkx.exception.NetworkXError: Raised if the graph is not connected.
  """
    nx_graph = _program_graph_to_nx(graph, directed=False)
    return nx.algorithms.distance_measures.diameter(nx_graph)
```

#### max_betweenness

File: `python_graphs.analysis.program_graph_analysis`

```python
def max_betweenness(graph):
    """Returns the maximum node betweenness centrality in a ProgramGraph.

  Note: this is very slow for large graphs.

  Args:
    graph: A ProgramGraph.

  Returns:
    The maximum betweenness centrality value among all nodes in the graph. The
    graph is treated as an undirected graph.
  """
    nx_graph = _program_graph_to_nx(graph, directed=False)
    return max(nx.algorithms.centrality.betweenness_centrality(nx_graph).values())
```

#### get_percentiles

File: `python_graphs.analysis.run_program_graph_analysis`

```python
def get_percentiles(data, percentiles, integer_valued=True):
    """Returns a dict of percentiles of the data.

  Args:
    data: An unsorted list of datapoints.
    percentiles: A list of ints or floats in the range [0, 100] representing the
      percentiles to compute.
    integer_valued: Whether or not the values are all integers. If so,
      interpolate to the nearest datapoint (instead of computing a fractional
      value between the two nearest datapoints).

  Returns:
    A dict mapping each element of percentiles to the computed result.
  """
    interpolation = 'nearest' if integer_valued else 'linear'
    results = np.percentile(data, percentiles, interpolation=interpolation)
    return {percentiles[i]: results[i] for i in range(len(percentiles))}
```

#### analyze_graph

File: `python_graphs.analysis.run_program_graph_analysis`

```python
def analyze_graph(graph, identifier):
    """Performs various analyses on a graph.

  Args:
    graph: A ProgramGraph to analyze.
    identifier: A unique identifier for this graph (for later aggregation).

  Returns:
    A pair (identifier, result_dict), where result_dict contains the results of
    analyses run on the graph.
  """
    num_nodes = program_graph_analysis.num_nodes(graph)
    num_edges = program_graph_analysis.num_edges(graph)
    ast_height = program_graph_analysis.graph_ast_height(graph)
    degree_percentiles = [10, 25, 50, 75, 90]
    degrees = get_percentiles(program_graph_analysis.degrees(graph), degree_percentiles)
    in_degrees = get_percentiles(program_graph_analysis.in_degrees(graph), degree_percentiles)
    out_degrees = get_percentiles(program_graph_analysis.out_degrees(graph), degree_percentiles)
    diameter = program_graph_analysis.diameter(graph)
    max_betweenness = program_graph_analysis.max_betweenness(graph)
    result_dict = {'num_nodes': num_nodes, 'num_edges': num_edges, 'ast_height': ast_height, 'degrees': degrees, 'in_degrees': in_degrees, 'out_degrees': out_degrees, 'diameter': diameter, 'max_betweenness': max_betweenness}
    return (identifier, result_dict)
```

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.program_graph`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.control_flow`

#### 

File: `python_graphs.data_flow`

#### 

File: `python_graphs.data_flow`

#### 

File: `python_graphs.data_flow`

#### 

File: `python_graphs.program_graph_test`

#### 

File: `python_graphs.program_graph_test`

#### 

File: `python_graphs.instruction`

#### 

File: `python_graphs.instruction`

#### 

File: `python_graphs.analysis.program_graph_analysis_test`

#### 

File: `python_graphs.analysis.program_graph_analysis_test`

#### 

File: `python_graphs.analysis.program_graph_analysis_test`

#### 

File: `python_graphs.analysis.program_graph_analysis_test`

#### 

File: `python_graphs.analysis.program_graph_analysis_test`

#### 

File: `python_graphs.analysis.program_graph_analysis_test`

## Function Relationships

Common relationships between functions:

### Functions in python_graphs.program_graph

- make_node_from_instruction
- make_node_from_ast_node
- make_node_from_ast_value
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

### Functions in python_graphs.control_flow

- get_control_flow_graph
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

### Functions in python_graphs.program_utils

- getsource
- program_to_ast

### Functions in python_graphs.instruction

- get_accesses_from_ast_node
- 
- 

### Functions in python_graphs.cyclomatic_complexity

- cyclomatic_complexity
- cyclomatic_complexity2
- cyclomatic_complexity3

### Functions in python_graphs.analysis.program_graph_analysis

- ast_height
- _program_graph_to_nx
- diameter
- max_betweenness

### Functions in python_graphs.analysis.run_program_graph_analysis

- get_percentiles
- analyze_graph

### Functions in python_graphs.data_flow

- 
- 
- 

### Functions in python_graphs.program_graph_test

- 
- 

### Functions in python_graphs.analysis.program_graph_analysis_test

- 
- 
- 
- 
- 
- 

