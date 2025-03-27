#!/usr/bin/env python3
"""
R2E Environment Main Entry Point

This serves as a command-line interface to access all the functionality
of the R2E environment, including repository management, semantic search,
research trajectory generation, and documentation.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def print_color(text, color="blue"):
    """Print colored text to the terminal."""
    colors = {
        "blue": "\033[94m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m",
        "bold": "\033[1m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def list_experiments():
    """List all available experiments in the R2E environment."""
    bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
    extracted_data_dir = os.path.join(bucket_path, "extracted_data")
    
    if not os.path.exists(extracted_data_dir):
        print_color("No experiments found. Use 'add-repo' to add a repository first.", "yellow")
        return []
    
    files = [f for f in os.listdir(extracted_data_dir) if f.endswith("_extracted.json")]
    experiments = [f.replace("_extracted.json", "") for f in files]
    
    print_color("Available experiments:", "bold")
    for i, exp in enumerate(experiments):
        print(f"  {i+1}. {exp}")
    
    return experiments

def add_repository(repo_url, exp_id):
    """Add a new repository to the R2E environment."""
    script_path = os.path.join(BASE_DIR, "add_repo.sh")
    
    if not os.path.exists(script_path):
        print_color(f"Error: add_repo.sh script not found at {script_path}", "red")
        return False
    
    try:
        print_color(f"Adding repository {repo_url} as experiment '{exp_id}'...", "blue")
        result = subprocess.run(["bash", script_path, repo_url, exp_id], 
                                check=True, capture_output=True, text=True)
        print(result.stdout)
        print_color("Repository added successfully!", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"Error adding repository: {e}", "red")
        print(e.stderr)
        return False

def search_repository(exp_id, query, arxiv_url=None, show_code=False):
    """Search within a repository using the R2E Query Engine."""
    script_path = os.path.join(BASE_DIR, "r2e_query_engine.py")
    
    if not os.path.exists(script_path):
        print_color(f"Error: r2e_query_engine.py not found at {script_path}", "red")
        return False
    
    cmd = [sys.executable, script_path, "--exp_id", exp_id, "--query", query, "--document"]
    
    if show_code:
        cmd.append("--show-code")
        
    if arxiv_url:
        cmd.extend(["--arxiv", arxiv_url])
    
    try:
        print_color(f"Searching in experiment '{exp_id}' for: {query}", "blue")
        if arxiv_url:
            print_color(f"Using arXiv paper as context: {arxiv_url}", "blue")
            
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"Error during search: {e}", "red")
        return False

def generate_research(exp_id, research_query, arxiv_url=None):
    """Generate research trajectories based on a query."""
    script_path = os.path.join(BASE_DIR, "r2e_query_engine.py")
    
    if not os.path.exists(script_path):
        print_color(f"Error: r2e_query_engine.py not found at {script_path}", "red")
        return False
    
    cmd = [sys.executable, script_path, "--exp_id", exp_id, "--research", research_query, "--document"]
    
    if arxiv_url:
        cmd.extend(["--arxiv", arxiv_url])
    
    try:
        print_color(f"Generating research trajectories in '{exp_id}' for: {research_query}", "blue")
        if arxiv_url:
            print_color(f"Using arXiv paper as context: {arxiv_url}", "blue")
            
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"Error generating research: {e}", "red")
        return False

def start_lotus_ui():
    """Start the LOTUS Bridge UI for interactive exploration."""
    script_path = os.path.join(BASE_DIR, "lotus_bridge.py")
    
    if not os.path.exists(script_path):
        print_color(f"Error: lotus_bridge.py not found at {script_path}", "red")
        return False
    
    try:
        print_color("Starting LOTUS Bridge UI...", "blue")
        subprocess.run([sys.executable, script_path, "--ui"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"Error starting UI: {e}", "red")
        return False

def generate_documentation(exp_id=None):
    """Generate documentation for one or all experiments."""
    script_path = os.path.join(BASE_DIR, "generate_docs.py")
    
    if not os.path.exists(script_path):
        # Try living_doc.py as fallback
        script_path = os.path.join(BASE_DIR, "living_doc.py")
        if not os.path.exists(script_path):
            print_color("Error: No documentation generator found", "red")
            return False
    
    try:
        if exp_id:
            print_color(f"Generating documentation for experiment '{exp_id}'...", "blue")
            subprocess.run([sys.executable, script_path, "--exp_id", exp_id], check=True)
        else:
            print_color("Generating documentation for all experiments...", "blue")
            subprocess.run([sys.executable, script_path, "--generate_html"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"Error generating documentation: {e}", "red")
        return False

def interactive_mode():
    """Start an interactive session."""
    print_color("\n===== R2E Environment Interactive Mode =====", "bold")
    print_color("Type 'help' for available commands, 'exit' to quit\n", "blue")
    
    experiments = list_experiments()
    current_exp = experiments[0] if experiments else None
    
    while True:
        if current_exp:
            prompt = f"r2e ({current_exp})> "
        else:
            prompt = "r2e> "
            
        try:
            cmd = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
            
        if not cmd:
            continue
            
        parts = cmd.split()
        command = parts[0].lower()
        
        if command == "exit" or command == "quit":
            break
            
        elif command == "help":
            print_color("\nAvailable commands:", "bold")
            print("  list                       - List available experiments")
            print("  use <exp_id>               - Switch to a different experiment")
            print("  add-repo <url> <exp_id>    - Add a new repository")
            print("  search <query> [--arxiv url] - Search in current experiment")
            print("  research <query> [--arxiv url] - Generate research trajectories")
            print("  ui                         - Start the LOTUS Bridge UI")
            print("  docs [exp_id]              - Generate documentation")
            print("  exit                       - Exit the interactive mode")
            
        elif command == "list":
            experiments = list_experiments()
            
        elif command == "use":
            if len(parts) < 2:
                print_color("Error: Missing experiment ID", "red")
                continue
                
            exp_id = parts[1]
            if exp_id in experiments:
                current_exp = exp_id
                print_color(f"Switched to experiment: {current_exp}", "green")
            else:
                print_color(f"Error: Experiment '{exp_id}' not found", "red")
                
        elif command == "add-repo":
            if len(parts) < 3:
                print_color("Error: Missing repository URL or experiment ID", "red")
                print("Usage: add-repo <url> <exp_id>")
                continue
                
            repo_url = parts[1]
            exp_id = parts[2]
            if add_repository(repo_url, exp_id):
                experiments = list_experiments()
                current_exp = exp_id
                
        elif command == "search":
            if not current_exp:
                print_color("Error: No experiment selected. Use 'use <exp_id>' first.", "red")
                continue
                
            if len(parts) < 2:
                print_color("Error: Missing search query", "red")
                continue
                
            # Check for --arxiv flag
            arxiv_url = None
            show_code = False
            query_parts = []
            
            i = 1
            while i < len(parts):
                if parts[i] == "--arxiv" and i+1 < len(parts):
                    arxiv_url = parts[i+1]
                    i += 2
                elif parts[i] == "--show-code":
                    show_code = True
                    i += 1
                else:
                    query_parts.append(parts[i])
                    i += 1
            
            query = " ".join(query_parts)
            search_repository(current_exp, query, arxiv_url, show_code)
            
        elif command == "research":
            if not current_exp:
                print_color("Error: No experiment selected. Use 'use <exp_id>' first.", "red")
                continue
                
            if len(parts) < 2:
                print_color("Error: Missing research query", "red")
                continue
                
            # Check for --arxiv flag
            arxiv_url = None
            query_parts = []
            
            i = 1
            while i < len(parts):
                if parts[i] == "--arxiv" and i+1 < len(parts):
                    arxiv_url = parts[i+1]
                    i += 2
                else:
                    query_parts.append(parts[i])
                    i += 1
            
            query = " ".join(query_parts)
            generate_research(current_exp, query, arxiv_url)
            
        elif command == "ui":
            start_lotus_ui()
            
        elif command == "docs":
            if len(parts) > 1:
                generate_documentation(parts[1])
            else:
                generate_documentation()
                
        else:
            print_color(f"Unknown command: {command}", "red")
            print("Type 'help' for available commands")

def main():
    parser = argparse.ArgumentParser(description="R2E Environment - Integrated Interface for all R2E Tools")
    
    # Add commands as subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available experiments")
    
    # Add repository command
    add_parser = subparsers.add_parser("add-repo", help="Add a new repository")
    add_parser.add_argument("url", help="URL of the repository to add")
    add_parser.add_argument("exp_id", help="Experiment ID to use for this repository")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search within a repository")
    search_parser.add_argument("exp_id", help="Experiment ID to search in")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--arxiv", help="arXiv paper URL to include as context")
    search_parser.add_argument("--show-code", action="store_true", help="Show full code in results")
    
    # Research command
    research_parser = subparsers.add_parser("research", help="Generate research trajectories")
    research_parser.add_argument("exp_id", help="Experiment ID to use")
    research_parser.add_argument("query", help="Research question or direction")
    research_parser.add_argument("--arxiv", help="arXiv paper URL to include as context")
    
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Start the LOTUS Bridge UI")
    
    # Documentation command
    docs_parser = subparsers.add_parser("docs", help="Generate documentation")
    docs_parser.add_argument("exp_id", nargs="?", help="Experiment ID (optional, generates for all if not specified)")
    
    # Interactive mode command
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive mode")
    
    args = parser.parse_args()
    
    # Default to interactive mode if no command provided
    if not args.command:
        interactive_mode()
        return
    
    # Execute the appropriate command
    if args.command == "list":
        list_experiments()
        
    elif args.command == "add-repo":
        add_repository(args.url, args.exp_id)
        
    elif args.command == "search":
        search_repository(args.exp_id, args.query, args.arxiv, args.show_code)
        
    elif args.command == "research":
        generate_research(args.exp_id, args.query, args.arxiv)
        
    elif args.command == "ui":
        start_lotus_ui()
        
    elif args.command == "docs":
        generate_documentation(args.exp_id)
        
    elif args.command == "interactive":
        interactive_mode()

if __name__ == "__main__":
    main()