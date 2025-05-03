# OmniNexus - connectors.py
# Defines the base structure for data connectors and implements specific connectors.

import os
import glob
from abc import ABC, abstractmethod
import datetime
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
    Adheres to Phase 2 Data Item Structure.
    """
    SUPPORTED_EXTENSIONS = ['.txt', '.md']

    @classmethod
    def get_config_schema(cls):
        return {
            "path": {"type": "string", "required": True, "description": "Absolute path to the directory containing text files."},
            "recursive": {"type": "boolean", "required": False, "default": False, "description": "Search recursively in subdirectories."},
            "encoding": {"type": "string", "required": False, "default": "utf-8", "description": "Text encoding to use (e.g., utf-8, latin-1)."}
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
             # Try resolving relative paths, useful in some contexts
             abs_path = os.path.abspath(path)
             if not os.path.isdir(abs_path):
                 raise ValueError(f"Provided path '{path}' (resolved to '{abs_path}') is not a valid directory or is inaccessible.")
             else:
                 # Update config with absolute path if validation passes
                 self.config['path'] = abs_path
                 print(f"Relative path '{path}' resolved to absolute path '{abs_path}'.")


        recursive = self.config.get("recursive", schema['recursive']['default'])
        if not isinstance(recursive, bool):
            raise TypeError("Configuration key 'recursive' must be a boolean (true/false).")
        self.config['recursive'] = recursive

        encoding = self.config.get("encoding", schema['encoding']['default'])
        if not isinstance(encoding, str):
             raise TypeError("Configuration key 'encoding' must be a string.")
        try:
             "test".encode(encoding) # Test if encoding is valid
        except LookupError:
             raise ValueError(f"Invalid encoding specified: '{encoding}'")
        self.config['encoding'] = encoding


    def connect(self):
        """No explicit connection needed for local files."""
        print(f"LocalFilesConnector '{self.connector_id}': Ready to access '{self.config['path']}'.")
        return True

    def disconnect(self):
        """No explicit disconnection needed."""
        pass

    def get_metadata(self):
        """Returns metadata about this local files connector."""
        return {
            "connector_id": self.connector_id,
            "type": "local_files",
            "path": self.config.get("path"),
            "recursive": self.config.get("recursive"),
            "encoding": self.config.get("encoding"),
            "supported_extensions": self.SUPPORTED_EXTENSIONS,
            "status": "ready" if os.path.isdir(self.config.get("path", "")) else "error - path invalid"
        }

    def query_data(self, query_params=None):
        """
        Retrieves content from text files, structuring output as standard Data Items.
        Ignores query_params for now.
        """
        data_items = []
        base_path = self.config.get("path")
        recursive = self.config.get("recursive", False)
        encoding = self.config.get("encoding", "utf-8") # Fallback just in case

        if not base_path or not os.path.isdir(base_path):
            print(f"Error: Path '{base_path}' for connector '{self.connector_id}' is invalid.")
            return data_items # Return empty list

        if recursive:
            pattern = os.path.join(base_path, '**', '*')
        else:
            pattern = os.path.join(base_path, '*')

        print(f"Querying path: {base_path}, Recursive: {recursive}, Encoding: {encoding}")

        try:
            # Import protocol utilities here to avoid circular dependency at top level
            from protocol import create_iso_timestamp, generate_item_id

            all_files = glob.glob(pattern, recursive=recursive)

            for filepath in all_files:
                if os.path.isfile(filepath):
                    _, ext = os.path.splitext(filepath)
                    if ext.lower() in self.SUPPORTED_EXTENSIONS:
                        try:
                            # Get file metadata
                            stat_result = os.stat(filepath)
                            created_time = datetime.datetime.fromtimestamp(stat_result.st_ctime, tz=datetime.timezone.utc).isoformat()
                            modified_time = datetime.datetime.fromtimestamp(stat_result.st_mtime, tz=datetime.timezone.utc).isoformat()
                            file_size = stat_result.st_size

                            # Read content
                            with open(filepath, 'r', encoding=encoding) as f:
                                content = f.read()

                            # Create Data Item
                            item = {
                                "item_id": generate_item_id(),
                                "connector_id": self.connector_id,
                                "source_uri": f"file://{os.path.abspath(filepath)}", # Use file URI scheme
                                "retrieved_at": create_iso_timestamp(),
                                "metadata": {
                                    "type": "text/plain" if ext.lower() == '.txt' else "text/markdown",
                                    "filename": os.path.basename(filepath),
                                    "created_time": created_time,
                                    "modified_time": modified_time,
                                    "size_bytes": file_size,
                                    "encoding": encoding,
                                    "full_path": os.path.abspath(filepath) # Keep path accessible if needed
                                },
                                "payload": {
                                    "content": content
                                }
                            }
                            data_items.append(item)
                        except Exception as e:
                            print(f"Warning: Could not process file '{filepath}': {e}")
            return data_items

        except Exception as e:
             print(f"Error querying files for connector '{self.connector_id}': {e}")
             return []


# Add near the top with other imports
import imaplib
import email
import socket # For timeout handling later
import ssl # For secure connection later

# (Keep BaseConnector and LocalFilesConnector classes above this)

class ImapConnector(BaseConnector):
    """
    Connector for accessing emails via IMAP protocol. (Skeleton for Phase 2)
    Handles basic connection structure and config. Fetching logic TBD.
    """
    DEFAULT_IMAP_PORT = 993 # Standard IMAP over SSL port

    @classmethod
    def get_config_schema(cls):
        return {
            "server": {"type": "string", "required": True, "description": "IMAP server address (e.g., imap.gmail.com)."},
            "port": {"type": "integer", "required": False, "default": cls.DEFAULT_IMAP_PORT, "description": "IMAP server port."},
            "username": {"type": "string", "required": True, "description": "Email account username."},
            "password_or_token": {"type": "string", "required": True, "description": "Account password or App Password/Token (store securely!)."}, # SECURITY WARNING
            "mailbox": {"type": "string", "required": False, "default": "INBOX", "description": "Mailbox/folder to access."},
            "use_ssl": {"type": "boolean", "required": False, "default": True, "description": "Use SSL/TLS for connection."},
            # Future: add search criteria, date ranges, etc.
        }

    def __init__(self, connector_id, config):
        """Initializes IMAP connector specific state."""
        super().__init__(connector_id, config)
        self.connection = None # Holds the imaplib connection object
        self._is_connected = False

    def validate_config(self):
        """Validates the configuration for ImapConnector."""
        schema = self.get_config_schema()
        required_keys = {k for k, v in schema.items() if v.get("required")}
        provided_keys = set(self.config.keys())

        # Remove 'type' as it's handled by the factory
        provided_keys.discard('type')

        if not required_keys.issubset(provided_keys):
             missing = required_keys - provided_keys
             raise ValueError(f"Missing required configuration keys: {missing}")

        # Basic type checks (can be expanded)
        if not isinstance(self.config.get("server"), str): raise TypeError("Config 'server' must be a string.")
        if not isinstance(self.config.get("username"), str): raise TypeError("Config 'username' must be a string.")
        if not isinstance(self.config.get("password_or_token"), str): raise TypeError("Config 'password_or_token' must be a string.") # Stored insecurely for now!
        port = self.config.get("port", schema['port']['default'])
        if not isinstance(port, int): raise TypeError("Config 'port' must be an integer.")
        use_ssl = self.config.get("use_ssl", schema['use_ssl']['default'])
        if not isinstance(use_ssl, bool): raise TypeError("Config 'use_ssl' must be a boolean.")
        mailbox = self.config.get("mailbox", schema['mailbox']['default'])
        if not isinstance(mailbox, str): raise TypeError("Config 'mailbox' must be a string.")

        # Assign defaults if not present
        self.config['port'] = port
        self.config['use_ssl'] = use_ssl
        self.config['mailbox'] = mailbox

        print("IMAP Config basic validation passed. WARNING: Password stored insecurely in config!")


    def connect(self):
        """Establishes connection to the IMAP server and logs in."""
        if self._is_connected:
            print(f"IMAP connector '{self.connector_id}' already connected.")
            return True

        server = self.config.get("server")
        port = self.config.get("port")
        use_ssl = self.config.get("use_ssl")
        username = self.config.get("username")
        password = self.config.get("password_or_token") # INSECURE retrieval

        print(f"Connecting to IMAP server {server}:{port} for user {username}...")

        try:
            # === Placeholder Connection Logic ===
            # A real implementation requires error handling, timeouts, choosing SSL/TLS correctly.
            print("Placeholder: Simulating IMAP connection and login.")
            # Example (needs refinement):
            # if use_ssl:
            #     self.connection = imaplib.IMAP4_SSL(server, port)
            # else:
            #     self.connection = imaplib.IMAP4(server, port)
            # status, messages = self.connection.login(username, password)
            # if status != 'OK':
            #     raise imaplib.IMAP4.error(f"Login failed: {messages}")
            # print("IMAP login successful.")
            # status, messages = self.connection.select(self.config['mailbox'])
            # if status != 'OK':
            #     raise imaplib.IMAP4.error(f"Mailbox selection failed: {messages}")
            # print(f"Mailbox '{self.config['mailbox']}' selected.")

            self._is_connected = True # Mark as connected on placeholder success
            print(f"IMAP Connector '{self.connector_id}': Placeholder connection established.")
            return True

        except (imaplib.IMAP4.error, socket.gaierror, socket.timeout, ssl.SSLError) as e:
            print(f"Error connecting/logging into IMAP server {server}: {e}")
            self.connection = None
            self._is_connected = False
            return False
        except Exception as e:
             print(f"Unexpected error during IMAP connection: {e}")
             self.connection = None
             self._is_connected = False
             return False


    def disconnect(self):
        """Logs out and closes the IMAP connection."""
        if self.connection and self._is_connected:
            print(f"Disconnecting IMAP connector '{self.connector_id}'...")
            try:
                # === Placeholder Disconnect Logic ===
                print("Placeholder: Simulating IMAP logout and close.")
                # Example (needs refinement):
                # self.connection.close() # Close current mailbox first
                # self.connection.logout()
                # print("IMAP logout successful.")
            except imaplib.IMAP4.error as e:
                print(f"Error during IMAP logout/close: {e}")
            finally:
                self.connection = None
                self._is_connected = False
        else:
            print(f"IMAP connector '{self.connector_id}' already disconnected or never connected.")


    def get_metadata(self):
        """Returns metadata about this IMAP connector."""
        return {
            "connector_id": self.connector_id,
            "type": "imap",
            "server": self.config.get("server"),
            "port": self.config.get("port"),
            "username": self.config.get("username"),
            "mailbox": self.config.get("mailbox"),
            "status": "connected" if self._is_connected else "disconnected"
            # Future: add email counts, capabilities etc.
        }


    def query_data(self, query_params=None):
        """
        Fetches emails based on criteria. (Placeholder for Phase 2)
        Should return data structured as standard Data Items.
        """
        if not self._is_connected or not self.connection:
            print(f"Error: IMAP connector '{self.connector_id}' is not connected.")
            return []

        print(f"IMAP Connector '{self.connector_id}': Placeholder query_data called.")
        # === Placeholder Query & Parsing Logic ===
        # 1. Define search criteria (e.g., UNSEEN, SINCE date, FROM sender) - based on query_params
        # 2. Use self.connection.search() to get email UIDs
        # 3. For each UID (or batch):
        #      Use self.connection.fetch(uid, '(RFC822)') to get raw email data
        #      Parse raw email using `email.message_from_bytes()`
        #      Extract headers (Subject, From, To, Date), body (plaintext/html)
        #      Handle character encodings, attachments (TBD)
        #      Construct a Data Item dictionary conforming to protocol.DATA_ITEM_STRUCTURE:
        #          item_id = generate_item_id()
        #          connector_id = self.connector_id
        #          source_uri = f"imap://{self.config['username']}@{self.config['server']}/{self.config['mailbox']};UID={uid}"
        #          retrieved_at = create_iso_timestamp()
        #          metadata = { 'type': 'message/rfc822', 'subject': ..., 'from': ..., 'date': ... }
        #          payload = { 'headers': {...}, 'body_text': ..., 'body_html': ... (optional) }
        # 4. Append Data Item to a list
        # 5. Return the list of Data Items

        # For now, return empty list
        print("Placeholder: Returning empty list. IMAP fetching not implemented.")
        return []

# --- Connector Registry and Factory ---

# Add the new connector class to the registry dictionary
_connector_types = {
    "local_files": LocalFilesConnector,
    "imap": ImapConnector # Add the new type here
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