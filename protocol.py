# OmniNexus - protocol.py
# Defines constants, standard formats, and conventions for OmniNexus PoC.
# For the PoC, this is primarily documentation. A real protocol would be more formal.

# --- Data Structures ---

# Structure expected for data returned by Connector query_data methods:
# A list of dictionaries. Each dictionary represents a data item.
# The exact keys in the dictionary depend on the connector, but a
# 'content' key is often expected by agents processing text.
# Example from LocalFilesConnector:
# [
#   {
#     "filepath": "/path/to/file.txt",
#     "content": "Text content...",
#     "connector_id": "connector_instance_id" # Identifies the source
#   },
#   # ... more items
# ]
CONNECTOR_QUERY_OUTPUT_FORMAT = "List[Dict]"


# Structure expected as input ('data_inputs') to Agent execute methods:
# Typically, this will be the output from one or more connector queries,
# potentially filtered or combined by the orchestrator (main.py for now).
# Example for WordCountAgent:
# [
#   {'content': 'Text one', 'source': 'connector_id_or_filepath'},
#   {'content': 'Text two', 'source': '...'},
# ]
AGENT_EXECUTE_INPUT_FORMAT = "List[Dict]"


# Structure expected as output from Agent execute methods:
# Highly dependent on the specific agent's function.
# Example from WordCountAgent:
# {
#   "total_words": 123
# }
# Future agents might return lists, structured text, boolean flags, etc.
AGENT_EXECUTE_OUTPUT_FORMAT = "Dict or other format depending on agent"


# --- Configuration Schemas ---

# Connectors and Agents should implement the class method `get_config_schema()`
# which returns a dictionary describing needed configuration parameters.
# Example Schema Structure:
# {
#   "config_key_name": {
#       "type": "string" | "integer" | "boolean" | "filepath" | "directorypath",
#       "required": True | False,
#       "default": "some_default_value" (if not required),
#       "description": "User-friendly explanation of the parameter."
#   },
#   # ... more keys
# }
CONFIG_SCHEMA_FORMAT = "Dict[str, Dict]"


# --- Reserved Configuration Keys ---

# Key used in configuration dictionaries passed to factories to specify
# the type of component to create.
COMPONENT_TYPE_KEY = "type"


# --- Status / Error Codes (Conceptual for PoC) ---
# In a larger system, we might define standard error codes/messages.
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
ERROR_INVALID_CONFIG = "INVALID_CONFIG"
ERROR_CONNECTION_FAILED = "CONNECTION_FAILED"
ERROR_QUERY_FAILED = "QUERY_FAILED"
ERROR_EXECUTION_FAILED = "EXECUTION_FAILED"
ERROR_NOT_FOUND = "NOT_FOUND"


# --- Security Considerations (Placeholders for PoC) ---
# - PoC uses unencrypted local private key storage (identity.py). **INSECURE**
# - PoC assumes local execution environment is trusted.
# - No network communication security implemented yet.
# - No granular access control between agents and connectors yet.
# - Input sanitization in agents/connectors is minimal.

print("OmniNexus Protocol Definitions (PoC) - Loaded.") # Just to show file is read