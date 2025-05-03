# OmniNexus - The Personal Cognitive Fabric (Proof-of-Concept)

## Vision

OmniNexus aims to be a decentralized, privacy-preserving protocol and software framework acting as the foundational layer for personalized AI. It allows individuals to securely integrate disparate data sources and orchestrate personalized AI agents working on their behalf, under their explicit control.

This repository contains the initial Proof-of-Concept (PoC) demonstrating the core architecture.

## Current Status (Phase 1 PoC)

*   Basic CLI application (main.py).
*   Rudimentary local identity generation (identity.py, insecure key storage).
*   Simple file-based datastore for configurations (datastore.py).
*   Connector framework (connectors.py) with a local_files connector (reads .txt, .md).
*   Agent framework (agents.py) with a word_counter agent.
*   Basic orchestration via CLI commands.

WARNING: This PoC is for demonstration purposes ONLY. It lacks crucial security features, error handling, and many planned functionalities. Do not use with sensitive data.

## Running the PoC

1.  Clone the repository: git clone https://github.com/Esrbwt1/OmniNexus.git
2.  Navigate to the directory: cd OmniNexus
3.  Install dependencies: pip install cryptography
4.  Run the main script: python main.py
5.  Follow the CLI commands (type help for options). You will need to create a test directory with some .txt or .md files to use the local_files connector.

## Next Steps (Phase 2 & Beyond)

*   Refine core protocol and architecture.
*   Implement robust security and privacy measures (encryption, proper key handling).
*   Develop more connectors (e.g., Email (IMAP), Cloud Storage, Notes Apps).
*   Develop more sophisticated agents (e.g., Summarization, Keyword Extraction).
*   Improve CLI / Develop GUI.
*   Formalize protocol specification.
*   Build community and documentation.

## Contribution

This project is in its very early stages. Feedback and contributions (especially on the protocol design and technical implementation) will be welcome as the project matures. (Formal contribution guidelines TBD).