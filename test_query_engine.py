#!/usr/bin/env python3
"""
Test script for the R2E Query Engine that doesn't require user input
"""

import os
import sys
import subprocess
from pathlib import Path

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """Main function to test the R2E Query Engine."""
    print("\n== R2E Query Engine Test ==\n")
    
    # First, ensure pandas is installed in the main environment
    print("Installing required dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pandas", "numpy", "openai"],
        check=False,
    )
    
    # Try simple keyword search (no API key needed)
    print("\nTesting keyword search in existing extracted functions...")
    
    # Find the 'quickstart' extracted file or any other experiment
    bucket_path = os.path.expanduser("~/buckets/r2e_bucket")
    extracted_data_dir = os.path.join(bucket_path, "extracted_data")
    
    if not os.path.exists(extracted_data_dir):
        print(f"Error: Extracted data directory not found at {extracted_data_dir}")
        print("Please run 'r2e extract -e quickstart' first")
        return
    
    # Find any extracted data file
    extracted_files = [f for f in os.listdir(extracted_data_dir) if f.endswith("_extracted.json")]
    
    if not extracted_files:
        print("No extracted data files found. Please run 'r2e extract' first.")
        return
    
    # Use the first extracted file
    experiment_id = extracted_files[0].replace("_extracted.json", "")
    print(f"Found experiment: {experiment_id}")
    
    # Run the query engine with a simple keyword search
    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "r2e_query_engine.py"),
        "--exp_id", experiment_id,
        "--query", "graph algorithm"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)
    
    print("\nTest completed. If you see results above, the query engine is working!")
    print("For interactive mode, run: python r2e_query_wrapper.py")

if __name__ == "__main__":
    main()