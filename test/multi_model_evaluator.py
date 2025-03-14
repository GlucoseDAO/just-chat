#!/usr/bin/env python3
import yaml
import pandas as pd
import argparse
import os
import time
import re
from typing import List, Dict, Any
from just_agents.base_agent import BaseAgent
import litellm
from dotenv import load_dotenv

# Configure LiteLLM to handle custom endpoints correctly
litellm.api_url_paths = {
    "custom": {
        "chat_completions": "/v1/chat/completions",
        "completions": "/v1/chat/completions"  # Force completions to use chat endpoint
    }
}

# Load environment variables from .env files
def load_env_files():
    """Load environment variables from multiple possible .env files"""
    # Try to load from different possible locations
    env_files = [
        "env/.env.keys",
        ".env.keys",
        ".env",
        "env/.env"
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"Loading environment variables from {env_file}")
            load_dotenv(env_file)
            return True
    
    print("Warning: No .env file found. Make sure API keys are set in environment variables.")
    return False

class MultiModelEvaluator:
    def __init__(self, config_path: str, questions_path: str, output_path: str = None):
        """
        Initialize the evaluator with configuration and questions
        
        Args:
            config_path: Path to the YAML configuration file
            questions_path: Path to the text file containing questions
            output_path: Path to save the results (default: results.csv)
        """
        self.config_path = config_path
        self.questions_path = questions_path
        self.output_path = output_path or "results.csv"
        
        # Load configuration
        self.config = self._load_config()
        
        # Load questions
        self.questions = self._load_questions()
        
        # Initialize results dataframe
        self.results = pd.DataFrame(columns=["question", "model", "agent_name", "response", "time_taken"])
        
    def _load_config(self) -> Dict[str, Any]:
        """Load the YAML configuration file and substitute environment variables"""
        with open(self.config_path, 'r') as f:
            config_str = f.read()
            
        # Replace ${ENV_VAR} with the actual environment variable value
        def replace_env_var(match):
            env_var = match.group(1)
            env_value = os.environ.get(env_var)
            if env_value is None:
                print(f"Warning: Environment variable {env_var} not found")
                return "${" + env_var + "}"
            return env_value
            
        # Substitute environment variables in the config string
        config_str = re.sub(r'\${([^}]+)}', replace_env_var, config_str)
        
        # Parse the YAML with substituted values
        return yaml.safe_load(config_str)
    
    def _load_questions(self) -> List[str]:
        """Load questions from a text file"""
        with open(self.questions_path, 'r') as f:
            # Strip whitespace and filter out empty lines
            return [line.strip() for line in f.readlines() if line.strip()]
    
    def _create_agent(self, agent_config: Dict[str, Any]) -> BaseAgent:
        """Create an agent based on configuration"""
        # Extract LLM options from the agent configuration
        llm_options = agent_config.get("llm_options", {})
        
        # Print the LLM options for debugging
        print(f"LLM options: {llm_options}")
        
        # Get system prompt
        system_prompt = agent_config.get("system_prompt", "You are a helpful assistant.")
        
        # Create and return the agent
        return BaseAgent(llm_options=llm_options, system_prompt=system_prompt)
    
    def run_evaluation(self):
        """Run the evaluation across all models and questions"""
        # Get the list of agent profiles to evaluate
        agent_profiles = self.config.get("agent_profiles", {})
        
        # For each agent profile
        for agent_name, agent_config in agent_profiles.items():
            print(f"Evaluating agent: {agent_name}")
            
            # Skip hidden agents if specified
            if agent_config.get("hidden", False):
                print(f"Skipping hidden agent: {agent_name}")
                continue
                
            # Check if API key is required but missing
            llm_options = agent_config.get("llm_options", {})
            if "api_key" in llm_options and (llm_options["api_key"] is None or llm_options["api_key"].startswith("${")):
                print(f"Skipping agent {agent_name} due to missing API key")
                continue
                
            # Create the agent
            try:
                agent = self._create_agent(agent_config)
                
                # Process each question
                for question in self.questions:
                    print(f"Processing question: {question[:50]}...")
                    
                    # Measure response time
                    start_time = time.time()
                    
                    try:
                        # Query the agent
                        response = agent.query(question)
                        
                        # Calculate time taken
                        time_taken = time.time() - start_time
                        
                        # Add to results
                        self.results = pd.concat([
                            self.results, 
                            pd.DataFrame([{
                                "question": question,
                                "model": agent_config.get("llm_options", {}).get("model", "unknown"),
                                "agent_name": agent_name,
                                "response": response,
                                "time_taken": time_taken
                            }])
                        ], ignore_index=True)
                        
                        # Save intermediate results
                        self._save_results()
                        
                        # Add a small delay to avoid rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"Error querying agent {agent_name} with question: {question}")
                        print(f"Error details: {str(e)}")
                        
                        # Add error to results
                        self.results = pd.concat([
                            self.results, 
                            pd.DataFrame([{
                                "question": question,
                                "model": agent_config.get("llm_options", {}).get("model", "unknown"),
                                "agent_name": agent_name,
                                "response": f"ERROR: {str(e)}",
                                "time_taken": time.time() - start_time
                            }])
                        ], ignore_index=True)
                        
                        # Save intermediate results
                        self._save_results()
                
            except Exception as e:
                print(f"Error creating agent {agent_name}: {str(e)}")
        
        # Save final results
        self._save_results()
        print(f"Evaluation complete. Results saved to {self.output_path}")
    
    def _save_results(self):
        """Save results to CSV file"""
        self.results.to_csv(self.output_path, index=False)
        
        # Also save as Excel if pandas has openpyxl
        try:
            excel_path = os.path.splitext(self.output_path)[0] + ".xlsx"
            self.results.to_excel(excel_path, index=False)
            print(f"Results also saved to Excel: {excel_path}")
        except Exception:
            pass  # Skip Excel export if not available

def main():
    # Load environment variables first
    load_env_files()
    
    # Print available API keys (masked for security)
    for key in ['GROQ_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY']:
        if key in os.environ:
            value = os.environ[key]
            masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
            print(f"Found {key}: {masked}")
        else:
            print(f"Missing {key}")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Evaluate multiple LLM models on a set of questions")
    parser.add_argument("--config", required=True, help="Path to the YAML configuration file")
    parser.add_argument("--questions", required=True, help="Path to the text file containing questions")
    parser.add_argument("--output", help="Path to save the results (default: results.csv)")
    parser.add_argument("--env", help="Path to .env file with API keys")
    
    args = parser.parse_args()
    
    # Load specific env file if provided
    if args.env and os.path.exists(args.env):
        print(f"Loading environment variables from {args.env}")
        load_dotenv(args.env)
    
    # Create and run the evaluator
    evaluator = MultiModelEvaluator(
        config_path=args.config,
        questions_path=args.questions,
        output_path=args.output
    )
    
    evaluator.run_evaluation()

if __name__ == "__main__":
    main()