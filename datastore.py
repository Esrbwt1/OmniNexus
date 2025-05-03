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
    print(f"Connectors data loaded. {_connectors_data}") # Debug print
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
    """Adds a new connector or updates an existing one."""
    if not isinstance(connector_config, dict):
         print("Error: connector_config must be a dictionary.")
         return False
    _connectors_data[connector_id] = connector_config
    save_connectors() # Persist change immediately
    print(f"Connector '{connector_id}' added/updated.")
    return True

def remove_connector(connector_id):
    """Removes a connector by ID."""
    if connector_id in _connectors_data:
        del _connectors_data[connector_id]
        save_connectors() # Persist change immediately
        print(f"Connector '{connector_id}' removed.")
        return True
    else:
        print(f"Connector '{connector_id}' not found.")
        return False


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
    initialize_datastore()

    # Test Connector Operations
    print("\n--- Testing Connectors ---")
    add_or_update_connector("conn1", {"type": "local_files", "path": "/tmp/docs", "enabled": True})
    add_or_update_connector("conn2", {"type": "email", "account": "test@example.com"})
    print("All Connectors:", get_all_connectors())
    conn1_details = get_connector("conn1")
    print("Details for conn1:", conn1_details)
    remove_connector("conn2")
    print("All Connectors after removal:", get_all_connectors())
    # Test adding invalid config
    add_or_update_connector("conn_invalid", "not a dict")


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