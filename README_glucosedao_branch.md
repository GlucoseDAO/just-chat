# GlucoseDAO Branch - Just-Chat

## Overview
This branch of the just-chat repo was created to provide a chatbot agent to answer questions about GlucoseDAO and questions regarding diabetic issues found in research papers.

## Features
- Integration with Meilisearch, allowing semantic search of indexed files (regarding GlucoseDAO) and research papers (regarding diabetic and glucose studies)
- A specialized structure of chat agents used to cover various aspects of diabetes and glucose prediction

## Agent Architecture
This branch uses an approach with three specialized agents:

1. **Sugar Genie Assistant** (🍬 A Blood Sugar Prediction Genie) - When a user sends a request, it's first received by this agent whose sole purpose is to route the request to the appropriate specialized agent using the `call_expert_agent` tool.

2. **Sugar Genie Original** (🍬 A Blood Sugar Prediction Genie -ORIGINAL) - The expert agent equipped with semantic search tools (`search_documents` and `all_indexes`) :
   - Specializes in questions about GlucoseDAO by searching the "glucosedao" index
   - Uses document searches to provide detailed information with proper source attribution
   - Has access to the "glucose_txt" directory of indexed documents

3. **Sugar Genie Generic** (🍬 A Blood Sugar Prediction Genie -uses only generic info-) - this agent is used when the expert agent doesn't find relevant information to answer questions about diabetic issues or any other generic topics from its trained knowledge

Additional supporting agents include:
- **Chat Naming Agent** (📜) - Used for generating concise chat titles in the UI
- **RAG Agent** (🕵) - Handles advanced semantic search operations
- **Annotation Agent** (📝) - Extracts abstracts, authors, and titles from research papers

The multi-agent system ensures that:
- All requests are answered with the latest information, supplementing the general knowledge the models were trained on
- By splitting agents into specialized roles, we can control which models are used at each stage, ensuring appropriate coordination and cost control

## Benchmarking
Another feature of this branch is the test folder that contains a benchmarking method for different models:
- The folder contains a list of questions to test how different models respond
- A Python script processes each question from the text file and gets responses from each model listed in the YAML configuration
- Results are written to a CSV file for easy human comparison
- For more details, please consult the README in the test folder

## Important URLs
All these addresses are defined in the `docker-compose.yml` file:

- `0.0.0.0:3000` - The chat interface where you can interact with the agents
- `0.0.0.0:7700` - The Meilisearch server address to check indexed papers and available indexes
- `0.0.0.0:8091/docs` - The Swagger documentation address with several API options

## API Endpoints

### POST Endpoints
- `/v1/chat/completions` - Shows predicted output from a request (used for testing)
- `/search` - Performs semantic search (used for testing search functionality)
- `/search_agent` - Performs advanced RAG-based search
- `/list_indexes` - Gets all indexes in the Meilisearch container
- `/index_markdown_folder` - Indexes a folder containing markdown or text files (must be in the repo at a location mounted in the container, such as `data`)
- `/upload_markdown_folder` - Indexes a folder containing markdown or text files from anywhere on the computer (requires absolute path)
- `/upload_pdf` - Indexes a PDF file from the computer (each file must be selected individually)
- `/upload_text` - Indexes a text file from the computer (file must be selected individually)
- `/delete_by_source` - Deletes documents by their source