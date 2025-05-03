# OmniNexus - main.py
# PoC Entry Point & Basic CLI Orchestrator

import sys
import os
import traceback # For printing detailed error messages

# Import our modules
import identity
import datastore
import connectors
import agents
import protocol # Although mostly comments, importing shows dependency

# Global dictionary to hold active connector instances (simplification for PoC)
# Key: connector_id, Value: connector instance
active_connectors = {}

def initialize_system():
    """Initializes all necessary components."""
    print("--- Initializing OmniNexus PoC ---")
    identity.get_or_create_identity() # Ensure identity exists
    datastore.initialize_datastore() # Load existing configs
    # TODO: Maybe load/activate connectors from datastore automatically? For PoC, manual activation.
    print("--- System Initialized ---")

def display_help():
    """Displays available commands."""
    print("\nOmniNexus PoC CLI Commands:")
    print("  help                - Show this help message")
    print("  info                - Show system info (e.g., Public Key)")
    print("  types               - List available connector and agent types")
    print("  add_connector       - Add and configure a new connector instance")
    print("  list_connectors     - List configured connector instances")
    print("  activate_connector <id> - Load connector instance into memory (required before run)")
    print("  deactivate_connector <id> - Remove connector instance from memory")
    print("  remove_connector <id> - Remove connector configuration permanently")
    # Add Agent commands later if needed, for PoC focus on running one
    print("  run_word_count <connector_id> - Run WordCountAgent on data from the specified *active* connector")
    print("  quit / exit         - Exit the application")
    print("-" * 20)

def display_info():
    """Displays system information."""
    print("\n--- System Info ---")
    pub_key = identity.get_public_key_pem()
    if pub_key:
        print("Local Identity Public Key (PEM):")
        print(pub_key)
    else:
        print("Could not load identity.")
    print(f"Datastore Directory: {os.path.abspath(datastore.DATASTORE_DIR)}")
    print(f"Active Connector Instances in Memory: {list(active_connectors.keys())}")
    print("-" * 20)


def list_available_types():
    """Lists available component types."""
    print("\n--- Available Component Types ---")
    print("Connector Types:", connectors.get_available_connector_types())
    print("Agent Types:", agents.get_available_agent_types())
    print("-" * 20)

def add_connector_cli():
    """Handles the CLI interaction for adding a connector."""
    print("\n--- Add New Connector ---")
    connector_type = input("Enter connector type (e.g., 'local_files'): ").strip()

    ConnectorClass = connectors.get_connector_class(connector_type)
    if not ConnectorClass:
        print(f"Error: Unknown connector type '{connector_type}'. Available: {connectors.get_available_connector_types()}")
        return

    print(f"\nConfiguring '{connector_type}':")
    schema = ConnectorClass.get_config_schema()
    config = {"type": connector_type} # Start config with the type

    for key, details in schema.items():
        required = details.get("required", False)
        prompt = f"Enter value for '{key}' ({details.get('type', 'any')})"
        if required:
            prompt += " (required)"
        else:
            prompt += f" (optional, default: {details.get('default', 'None')})"
        prompt += f":\n  ({details.get('description', 'No description')})\n> "

        while True:
            value_str = input(prompt).strip()
            if value_str:
                # Basic type conversion attempt (extend later if needed)
                try:
                    type_hint = details.get("type")
                    if type_hint == "boolean":
                        if value_str.lower() in ['true', 'yes', '1', 't']:
                            value = True
                        elif value_str.lower() in ['false', 'no', '0', 'f']:
                             value = False
                        else:
                             raise ValueError("Enter true or false")
                    elif type_hint == "integer":
                         value = int(value_str)
                    # Add other types like float if needed
                    else: # Assume string otherwise
                        value = value_str
                    config[key] = value
                    break # Value accepted
                except ValueError as e:
                     print(f"Invalid input: {e}. Please try again.")
            elif required:
                print("This field is required. Please enter a value.")
            else:
                # Optional field left blank, use default if available
                if 'default' in details:
                    config[key] = details['default']
                    print(f"Using default value: {config[key]}")
                break # Optional field left blank is okay

    # Get a unique ID for this connector instance
    while True:
        connector_id = input("Enter a unique ID for this connector instance (e.g., 'my_docs'): ").strip()
        if not connector_id:
            print("Connector ID cannot be empty.")
        elif datastore.get_connector(connector_id):
            print(f"Error: Connector ID '{connector_id}' already exists. Choose another.")
        else:
            break

    # Try to create a temporary instance just to validate config *before* saving
    print("Validating configuration...")
    temp_instance = connectors.create_connector_instance(connector_id, config)
    if temp_instance:
        print("Configuration seems valid.")
        if datastore.add_or_update_connector(connector_id, config):
            print(f"Connector '{connector_id}' configuration saved successfully.")
            print("Remember to 'activate_connector' before using it.")
        else:
             print(f"Error saving connector '{connector_id}' configuration to datastore.")
    else:
        print("Failed to create connector instance. Configuration might be invalid. Not saved.")
        # Error message should have been printed by create_connector_instance

    print("-" * 20)


def list_connectors_cli():
    """Lists configured connector instances from the datastore."""
    print("\n--- Configured Connector Instances ---")
    all_connectors = datastore.get_all_connectors()
    if not all_connectors:
        print("No connectors configured yet. Use 'add_connector'.")
    else:
        for conn_id, config in all_connectors.items():
            active_status = "(Active)" if conn_id in active_connectors else "(Inactive)"
            print(f"ID: {conn_id} {active_status}")
            print(f"  Type: {config.get('type', 'N/A')}")
            print(f"  Config: {config}") # Display full config for PoC
            print("-" * 10)
    print("-" * 20)


