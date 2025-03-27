#!/usr/bin/env python3
"""
Test prototype for R2E Query Results Visualization

This script uses the existing parallel_graph_prototype.py and extends it
to visualize relationships between functions in the repositories.
"""

import os
import json
import sys
import pandas as pd
import numpy as np
import re
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict

# Configuration
R2E_BUCKET_PATH = os.path.expanduser("~/buckets/r2e_bucket")

def load_extracted_functions(exp_id):
    """
    Load the extracted functions from the R2E bucket.
    
    Args:
        exp_id: The experiment ID
        
    Returns:
        Dictionary of functions with their code and metadata
    """
    extracted_data_path = os.path.join(R2E_BUCKET_PATH, "extracted_data", f"{exp_id}_extracted.json")
    
    if not os.path.exists(extracted_data_path):
        print(f"Error: No extracted data found at {extracted_data_path}")
        return None
        
    try:
        with open(extracted_data_path, 'r') as f:
            extracted_functions = json.load(f)
        
        # Convert to a more convenient format
        functions_dict = {}
        for func in extracted_functions:
            func_name = func.get("function_name", "")
            if not func_name:
                continue
                
            functions_dict[func_name] = {
                "code": func.get("function_code", ""),
                "repo_name": func.get("file", {}).get("file_module", {}).get("repo", {}).get("repo_name", ""),
                "file_path": func.get("file", {}).get("file_module", {}).get("module_id", {}).get("identifier", ""),
                "type": "function"  # Default, can be refined later
            }
            
        print(f"Loaded {len(functions_dict)} functions from {extracted_data_path}")
        return functions_dict
    
    except Exception as e:
        print(f"Error loading extracted data: {e}")
        return None

def detect_function_calls(functions_dict):
    """
    Analyze function code to detect calls to other functions in the dataset.
    
    Args:
        functions_dict: Dictionary of functions to analyze
        
    Returns:
        Dictionary of function calls (caller -> list of callees)
    """
    function_calls = defaultdict(list)
    function_names = list(functions_dict.keys())
    
    # Sort function names by length (descending) to avoid substring matches
    function_names.sort(key=len, reverse=True)
    
    # Regex patterns for function call detection
    # This is a simplistic approach and might need refinements for complex code
    patterns = [
        r'(\b{}\s*\([^)]*\))',  # Basic function call: function_name(args)
        r'(\b{}\b)',            # Just the function name without parentheses
    ]
    
    for caller, caller_info in functions_dict.items():
        code = caller_info["code"]
        
        if not code:
            continue
            
        # Look for calls to other functions
        for callee in function_names:
            if callee == caller:
                continue  # Skip self-calls
                
            # Check for callee name in the code using different patterns
            for pattern_template in patterns:
                pattern = pattern_template.format(re.escape(callee))
                if re.search(pattern, code):
                    # Found a potential call
                    function_calls[caller].append(callee)
                    break  # Move to the next callee
    
    return function_calls

def build_relationship_graph(functions_dict, function_calls):
    """
    Build a NetworkX graph representing function relationships.
    
    Args:
        functions_dict: Dictionary of functions with metadata
        function_calls: Dictionary of function calls
        
    Returns:
        NetworkX graph object
    """
    G = nx.DiGraph()
    
    # Add nodes for each function
    for func_name, func_info in functions_dict.items():
        G.add_node(
            func_name, 
            type=func_info["type"],
            repo=func_info["repo_name"],
            file=func_info["file_path"]
        )
    
    # Add edges for function calls
    for caller, callees in function_calls.items():
        for callee in callees:
            if callee in G:  # Make sure callee exists in graph
                G.add_edge(caller, callee, relationship="calls")
    
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    return G

