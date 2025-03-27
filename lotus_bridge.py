#!/usr/bin/env python3
"""
LOTUS Bridge - Connect R2E Query Engine with LOTUS semantic operators
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import importlib.util
from typing import List, Dict, Any, Optional, Union, Callable

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add current directory to path
sys.path.insert(0, BASE_DIR)

# Import R2EQueryEngine
from r2e_query_engine import R2EQueryEngine

class LOTUSBridge:
    """Bridge between R2E Query Engine and LOTUS semantic operators."""
    
    def __init__(self, exp_id: str, api_key: Optional[str] = None, use_openrouter: bool = False):
        """Initialize the LOTUS Bridge.
        
        Args:
            exp_id: The experiment ID used in R2E
            api_key: Optional API key for LLM services
            use_openrouter: Whether to use OpenRouter API
        """
        self.r2e_engine = R2EQueryEngine(exp_id, api_key, use_openrouter)
        self.lotus_available = self._check_lotus_available()
        
        if self.lotus_available:
            import lotus
            from lotus.models import LM
            self.lotus = lotus
            
            # Configure LOTUS with the same API key
            if api_key:
                lm = LM(model="gpt-4-turbo")
                self.lotus.settings.configure(lm=lm)
        
        # Load R2E data
        self.r2e_engine.load_data()
    
    def _check_lotus_available(self) -> bool:
        """Check if LOTUS library is available."""
        try:
            lotus_spec = importlib.util.find_spec("lotus")
            return lotus_spec is not None
        except ImportError:
            return False
    
    def search(self, query: str) -> pd.DataFrame:
        """Perform a semantic search using R2E engine.
        
        Args:
            query: The search query
            
        Returns:
            DataFrame of results
        """
        return self.r2e_engine.semantic_search(query)
    
    def sem_filter(self, df: pd.DataFrame, filter_query: str) -> pd.DataFrame:
        """Apply semantic filtering using LOTUS if available.
        
        Args:
            df: DataFrame to filter
            filter_query: Natural language filter query
            
        Returns:
            Filtered DataFrame
        """
        if not self.lotus_available:
            print("LOTUS not available. Using basic keyword matching instead.")
            # Fall back to basic filtering
            keywords = filter_query.lower().split()
            
            def contains_keywords(row):
                text = f"{row['function_name']} {row['code']}".lower()
                return all(keyword in text for keyword in keywords)
            
            return df[df.apply(contains_keywords, axis=1)]
        
        # Use LOTUS semantic filtering
        return df.sem_filter(filter_query)
    
    def sem_join(self, df1: pd.DataFrame, df2: pd.DataFrame, join_query: str) -> pd.DataFrame:
        """Perform semantic join between two DataFrames.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            join_query: Natural language join condition
            
        Returns:
            Joined DataFrame
        """
        if not self.lotus_available:
            print("LOTUS not available. Using basic cross join instead.")
            # Fall back to basic cross join with similarity scoring
            result = []
            
            for _, row1 in df1.iterrows():
                for _, row2 in df2.iterrows():
                    # Compute a simple similarity score
                    score = self._compute_similarity(row1, row2)
                    if score > 0.5:  # Arbitrary threshold
                        combined = {**row1.to_dict(), **{f"df2_{k}": v for k, v in row2.to_dict().items()}}
                        combined['similarity'] = score
                        result.append(combined)
            
            return pd.DataFrame(result)
        
        # Use LOTUS semantic join
        return df1.sem_join(df2, join_query)
    
    def _compute_similarity(self, row1, row2) -> float:
        """Compute simple similarity between two rows."""
        # Extract text to compare
        text1 = f"{row1['function_name']} {row1.get('code', '')}"
        text2 = f"{row2['function_name']} {row2.get('code', '')}"
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def generate_research(self, df: pd.DataFrame, research_query: str) -> List[Dict[str, Any]]:
        """Generate research trajectories from function data.
        
        Args:
            df: DataFrame containing function data
            research_query: Research question
            
        Returns:
            List of research trajectories
        """
        return self.r2e_engine.generate_research_trajectories(research_query)
    
    def get_available_experiments(self) -> List[str]:
        """Get list of available R2E experiments."""
        bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
        extracted_data_dir = os.path.join(bucket_path, "extracted_data")
        
        if not os.path.exists(extracted_data_dir):
            return []
        
        files = [f for f in os.listdir(extracted_data_dir) if f.endswith("_extracted.json")]
        return [f.replace("_extracted.json", "") for f in files]

def generate_lotus_documentation(exp_id, api_key=None, use_openrouter=False):
    """Generate documentation using LOTUS semantic capabilities."""
    bridge = LOTUSBridge(exp_id, api_key, use_openrouter)
    
    # Directory for documentation
    docs_dir = os.path.join(BASE_DIR, "lotus_docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    # Output files
    md_file = os.path.join(docs_dir, f"{exp_id}_documentation.md")
    html_file = os.path.join(docs_dir, f"{exp_id}_documentation.html")
    
    # Get all functions from the experiment - use direct file access as fallback
    try:
        all_functions = bridge.search("")
    except Exception as e:
        print(f"Error using search API: {e}")
        print("Trying direct file access...")
        
        try:
            # Direct file access as fallback
            bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
            extracted_data_path = os.path.join(bucket_path, "extracted_data", f"{exp_id}_extracted.json")
            
            with open(extracted_data_path, 'r') as f:
                raw_data = json.load(f)
            
            # Convert to DataFrame manually
            all_functions = pd.DataFrame([
                {
                    "function_name": func.get("function_name", ""),
                    "repo_name": func.get("file", {}).get("file_module", {}).get("repo", {}).get("repo_name", ""),
                    "file_path": func.get("file", {}).get("file_module", {}).get("module_id", {}).get("identifier", ""),
                    "code": func.get("function_code", "")
                }
                for func in raw_data
            ])
            print(f"Loaded {len(all_functions)} functions directly from file")
        except Exception as e:
            print(f"Error loading directly from file: {e}")
            all_functions = pd.DataFrame()
    
    if len(all_functions) == 0:
        print(f"No functions found in experiment {exp_id}")
        return None
    
    # If LOTUS is available, use it for advanced documentation
    if bridge.lotus_available:
        print("Using LOTUS for semantic documentation generation...")
        
        # Convert functions to specialized dataframe for LOTUS
        functions_df = pd.DataFrame(all_functions)
        
        # Use LOTUS to generate structured documentation
        try:
            # Create documentation sections with semantic operations
            overview = bridge.lotus.make_prompt("Generate a comprehensive overview for a code repository based on these functions")
            # Get summary using semantic map
            summary_df = functions_df.sem_map(
                "Summarize this function in one concise paragraph",
                input_col="code",
                output_col="summary"
            )
            
            # Group functions by purpose
            grouped_df = functions_df.sem_group_by(
                "What is the main purpose of this function? Choose one from: [Utility, Core, Analysis, Visualization, Data Processing]",
                input_col="code", 
                output_col="category"
            )
            
            # Generate relationship graph
            relations_df = functions_df.sem_join(
                functions_df, 
                "Describe how {function_name} could be used together with or is related to {function_name}",
                threshold=0.7
            )
            
            # Generate markdown documentation
            with open(md_file, "w") as f:
                f.write(f"# Documentation for {exp_id}\n\n")
                f.write("## Overview\n\n")
                f.write(overview)
                f.write("\n\n## Function Categories\n\n")
                
                for category, group in grouped_df.groupby("category"):
                    f.write(f"### {category}\n\n")
                    for _, func in group.iterrows():
                        f.write(f"#### {func['function_name']}\n\n")
                        f.write(f"**Summary**: {func['summary']}\n\n")
                        f.write("```python\n{func['code']}\n```\n\n")
                
                f.write("## Function Relationships\n\n")
                for _, rel in relations_df.iterrows():
                    f.write(f"- {rel['function_name']} → {rel['function_name_right']}: {rel['relationship']}\n")
                    
            # Convert to HTML
            try:
                import markdown
                with open(md_file, "r") as f:
                    md_content = f.read()
                
                html_content = markdown.markdown(md_content, extensions=['fenced_code'])
                
                with open(html_file, "w") as f:
                    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentation for {exp_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3, h4 {{ color: #333; }}
        code {{ background-color: #f5f5f5; padding: 2px 4px; }}
        pre {{ background-color: #f5f5f5; padding: 15px; overflow-x: auto; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>""")
                
                print(f"HTML documentation generated: {html_file}")
            except Exception as e:
                print(f"Error generating HTML: {e}")
                
            return md_file
            
        except Exception as e:
            print(f"Error using LOTUS for documentation: {e}")
            print("Falling back to standard documentation...")
    
    # If LOTUS is not available or failed, fall back to simpler documentation
    with open(md_file, "w") as f:
        f.write(f"# Documentation for {exp_id}\n\n")
        f.write("## Functions\n\n")
        
        # Group by repo_name
        grouped = all_functions.groupby("repo_name")
        for repo_name, group in grouped:
            f.write(f"### Repository: {repo_name}\n\n")
            
            for _, func in group.iterrows():
                f.write(f"#### {func['function_name']}\n\n")
                if 'code' in func and func['code']:
                    f.write("```python\n")
                    f.write(func['code'])
                    f.write("\n```\n\n")
    
    print(f"Documentation generated: {md_file}")
    return md_file

