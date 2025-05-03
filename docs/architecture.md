# OmniNexus PoC Architecture Overview

This document describes the high-level architecture of the OmniNexus Proof-of-Concept (PoC) as implemented in the Python codebase.

## Core Components

The PoC consists of several distinct Python modules working together:

1.  `main.py` (CLI Orchestrator):
    *   Role: The main entry point and user interface for the PoC.
    *   Functionality:
        *   Initializes the system (identity, datastore).
        *   Provides a simple Command-Line Interface (CLI) for user interaction.
        *   Parses user commands (e.g., add_connector, run_word_count).
        *   Orchestrates the basic workflow: loading configurations, activating/deactivating components, calling connector queries, invoking agent executions, and displaying results.
        *   Manages a simple in-memory dictionary (active_connectors) of currently activated connector instances.
    *   Key Interactions: Imports and uses functions from all other modules.

2.  `identity.py` (Identity Management):
    *   Role: Handles the user's local cryptographic identity.
    *   Functionality:
        *   Generates a local RSA public/private key pair.
        *   Serializes the keys into PEM format.
        *   Encrypts the private key PEM using a user-provided password (cryptography.hazmat.primitives.serialization.BestAvailableEncryption).
        *   Stores the encrypted private key PEM and the public key PEM in a local JSON file (local_identity.json).
        *   Loads the identity, prompting the user for the password to decrypt the private key.
        *   Provides functions (get_or_create_identity, get_public_key_pem) for other modules to access the identity.
    *   Key Interactions: Used by main.py during initialization and for display (info command). Cryptographic keys would be used for signing/verification in future secure protocol versions.

3.  `datastore.py` (Configuration Storage):
    *   Role: Persistently stores configurations for connectors and agents.
    *   Functionality:
        *   Manages JSON files (omnidata/connectors.json, omnidata/agents.json) to store configuration dictionaries.
        *   Uses a simple file-based approach with atomic writes (via temp file + rename) for basic robustness.
        *   Provides functions for CRUD-like operations (add, get, update, remove, list all) on connector and agent configurations.
        *   Maintains a simple in-memory cache (_connectors_data, _agents_data) loaded at startup (simplification for PoC).
    *   Key Interactions: Used by main.py to load, save, and manage component configurations.

4.  `protocol.py` (Definitions & Conventions):
    *   Role: Defines standard data structures and conventions used within the PoC.
    *   Functionality:
        *   Specifies the standard DATA_ITEM_STRUCTURE dictionary format for data flowing between connectors and agents (including keys like item_id, connector_id, source_uri, retrieved_at, metadata, payload).
        *   Provides utility functions (create_iso_timestamp, generate_item_id).
        *   Documents expected formats for configuration schemas and component interactions (primarily via comments in the PoC).
    *   Key Interactions: Imported by connectors.py and agents.py to ensure adherence to the standard data item structure and use utility functions. Referenced conceptually by main.py.

5.  `connectors.py` (Data Connector Framework & Implementations):
    *   Role: Defines how OmniNexus interfaces with external data sources and implements specific connectors.
    *   Functionality:
        *   Defines an abstract base class BaseConnector outlining the required interface (validate_config, connect, disconnect, get_metadata, query_data, get_config_schema).
        *   Implements specific connectors inheriting from BaseConnector (e.g., LocalFilesConnector, ImapConnector skeleton).
        *   Each connector handles source-specific logic for connection, authentication (rudimentary/placeholder), and data querying/parsing.
        *   Connectors format their retrieved data into the standard DATA_ITEM_STRUCTURE defined in protocol.py.
        *   Includes a registry (_connector_types) and a factory function (create_connector_instance) to instantiate connectors based on the type key in their configuration.
    *   Key Interactions: Connector classes used by the factory in main.py. Instances are created and managed (activated/deactivated) by main.py. query_data is called by main.py's run commands. Uses protocol.py for data structure.

6.  `agents.py` (AI Agent Framework & Implementations):
    *   Role: Defines how OmniNexus performs computations or tasks on data and implements specific agents.
    *   Functionality:
        *   Defines an abstract base class BaseAgent outlining the required interface (validate_config, get_metadata, execute, get_config_schema).
        *   Implements specific agents inheriting from BaseAgent (e.g., WordCountAgent, KeywordExtractAgent).
        *   Each agent implements its specific logic in the execute method, processing a list of standard Data Items.
        *   Agents can accept optional runtime parameters in their execute method to modify behavior for a specific run.
        *   Includes a registry (_agent_types) and a factory function (create_agent_instance) to instantiate agents based on the type key in their configuration (though agent configuration is minimal in the PoC).
    *   Key Interactions: Agent classes used by the factory in main.py. Instances are typically created on-demand by main.py's run commands. The execute method is called with data retrieved by connectors. Uses protocol.py for expected input data structure.

## Data Flow Example (run_keyword_extractor my_docs_test)

1.  User enters command in main.py CLI.
2.  main.py parses command (run_keyword_extractor) and args (my_docs_test).
3.  main.py checks if my_docs_test connector instance exists in active_connectors.
4.  If not, main.py calls datastore.get_connector('my_docs_test') to get its config.
5.  main.py calls connectors.create_connector_instance('my_docs_test', config) (which finds
LocalFilesConnector in the registry).
6.  main.py calls connector_instance.connect() (which is a no-op for local files).
7.  main.py adds the connector_instance to active_connectors.
8.  main.py calls connector_instance.query_data(None).
9.  LocalFilesConnector.query_data finds relevant files, reads them, and formats each as a standard Data Item dictionary (using protocol.generate_item_id, etc.), returning a list of these items.
10. main.py calls agents.create_agent_instance('poc_keyword_extractor', {'type': 'keyword_extractor'}) (which finds KeywordExtractAgent in the registry).
11. main.py calls agent_instance.execute(data_inputs=list_of_data_items, parameters=parsed_cli_params).
12. KeywordExtractAgent.execute iterates through the data items, extracts text from item['payload']['content'], performs keyword analysis, and returns a result dictionary.
13. main.py receives the result and prints it to the CLI.

## Limitations of PoC Architecture

*   Single Process: All components run within the same Python process.
*   Basic Orchestration: main.py handles only simple, user-triggered workflows. No background tasks or complex agent chaining.
*   In-Memory Activation: Only explicitly activated connectors are readily available for use. State is lost on exit (except for datastore configs).
*   Limited Security: Key stored encrypted but password requested interactively. No inter-component authentication/authorization. No sandboxing for agents/connectors.
*   Basic Error Handling: Error handling is present but could be more robust and user-friendly.