def find_related_functions(G, query_results, depth=1):
    """
    Find functions related to the query results.
    
    Args:
        G: NetworkX graph of functions
        query_results: List of function names from query results
        depth: How many levels of relationships to include
        
    Returns:
        Subgraph containing related functions
    """
    related_nodes = set(query_results)
    
    # Find n-level neighbors
    for _ in range(depth):
        new_neighbors = set()
        for node in related_nodes:
            if node in G:
                # Get predecessors and successors
                predecessors = set(G.predecessors(node))
                successors = set(G.successors(node))
                new_neighbors.update(predecessors)
                new_neighbors.update(successors)
        
        related_nodes.update(new_neighbors)
    
    # Create subgraph of nodes that exist in G
    valid_nodes = [node for node in related_nodes if node in G]
    return G.subgraph(valid_nodes)

def detect_common_patterns(functions_dict, query_results):
    """
    Detect common patterns in the top search results.
    
    Args:
        functions_dict: Dictionary of functions with metadata
        query_results: List of function names from query results
        
    Returns:
        Dictionary of detected patterns and classifications
    """
    # Get code for the top results
    top_functions = {f: functions_dict[f]["code"] for f in query_results if f in functions_dict}
    
    patterns = {
        "AST processing": [
            r'ast\.', 
            r'\bast\b',
            r'abstract syntax tree',
            r'parse',
            r'syntax'
        ],
        "Graph operations": [
            r'graph',
            r'node',
            r'edge',
            r'traverse',
            r'visit',
            r'successor',
            r'predecessor'
        ],
        "Control flow": [
            r'control flow',
            r'cfg',
            r'branch',
            r'loop',
            r'conditional',
            r'if.*?else',
            r'while',
            r'for'
        ],
        "Data flow": [
            r'data flow',
            r'variable',
            r'assign',
            r'read',
            r'write',
            r'access'
        ],
        "Visualization": [
            r'visualize',
            r'graphviz',
            r'draw',
            r'plot',
            r'render'
        ]
    }
    
    # Analyze each function
    function_patterns = {}
    for func_name, code in top_functions.items():
        function_patterns[func_name] = set()
        
        for pattern_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, code, re.IGNORECASE):
                    function_patterns[func_name].add(pattern_name)
                    break
    
    return function_patterns

def visualize_graph(G, output_path=None, highlight_nodes=None):
    """
    Visualize the function relationship graph.
    
    Args:
        G: NetworkX graph to visualize
        output_path: Path to save the visualization (if None, display it)
        highlight_nodes: List of node names to highlight
    """
    if not G.nodes:
        print("Graph has no nodes to visualize.")
        return

    plt.figure(figsize=(12, 10))
    
    # Get positions for nodes
    pos = nx.spring_layout(G, seed=42)
    
    # Extract node attributes for visualization
    node_colors = []
    for node in G.nodes():
        if highlight_nodes and node in highlight_nodes:
            node_colors.append('red')
        else:
            node_colors.append('lightblue')
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color=node_colors, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, arrowsize=15)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=8)
    
    plt.title("Function Relationship Graph")
    plt.axis("off")
    
    if output_path:
        plt.savefig(output_path, format="png", dpi=300, bbox_inches="tight")
        print(f"Graph visualization saved to {output_path}")
    else:
        try:
            plt.savefig("/tmp/graph_vis.png", format="png", dpi=300, bbox_inches="tight")
            print(f"Graph visualization saved to /tmp/graph_vis.png")
        except Exception as e:
            print(f"Error saving visualization: {e}")
        plt.close()

