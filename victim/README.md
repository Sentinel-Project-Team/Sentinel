# Victim App

Stub placeholder — to be implemented in Phase 1.

This service is an OpenAI-compatible chatbot (`/v1/chat/completions`) backed by Ollama, with canary secrets injected into its system prompt.

## Canaries

Defined in `canaries.yaml`. Each canary is a fake secret (ID, password, name) that can only appear in a model answer if the system prompt was leaked.
