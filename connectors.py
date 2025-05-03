# OmniNexus - connectors.py
# Defines the base structure for data connectors and implements specific connectors.

import os
import glob
from abc import ABC, abstractmethod

# --- Base Connector Class ---

class BaseConnector(ABC):
    """
    Abstract base class for all OmniNexus data connectors.
    Defines the common interface that agents will use.
    """
    def __init__(self, connector_id, config):
        """
        Initializes the connector.
        :param connector_id: A unique identifier for this connector instance.
        :param config: A dictionary containing configuration specific to this connector instance (e.g., path, API key).
        """
        self.connector_id = connector_id
        self.config = config
        self.validate_config() # Call validation during initialization

    @abstractmethod
    def validate_config(self):
        """
        Validates the provided configuration.
        Should raise ValueError or TypeError for invalid configs.
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Establishes connection or performs necessary setup.
        May not be needed for all connector types (e.g., local files).
        Should return True on success, False on failure.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Cleans up resources or disconnects from services.
        """
        pass

    @abstractmethod
    def get_metadata(self):
        """
        Returns metadata about the connector itself or the data source.
        Example: type, path, connection status, capabilities.
        """
        pass

    @abstractmethod
    def query_data(self, query_params=None):
        """
        The core method to retrieve data based on query parameters.
        The structure of query_params and the returned data will vary
        significantly between connector types.
        For PoC, this might be simple (e.g., return all text content).
        :param query_params: Dictionary specifying what data to retrieve.
        :return: Data retrieved from the source (format depends on connector).
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls):
        """
        Returns a description of the required configuration parameters
        for this connector type. Useful for UI/CLI setup.
        :return: Dictionary describing config keys, types, and if they are required.
        """
        pass

# --- Specific Connector Implementations ---

class LocalFilesConnector(BaseConnector):
    """
    Connector for accessing plain text files (.txt, .md) in a local directory.
    """
    SUPPORTED_EXTENSIONS = ['.txt', '.md']

    @classmethod
    def get_config_schema(cls):
        return {
            "path": {"type": "string", "required": True, "description": "Absolute path to the directory containing text files."},
            "recursive": {"type": "boolean", "required": False, "default": False, "description": "Search recursively in subdirectories."},
            # Future: add encoding, specific extensions, etc.
        }

    def validate_config(self):
        """Validates the configuration for LocalFilesConnector."""
        schema = self.get_config_schema()
        if not self.config or not isinstance(self.config, dict):
             raise ValueError("Configuration must be a dictionary.")

        path = self.config.get("path")
        if not path:
            raise ValueError("Configuration key 'path' is required.")
        if not isinstance(path, str):
             raise TypeError("Configuration key 'path' must be a string.")
        if not os.path.isdir(path):
             raise ValueError(f"Provided path '{path}' is not a valid directory or is inaccessible.")

        # Validate 'recursive' if present
        recursive = self.config.get("recursive", schema['recursive']['default']) # Use default if not present
        if not isinstance(recursive, bool):
            raise TypeError("Configuration key 'recursive' must be a boolean (true/false).")
        self.config['recursive'] = recursive # Ensure default is set if not provided

    def connect(self):
        """No explicit connection needed for local files."""
        print(f"LocalFilesConnector '{self.connector_id}': Ready to access '{self.config['path']}'.")
        return True # Always succeeds if path is valid

    def disconnect(self):
        """No explicit disconnection needed."""
        pass # Nothing to clean up

    def get_metadata(self):
        """Returns metadata about this local files connector."""
        return {
            "connector_id": self.connector_id,
            "type": "local_files",
            "path": self.config.get("path"),
            "recursive": self.config.get("recursive"),
            "supported_extensions": self.SUPPORTED_EXTENSIONS,
            "status": "ready" if os.path.isdir(self.config.get("path", "")) else "error - path invalid"
        }

    def query_data(self, query_params=None):
        """
        Retrieves content from text files in the configured directory.
        For PoC: Returns a list of dictionaries, each containing filepath and content.
        Ignores query_params for now.
        """
        data = []
        base_path = self.config.get("path")
        recursive = self.config.get("recursive", False)

        if not base_path or not os.path.isdir(base_path):
            print(f"Error: Path '{base_path}' for connector '{self.connector_id}' is invalid.")
            return data # Return empty list

        # Prepare the glob pattern
        if recursive:
            pattern = os.path.join(base_path, '**', '*') # Search all files in all subdirs
        else:
            pattern = os.path.join(base_path, '*') # Search only files in the base dir

        print(f"Querying path: {base_path}, Recursive: {recursive}, Pattern: {pattern}")

        try:
            # Use glob to find files
            all_files = glob.glob(pattern, recursive=recursive)

            for filepath in all_files:
                # Check if it's a file and has a supported extension
                if os.path.isfile(filepath):
                    _, ext = os.path.splitext(filepath)
                    if ext.lower() in self.SUPPORTED_EXTENSIONS:
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            data.append({
                                "filepath": filepath,
                                "content": content,
                                "connector_id": self.connector_id # Tag data with its source
                            })
                        except Exception as e:
                            print(f"Warning: Could not read file '{filepath}': {e}")
            return data

        except Exception as e:
             print(f"Error querying files for connector '{self.connector_id}': {e}")
             return [] # Return empty list on error


# --- Connector Registry and Factory ---

# Dictionary to hold available connector *classes* (not instances)
_connector_types = {
    "local_files": LocalFilesConnector
    # Future: Add more connector types here (e.g., "email", "web_bookmark")
}

def get_available_connector_types():
    """Returns a list of registered connector type names."""
    return list(_connector_types.keys())

def get_connector_class(connector_type):
    """Gets the class for a given connector type name."""
    return _connector_types.get(connector_type)

def create_connector_instance(connector_id, config):
    """
    Factory function to create connector instances based on config type.
    :param connector_id: Unique ID for this instance.
    :param config: Dictionary containing configuration, MUST include 'type'.
    :return: An instance of a BaseConnector subclass, or None if type is invalid/missing.
    """
    if not config or not isinstance(config, dict):
        print("Error: Connector config must be a dictionary.")
        return None

    connector_type = config.get("type")
    if not connector_type:
        print("Error: Connector config must include a 'type' key.")
        return None

    ConnectorClass = get_connector_class(connector_type)
    if ConnectorClass:
        try:
            # Instantiate the specific connector class
            instance = ConnectorClass(connector_id=connector_id, config=config)
            print(f"Successfully created connector instance '{connector_id}' of type '{connector_type}'.")
            return instance
        except (ValueError, TypeError) as e:
            print(f"Error creating connector '{connector_id}' of type '{connector_type}': Invalid config - {e}")
            return None
        except Exception as e:
            print(f"Unexpected error creating connector '{connector_id}': {e}")
            return None
    else:
        print(f"Error: Unknown connector type '{connector_type}'. Available types: {get_available_connector_types()}")
        return None

# Example of how to use it (will be called from main.py later)
if __name__ == "__main__":
    print("Running connectors module directly for testing...")

    # --- Test LocalFilesConnector ---
    print("\n--- Testing LocalFilesConnector ---")

    # 1. Create a temporary directory and files for testing
    test_dir = "temp_test_docs"
    sub_dir = os.path.join(test_dir, "subdir")
    os.makedirs(sub_dir, exist_ok=True)
    with open(os.path.join(test_dir, "file1.txt"), "w") as f: f.write("Content of file 1.")
    with open(os.path.join(test_dir, "file2.md"), "w") as f: f.write("Markdown content here.")
    with open(os.path.join(test_dir, "image.jpg"), "w") as f: f.write("fake image") # Should be ignored
    with open(os.path.join(sub_dir, "sub_file.txt"), "w") as f: f.write("Content in subdirectory.")
    print(f"Created test directory: {os.path.abspath(test_dir)}")

    # 2. Test valid config (non-recursive)
    valid_config_nonrec = {
        "type": "local_files",
        "path": os.path.abspath(test_dir) # Use absolute path
        # "recursive" is omitted, should default to False
    }
    connector_nonrec = create_connector_instance("test_local_nonrec", valid_config_nonrec)

    if connector_nonrec:
        print("Metadata:", connector_nonrec.get_metadata())
        if connector_nonrec.connect():
            print("Querying non-recursively...")
            results_nonrec = connector_nonrec.query_data()
            print(f"Found {len(results_nonrec)} files:")
            for item in results_nonrec:
                print(f"- {item['filepath']} (Content: '{item['content']}')")
            connector_nonrec.disconnect()

    # 3. Test valid config (recursive)
    valid_config_rec = {
        "type": "local_files",
        "path": os.path.abspath(test_dir),
        "recursive": True
    }
    connector_rec = create_connector_instance("test_local_rec", valid_config_rec)

    if connector_rec:
         print("\nQuerying recursively...")
         results_rec = connector_rec.query_data()
         print(f"Found {len(results_rec)} files:")
         for item in results_rec:
             print(f"- {item['filepath']} (Content: '{item['content']}')")

    # 4. Test invalid config (missing path)
    print("\n--- Testing Invalid Config ---")
    invalid_config_missing = {"type": "local_files"}
    create_connector_instance("test_invalid_missing", invalid_config_missing)

    # 5. Test invalid config (path is not a directory)
    invalid_config_notdir = {"type": "local_files", "path": os.path.join(test_dir, "file1.txt")}
    create_connector_instance("test_invalid_notdir", invalid_config_notdir)

    # 6. Test invalid type
    print("\n--- Testing Invalid Type ---")
    invalid_config_type = {"type": "non_existent_type", "path": test_dir}
    create_connector_instance("test_invalid_type", invalid_config_type)

    # 7. Clean up test directory (optional, but good practice)
    # import shutil
    # try:
    #     shutil.rmtree(test_dir)
    #     print(f"\nCleaned up test directory: {test_dir}")
    # except Exception as e:
    #     print(f"Error cleaning up test directory: {e}")