def process_query_results(query_results_file):
    """
    Process query results from living documentation.
    
    Args:
        query_results_file: Path to the research doc with query results
        
    Returns:
        Dictionary of query results for each experiment
    """
    try:
        with open(query_results_file, 'r') as f:
            content = f.read()
        
        # Simple pattern matching to extract query results
        # This is a basic implementation and could be improved
        queries = {}
        current_query = None
        current_exp_id = None
        current_functions = []
        
        # Regex to find query sections
        query_pattern = r'## Query: "(.*?)" on (.*?) \(.*?\)'
        top_results_pattern = r'\*\*(\d+)\. (.*?)\*\* \((.*?)\)'
        
        # Find all queries
        for line in content.split('\n'):
            query_match = re.match(query_pattern, line)
            if query_match:
                # Save previous query if exists
                if current_query and current_exp_id:
                    queries[(current_query, current_exp_id)] = current_functions
                
                # Start new query
                current_query = query_match.group(1)
                current_exp_id = query_match.group(2)
                current_functions = []
                continue
            
            # Find top results in current query
            result_match = re.match(top_results_pattern, line)
            if current_query and result_match:
                func_name = result_match.group(2)
                current_functions.append(func_name)
        
        # Save the last query
        if current_query and current_exp_id:
            queries[(current_query, current_exp_id)] = current_functions
            
        return queries
        
    except Exception as e:
        print(f"Error processing query results: {e}")
        return {}

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="R2E Function Graph Visualization")
    parser.add_argument("--exp_id", type=str, default=None, help="Experiment ID to analyze")
    parser.add_argument("--query", type=str, default=None, help="Focus on functions matching this query")
    parser.add_argument("--depth", type=int, default=1, help="Relationship depth to include")
    parser.add_argument("--output", type=str, default=None, help="Output file path for the visualization")
    parser.add_argument("--from_docs", action="store_true", help="Extract queries from research documentation")
    
    args = parser.parse_args()
    
    if args.from_docs:
        # Process existing query results
        doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "research_doc.md")
        queries = process_query_results(doc_path)
        
        if not queries:
            print("No queries found in research documentation.")
            return
            
        print(f"Found {len(queries)} queries in documentation:")
        for i, ((query, exp_id), functions) in enumerate(queries.items()):
            print(f"{i+1}. \"{query}\" on {exp_id} ({len(functions)} functions)")
        
        # Process each query
        for (query, exp_id), functions in queries.items():
            if not functions:
                continue  # Skip if no functions found
                
            print(f"\nProcessing query \"{query}\" on {exp_id}...")
            
            # Load functions for this experiment
            functions_dict = load_extracted_functions(exp_id)
            if not functions_dict:
                continue
                
            # Detect function calls
            function_calls = detect_function_calls(functions_dict)
            
            # Build the graph
            G = build_relationship_graph(functions_dict, function_calls)
            
            # Find related functions
            if functions:
                subgraph = find_related_functions(G, functions, depth=args.depth)
                
                # Detect patterns
                patterns = detect_common_patterns(functions_dict, functions)
                print("\nDetected patterns in top functions:")
                for func, pattern_set in patterns.items():
                    if pattern_set:
                        print(f"- {func}: {', '.join(pattern_set)}")
                    
                # Visualize
                output_path = None
                if args.output:
                    base, ext = os.path.splitext(args.output)
                    output_path = f"{base}_{exp_id}_{query.replace(' ', '_')}{ext}"
                else:
                    output_path = f"/Users/imac/Desktop/r2e_env/docs/graphs/{exp_id}_{query.replace(' ', '_')}.png"
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                visualize_graph(subgraph, output_path, highlight_nodes=functions)
    else:
        # Process a single experiment
        if not args.exp_id:
            print("Error: Please provide an experiment ID with --exp_id")
            return
            
        # Load functions
        functions_dict = load_extracted_functions(args.exp_id)
        if not functions_dict:
            return
            
        # Detect function calls
        function_calls = detect_function_calls(functions_dict)
        
        # Build the graph
        G = build_relationship_graph(functions_dict, function_calls)
        
        # Find relevant subgraph if query provided
        query_functions = list(functions_dict.keys())
        if args.query:
            # Simple keyword matching to find relevant functions
            query_terms = args.query.lower().split()
            query_functions = []
            
            for func_name, func_info in functions_dict.items():
                text = f"{func_name} {func_info['code']}".lower()
                if all(term in text for term in query_terms):
                    query_functions.append(func_name)
            
            print(f"Found {len(query_functions)} functions matching query \"{args.query}\"")
            
            if query_functions:
                G = find_related_functions(G, query_functions, depth=args.depth)
        
        # Visualize the graph
        output_path = args.output
        if not output_path:
            query_str = args.query.replace(' ', '_') if args.query else "all"
            output_path = f"/Users/imac/Desktop/r2e_env/docs/graphs/{args.exp_id}_{query_str}.png"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        visualize_graph(G, output_path, highlight_nodes=query_functions if args.query else None)

if __name__ == "__main__":
    main()