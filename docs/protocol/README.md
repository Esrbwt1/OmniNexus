# OmniNexus Protocol (ONP) - PoC Introduction

The OmniNexus Protocol (ONP) defines the standards, data formats, and communication patterns used within the OmniNexus framework. In this early Proof-of-Concept (PoC), the protocol is primarily defined by the internal interfaces and data structures used by the Python code.

## Core Principles (PoC Implementation)

1.  Component Modularity: Connectors and Agents are distinct modules with defined interfaces (BaseConnector, BaseAgent).
2.  Factory Pattern: Instances are created via factory functions (create_connector_instance, create_agent_instance) based on a type specified in configuration.
3.  Standard Data Flow: Connectors query external sources and produce data items. The orchestrator (currently main.py) passes these items to Agents for processing.
4.  Standard Data Item Structure: Data flowing between components should adhere to a defined [Standard Data Item Structure](./data_item_structure.md). This ensures consistency and allows agents to process data from different sources reliably.
5.  Configuration Schemas: Components define their required configuration parameters via a get_config_schema() class method, allowing for guided setup and validation.
6.  Local Identity: A basic, password-protected local cryptographic identity is used ([Identity Management](./identity.md)).

## Key Protocol Elements (PoC)

*   [Standard Data Item Structure](./data_item_structure.md): The format for data passed between connectors and agents.
*   BaseConnector Interface (connectors.py): Defines methods like validate_config, connect, disconnect, get_metadata, query_data, get_config_schema.
*   BaseAgent Interface (agents.py): Defines methods like validate_config, get_metadata, execute, get_config_schema.
*   Configuration Dictionary Format: Standard Python dictionaries used for configuration, including the mandatory type key.

## Future Evolution

As OmniNexus matures, the ONP will be formalized using:

*   More rigorous interface definitions (potentially using abstract base classes more strictly or formal interface specifications).
*   Standardized serialization formats (e.g., JSON Schema, potentially Protobuf) for data items and configurations, especially if components communicate across processes or networks.
*   Defined communication protocols (e.g., REST APIs over localhost, RPC mechanisms) if components become separate services.
*   Enhanced security protocols for authentication, authorization (likely leveraging DIDs/VCs), and data exchange.
*   Standardized query languages or parameter formats for query_data and execute.