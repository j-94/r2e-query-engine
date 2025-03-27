#!/usr/bin/env python3
"""
Search across multiple repositories with R2E Query Engine
"""

import os
import sys
import glob
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add current directory to path
sys.path.insert(0, BASE_DIR)

# Import R2EQueryEngine
from r2e_query_engine import R2EQueryEngine

def search_repository(exp_id, query, use_openrouter=False, show_code=False):
    """Search a single repository and return the results"""
    # Use environment variable for API key
    api_key = os.environ.get("OPENROUTER_API_KEY") if use_openrouter else os.environ.get("OPENAI_API_KEY")
    
    # Initialize the query engine
    engine = R2EQueryEngine(exp_id, api_key, use_openrouter=use_openrouter)
    
    # Load the extracted data
    if not engine.load_data():
        return pd.DataFrame()  # Return empty dataframe if loading fails
    
    # Perform the search
    results = engine.semantic_search(query)
    
    # Add repository identifier
    if not results.empty:
        results['experiment'] = exp_id
        
    return results

def get_all_experiments():
    """Get all available experiment IDs from extracted data directory"""
    bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
    extracted_data_dir = os.path.join(bucket_path, "extracted_data")
    
    if not os.path.exists(extracted_data_dir):
        return []
    
    # Find all extracted data files
    files = glob.glob(os.path.join(extracted_data_dir, "*_extracted.json"))
    experiments = [os.path.basename(f).replace("_extracted.json", "") for f in files]
    
    return experiments

def display_results(results, show_code=False):
    """Display the combined search results"""
    if results.empty:
        print("No matching functions found.")
        return
    
    # Sort by relevance
    results = results.sort_values('relevance', ascending=False)
    
    print(f"\nFound {len(results)} relevant functions across repositories:")
    
    for i, (_, func) in enumerate(results.iterrows()):
        exp_id = func.get('experiment', 'unknown')
        print(f"\n{i+1}. {func['function_name']} ({func['repo_name']}) [{exp_id}]")
        
        if 'relevance_score' in func:
            print(f"   Relevance: {func['relevance_score']}/10")
        if 'explanation' in func:
            print(f"   Why: {func['explanation']}")
        
        # Display code
        if show_code and 'code' in func and func['code']:
            if i < 5 or show_code:  # Show full code for top 5 or if explicitly requested
                code = func['code']
                print(f"\n   Code:\n   {code.replace(chr(10), chr(10)+'   ')}")
            else:
                # Show snippet for others
                code_snippet = func['code'][:150] + "..." if len(func['code']) > 150 else func['code']
                print(f"\n   Code snippet:\n   {code_snippet.replace(chr(10), chr(10)+'   ')}")

def main():
    parser = argparse.ArgumentParser(description="Search across multiple R2E repositories")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--experiments", type=str, nargs="*", help="Specific experiment IDs to search")
    parser.add_argument("--use_openrouter", action="store_true", help="Use OpenRouter API")
    parser.add_argument("--show-code", action="store_true", help="Show full code for functions")
    
    args = parser.parse_args()
    
    # Get experiments to search
    if args.experiments:
        experiments = args.experiments
    else:
        experiments = get_all_experiments()
        
    if not experiments:
        print("No experiments found. Extract functions from repositories first.")
        sys.exit(1)
    
    print(f"Searching across {len(experiments)} repositories: {', '.join(experiments)}")
    print(f"Query: {args.query}")
    
    # Perform searches in parallel
    all_results = []
    with ProcessPoolExecutor(max_workers=min(os.cpu_count(), len(experiments))) as executor:
        futures = [executor.submit(search_repository, exp_id, args.query, args.use_openrouter, args.show_code) 
                  for exp_id in experiments]
        
        for future in futures:
            results = future.result()
            if not results.empty:
                all_results.append(results)
    
    # Combine and display results
    if all_results:
        combined_results = pd.concat(all_results)
        display_results(combined_results, args.show_code)
    else:
        print("No matching functions found.")

if __name__ == "__main__":
    main()