#!/usr/bin/env python3
"""
Self-installing wrapper for the R2E Query Engine
Based on the article: https://treyhunner.com/2024/12/lazy-self-installing-python-scripts-with-uv/
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

# Base directory containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
DEPENDENCIES = [
    "pandas",
    "numpy", 
    "openai>=1.0.0",
    "rich",
]

# Path to virtual environment - prefer existing env if available
ENV_DIR = os.path.join(BASE_DIR, "env")
if os.path.exists(ENV_DIR):
    VENV_DIR = ENV_DIR
else:
    VENV_DIR = os.path.join(BASE_DIR, ".venv")
PYTHON = os.path.join(VENV_DIR, "bin", "python")
PIP = os.path.join(VENV_DIR, "bin", "pip")
UV = shutil.which("uv")  # Find uv in PATH

def is_venv_initialized():
    """Check if virtual environment exists and is properly initialized."""
    return os.path.exists(VENV_DIR) and os.path.exists(PYTHON)

def create_venv():
    """Create a virtual environment using uv."""
    try:
        print("🔧 Creating virtual environment...")
        if not UV:
            print("❌ uv not found in PATH. Installing venv using traditional methods.")
            subprocess.run(
                [sys.executable, "-m", "venv", VENV_DIR],
                check=True,
            )
            subprocess.run(
                [PIP, "install", "--upgrade", "pip"],
                check=True,
            )
        else:
            print(f"✅ Using uv: {UV}")
            subprocess.run(
                [UV, "venv", VENV_DIR],
                check=True,
                cwd=BASE_DIR,
            )
        print(f"✅ Virtual environment created at: {VENV_DIR}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    try:
        print("📦 Installing dependencies...")
        if UV:
            # Use UV if available
            subprocess.run(
                [UV, "pip", "install"] + DEPENDENCIES,
                check=True,
                cwd=BASE_DIR,
            )
        else:
            # Fall back to pip
            subprocess.run(
                [PIP, "install"] + DEPENDENCIES,
                check=True,
            )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_r2e_installation():
    """Check if R2E is installed and working."""
    try:
        result = subprocess.run(
            [PYTHON, "-c", "import sys; sys.path.insert(0, '.'); from r2e_query_engine import R2EQueryEngine; print('R2E Query Engine class loaded successfully')"],
            check=True,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )
        print(f"✅ R2E Query Engine successfully loaded: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking R2E installation: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def run_r2e_query_engine(args):
    """Run the R2E Query Engine with the given arguments."""
    try:
        print(f"🚀 Running R2E Query Engine with args: {args}")
        
        # Create a complete command list
        cmd = [PYTHON, os.path.join(BASE_DIR, "r2e_query_engine.py")] + args
        
        # Run the command
        subprocess.run(cmd, check=True, cwd=BASE_DIR)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running R2E Query Engine: {e}")
        return False

def setup():
    """Set up the environment if necessary."""
    if not is_venv_initialized():
        print("🔍 Virtual environment not found. Setting up now...")
        if not create_venv():
            return False
        if not install_dependencies():
            return False
    
    if not check_r2e_installation():
        print("⚠️ R2E Query Engine check failed. Will attempt to run anyway.")
    
    return True

def set_api_keys(non_interactive=False, use_openrouter=False):
    """Prompt for API keys if not set."""
    if use_openrouter:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("\n⚠️ OPENROUTER_API_KEY environment variable not set.")
            # Fall back to OpenAI key if available
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                os.environ["OPENROUTER_API_KEY"] = openai_key
                print("✅ Using OpenAI API key for OpenRouter")
                return
                
            if non_interactive:
                print("⚠️ Running in non-interactive mode. Will use keyword search only.")
                return
            try:
                api_key = input("Enter your OpenRouter API key (or press Enter to use keyword search only): ").strip()
                if api_key:
                    os.environ["OPENROUTER_API_KEY"] = api_key
                    print("✅ OpenRouter API key set for this session")
                else:
                    print("⚠️ No API key provided. Will use keyword search only.")
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️ Input interrupted. Will use keyword search only.")
        else:
            print("✅ Using OpenRouter API key from environment")
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("\n⚠️ OPENAI_API_KEY environment variable not set.")
            if non_interactive:
                print("⚠️ Running in non-interactive mode. Will use keyword search only.")
                return
            try:
                api_key = input("Enter your OpenAI API key (or press Enter to use keyword search only): ").strip()
                if api_key:
                    os.environ["OPENAI_API_KEY"] = api_key
                    print("✅ OpenAI API key set for this session")
                else:
                    print("⚠️ No API key provided. Will use keyword search only.")
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️ Input interrupted. Will use keyword search only.")
        else:
            print("✅ Using OpenAI API key from environment")

def main():
    """Main entry point."""
    print("\n🔍 R2E Query Engine Wrapper")
    
    if not setup():
        print("❌ Setup failed. Exiting.")
        sys.exit(1)
    
    # Initialize cmd_args list
    cmd_args = []
    
    # Check command line options
    non_interactive = "--non-interactive" in sys.argv
    if non_interactive:
        sys.argv.remove("--non-interactive")
    
    use_openrouter = "--use_openrouter" in sys.argv
    if use_openrouter:
        sys.argv.remove("--use_openrouter")
        # Add the flag back for the query engine
        cmd_args.append("--use_openrouter")
    
    # Set API keys based on which service we're using
    set_api_keys(non_interactive=non_interactive, use_openrouter=use_openrouter)
    
    # Get experiment ID
    exp_id = None
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--exp_id" and i+1 < len(sys.argv[1:]):
            exp_id = sys.argv[i+2]
            break
    
    if not exp_id:
        # By default, use 'quickstart'
        exp_id = "quickstart"
        print(f"ℹ️ No experiment ID provided. Using default: '{exp_id}'")
        cmd_args = ["--exp_id", exp_id] + sys.argv[1:]
    else:
        cmd_args = sys.argv[1:]
    
    # If no action specified, use interactive mode
    if "--interactive" not in cmd_args and "--query" not in cmd_args:
        print("ℹ️ No action specified. Starting interactive mode.")
        cmd_args.append("--interactive")
    
    # Run the query engine
    run_r2e_query_engine(cmd_args)

if __name__ == "__main__":
    main()