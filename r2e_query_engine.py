#!/usr/bin/env python
"""
R2E Query Engine - A tool for semantic querying of code extracted with R2E

This script implements core functionality similar to LOTUS but tailored
specifically for working with code extracted from R2E.
"""

import json
import os
import sys
import subprocess
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import re
import argparse
import requests
from pathlib import Path
from openai import OpenAI

# Configuration
R2E_BUCKET_PATH = os.path.expanduser("~/buckets/r2e_bucket")
R2E_REPOS_PATH = os.path.expanduser("~/buckets/local_repoeval_bucket/repos")

class OpenRouterClient:
    """A client for OpenRouter API to access various LLM models."""
    
    def __init__(self, api_key: str):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: The OpenRouter API key
        """
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        
    def chat_completions_create(self, model: str, messages: List[Dict], 
                                temperature: float = 0.7, 
                                response_format: Optional[Dict] = None,
                                max_tokens: Optional[int] = None):
        """
        Create a chat completion using OpenRouter API.
        
        Args:
            model: The model to use (e.g., "openai/gpt-4")
            messages: List of message objects
            temperature: Sampling temperature
            response_format: Desired format for the response
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response object similar to OpenAI's response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        if response_format:
            payload["response_format"] = response_format
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Error code: {response.status_code} - {response.text}")
            
        # Print the raw response for debugging
        print(f"OpenRouter response status: {response.status_code}")
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Raw response: {response.text[:500]}...")
            raise Exception(f"Failed to decode OpenRouter response")

