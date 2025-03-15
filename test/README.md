# Multi-Model Evaluator Test

## Prerequisites

Before running the test, ensure you have:

1. **Dev Containers** extension installed in VS Code
2. Docker running on your system

## Setup and Execution

1. Start the environment:
   ```bash
   docker compose up
   ```

2. Attach to the container:
   - Press `CTRL+SHIFT+P` and select `Dev Containers: Attach to Running Container`
   - Select the `chat-ui-agents` container

3. Install required dependencies:
   ```bash
   pip install python-dotenv
   ```

4. Run the test:
   ```bash
   python test/multi_model_evaluator.py --config test/model_config.yaml --questions test/questions.txt --output test/results.csv
   ```

## Test Components

The test consists of three main files:
- `multi_model_evaluator.py` - Main evaluation script
- `model_config.yaml` - Configuration for models to be evaluated
- `questions.txt` - Test questions/prompts

## Output

The test generates a `results.csv` file containing the evaluation results.