def start_web_ui():
    """Start a simple web UI for LOTUS Bridge."""
    try:
        import gradio as gr
    except ImportError:
        print("Gradio not installed. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio"])
        import gradio as gr

    # Get available experiments
    bridge = LOTUSBridge("quickstart")  # Temporary instance to access methods
    experiments = bridge.get_available_experiments()
    
    if not experiments:
        print("No experiments found. Please extract functions from repositories first.")
        return

    # Create the UI
    with gr.Blocks(title="LOTUS Bridge UI") as ui:
        gr.Markdown("# LOTUS Bridge - R2E Query Engine with LOTUS-inspired Semantic Operations")
        
        with gr.Row():
            with gr.Column():
                experiment = gr.Dropdown(
                    experiments, 
                    label="Select Experiment", 
                    value=experiments[0] if experiments else None
                )
                api_key = gr.Textbox(label="API Key (OpenAI or OpenRouter)", type="password")
                use_openrouter = gr.Checkbox(label="Use OpenRouter", value=False)
                
        with gr.Tabs():
            with gr.TabItem("Semantic Search"):
                search_query = gr.Textbox(label="Search Query")
                search_button = gr.Button("Search")
                search_results = gr.Dataframe(label="Search Results")
                
            with gr.TabItem("Semantic Filter"):
                filter_query = gr.Textbox(label="Filter Query")
                filter_button = gr.Button("Apply Filter")
                filter_results = gr.Dataframe(label="Filtered Results")
                
            with gr.TabItem("Research Generation"):
                research_query = gr.Textbox(label="Research Question")
                research_button = gr.Button("Generate Research Trajectories")
                research_results = gr.JSON(label="Research Trajectories")
                
            with gr.TabItem("LOTUS Documentation"):
                gr.Markdown("""
                ## Generate Semantic Documentation
                
                This feature uses LOTUS to analyze your code and generate intelligent documentation,
                organizing functions by purpose, extracting relationships, and providing summaries.
                """)
                
                doc_experiment = gr.Dropdown(
                    experiments, 
                    label="Select Experiment to Document", 
                    value=experiments[0] if experiments else None
                )
                
                doc_buttons = gr.Row()
                with doc_buttons:
                    generate_doc_button = gr.Button("Generate Documentation")
                    generate_all_button = gr.Button("Document All Experiments")
                
                doc_output = gr.Textbox(label="Documentation Status", lines=10)
                doc_progress = gr.HTML(label="Generation Progress")
                
        # Define functionality
        def initialize_bridge(exp_id, api_key, use_openrouter):
            bridge = LOTUSBridge(exp_id, api_key, use_openrouter)
            return bridge
        
        def perform_search(exp_id, api_key, use_openrouter, query):
            bridge = initialize_bridge(exp_id, api_key, use_openrouter)
            results = bridge.search(query)
            # Select relevant columns for display
            display_cols = ["function_name", "repo_name", "relevance", "code"]
            return results[display_cols] if not results.empty else pd.DataFrame()
        
        def perform_filter(exp_id, api_key, use_openrouter, filter_text):
            bridge = initialize_bridge(exp_id, api_key, use_openrouter)
            results = bridge.search("")  # Get all functions
            filtered = bridge.sem_filter(results, filter_text)
            display_cols = ["function_name", "repo_name", "code"]
            return filtered[display_cols] if not filtered.empty else pd.DataFrame()
        
        def generate_research_trajectories(exp_id, api_key, use_openrouter, question):
            bridge = initialize_bridge(exp_id, api_key, use_openrouter)
            trajectories = bridge.generate_research(None, question)
            return trajectories if trajectories else []
            
        def generate_documentation_for_exp(exp_id, api_key, use_openrouter):
            try:
                doc_file = generate_lotus_documentation(exp_id, api_key, use_openrouter)
                if doc_file:
                    output = f"Documentation generated successfully.\n\nMarkdown: {doc_file}\n"
                    html_file = doc_file.replace(".md", ".html")
                    if os.path.exists(html_file):
                        output += f"HTML: {html_file}\n"
                        # Create a clickable link
                        progress_html = f'<a href="file://{html_file}" target="_blank">Open HTML Documentation</a>'
                        return output, progress_html
                    return output, ""
                return "Failed to generate documentation.", ""
            except Exception as e:
                return f"Error generating documentation: {e}", ""
        
        def generate_all_documentation(api_key, use_openrouter):
            output = "Starting documentation generation for all experiments:\n\n"
            progress_html = ""
            
            for exp_id in experiments:
                output += f"• Processing {exp_id}...\n"
                try:
                    doc_file = generate_lotus_documentation(exp_id, api_key, use_openrouter)
                    if doc_file:
                        output += f"  ✓ Success: {doc_file}\n"
                        html_file = doc_file.replace(".md", ".html")
                        if os.path.exists(html_file):
                            # Add a link to each documentation file
                            progress_html += f'<p><a href="file://{html_file}" target="_blank">Open {exp_id} Documentation</a></p>'
                    else:
                        output += f"  ✗ Failed: No functions found\n"
                except Exception as e:
                    output += f"  ✗ Error: {e}\n"
            
            output += "\nDocumentation generation completed."
            return output, progress_html
            
        # Connect UI elements
        search_button.click(
            perform_search,
            inputs=[experiment, api_key, use_openrouter, search_query],
            outputs=search_results
        )
        
        filter_button.click(
            perform_filter,
            inputs=[experiment, api_key, use_openrouter, filter_query],
            outputs=filter_results
        )
        
        research_button.click(
            generate_research_trajectories,
            inputs=[experiment, api_key, use_openrouter, research_query],
            outputs=research_results
        )
        
        # Documentation buttons
        generate_doc_button.click(
            generate_documentation_for_exp,
            inputs=[doc_experiment, api_key, use_openrouter],
            outputs=[doc_output, doc_progress]
        )
        
        generate_all_button.click(
            generate_all_documentation,
            inputs=[api_key, use_openrouter],
            outputs=[doc_output, doc_progress]
        )
    
    # Launch the UI
    ui.launch(share=False)