class R2EQueryEngine:
    """A query engine for code extracted by R2E using LLMs."""
    
    def __init__(self, exp_id: str, api_key: Optional[str] = None, use_openrouter: bool = False):
        """
        Initialize the R2E Query Engine.
        
        Args:
            exp_id: The experiment ID used in R2E
            api_key: Optional API key (falls back to env var)
            use_openrouter: Whether to use OpenRouter API instead of OpenAI
        """
        self.exp_id = exp_id
        self.functions_df = None
        self.extracted_data_path = os.path.join(R2E_BUCKET_PATH, "extracted_data", f"{exp_id}_extracted.json")
        self.use_openrouter = use_openrouter
        
        # Initialize LLM client
        if use_openrouter:
            self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                print("Warning: No OpenRouter API key provided. LLM queries will not work.")
            else:
                self.client = OpenRouterClient(api_key=self.api_key)
                print("Using OpenRouter for LLM queries.")
        else:
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                print("Warning: No OpenAI API key provided. LLM queries will not work.")
            else:
                self.client = OpenAI(api_key=self.api_key)
    
    def load_data(self) -> bool:
        """
        Load the extracted functions data from R2E.
        
        Returns:
            bool: True if data was loaded successfully
        """
        if not os.path.exists(self.extracted_data_path):
            print(f"Error: No extracted data found at {self.extracted_data_path}")
            print(f"Run 'r2e extract -e {self.exp_id}' first")
            return False
            
        try:
            with open(self.extracted_data_path, 'r') as f:
                extracted_functions = json.load(f)
            
            # Convert to DataFrame for easier querying based on the actual format
            self.functions_df = pd.DataFrame([
                {
                    "function_name": func.get("function_name", ""),
                    "repo_name": func.get("file", {}).get("file_module", {}).get("repo", {}).get("repo_name", ""),
                    "file_path": func.get("file", {}).get("file_module", {}).get("module_id", {}).get("identifier", ""),
                    "signature": "",  # Not in the current format
                    "docstring": "",  # Not in the current format
                    "code": func.get("function_code", ""),
                    "params": "",  # Not in the current format
                    "return_type": "",  # Not in the current format
                    "function_type": "function",  # Default
                    "source": f"{func.get('file', {}).get('file_module', {}).get('repo', {}).get('repo_id', '')}"
                }
                for func in extracted_functions
            ])
            
            print(f"Loaded {len(self.functions_df)} functions from {self.extracted_data_path}")
            return True
            
        except Exception as e:
            print(f"Error loading extracted data: {e}")
            return False
    
    def simple_keyword_search(self, keywords: str) -> pd.DataFrame:
        """
        Perform a simple keyword search across all functions.
        
        Args:
            keywords: Space-separated keywords to search for
            
        Returns:
            DataFrame of matching functions
        """
        if self.functions_df is None:
            print("No data loaded. Call load_data() first.")
            return pd.DataFrame()
            
        keywords = keywords.lower().split()
        
        # Create a simple relevance score based on keyword matches
        def score_function(row):
            # Focus primarily on code and function name since docstring isn't available
            text = f"{row['function_name']} {row['code']}".lower()
            return sum(1 for keyword in keywords if keyword in text)
        
        self.functions_df['relevance'] = self.functions_df.apply(score_function, axis=1)
        results = self.functions_df[self.functions_df['relevance'] > 0].sort_values('relevance', ascending=False)
        
        return results.reset_index(drop=True)
    
    def semantic_search(self, query: str, limit: int = 10, arxiv_url: Optional[str] = None) -> pd.DataFrame:
        """
        Perform a semantic search using LLM to find relevant functions.
        
        Args:
            query: Natural language query about code
            limit: Maximum number of results to return
            arxiv_url: Optional arXiv paper URL to include in context
            
        Returns:
            DataFrame of matching functions ranked by relevance
        """
        if self.functions_df is None:
            print("No data loaded. Call load_data() first.")
            return pd.DataFrame()
            
        if not self.api_key:
            print("No API key provided. Falling back to keyword search.")
            return self.simple_keyword_search(query)
        
        # Fetch arXiv paper content if URL provided
        arxiv_context = ""
        if arxiv_url:
            try:
                import requests
                from bs4 import BeautifulSoup

                # Convert to PDF URL if not already
                if "arxiv.org/abs/" in arxiv_url:
                    paper_id = arxiv_url.split("/abs/")[1].split(".")[0]
                    pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
                elif "arxiv.org/pdf/" in arxiv_url:
                    pdf_url = arxiv_url
                else:
                    print(f"Invalid arXiv URL format: {arxiv_url}")
                    pdf_url = None
                
                if pdf_url:
                    # Use the arxiv API to get metadata instead of parsing PDF
                    # This is a more reliable way to get the abstract
                    api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
                    response = requests.get(api_url)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'xml')
                        title = soup.find('title').text.strip()
                        abstract = soup.find('summary').text.strip()
                        authors = [author.find('name').text for author in soup.find_all('author')]
                        
                        arxiv_context = f"""
ARXIV PAPER CONTEXT:
Title: {title}
Authors: {', '.join(authors)}
URL: {arxiv_url}
Abstract: {abstract}
"""
                        print(f"Successfully retrieved arXiv paper: {title}")
            except Exception as e:
                print(f"Error fetching arXiv paper: {e}")
                # Continue without the paper context
        
        # Group functions by repo for context
        repos = self.functions_df['repo_name'].unique()
        
        prompt = f"""
You are a code analysis assistant. I will provide you with a list of functions 
extracted from various repositories, and your task is to find the most relevant 
ones for the following query:

QUERY: {query}

First, analyze what the query is asking for, then identify the most relevant 
functions based on their name, docstring, and functionality.

{arxiv_context}

For each repository you'll analyze functions from, I will provide:
- Repository name
- List of functions with their signatures and docstrings

REPOSITORIES:
"""
        
        # Add information about each repository's functions
        for repo in repos:
            repo_funcs = self.functions_df[self.functions_df['repo_name'] == repo].head(50)  # Limit per repo to avoid token limits
            
            if len(repo_funcs) == 0:
                continue
                
            prompt += f"\n=== Repository: {repo} ===\n"
            
            for _, func in repo_funcs.iterrows():
                prompt += f"\nFunction: {func['function_name']}\n"
                prompt += f"Signature: {func['signature']}\n"
                if func['docstring']:
                    # Truncate long docstrings
                    docstring = func['docstring']
                    if len(docstring) > 200:
                        docstring = docstring[:200] + "..."
                    prompt += f"Description: {docstring}\n"
        
        prompt += f"""
Based on the information provided, identify the {limit} most relevant functions for the query.
For each function, provide:
1. The function name
2. The repository it's from
3. A relevance score from 0-10 (10 being most relevant)
4. A brief explanation of why it's relevant

Format your response as a JSON array with this structure:
[
  {{
    "function_name": "example_function",
    "repo_name": "example_repo",
    "relevance_score": 9,
    "explanation": "This function is highly relevant because..."
  }},
  ...
]

IMPORTANT: Only include functions that are genuinely relevant to the query.
"""
        
        try:
            if self.use_openrouter:
                try:
                    # Use OpenRouter client
                    print("Making OpenRouter API request with Google Gemini 2.5...")
                    
                    # Wrap the prompt to emphasize JSON format
                    json_prompt = f"""
{prompt}

CRITICAL: You MUST respond with valid JSON only. Your response must be a JSON object with a 'results' array containing objects with the fields: function_name, repo_name, relevance_score, and explanation.

Example response format:
{{
  "results": [
    {{
      "function_name": "example_function",
      "repo_name": "example_repo",
      "relevance_score": 9,
      "explanation": "This function is relevant because..."
    }}
  ]
}}
"""
                    
                    # Try to use Google Gemini 2.5 Pro Flash if available (or fall back to a similar model)
                    try:
                        response = self.client.chat_completions_create(
                            model="google/gemini-pro",  # Using Google Gemini Pro
                            messages=[
                                {"role": "system", "content": "You are a code analysis assistant that helps find relevant functions in repositories. You MUST return valid JSON."},
                                {"role": "user", "content": json_prompt}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.2
                        )
                    except Exception as e:
                        print(f"Failed to use Gemini: {e}, falling back to GPT model")
                        response = self.client.chat_completions_create(
                            model="openai/gpt-3.5-turbo",  # Fallback to GPT-3.5-Turbo 
                            messages=[
                                {"role": "system", "content": "You are a code analysis assistant that helps find relevant functions in repositories. You MUST return valid JSON."},
                                {"role": "user", "content": json_prompt}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.2
                        )
                    
                    # Print debug information
                    print(f"OpenRouter response received with type: {type(response)}")
                    
                    # Parse the OpenRouter response
                    if "choices" in response and len(response["choices"]) > 0:
                        content = response["choices"][0]["message"]["content"]
                        print(f"Content received: {content[:100]}...")
                        try:
                            parsed_content = json.loads(content)
                            results = parsed_content.get("results", [])
                        except json.JSONDecodeError as e:
                            print(f"Error parsing content as JSON: {e}")
                            print(f"Raw content: {content[:200]}...")
                            # Fall back to keyword search
                            return self.simple_keyword_search(query)
                    else:
                        print(f"Unexpected response structure: {response.keys()}")
                        # Fall back to keyword search
                        return self.simple_keyword_search(query)
                except Exception as e:
                    print(f"OpenRouter request failed: {e}")
                    # Fall back to keyword search
                    return self.simple_keyword_search(query)
            else:
                # Use OpenAI client
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a code analysis assistant that helps find relevant functions in repositories."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                
                # Parse the OpenAI response
                content = response.choices[0].message.content
                results = json.loads(content).get("results", [])
            
            # Match with our dataframe to get complete information
            relevant_functions = []
            for result in results:
                func_name = result.get("function_name")
                repo_name = result.get("repo_name")
                
                # Find the matching function in our dataframe
                matches = self.functions_df[
                    (self.functions_df['function_name'] == func_name) & 
                    (self.functions_df['repo_name'] == repo_name)
                ]
                
                if len(matches) > 0:
                    func_data = matches.iloc[0].to_dict()
                    func_data['relevance_score'] = result.get("relevance_score", 0)
                    func_data['explanation'] = result.get("explanation", "")
                    relevant_functions.append(func_data)
            
            # Convert to DataFrame and sort by relevance
            results_df = pd.DataFrame(relevant_functions)
            if len(results_df) > 0:
                results_df = results_df.sort_values('relevance_score', ascending=False)
            
            return results_df
            
        except Exception as e:
            print(f"Error performing semantic search: {e}")
            return self.simple_keyword_search(query)
    
    def generate_research_trajectories(self, query: str, num_trajectories: int = 3) -> List[Dict[str, Any]]:
        """
        Generate potential research trajectories based on a query and the available code.
        
        Args:
            query: Research question or direction
            num_trajectories: Number of research trajectories to generate
            
        Returns:
            List of research trajectories with details
        """
        if self.functions_df is None:
            print("No data loaded. Call load_data() first.")
            return []
            
        if not self.api_key:
            print("API key required for generating research trajectories.")
            return []
        
        # First, find relevant functions for this query
        relevant_functions = self.semantic_search(query, limit=20)
        
        if len(relevant_functions) == 0:
            print("No relevant functions found for this research query.")
            return []
        
        # Extract the most relevant functions with their details
        functions_context = []
        for _, func in relevant_functions.iterrows():
            functions_context.append({
                "name": func['function_name'],
                "repo": func['repo_name'],
                "signature": func['signature'],
                "docstring": func['docstring'][:200] + "..." if len(func['docstring']) > 200 else func['docstring']
            })
        
        prompt = f"""
You are a research assistant helping to identify promising research trajectories 
based on available code components. Given a research question and a set of functions 
extracted from various repositories, suggest {num_trajectories} potential research 
trajectories.

RESEARCH QUESTION: {query}

AVAILABLE CODE COMPONENTS:
{json.dumps(functions_context, indent=2)}

For each research trajectory, provide:
1. A title for the research direction
2. A description of the core research question/objective
3. An explanation of why this is interesting and potentially impactful
4. The key components that would be used from the available functions
5. What new components would need to be developed
6. Potential challenges and approaches to address them
7. How you would evaluate success

Format your response as a JSON array with this structure:
[
  {{
    "title": "Research Trajectory Title",
    "core_question": "Specific research question to investigate",
    "rationale": "Why this direction is interesting and impactful",
    "existing_components": ["component1", "component2", ...],
    "new_components": ["new_component1", "new_component2", ...],
    "challenges": ["challenge1", "challenge2", ...],
    "evaluation": "How to evaluate success"
  }},
  ...
]

IMPORTANT: The research trajectories should be novel, feasible given the available 
components, and have clear potential for impact. They should also be distinct from 
each other to explore different possibilities.
"""
        
        try:
            if self.use_openrouter:
                try:
                    # Use OpenRouter client
                    print("Making OpenRouter research request with Google Gemini...")
                    
                    # Wrap the prompt to emphasize JSON format
                    json_prompt = f"""
{prompt}

CRITICAL: You MUST respond with valid JSON only. Your response must be a JSON object with a 'trajectories' array containing objects with the fields specified in the prompt.

Example response format:
{{
  "trajectories": [
    {{
      "title": "Research Trajectory Title",
      "core_question": "Specific research question to investigate",
      "rationale": "Why this direction is interesting and impactful",
      "existing_components": ["component1", "component2"],
      "new_components": ["new_component1", "new_component2"],
      "challenges": ["challenge1", "challenge2"],
      "evaluation": "How to evaluate success"
    }}
  ]
}}
"""
                    
                    # Try to use Google Gemini Pro for research trajectory generation
                    try:
                        response = self.client.chat_completions_create(
                            model="google/gemini-pro",  # Using Google Gemini Pro
                            messages=[
                                {"role": "system", "content": "You are a research assistant that helps identify promising and creative research directions. You MUST return valid JSON."},
                                {"role": "user", "content": json_prompt}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.7  # Higher temperature for more creative research ideas
                        )
                    except Exception as e:
                        print(f"Failed to use Gemini for research generation: {e}, falling back to GPT model")
                        response = self.client.chat_completions_create(
                            model="openai/gpt-3.5-turbo",  # Fallback to GPT-3.5-Turbo
                            messages=[
                                {"role": "system", "content": "You are a research assistant that helps identify promising research directions. You MUST return valid JSON."},
                                {"role": "user", "content": json_prompt}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.7  # Higher temperature for more creative research ideas
                        )
                    
                    # Print debug information
                    print(f"OpenRouter research response received")
                    
                    # Parse the OpenRouter response
                    if "choices" in response and len(response["choices"]) > 0:
                        content = response["choices"][0]["message"]["content"]
                        try:
                            parsed_content = json.loads(content)
                            trajectories = parsed_content.get("trajectories", [])
                        except json.JSONDecodeError as e:
                            print(f"Error parsing research response as JSON: {e}")
                            return []
                    else:
                        print(f"Unexpected research response structure")
                        return []
                except Exception as e:
                    print(f"OpenRouter research request failed: {e}")
                    return []
            else:
                # Use OpenAI client
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a research assistant that helps identify promising research directions."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7  # Higher temperature for more creative research ideas
                )
                
                # Parse the OpenAI response
                content = response.choices[0].message.content
                trajectories = json.loads(content).get("trajectories", [])
            
            return trajectories
            
        except Exception as e:
            print(f"Error generating research trajectories: {e}")
            return []
    
    def generate_prototype(self, research_trajectory: Dict[str, Any]) -> str:
        """
        Generate a prototype implementation for a research trajectory.
        
        Args:
            research_trajectory: A research trajectory dictionary
            
        Returns:
            String containing prototype code
        """
        if self.functions_df is None:
            print("No data loaded. Call load_data() first.")
            return ""
            
        if not self.api_key:
            print("API key required for generating prototype code.")
            return ""
        
        # Extract existing components that would be used
        existing_components = research_trajectory.get("existing_components", [])
        
        # Get the actual code for these components
        component_details = []
        for component in existing_components:
            matches = self.functions_df[self.functions_df['function_name'] == component]
            if len(matches) > 0:
                component_details.append({
                    "name": matches.iloc[0]['function_name'],
                    "signature": matches.iloc[0]['signature'],
                    "code": matches.iloc[0]['code'],
                    "docstring": matches.iloc[0]['docstring']
                })
        
        prompt = f"""
You are tasked with creating a prototype implementation for a research project. 
I will provide you with a research trajectory and existing code components to leverage.

RESEARCH TRAJECTORY:
{json.dumps(research_trajectory, indent=2)}

EXISTING COMPONENTS TO USE:
{json.dumps(component_details, indent=2)}

Your task is to generate a prototype implementation that:
1. Implements the core functionality needed for this research direction
2. Leverages the existing components appropriately
3. Adds new components as specified in the research trajectory
4. Includes clear comments and documentation
5. Follows best practices for code organization

The prototype should be a complete Python module that can be executed and tested.
Include all necessary imports, class definitions, and a main function that demonstrates
the prototype functionality.

FORMAT YOUR RESPONSE AS VALID PYTHON CODE ONLY, WITHOUT ANY ADDITIONAL EXPLANATION OR MARKDOWN.
"""
        
        try:
            if self.use_openrouter:
                try:
                    # Use OpenRouter client
                    print("Making OpenRouter prototype generation request with Google Gemini...")
                    
                    # Prepare the prompt for code generation
                    code_prompt = f"""
{prompt}

IMPORTANT: Respond with ONLY valid Python code. Do not include any other text or explanations.
The code should be well-structured, properly commented, and follow best practices.
Include proper error handling and make the code modular and maintainable.
"""
                    
                    # Try to use Google Gemini Pro for code generation
                    try:
                        response = self.client.chat_completions_create(
                            model="google/gemini-pro",  # Using Google Gemini Pro
                            messages=[
                                {"role": "system", "content": "You are a research code generator that creates prototype implementations. You excel at writing clean, efficient Python code. Respond with ONLY valid Python code."},
                                {"role": "user", "content": code_prompt}
                            ],
                            temperature=0.2  # Lower temperature for more focused code generation
                        )
                    except Exception as e:
                        print(f"Failed to use Gemini for code generation: {e}, falling back to GPT model")
                        response = self.client.chat_completions_create(
                            model="openai/gpt-3.5-turbo",  # Fallback to GPT-3.5-Turbo
                            messages=[
                                {"role": "system", "content": "You are a research code generator that creates prototype implementations. Respond with ONLY valid Python code."},
                                {"role": "user", "content": code_prompt}
                            ],
                            temperature=0.2  # Lower temperature for more focused code generation
                        )
                    
                    # Print debug information
                    print(f"OpenRouter prototype response received")
                    
                    # Return the generated code from OpenRouter
                    if "choices" in response and len(response["choices"]) > 0:
                        return response["choices"][0]["message"]["content"]
                    else:
                        print("Unexpected prototype response structure")
                        return ""
                except Exception as e:
                    print(f"OpenRouter prototype request failed: {e}")
                    return ""
            else:
                # Use OpenAI client
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a research code generator that creates prototype implementations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2  # Lower temperature for more focused code generation
                )
                
                # Return the generated code from OpenAI
                return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating prototype code: {e}")
            return ""
    
    def interactive_mode(self):
        """Start an interactive query session."""
        print("\n===== R2E Query Engine Interactive Mode =====")
        print(f"Experiment ID: {self.exp_id}")
        print("Type 'exit' to quit, 'help' for commands\n")
        
        while True:
            command = input("\nCommand (search/research/prototype/help/exit): ").strip().lower()
            
            if command == 'exit':
                break
                
            elif command == 'help':
                print("\nAvailable commands:")
                print("  search <query>    - Search for relevant functions")
                print("  research <query>  - Generate research trajectories")
                print("  prototype <index> - Generate prototype for research trajectory")
                print("  help              - Show this help message")
                print("  exit              - Exit the interactive mode")
            
            elif command.startswith('search '):
                query = command[7:]
                print(f"\nSearching for: {query}")
                results = self.semantic_search(query)
                
                if len(results) == 0:
                    print("No matching functions found.")
                else:
                    print(f"\nFound {len(results)} relevant functions:")
                    for i, (_, func) in enumerate(results.iterrows()):
                        print(f"\n{i+1}. {func['function_name']} ({func['repo_name']})")
                        print(f"   Relevance: {func['relevance_score']}/10")
                        print(f"   Why: {func['explanation']}")
                        
                    # Option to show more details
                    while True:
                        detail_idx = input("\nEnter number to see function details (or press Enter to continue): ")
                        if not detail_idx:
                            break
                            
                        try:
                            idx = int(detail_idx) - 1
                            if 0 <= idx < len(results):
                                func = results.iloc[idx]
                                print(f"\n=== {func['function_name']} ===")
                                print(f"Repository: {func['repo_name']}")
                                print(f"File: {func['file_path']}")
                                print(f"Signature: {func['signature']}")
                                if func['docstring']:
                                    print(f"\nDocstring:\n{func['docstring']}")
                                print(f"\nCode:\n{func['code']}")
                            else:
                                print("Invalid index.")
                        except ValueError:
                            print("Please enter a valid number.")
            
            elif command.startswith('research '):
                query = command[9:]
                print(f"\nGenerating research trajectories for: {query}")
                self.current_trajectories = self.generate_research_trajectories(query)
                
                if not self.current_trajectories:
                    print("Failed to generate research trajectories.")
                else:
                    print(f"\nGenerated {len(self.current_trajectories)} research trajectories:")
                    for i, trajectory in enumerate(self.current_trajectories):
                        print(f"\n{i+1}. {trajectory['title']}")
                        print(f"   Core Question: {trajectory['core_question']}")
                        print(f"   Rationale: {trajectory['rationale'][:100]}...")
                        print(f"   Existing Components: {', '.join(trajectory['existing_components'])}")
                    
                    # Option to see more details
                    while True:
                        detail_idx = input("\nEnter number to see trajectory details (or press Enter to continue): ")
                        if not detail_idx:
                            break
                            
                        try:
                            idx = int(detail_idx) - 1
                            if 0 <= idx < len(self.current_trajectories):
                                trajectory = self.current_trajectories[idx]
                                print(f"\n=== {trajectory['title']} ===")
                                print(f"Core Question: {trajectory['core_question']}")
                                print(f"\nRationale:\n{trajectory['rationale']}")
                                print(f"\nExisting Components:")
                                for comp in trajectory['existing_components']:
                                    print(f"  - {comp}")
                                print(f"\nNew Components to Develop:")
                                for comp in trajectory['new_components']:
                                    print(f"  - {comp}")
                                print(f"\nChallenges:")
                                for challenge in trajectory['challenges']:
                                    print(f"  - {challenge}")
                                print(f"\nEvaluation:\n{trajectory['evaluation']}")
                            else:
                                print("Invalid index.")
                        except ValueError:
                            print("Please enter a valid number.")
                        except KeyError:
                            print("Trajectory details incomplete.")
            
            elif command.startswith('prototype '):
                idx_str = command[10:]
                try:
                    idx = int(idx_str) - 1
                    if hasattr(self, 'current_trajectories') and 0 <= idx < len(self.current_trajectories):
                        trajectory = self.current_trajectories[idx]
                        print(f"\nGenerating prototype for: {trajectory['title']}")
                        code = self.generate_prototype(trajectory)
                        
                        if code:
                            print("\n=== Generated Prototype ===\n")
                            print(code)
                            
                            # Option to save the code
                            save = input("\nSave prototype to file? (y/n): ").strip().lower()
                            if save == 'y':
                                filename = f"prototype_{idx+1}_{trajectory['title'].replace(' ', '_').lower()}.py"
                                with open(filename, 'w') as f:
                                    f.write(code)
                                print(f"Prototype saved to {filename}")
                        else:
                            print("Failed to generate prototype code.")
                    else:
                        print("Invalid trajectory index or no trajectories generated yet.")
                except ValueError:
                    print("Please enter a valid number.")
            
            else:
                print("Unknown command. Type 'help' for available commands.")

def main():
    parser = argparse.ArgumentParser(description="R2E Query Engine - A tool for semantic querying of code extracted with R2E")
    parser.add_argument("--exp_id", type=str, required=True, help="R2E experiment ID")
    parser.add_argument("--api_key", type=str, help="API key (will use environment variable if not provided)")
    parser.add_argument("--use_openrouter", action="store_true", help="Use OpenRouter API instead of OpenAI")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")
    parser.add_argument("--query", type=str, help="Query to run in non-interactive mode")
    parser.add_argument("--research", type=str, help="Generate research trajectories for the given topic")
    parser.add_argument("--show-code", action="store_true", help="Show full code for functions instead of snippets")
    parser.add_argument("--model", type=str, default="anthropic/claude-3-opus", help="Model to use with OpenRouter")
    parser.add_argument("--document", action="store_true", help="Add results to living documentation")
    parser.add_argument("--no-document", action="store_true", help="Don't add results to living documentation")
    parser.add_argument("--arxiv", type=str, help="ArXiv paper URL to include as context")
    
    args = parser.parse_args()
    
    # Initialize the query engine
    engine = R2EQueryEngine(args.exp_id, args.api_key, args.use_openrouter)
    
    # Load the extracted data
    if not engine.load_data():
        print("Failed to load data. Exiting.")
        sys.exit(1)
    
    if args.interactive:
        engine.interactive_mode()
    elif args.research:
        print(f"Generating research trajectories for: {args.research}")
        trajectories = engine.generate_research_trajectories(args.research)
        
        if not trajectories:
            print("Failed to generate research trajectories.")
        else:
            print(f"\nGenerated {len(trajectories)} research trajectories:")
            for i, trajectory in enumerate(trajectories):
                print(f"\n{i+1}. {trajectory['title']}")
                print(f"   Core Question: {trajectory['core_question']}")
                print(f"   Rationale: {trajectory['rationale'][:100]}...")
                print(f"   Existing Components: {', '.join(trajectory['existing_components'])}")
            
            # Document research trajectories if requested
            should_document = args.document or (not args.no_document and not args.interactive)
            if should_document:
                try:
                    # Import here to avoid circular imports
                    from living_doc import LivingDoc
                    doc = LivingDoc()
                    # Create empty results since we don't have search results
                    empty_results = pd.DataFrame()
                    doc.document_query(args.exp_id, args.research, empty_results, trajectories)
                    doc.generate_html()
                    print("\nAdded research trajectories to living documentation.")
                except Exception as e:
                    print(f"Error documenting research: {e}")
    elif args.query:
        print(f"Searching for: {args.query}")
        arxiv_url = args.arxiv
        if arxiv_url:
            print(f"Including arXiv paper as context: {arxiv_url}")
        
        results = engine.semantic_search(args.query, arxiv_url=arxiv_url)
        
        if len(results) == 0:
            print("No matching functions found.")
        else:
            print(f"\nFound {len(results)} relevant functions:")
            for i, (_, func) in enumerate(results.iterrows()):
                print(f"\n{i+1}. {func['function_name']} ({func['repo_name']})")
                if 'relevance_score' in func:
                    print(f"   Relevance: {func['relevance_score']}/10")
                if 'explanation' in func:
                    print(f"   Why: {func['explanation']}")
                
                # Show code (full or snippet)
                if func['code']:
                    if args.show_code:
                        # Show full code
                        print(f"\n   Code:\n   {func['code'].replace(chr(10), chr(10)+'   ')}")
                    elif i < 3:
                        # Show snippet for top 3 results
                        code_snippet = func['code'][:200] + "..." if len(func['code']) > 200 else func['code']
                        print(f"\n   Code snippet:\n   {code_snippet.replace(chr(10), chr(10)+'   ')}")
            
            # Document search results if requested
            should_document = args.document or (not args.no_document and not args.interactive)
            if should_document:
                try:
                    # Import here to avoid circular imports
                    from living_doc import LivingDoc
                    doc = LivingDoc()
                    doc.document_query(args.exp_id, args.query, results, arxiv_url=arxiv_url)
                    doc.generate_html()
                    print("\nAdded search results to living documentation.")
                except Exception as e:
                    print(f"Error documenting search: {e}")
    else:
        print("No action specified. Use --interactive, --query, or --research")
        parser.print_help()

if __name__ == "__main__":
    main()