# Hardened Local Cybersecurity AI Assistant

A zero-trust, locally hosted LLM chat interface designed for security analysis, log review, and defensive engineering tasks. Built with Streamlit, LangChain, and Ollama (Llama3).

## 🛡️ Implemented Security Matrix
- **Authentication Gateway:** Protected via standard PBKDF2 cryptographic key derivation (enforced via terminal environment variables).
- **Transport Security:** Local end-to-end TLS/HTTPS encryption.
- **Data-at-Rest Security:** Automated AES-256 chat history encryption using Fernet primitives.
- **Input Sanitization:** Deep XSS/HTML element stripping using Bleach.
- **WAF Guardrails:** Intent verification algorithms to strictly enforce cybersecurity-only operational scopes.
- **Context Optimization:** Intelligent text chunking and sliding windows to prevent context overflow or resource depletion.

## 🚀 Local Deployment Instructions

1. **Clone the Repository:**
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>