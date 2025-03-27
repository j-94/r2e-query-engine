#!/usr/bin/env python3
"""
Test script for generating a prototype for parallel graph processing
"""

import os
import json
import sys
from pathlib import Path

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the base directory to sys.path
sys.path.insert(0, BASE_DIR)

# Import R2EQueryEngine
from r2e_query_engine import R2EQueryEngine

def main():
    """Generate a prototype for parallel graph processing research trajectory"""
    print("\n== Testing Prototype Generation with Gemini via OpenRouter ==\n")
    
    # Set OpenRouter API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize the query engine
    engine = R2EQueryEngine("quickstart", api_key, use_openrouter=True)
    
    # Load the extracted data
    if not engine.load_data():
        print("Failed to load data. Exiting.")
        sys.exit(1)

    # Create a sample research trajectory for parallel graph processing
    trajectory = {
        "title": "Parallel Graph Traversal for Large-Scale Network Analysis",
        "core_question": "How can we efficiently parallelize graph traversal algorithms to analyze massive networks?",
        "rationale": "Efficient parallel traversal is crucial for analyzing large-scale networks in a timely manner.",
        "existing_components": ["_program_graph_to_nx", "diameter", "max_betweenness"],
        "new_components": ["parallel_traversal", "distributed_processing", "load_balancing"],
        "challenges": ["synchronization", "partitioning", "communication overhead"],
        "evaluation": "Measure speedup and scalability across different network sizes"
    }
    
    # Generate prototype
    print(f"Generating prototype for: {trajectory['title']}")
    print(f"Using existing components: {', '.join(trajectory['existing_components'])}")
    code = engine.generate_prototype(trajectory)
    
    # Save the prototype
    if code:
        prototype_path = os.path.join(BASE_DIR, "parallel_graph_prototype.py")
        with open(prototype_path, 'w') as f:
            f.write(code)
        print(f"\nPrototype saved to {prototype_path}")
    else:
        print("Failed to generate prototype code.")

if __name__ == "__main__":
    main()