# OmniNexus - datastore.py
# Simple file-based JSON datastore for PoC metadata (connectors, agents).

import json
import os
import threading # To prevent race conditions during save

# Configuration
DATASTORE_DIR = "omnidata"
CONNECTORS_FILE = os.path.join(DATASTORE_DIR, "connectors.json")
AGENTS_FILE = os.path.join(DATASTORE_DIR, "agents.json")

# In-memory cache of the data (simplification for PoC)
_connectors_data = {}
_agents_data = {}

# Lock to prevent race conditions when writing files
_save_lock = threading.Lock()

def _ensure_datastore_dir():
    """Ensures the datastore directory exists."""
    os.makedirs(DATASTORE_DIR, exist_ok=True)

def _load_json_file(filepath):
    """Loads data from a JSON file."""
    _ensure_datastore_dir()
    if not os.path.exists(filepath):
        return {} # Return empty dict if file doesn't exist
    try:
        with open(filepath, 'r') as f:
            # Handle empty file case
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading datastore file {filepath}: {e}")
        # In case of error, maybe return empty or raise? For PoC, return empty.
        return {}

def _save_json_file(filepath, data):
    """Saves data to a JSON file atomically (using a lock)."""
    _ensure_datastore_dir()
    with _save_lock: # Acquire lock before writing
        try:
            # Write to a temporary file first
            temp_filepath = filepath + ".tmp"
            with open(temp_filepath, 'w') as f:
                json.dump(data, f, indent=4)
            # Rename temporary file to the actual file (atomic on most OS)
            os.replace(temp_filepath, filepath)
            # print(f"Data saved to {filepath}") # Optional: uncomment for debugging
        except IOError as e:
            print(f"Error saving datastore file {filepath}: {e}")
        finally:
            # Ensure temporary file is removed if rename failed
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError as e:
                     print(f"Error removing temporary file {temp_filepath}: {e}")


# --- Connectors Data Management ---

def load_connectors():
    """Loads connector data from file into memory."""
    global _connectors_data
    _connectors_data = _load_json_file(CONNECTORS_FILE)
    # Ensure existing connectors have the permissions field (backward compatibility)
    updated = False
    for conn_id, config in _connectors_data.items():
         if 'allowed_agent_types' not in config:
              config['allowed_agent_types'] = [] # Default to empty list (no agents allowed)
              updated = True
         # Ensure it's a list
         elif not isinstance(config['allowed_agent_types'], list):
              config['allowed_agent_types'] = []
              updated = True
    if updated:
         print("Updated existing connector configs with default 'allowed_agent_types'.")
         save_connectors() # Save immediately if migration occurred
    # print(f"Connectors data loaded. {_connectors_data}") # Debug print can be noisy
    return _connectors_data

def save_connectors():
    """Saves the current in-memory connector data to file."""
    _save_json_file(CONNECTORS_FILE, _connectors_data)

def get_all_connectors():
    """Returns the dictionary of all registered connectors."""
    return _connectors_data.copy() # Return a copy to prevent external modification

def get_connector(connector_id):
    """Gets details for a specific connector by ID."""
    return _connectors_data.get(connector_id)

def add_or_update_connector(connector_id, connector_config):
    """
    Adds a new connector or updates an existing one.
    Initializes 'allowed_agent_types' to an empty list if not present.
    """
    if not isinstance(connector_config, dict):
         print("Error: connector_config must be a dictionary.")
         return False

    # Ensure the permissions list exists, default to empty (no agents allowed)
    if 'allowed_agent_types' not in connector_config:
         connector_config['allowed_agent_types'] = []
    elif not isinstance(connector_config['allowed_agent_types'], list):
         print(f"Warning: 'allowed_agent_types' for {connector_id} was not a list. Resetting to empty.")
         connector_config['allowed_agent_types'] = []

    _connectors_data[connector_id] = connector_config
    save_connectors() # Persist change immediately
    # print(f"Connector '{connector_id}' added/updated.") # Make slightly less verbose maybe
    return True

def remove_connector(connector_id):
    """Removes a connector by ID."""
    if connector_id in _connectors_data:
        del _connectors_data[connector_id]
        save_connectors() # Persist change immediately
        print(f"Connector '{connector_id}' removed.")
        return True
    else:
        # print(f"Connector '{connector_id}' not found.") # CLI will handle message
        return False


def get_allowed_agents_for_connector(connector_id):
    """Returns the list of allowed agent types for a connector, or None if connector not found."""
    connector_config = get_connector(connector_id)
    if connector_config:
        # Ensure field exists (should be handled by load/add, but double-check)
        return connector_config.get('allowed_agent_types', [])
    return None

def allow_agent_for_connector(connector_id, agent_type):
    """Adds an agent type to the allowed list for a specific connector."""
    connector_config = get_connector(connector_id)
    if not connector_config:
        print(f"Error: Connector '{connector_id}' not found.")
        return False

    allowed_list = connector_config.get('allowed_agent_types', [])
    if not isinstance(allowed_list, list): # Ensure it's a list before appending
         allowed_list = []

    if agent_type not in allowed_list:
        allowed_list.append(agent_type)
        connector_config['allowed_agent_types'] = allowed_list # Update the config dict
        _connectors_data[connector_id] = connector_config # Ensure update is reflected in main dict
        save_connectors() # Persist the change
        print(f"Agent type '{agent_type}' allowed for connector '{connector_id}'.")
        return True
    else:
        print(f"Agent type '{agent_type}' is already allowed for connector '{connector_id}'.")
        return True # Indicate success even if no change needed

