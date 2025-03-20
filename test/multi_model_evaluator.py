#!/usr/bin/env python3
import yaml
import pandas as pd
import typer
import os
import time
import re
import datetime
from typing import List, Dict, Any, Optional
from just_agents.base_agent import BaseAgent
import litellm
from dotenv import load_dotenv
from pathlib import Path

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
            output_path: Path to save the results (default: test/results_{timestamp}.csv)
        """
        self.config_path = config_path
        self.questions_path = questions_path
        
        # Generate timestamp for use in filenames and data
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get the test directory path
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add timestamp to default output filename if none provided
        if output_path:
            # If output_path is not absolute, make it relative to test directory
            if not os.path.isabs(output_path):
                self.output_path = os.path.join(test_dir, output_path)
            else:
                self.output_path = output_path
        else:
            # Default output path in test directory
            self.output_path = os.path.join(test_dir, f"results_{self.timestamp}.csv")
        
        # Load configuration
        self.config = self._load_config()
        
        # Load questions
        self.questions = self._load_questions()
        
        # Initialize results dataframe with timestamp column
        self.results = pd.DataFrame(columns=["question", "model", "agent_name", "response", "time_taken", "timestamp"])
        
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
                # Try to create the agent using from_yaml
                try:
                    # First, try to load directly from the original config file
                    agent = BaseAgent.from_yaml(
                        section_name=agent_name,
                        parent_section="agent_profiles",
                        file_path=Path(self.config_path)
                    )
                    print(f"Loaded agent {agent_name} from original config file")
                except (KeyError, FileNotFoundError):
                    # If not found in original config, create a temporary file
                    temp_config = {
                        "agent_profiles": {
                            agent_name: agent_config
                        }
                    }
                    
                    temp_config_path = Path(f"temp_{agent_name}_config.yaml")
                    with open(temp_config_path, 'w') as f:
                        yaml.dump(temp_config, f)
                    
                    try:
                        # Create the agent using from_yaml
                        agent = BaseAgent.from_yaml(
                            section_name=agent_name,
                            parent_section="agent_profiles",
                            file_path=temp_config_path
                        )
                        
                        # Clean up the temporary file
                        os.remove(temp_config_path)
                    except Exception as e:
                        # Clean up the temporary file
                        if os.path.exists(temp_config_path):
                            os.remove(temp_config_path)
                        
                        print(f"Error creating agent using from_yaml: {str(e)}")
                        print("Falling back to direct instantiation")
                        
                        # Extract LLM options from the agent configuration
                        llm_options = agent_config.get("llm_options", {})
                        
                        # Print the LLM options for debugging
                        print(f"LLM options: {llm_options}")
                        
                        # Get system prompt
                        system_prompt = agent_config.get("system_prompt", "You are a helpful assistant.")
                        
                        # Create and return the agent
                        agent = BaseAgent(llm_options=llm_options, system_prompt=system_prompt)
                
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
                        
                        # Add to results with timestamp
                        self.results = pd.concat([
                            self.results, 
                            pd.DataFrame([{
                                "question": question,
                                "model": agent_config.get("llm_options", {}).get("model", "unknown"),
                                "agent_name": agent_name,
                                "response": response,
                                "time_taken": time_taken,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                        ], ignore_index=True)
                        
                        # Save intermediate results
                        self._save_results()
                        
                        # Add a small delay to avoid rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"Error querying agent {agent_name} with question: {question}")
                        print(f"Error details: {str(e)}")
                        
                        # Add error to results with timestamp
                        self.results = pd.concat([
                            self.results, 
                            pd.DataFrame([{
                                "question": question,
                                "model": agent_config.get("llm_options", {}).get("model", "unknown"),
                                "agent_name": agent_name,
                                "response": f"ERROR: {str(e)}",
                                "time_taken": time.time() - start_time,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        """Save results to CSV file with timestamp"""
        # Restructure the results dataframe to have questions as rows and models as columns
        if not self.results.empty:
            # Create a unique identifier for each model/agent combination
            self.results['model_agent'] = self.results['agent_name'] + ' (' + self.results['model'] + ')'
            
            # Create a pivot table with questions as rows and model/agent as columns
            # Include timestamps in the pivoted results by using the most recent timestamp for each question-model pair
            pivoted_df = pd.DataFrame()
            
            # Get unique questions
            unique_questions = self.results['question'].unique()
            
            # For each question, find the latest response from each model_agent
            for question in unique_questions:
                question_df = self.results[self.results['question'] == question]
                # Group by model_agent and get the row with the latest timestamp
                latest_responses = question_df.sort_values('timestamp').groupby('model_agent').last().reset_index()
                pivoted_df = pd.concat([pivoted_df, latest_responses], ignore_index=True)
            
            # Create the final pivoted view
            pivoted_results = pivoted_df.pivot(
                index='question',
                columns='model_agent',
                values='response'
            )
            
            # Reset index to make 'question' a regular column
            pivoted_results = pivoted_results.reset_index()
            
            # Save the pivoted results to CSV
            pivoted_results.to_csv(self.output_path, index=False)
            print(f"Results saved to: {self.output_path}")
            
        else:
            # If results are empty, save an empty dataframe
            pd.DataFrame(columns=["question", "timestamp"]).to_csv(self.output_path, index=False)

def main(
    config: str = typer.Option(..., "--config", help="Path to the YAML configuration file"),
    questions: str = typer.Option(..., "--questions", help="Path to the text file containing questions"),
    output: Optional[str] = typer.Option(None, "--output", help="Path to save the results (default: test/results_{timestamp}.csv)"),
    env: Optional[str] = typer.Option(None, "--env", help="Path to .env file with API keys")
):
    """
    Evaluate multiple LLM models on a set of questions.
    """
    # Load environment variables first
    load_env_files()
    
    
    # Load specific env file if provided
    if env and os.path.exists(env):
        print(f"Loading environment variables from {env}")
        load_dotenv(env)
    
    # Create and run the evaluator
    evaluator = MultiModelEvaluator(
        config_path=config,
        questions_path=questions,
        output_path=output
    )
    
    evaluator.run_evaluation()

if __name__ == "__main__":
    typer.run(main)