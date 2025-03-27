#!/usr/bin/env python3
"""
Living Documentation System - Automatically track and document repository research
"""

import os
import sys
import json
import time
import glob
import pandas as pd
from pathlib import Path
import argparse
import datetime
import markdown
from typing import List, Dict, Any, Optional, Union

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Docs directory for storing living documentation
DOCS_DIR = os.path.join(BASE_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

# Main documentation file
MAIN_DOC = os.path.join(DOCS_DIR, "research_doc.md")
if not os.path.exists(MAIN_DOC):
    with open(MAIN_DOC, "w") as f:
        f.write("# R2E Query Engine Research Documentation\n\n")
        f.write("*This is an automatically generated living document of your research.*\n\n")

class LivingDoc:
    """Living documentation system for R2E Query Engine research."""
    
    def __init__(self):
        """Initialize the living documentation system."""
        self.doc_path = MAIN_DOC
        self.experiments = self._get_available_experiments()
    
    def _get_available_experiments(self) -> List[str]:
        """Get list of available R2E experiments."""
        bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
        extracted_data_dir = os.path.join(bucket_path, "extracted_data")
        
        if not os.path.exists(extracted_data_dir):
            return []
        
        files = [f for f in os.listdir(extracted_data_dir) if f.endswith("_extracted.json")]
        return [f.replace("_extracted.json", "") for f in files]
    
    def _load_experiment_metadata(self, exp_id: str) -> Dict[str, Any]:
        """Load metadata about an experiment."""
        # Try to find repository info based on experiment ID
        if "_exp" in exp_id:
            repo_name = exp_id.replace("_exp", "")
        else:
            repo_name = exp_id
            
        # Default metadata if not found
        return {
            "name": exp_id,
            "repo": repo_name,
            "added_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "functions_count": "Unknown"  # Would need to load the actual file to count
        }
    
    def document_new_repository(self, repo_url: str, exp_id: str):
        """Document a newly added repository."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract repo name from URL
        repo_name = repo_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        
        # Create section header based on timestamp to avoid duplicates
        section_id = f"repo-{int(time.time())}"
        
        with open(self.doc_path, "a") as f:
            f.write(f"\n## Repository: {repo_name} ({exp_id}) {timestamp}\n\n")
            f.write(f"<div id='{section_id}'>\n\n")
            f.write(f"* **URL**: [{repo_url}]({repo_url})\n")
            f.write(f"* **Added**: {timestamp}\n")
            f.write(f"* **Experiment ID**: `{exp_id}`\n")
            f.write("\n### Initial Assessment\n\n")
            f.write("Repository added to the R2E Query Engine. Use the following command to search this repository:\n\n")
            f.write(f"```bash\n./r2e_query_engine.py --exp_id {exp_id} --query \"your search query\"\n```\n\n")
            f.write("</div>\n")
        
        print(f"Added documentation for {repo_name} to {self.doc_path}")
    
    def document_query(self, exp_id: str, query: str, results: pd.DataFrame, research: Optional[List] = None,
                         arxiv_url: Optional[str] = None):
        """
        Document the results of a query.
        
        Args:
            exp_id: Experiment ID
            query: The search query
            results: DataFrame containing the results
            research: Optional list of research trajectories
            arxiv_url: Optional arXiv URL used for context
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get experiment metadata if available
        exp_meta = self._load_experiment_metadata(exp_id)
        
        # Create section header based on timestamp
        section_id = f"query-{int(time.time())}"
        
        with open(self.doc_path, "a") as f:
            f.write(f"\n## Query: \"{query}\" on {exp_id} ({timestamp})\n\n")
            f.write(f"<div id='{section_id}'>\n\n")
            
            # Query details
            f.write(f"* **Repository**: {exp_meta['repo']}\n")
            f.write(f"* **Experiment ID**: `{exp_id}`\n")
            f.write(f"* **Timestamp**: {timestamp}\n")
            
            # Add arXiv information if provided
            if arxiv_url:
                f.write(f"* **arXiv Paper**: [{arxiv_url}]({arxiv_url})\n")
                
                # Try to extract paper metadata
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    
                    if "arxiv.org/abs/" in arxiv_url:
                        paper_id = arxiv_url.split("/abs/")[1].split(".")[0]
                        api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
                        response = requests.get(api_url)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'xml')
                            title = soup.find('title').text.strip()
                            abstract = soup.find('summary').text.strip()
                            authors = [author.find('name').text for author in soup.find_all('author')]
                            
                            f.write(f"* **Paper Title**: {title}\n")
                            f.write(f"* **Authors**: {', '.join(authors)}\n")
                            f.write("\n**Abstract**:\n\n")
                            f.write(f"> {abstract}\n\n")
                except Exception as e:
                    # Continue without the metadata
                    pass
            
            # Results summary
            f.write("\n### Results Summary\n\n")
            if results is None or len(results) == 0:
                f.write("No results found for this query.\n\n")
            else:
                f.write(f"Found {len(results)} relevant functions.\n\n")
                
                # Top 3 results
                f.write("#### Top Results\n\n")
                top_results = results.head(3)
                for i, (_, func) in enumerate(top_results.iterrows()):
                    f.write(f"**{i+1}. {func['function_name']}** ({func['repo_name']})\n\n")
                    if 'relevance_score' in func:
                        f.write(f"* Relevance: {func['relevance_score']}/10\n")
                    if 'explanation' in func:
                        f.write(f"* Why: {func['explanation']}\n")
                    f.write("\n")
                    
                    # Code snippet
                    if 'code' in func and func['code']:
                        code_snippet = func['code'][:200] + "..." if len(func['code']) > 200 else func['code']
                        f.write("```python\n")
                        f.write(code_snippet)
                        f.write("\n```\n\n")
            
            # Research trajectories if available
            if research and len(research) > 0:
                f.write("\n### Research Trajectories\n\n")
                for i, trajectory in enumerate(research):
                    f.write(f"#### {i+1}. {trajectory.get('title', 'Research Direction')}\n\n")
                    f.write(f"* **Question**: {trajectory.get('core_question', 'N/A')}\n")
                    f.write(f"* **Rationale**: {trajectory.get('rationale', 'N/A')[:200]}...\n")
                    
                    # Components
                    existing = trajectory.get('existing_components', [])
                    if existing:
                        f.write("* **Existing Components**: ")
                        f.write(", ".join(existing))
                        f.write("\n")
                    
                    new_comp = trajectory.get('new_components', [])
                    if new_comp:
                        f.write("* **New Components Needed**: ")
                        f.write(", ".join(new_comp))
                        f.write("\n\n")
            
            f.write("</div>\n")
        
        print(f"Added documentation for query '{query}' to {self.doc_path}")
    
    def document_prototype(self, exp_id: str, research_title: str, code: str):
        """Document a generated prototype."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a separate file for the prototype
        code_filename = f"prototype_{int(time.time())}.py"
        code_path = os.path.join(DOCS_DIR, code_filename)
        
        # Save the prototype code
        with open(code_path, "w") as f:
            f.write(f"# Prototype: {research_title}\n")
            f.write(f"# Generated: {timestamp}\n")
            f.write(f"# Based on experiment: {exp_id}\n\n")
            f.write(code)
        
        # Update the main documentation
        section_id = f"prototype-{int(time.time())}"
        
        with open(self.doc_path, "a") as f:
            f.write(f"\n## Prototype: {research_title} ({timestamp})\n\n")
            f.write(f"<div id='{section_id}'>\n\n")
            f.write(f"* **Based on**: Experiment `{exp_id}`\n")
            f.write(f"* **Generated**: {timestamp}\n")
            f.write(f"* **Saved as**: [{code_filename}](./docs/{code_filename})\n\n")
            
            # Code snippet
            snippet_length = min(20, len(code.split('\n')))
            snippet = '\n'.join(code.split('\n')[:snippet_length])
            if len(code.split('\n')) > snippet_length:
                snippet += "\n# ... (see full code in file)"
            
            f.write("```python\n")
            f.write(snippet)
            f.write("\n```\n\n")
            
            f.write("</div>\n")
        
        print(f"Added documentation for prototype '{research_title}' to {self.doc_path}")

    def generate_html(self):
        """Generate an HTML version of the documentation."""
        html_path = os.path.join(DOCS_DIR, "research_doc.html")
        
        # Read the markdown content
        with open(self.doc_path, "r") as f:
            md_content = f.read()
        
        # Convert to HTML
        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        # Add styling
        styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>R2E Query Engine Research Documentation</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
        }}
        h2 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 30px;
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
        div {{
            margin-bottom: 30px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
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
        // Add a table of contents
        window.onload = function() {{
            const toc = document.createElement('div');
            toc.className = 'navigation';
            toc.innerHTML = '<h3>Table of Contents</h3><ul></ul>';
            
            const headings = document.querySelectorAll('h2');
            const tocList = toc.querySelector('ul');
            
            headings.forEach((heading, index) => {{
                const link = document.createElement('a');
                link.textContent = heading.textContent;
                link.href = '#' + (heading.parentNode.id || `section-${{index}}`);
                
                if (!heading.parentNode.id) {{
                    heading.parentNode.id = `section-${{index}}`;
                }}
                
                const listItem = document.createElement('li');
                listItem.appendChild(link);
                tocList.appendChild(listItem);
            }});
            
            document.body.appendChild(toc);
        }};
    </script>
</body>
</html>
"""
        
        # Write the HTML file
        with open(html_path, "w") as f:
            f.write(styled_html)
        
        print(f"Generated HTML documentation at {html_path}")
        return html_path

