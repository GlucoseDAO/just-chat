from just_agents.base_agent import BaseAgent
import litellm

# Enable debug mode to see detailed API call information
litellm._turn_on_debug()

if __name__ == "__main__":
    llm_options = {
        "model": "sugar_genie_assistant",
        "api_base": "http://localhost:8089" #stuff with /v1/completions and /v1 also does not work
    }
    agent = BaseAgent(llm_options=llm_options, system_prompt="You are a helpful assistant that can answer questions about Glucosedao and its founders.")
    response = agent.query("What is Glucosedao and who are the founders?")
    print(response)
