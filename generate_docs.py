#!/usr/bin/env python3
"""
Generate documentation for R2E extracted functions
"""

import os
import sys
import json
import pandas as pd
import markdown
from pathlib import Path
import argparse
import datetime

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_available_experiments():
    """Get list of available R2E experiments."""
    bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
    extracted_data_dir = os.path.join(bucket_path, "extracted_data")
    
    if not os.path.exists(extracted_data_dir):
        return []
    
    files = [f for f in os.listdir(extracted_data_dir) if f.endswith("_extracted.json")]
    return [f.replace("_extracted.json", "") for f in files]

def load_experiment_data(exp_id):
    """Load extracted functions from an experiment."""
    bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
    extracted_data_path = os.path.join(bucket_path, "extracted_data", f"{exp_id}_extracted.json")
    
    if not os.path.exists(extracted_data_path):
        print(f"Error: No extracted data found for {exp_id}")
        return None
    
    try:
        with open(extracted_data_path, 'r') as f:
            raw_data = json.load(f)
        
        # Convert to DataFrame
        functions_df = pd.DataFrame([
            {
                "function_name": func.get("function_name", ""),
                "repo_name": func.get("file", {}).get("file_module", {}).get("repo", {}).get("repo_name", ""),
                "file_path": func.get("file", {}).get("file_module", {}).get("module_id", {}).get("identifier", ""),
                "code": func.get("function_code", "")
            }
            for func in raw_data
        ])
        
        print(f"Loaded {len(functions_df)} functions for {exp_id}")
        return functions_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def generate_documentation(exp_id):
    """Generate documentation for an experiment."""
    # Create directory for documentation
    docs_dir = os.path.join(BASE_DIR, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    # Output files
    md_file = os.path.join(docs_dir, f"{exp_id}_documentation.md")
    html_file = os.path.join(docs_dir, f"{exp_id}_documentation.html")
    
    # Load the function data
    functions_df = load_experiment_data(exp_id)
    if functions_df is None or len(functions_df) == 0:
        print(f"No functions found for {exp_id}")
        return None
    
    # Generate markdown documentation
    with open(md_file, "w") as f:
        f.write(f"# Documentation for {exp_id}\n\n")
        f.write("## Overview\n\n")
        f.write(f"This documentation was automatically generated for the {exp_id} experiment. ")
        f.write(f"It contains {len(functions_df)} functions from the extracted repositories.\n\n")
        
        f.write("## Functions by Repository\n\n")
        
        # Group by repository
        repos = functions_df['repo_name'].unique()
        for repo in repos:
            repo_functions = functions_df[functions_df['repo_name'] == repo]
            f.write(f"### Repository: {repo}\n\n")
            f.write(f"Contains {len(repo_functions)} functions.\n\n")
            
            # List all functions in this repo
            for _, func in repo_functions.iterrows():
                f.write(f"#### {func['function_name']}\n\n")
                
                if func['file_path']:
                    f.write(f"File: `{func['file_path']}`\n\n")
                
                # Add the code with syntax highlighting
                if func['code']:
                    f.write("```python\n")
                    f.write(func['code'])
                    f.write("\n```\n\n")
        
        # Add a basic relationships section
        f.write("## Function Relationships\n\n")
        f.write("Common relationships between functions:\n\n")
        
        # Create a simple relationship map based on file paths
        for repo in repos:
            repo_functions = functions_df[functions_df['repo_name'] == repo]
            file_paths = repo_functions['file_path'].unique()
            
            for file_path in file_paths:
                if not file_path:
                    continue
                    
                file_functions = repo_functions[repo_functions['file_path'] == file_path]
                if len(file_functions) > 1:
                    file_name = file_path.split("/")[-1] if "/" in file_path else file_path
                    f.write(f"### Functions in {file_name}\n\n")
                    for _, func in file_functions.iterrows():
                        f.write(f"- {func['function_name']}\n")
                    f.write("\n")
    
    # Generate HTML version
    try:
        with open(md_file, "r") as f:
            md_content = f.read()
        
        html_content = markdown.markdown(md_content, extensions=['fenced_code'])
        
        # Create HTML file with styling
        with open(html_file, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentation for {exp_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4 {{ color: #333; }}
        h2 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        .navigation {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            max-height: 300px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    {html_content}
    <script>
        // Add table of contents
        window.onload = function() {{
            const toc = document.createElement('div');
            toc.className = 'navigation';
            toc.innerHTML = '<h3>Table of Contents</h3><ul></ul>';
            
            const headings = document.querySelectorAll('h2, h3, h4');
            const tocList = toc.querySelector('ul');
            
            headings.forEach(function(heading) {{
                const link = document.createElement('a');
                link.textContent = heading.textContent;
                link.href = '#' + heading.id;
                
                if (!heading.id) {{
                    heading.id = heading.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-');
                }}
                
                const item = document.createElement('li');
                item.style.marginLeft = (heading.tagName.substring(1) - 2) * 10 + 'px';
                item.appendChild(link);
                tocList.appendChild(item);
            }});
            
            document.body.appendChild(toc);
        }};
    </script>
</body>
</html>""")
        
        print(f"HTML documentation generated: {html_file}")
        return html_file
    except Exception as e:
        print(f"Error generating HTML: {e}")
        return md_file

def main():
    parser = argparse.ArgumentParser(description="Generate documentation for R2E experiments")
    parser.add_argument("--exp_id", type=str, help="Experiment ID to document")
    parser.add_argument("--all", action="store_true", help="Document all experiments")
    
    args = parser.parse_args()
    
    if args.all:
        # Get all experiments
        experiments = get_available_experiments()
        if not experiments:
            print("No experiments found. Please extract functions from repositories first.")
            return
            
        for exp_id in experiments:
            print(f"Generating documentation for {exp_id}...")
            generate_documentation(exp_id)
            
    elif args.exp_id:
        generate_documentation(args.exp_id)
    else:
        print("Please specify an experiment ID with --exp_id or use --all")
        parser.print_help()

if __name__ == "__main__":
    main()