def main():
    parser = argparse.ArgumentParser(description="Living Documentation for R2E Query Engine")
    parser.add_argument("--document_repo", action="store_true", help="Document a new repository")
    parser.add_argument("--repo_url", type=str, help="URL of the repository to document")
    parser.add_argument("--exp_id", type=str, help="Experiment ID to document")
    parser.add_argument("--query", type=str, help="Query to document")
    parser.add_argument("--generate_html", action="store_true", help="Generate HTML documentation")
    
    args = parser.parse_args()
    
    doc = LivingDoc()
    
    if args.document_repo and args.repo_url and args.exp_id:
        doc.document_new_repository(args.repo_url, args.exp_id)
    
    if args.query and args.exp_id:
        # Here we would normally run the query and get results
        # For now, just add a placeholder
        results = pd.DataFrame({
            "function_name": ["example_function1", "example_function2"],
            "repo_name": ["example_repo", "example_repo"],
            "relevance": [0.9, 0.8],
            "code": ["def example_function1():\n    return 'example'", "def example_function2():\n    return 'example'"]
        })
        doc.document_query(args.exp_id, args.query, results)
    
    if args.generate_html or (not args.document_repo and not args.query):
        html_path = doc.generate_html()
        # Try to open the HTML file in the default browser
        try:
            import webbrowser
            webbrowser.open(f"file://{html_path}")
        except:
            pass

if __name__ == "__main__":
    main()