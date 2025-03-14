to run the test you have to:
1. have Dev containers extension installed
2. run docker compose up as usuall
3. CRTL+SHIFT+P and select Dev containers:attach to running containers
4. select the chat-ui agents container
5. be sure you have dotenv installed
pip install python-dotenv
6. run this comment
python test/multi_model_evaluator.py --config test/model_config.yaml --questions test/questions.txt --output results.csv

Test is composed of three files:
multi_model_evaluator.py
model_config.yaml
questions.txt

and it outputs a result.csv