def activate_connector_cli(connector_id):
    """Loads a configured connector into the active dictionary."""
    if not connector_id:
        print("Usage: activate_connector <connector_id>")
        return

    if connector_id in active_connectors:
        print(f"Connector '{connector_id}' is already active.")
        return

    config = datastore.get_connector(connector_id)
    if not config:
        print(f"Error: Connector configuration '{connector_id}' not found in datastore.")
        return

    print(f"Activating connector '{connector_id}'...")
    instance = connectors.create_connector_instance(connector_id, config)
    if instance:
        # Try to establish connection (if applicable)
        if instance.connect():
            active_connectors[connector_id] = instance
            print(f"Connector '{connector_id}' activated successfully.")
        else:
            print(f"Error: Connector '{connector_id}' failed to connect. Not activated.")
            # Optional: clean up instance if connect fails? Depends on connector logic.
    else:
        print(f"Error: Failed to create instance for connector '{connector_id}'. Check configuration and logs.")

    print("-" * 20)


def deactivate_connector_cli(connector_id):
    """Removes a connector from the active dictionary."""
    if not connector_id:
        print("Usage: deactivate_connector <connector_id>")
        return

    if connector_id in active_connectors:
        instance = active_connectors.pop(connector_id) # Remove and get instance
        try:
            instance.disconnect() # Attempt cleanup
        except Exception as e:
            print(f"Error during disconnect for '{connector_id}': {e}")
        print(f"Connector '{connector_id}' deactivated.")
    else:
        print(f"Connector '{connector_id}' is not currently active.")
    print("-" * 20)


def remove_connector_cli(connector_id):
    """Removes a connector configuration permanently from the datastore."""
    if not connector_id:
        print("Usage: remove_connector <connector_id>")
        return

    # Deactivate first if active
    if connector_id in active_connectors:
        print(f"Connector '{connector_id}' is active. Deactivating first...")
        deactivate_connector_cli(connector_id)

    # Remove from datastore
    if datastore.remove_connector(connector_id):
        print(f"Connector configuration '{connector_id}' permanently removed.")
    else:
        # remove_connector prints its own error if not found
        pass
    print("-" * 20)


def run_word_count_cli(connector_id):
    """Runs the word count agent on data from a specific active connector."""
    if not connector_id:
        print("Usage: run_word_count <connector_id>")
        return

    # 1. Get the active connector instance
    connector_instance = active_connectors.get(connector_id)
    if not connector_instance:
        print(f"Error: Connector '{connector_id}' is not active.")
        print("Please activate it using: activate_connector <id>")
        list_connectors_cli() # Show available/active connectors
        return

    # 2. Query data from the connector
    print(f"\nQuerying data from connector '{connector_id}'...")
    try:
        # For PoC, no specific query params needed for LocalFilesConnector
        # or WordCountAgent. Pass None.
        data = connector_instance.query_data(query_params=None)
        if data is None: # Check if query explicitly returned None (could indicate error)
             print("Error: Query to connector returned None.")
             return
        print(f"Retrieved {len(data)} data items from '{connector_id}'.")
        if not data:
             print("No data retrieved, nothing for the agent to process.")
             return
    except Exception as e:
        print(f"Error querying connector '{connector_id}': {e}")
        traceback.print_exc() # Print full traceback for debugging
        return

    # 3. Create the WordCountAgent instance
    # For PoC, agent config is hardcoded/simple. A real system would load/configure agents too.
    agent_id = "poc_word_counter"
    agent_config = {"type": "word_counter"}
    agent_instance = agents.create_agent_instance(agent_id, agent_config)

    if not agent_instance:
        print("Error: Failed to create WordCountAgent instance.")
        return

    # 4. Execute the agent with the retrieved data
    print(f"\nExecuting agent '{agent_id}'...")
    try:
        result = agent_instance.execute(data_inputs=data, parameters=None)
        print("\n--- Agent Execution Result ---")
        print(result)
        print("-" * 20)
    except Exception as e:
        print(f"Error executing agent '{agent_id}': {e}")
        traceback.print_exc() # Print full traceback for debugging
        print("-" * 20)


# --- Main Loop ---
def main():
    initialize_system()
    display_help()

    while True:
        try:
            command_line = input("OmniNexus> ").strip()
            if not command_line:
                continue

            parts = command_line.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None

            if command in ["quit", "exit"]:
                print("Exiting OmniNexus PoC.")
                # Ensure active connectors are disconnected on exit
                active_ids = list(active_connectors.keys()) # Get IDs before iterating
                if active_ids:
                     print("Deactivating remaining connectors...")
                     for conn_id in active_ids:
                         deactivate_connector_cli(conn_id)
                break
            elif command == "help":
                display_help()
            elif command == "info":
                display_info()
            elif command == "types":
                list_available_types()
            elif command == "add_connector":
                add_connector_cli()
            elif command == "list_connectors":
                list_connectors_cli()
            elif command == "activate_connector":
                activate_connector_cli(args)
            elif command == "deactivate_connector":
                deactivate_connector_cli(args)
            elif command == "remove_connector":
                 remove_connector_cli(args)
            elif command == "run_word_count":
                run_word_count_cli(args)
            # Add more commands here later
            else:
                print(f"Unknown command: '{command}'. Type 'help' for options.")

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            print("Please check the command and try again.")
            traceback.print_exc() # Print full traceback for debugging


if __name__ == "__main__":
    main()