def disallow_agent_for_connector(connector_id, agent_type):
    """Removes an agent type from the allowed list for a specific connector."""
    connector_config = get_connector(connector_id)
    if not connector_config:
        print(f"Error: Connector '{connector_id}' not found.")
        return False

    allowed_list = connector_config.get('allowed_agent_types', [])
    if not isinstance(allowed_list, list): # Handle case where it might be corrupted
         allowed_list = []

    if agent_type in allowed_list:
        allowed_list.remove(agent_type)
        connector_config['allowed_agent_types'] = allowed_list # Update the config dict
        _connectors_data[connector_id] = connector_config # Ensure update is reflected in main dict
        save_connectors() # Persist the change
        print(f"Agent type '{agent_type}' disallowed for connector '{connector_id}'.")
        return True
    else:
        print(f"Agent type '{agent_type}' was not in the allowed list for connector '{connector_id}'.")
        return True # Indicate success even if no change needed


# --- Agents Data Management --- (Structure is similar to Connectors)

def load_agents():
    """Loads agent data from file into memory."""
    global _agents_data
    _agents_data = _load_json_file(AGENTS_FILE)
    print(f"Agents data loaded. {_agents_data}") # Debug print
    return _agents_data

def save_agents():
    """Saves the current in-memory agent data to file."""
    _save_json_file(AGENTS_FILE, _agents_data)

def get_all_agents():
    """Returns the dictionary of all registered agents."""
    return _agents_data.copy()

def get_agent(agent_id):
    """Gets details for a specific agent by ID."""
    return _agents_data.get(agent_id)

def add_or_update_agent(agent_id, agent_config):
    """Adds a new agent or updates an existing one."""
    if not isinstance(agent_config, dict):
         print("Error: agent_config must be a dictionary.")
         return False
    _agents_data[agent_id] = agent_config
    save_agents() # Persist change immediately
    print(f"Agent '{agent_id}' added/updated.")
    return True

def remove_agent(agent_id):
    """Removes an agent by ID."""
    if agent_id in _agents_data:
        del _agents_data[agent_id]
        save_agents() # Persist change immediately
        print(f"Agent '{agent_id}' removed.")
        return True
    else:
        print(f"Agent '{agent_id}' not found.")
        return False

# --- Initialization ---

def initialize_datastore():
    """Loads initial data from files when the application starts."""
    print("Initializing datastore...")
    _ensure_datastore_dir()
    load_connectors()
    load_agents()
    print("Datastore initialized.")

# Example of how to use it (will be called from main.py later)
if __name__ == "__main__":
    print("Running datastore module directly for testing...")
    # Clean up old test data if necessary
    if os.path.exists(CONNECTORS_FILE): os.remove(CONNECTORS_FILE)
    if os.path.exists(AGENTS_FILE): os.remove(AGENTS_FILE)
    _connectors_data = {} # Reset memory cache
    _agents_data = {}
    
    initialize_datastore()

    # Test Connector Operations with Permissions
    print("\n--- Testing Connectors & Permissions ---")
    # Add connector - should initialize with empty allowed list
    add_or_update_connector("conn_perm_test", {"type": "local_files", "path": "/tmp/docs"})
    print("Config after add:", get_connector("conn_perm_test"))
    allowed = get_allowed_agents_for_connector("conn_perm_test")
    print(f"Initial allowed agents for conn_perm_test: {allowed}") # Should be []

    # Allow agents
    allow_agent_for_connector("conn_perm_test", "word_counter")
    allow_agent_for_connector("conn_perm_test", "summarizer")
    allow_agent_for_connector("conn_perm_test", "word_counter") # Try allowing again
    allowed = get_allowed_agents_for_connector("conn_perm_test")
    print(f"Allowed agents after additions: {allowed}") # Should be ['word_counter', 'summarizer']
    print("Full config:", get_connector("conn_perm_test"))

    # Disallow agent
    disallow_agent_for_connector("conn_perm_test", "word_counter")
    disallow_agent_for_connector("conn_perm_test", "non_existent_agent") # Try disallowing non-existent
    allowed = get_allowed_agents_for_connector("conn_perm_test")
    print(f"Allowed agents after removal: {allowed}") # Should be ['summarizer']

    # Test on non-existent connector
    allow_agent_for_connector("fake_conn", "word_counter")

    # Test loading preserves list (or adds it)
    print("\n--- Testing Load/Save ---")
    _connectors_data = {} # Clear memory
    load_connectors() # Load from file
    print("Loaded config:", get_connector("conn_perm_test"))
    allowed = get_allowed_agents_for_connector("conn_perm_test")
    print(f"Allowed agents after load: {allowed}") # Should be ['summarizer']

    # Add another connector to ensure file format works with multiple
    add_or_update_connector("conn_perm_test2", {"type": "imap", "server": "imap.example.com", "username": "test"})
    allow_agent_for_connector("conn_perm_test2", "keyword_extractor")
    print("\nAll connectors:", get_all_connectors())

    # Test Agent Operations
    print("\n--- Testing Agents ---")
    add_or_update_agent("agent1", {"module": "word_counter", "description": "Counts words in text files."})
    add_or_update_agent("agent2", {"module": "summarizer", "model": "local_basic"})
    print("All Agents:", get_all_agents())
    agent1_details = get_agent("agent1")
    print("Details for agent1:", agent1_details)
    remove_agent("agent2")
    print("All Agents after removal:", get_all_agents())
     # Test adding invalid config
    add_or_update_agent("agent_invalid", "not a dict")


    # Verify files were created/updated
    print(f"\nCheck contents of '{CONNECTORS_FILE}' and '{AGENTS_FILE}'")
    
    print("\n--- Testing Agents (Unaffected by Connector Permissions) ---")
    add_or_update_agent("agent_perm_test", {"type": "summarizer", "config_key": "value"})
    print("All Agents:", get_all_agents())
    remove_agent("agent_perm_test")