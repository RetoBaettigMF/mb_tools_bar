# AI-Powered CRM Chat

## Overview
This is a simple Chat application for our CRM
It uses an existing AI-Powered command Line Tool to talk to the CRM with natural language requests.

## CRM Interface
The CRM Interface is already implemented in ../crm-ai-service/crm_agent, it's a symlink you can call directly

## Requirements
- Write a simple python backend with chatbot functionality
- Use openrouter and the infos in .env
- Manage the chat history and call the crm interface if needed
- The backend exposes only one function
  - PostChatHistory (The client manages the entire Chat history, the backend can be stateless)
- Write a simple React frontend with a chat interface that manages the Chat History and allows to start a new chat
- Add a "copy" button to the frontend to copy the contents of the chat window to the copy/paste buffer
- Use a library that can render markdown nicely

## Additional requirements
- Add it to the git repo in the parent dir, commit and push regularly
- Test the solution
- Add a Readme.md