def main():
    parser = argparse.ArgumentParser(description="LOTUS Bridge for R2E Query Engine")
    parser.add_argument("--exp_id", type=str, help="R2E experiment ID")
    parser.add_argument("--api_key", type=str, help="API key for LLM services")
    parser.add_argument("--use_openrouter", action="store_true", help="Use OpenRouter API")
    parser.add_argument("--ui", action="store_true", help="Launch web UI")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--generate-docs", action="store_true", help="Generate LOTUS documentation")
    parser.add_argument("--all-experiments", action="store_true", help="Process all available experiments")
    
    args = parser.parse_args()
    
    # Get API key from environment if not provided
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    
    # Launch UI if requested
    if args.ui:
        start_web_ui()
        return
    
    # Get available experiments
    if args.all_experiments:
        bridge = LOTUSBridge("quickstart")  # Temporary instance to access methods
        experiments = bridge.get_available_experiments()
        if not experiments:
            print("No experiments found. Please extract functions from repositories first.")
            return
    else:
        if not args.exp_id:
            print("Please specify an experiment ID with --exp_id or use --all-experiments")
            parser.print_help()
            return
        experiments = [args.exp_id]
    
    # Generate documentation for all specified experiments
    if args.generate_docs:
        for exp_id in experiments:
            print(f"Generating LOTUS documentation for {exp_id}...")
            doc_file = generate_lotus_documentation(exp_id, api_key, args.use_openrouter)
            if doc_file:
                print(f"Documentation generated successfully: {doc_file}")
        return
    
    # For single experiment operations
    if not args.all_experiments:
        # Initialize bridge
        bridge = LOTUSBridge(args.exp_id, api_key, args.use_openrouter)
        
        # Perform search if query provided
        if args.query:
            results = bridge.search(args.query)
            print(f"Found {len(results)} relevant functions:")
            for i, (_, func) in enumerate(results.iterrows()):
                print(f"\n{i+1}. {func['function_name']} ({func['repo_name']})")
                print(f"   Relevance: {func.get('relevance_score', func.get('relevance', 0))}")
                if 'explanation' in func:
                    print(f"   Why: {func['explanation']}")
                
                # Show code snippet
                if i < 3 and 'code' in func and func['code']:
                    code_snippet = func['code'][:200] + "..." if len(func['code']) > 200 else func['code']
                    print(f"\n   Code snippet:\n   {code_snippet.replace(chr(10), chr(10)+'   ')}")
    
    # If no specific operation was requested
    if not (args.query or args.generate_docs or args.ui or args.all_experiments):
        print("No operation specified. Use --query, --generate-docs, or --ui")
        parser.print_help()

if __name__ == "__main__":
    main()