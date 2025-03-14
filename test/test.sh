#!/bin/bash
curl -X POST http://just-chat-ui-agents:8089/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"sugar_genie_original","messages":[{"role":"system","content":"You are a helpful assistant that can answer questions about Glucosedao and its founders."},{"role":"user","content":"What is Glucosedao and who are the founders?"}]}'

#chmod +x /app/test/test.sh
# /app/test/test.sh