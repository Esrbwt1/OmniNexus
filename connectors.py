# OmniNexus - connectors.py
# Defines the base structure for data connectors and implements specific connectors.

import os
import glob
from abc import ABC, abstractmethod
import datetime
# --- Base Connector Class ---

class BaseConnector(ABC):
    """
    Abstract Base Class for all OmniNexus data connectors.

    Defines the common interface for discovering, connecting to, querying,
    and managing external data sources within the OmniNexus framework.

    Subclasses must implement all methods decorated with @abstractmethod
    and the @classmethod get_config_schema.
    """
    def __init__(self, connector_id, config):
        """
        Initializes the connector instance.

        Should be called by subclasses using super().__init__(...).

        :param connector_id: A unique identifier for this specific connector instance (e.g., 'my_local_docs').
                             Provided by the orchestrator/user during configuration.
        :param config: A dictionary containing configuration parameters specific
                       to this connector instance (e.g., path, API key, server address).
                       Must include a 'type' key matching the registered connector type.
        """
        if not connector_id or not isinstance(connector_id, str):
             raise ValueError("Connector ID must be a non-empty string.")
        if not config or not isinstance(config, dict):
             raise ValueError("Connector config must be a dictionary.")
        # We don't validate 'type' here, assuming factory did its job based on it

        self.connector_id = connector_id
        # Make a copy to prevent external modification of the original config dict
        self.config = config.copy()
        # Validate the specific config keys required by the subclass
        try:
             self.validate_config()
        except (ValueError, TypeError) as e:
             # Add context to validation errors
             raise type(e)(f"Configuration validation failed for connector '{connector_id}' (type '{config.get('type', 'N/A')}'): {e}")

    @abstractmethod
    def validate_config(self):
        """
        Validates the self.config dictionary against the requirements of this specific connector type.

        - Should check for the presence and correct types of required keys.
        - Should validate the format or constraints of values (e.g., path exists, port is valid).
        - May assign default values from the schema to self.config if optional keys are missing.
        - Should raise ValueError or TypeError for invalid configurations.
        """
        pass

    @abstractmethod
    def connect(self):
        """
        Establishes a connection to the external data source or performs necessary setup.

        - For networked services (IMAP, APIs): Authenticate and establish a session.
        - For local resources (files): May simply verify access or perform initial scans.
        - Should store necessary connection state within the instance (e.g., self.connection object).
        - Should update internal state flags (e.g., self._is_connected).
        - Return True on successful connection/setup, False on failure.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Cleans up resources, closes connections, and logs out from services.

        - Should handle potential errors during disconnection gracefully.
        - Should reset internal connection state flags.
        - Called by the orchestrator when deactivating the connector or shutting down.
        """
        pass

    @abstractmethod
    def get_metadata(self):
        """
        Returns metadata about the connector instance and potentially the data source.

        :return: A dictionary containing information such as:
                 - connector_id: str
                 - type: str (e.g., 'local_files', 'imap')
                 - status: str (e.g., 'connected', 'disconnected', 'error')
                 - Configuration details (e.g., path, server) - careful with secrets!
                 - Potentially dynamic info (e.g., number of items, last sync time - for future)
        """
        pass

    @abstractmethod
    def query_data(self, query_params=None):
        """
        The core method to retrieve data from the source based on query parameters.

        :param query_params: Optional dictionary specifying what data to retrieve.
                             The structure and interpretation of these parameters are
                             defined by the specific connector implementation.
                             Examples: search keywords, date ranges, specific IDs, count limits.
                             If None, the connector might return default data (e.g., all items, recent items).

        :return: A list of dictionaries, where each dictionary conforms to the
                 `protocol.DATA_ITEM_STRUCTURE`. Returns an empty list if no data
                 matches or an error occurs during the query. Should not return None.
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls):
        """
        Returns a schema describing the configuration parameters required by this connector type.

        This is used by the UI/CLI to guide the user during setup and for validation.

        :return: A dictionary where keys are parameter names and values are dictionaries
                 describing the parameter:
                 {
                   "param_name": {
                       "type": "string" | "integer" | "boolean" | "filepath" | "directorypath" | ...,
                       "required": True | False,
                       "default": <default_value> (if not required),
                       "description": "User-friendly explanation."
                   },
                   ...
                 }
                 See `protocol.CONFIG_SCHEMA_FORMAT`.
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


# Add near the top if not already there
import imaplib
import email
from email.header import decode_header, make_header
import socket # For timeout handling
import ssl # For secure connection
import re # For cleaning up headers potentially

# (Keep BaseConnector and LocalFilesConnector classes above this)

class ImapConnector(BaseConnector):
    """
    Connector for accessing emails via IMAP protocol. (Phase 2 Implementation)
    Handles connection, login, and fetching basic header info for recent emails.
    WARNING: Currently retrieves password insecurely from config.
    """
    DEFAULT_IMAP_PORT_SSL = 993
    DEFAULT_IMAP_PORT_NONSSL = 143
    DEFAULT_FETCH_COUNT = 5 # Number of recent emails to fetch headers for

    @classmethod
    def get_config_schema(cls):
        return {
            "server": {"type": "string", "required": True, "description": "IMAP server address (e.g., imap.gmail.com)."},
            "port": {"type": "integer", "required": False, "default": None, "description": f"IMAP server port (defaults: {cls.DEFAULT_IMAP_PORT_SSL} for SSL, {cls.DEFAULT_IMAP_PORT_NONSSL} otherwise)."},
            "username": {"type": "string", "required": True, "description": "Email account username."},
            "password_or_token": {"type": "string", "required": True, "description": "Account password or App Password/Token (stored insecurely!)."}, # SECURITY WARNING
            "mailbox": {"type": "string", "required": False, "default": "INBOX", "description": "Mailbox/folder to access."},
            "use_ssl": {"type": "boolean", "required": False, "default": True, "description": "Use SSL/TLS for connection."},
            "fetch_count": {"type": "integer", "required": False, "default": cls.DEFAULT_FETCH_COUNT, "description": "Number of recent emails to fetch headers for."},
        }

    def __init__(self, connector_id, config):
        """Initializes IMAP connector specific state."""
        super().__init__(connector_id, config)
        self.connection = None # Holds the imaplib connection object
        self._is_connected = False
        self._selected_mailbox = None

    def validate_config(self):
        """Validates the configuration for ImapConnector."""
        schema = self.get_config_schema()
        required_keys = {k for k, v in schema.items() if v.get("required")}
        provided_keys = set(self.config.keys())
        provided_keys.discard('type') # Ignore 'type' key

        if not required_keys.issubset(provided_keys):
             missing = required_keys - provided_keys
             raise ValueError(f"Missing required configuration keys: {missing}")

        # Basic type checks and default assignments
        if not isinstance(self.config.get("server"), str): raise TypeError("Config 'server' must be a string.")
        if not isinstance(self.config.get("username"), str): raise TypeError("Config 'username' must be a string.")
        if not isinstance(self.config.get("password_or_token"), str): raise TypeError("Config 'password_or_token' must be a string.")

        use_ssl = self.config.get("use_ssl", schema['use_ssl']['default'])
        if not isinstance(use_ssl, bool): raise TypeError("Config 'use_ssl' must be a boolean.")
        self.config['use_ssl'] = use_ssl # Ensure default is set

        default_port = self.DEFAULT_IMAP_PORT_SSL if use_ssl else self.DEFAULT_IMAP_PORT_NONSSL
        port = self.config.get("port", default_port)
        # Allow overriding default even if None was explicitly passed in schema default
        if port is None: port = default_port
        if not isinstance(port, int): raise TypeError("Config 'port' must be an integer.")
        self.config['port'] = port # Ensure default is set

        mailbox = self.config.get("mailbox", schema['mailbox']['default'])
        if not isinstance(mailbox, str): raise TypeError("Config 'mailbox' must be a string.")
        self.config['mailbox'] = mailbox

        fetch_count = self.config.get("fetch_count", schema['fetch_count']['default'])
        if not isinstance(fetch_count, int) or fetch_count <= 0:
            raise ValueError("Config 'fetch_count' must be a positive integer.")
        self.config['fetch_count'] = fetch_count

        print("IMAP Config basic validation passed. WARNING: Password stored insecurely in config!")


    def connect(self):
        """Establishes connection to the IMAP server, logs in, and selects mailbox."""
        if self._is_connected:
            print(f"IMAP connector '{self.connector_id}' already connected to mailbox '{self._selected_mailbox}'.")
            return True

        server = self.config.get("server")
        port = self.config.get("port")
        use_ssl = self.config.get("use_ssl")
        username = self.config.get("username")
        password = self.config.get("password_or_token") # INSECURE retrieval
        mailbox = self.config.get("mailbox")

        print(f"Connecting to IMAP {server}:{port} (SSL: {use_ssl}) for user {username}...")

        try:
            # Establish connection
            if use_ssl:
                # Consider adding SSL context for better security later
                self.connection = imaplib.IMAP4_SSL(server, port)
            else:
                self.connection = imaplib.IMAP4(server, port)
            print(f"Connection established.")

            # Login
            status, messages = self.connection.login(username, password)
            if status != 'OK':
                raise imaplib.IMAP4.error(f"Login failed: {' '.join(m.decode() if isinstance(m, bytes) else str(m) for m in messages)}")
            print("IMAP login successful.")

            # Select Mailbox
            # Use read-only if possible to prevent accidental changes like marking read
            status, messages = self.connection.select(f'"{mailbox}"', readonly=True)
            # Fallback if readonly isn't supported
            if status != 'OK':
                 print(f"Read-only mailbox selection failed, trying read-write: {' '.join(m.decode() if isinstance(m, bytes) else str(m) for m in messages)}")
                 status, messages = self.connection.select(f'"{mailbox}"', readonly=False)
                 if status != 'OK':
                      raise imaplib.IMAP4.error(f"Mailbox selection failed: {' '.join(m.decode() if isinstance(m, bytes) else str(m) for m in messages)}")

            # `messages` usually contains the count of messages in the mailbox
            message_count = int(messages[0]) if messages and messages[0].isdigit() else 'N/A'
            print(f"Mailbox '{mailbox}' selected successfully ({message_count} messages).")
            self._selected_mailbox = mailbox
            self._is_connected = True
            return True

        except (imaplib.IMAP4.error, socket.gaierror, socket.timeout, ssl.SSLError) as e:
            print(f"Error connecting/logging into IMAP server {server}: {e}")
            # Ensure connection is closed/nulled if partially opened
            if self.connection:
                try: self.connection.shutdown() # Close SSL connection if applicable
                except: pass # Ignore errors during cleanup
            self.connection = None
            self._is_connected = False
            self._selected_mailbox = None
            return False
        except Exception as e:
             print(f"Unexpected error during IMAP connection: {e}")
             traceback.print_exc()
             self.connection = None
             self._is_connected = False
             self._selected_mailbox = None
             return False


    def disconnect(self):
        """Logs out and closes the IMAP connection."""
        if self.connection:
            print(f"Disconnecting IMAP connector '{self.connector_id}'...")
            try:
                # Unselect mailbox (implicitly done by close sometimes, but good practice)
                 if self._selected_mailbox:
                     try:
                         self.connection.close()
                         # print("Mailbox closed.")
                     except imaplib.IMAP4.error as e:
                         # Ignore errors closing if logout still works
                         print(f"Note: Error closing mailbox (might be ok): {e}")
                 # Logout
                 try:
                     status, msg = self.connection.logout()
                     # print(f"IMAP logout status: {status} - {msg}")
                 except Exception as e:
                      # Ignore errors if connection is likely dead anyway
                      print(f"Note: Error during logout (might be ok): {e}")

            finally:
                # Ensure state is reset even if logout had issues
                self.connection = None
                self._is_connected = False
                self._selected_mailbox = None
                print(f"IMAP connector '{self.connector_id}' disconnected.")
        else:
            # print(f"IMAP connector '{self.connector_id}' already disconnected.") # Can be noisy
            self._is_connected = False # Ensure state is correct
            self._selected_mailbox = None


    def get_metadata(self):
        """Returns metadata about this IMAP connector."""
        status = "disconnected"
        if self._is_connected and self._selected_mailbox:
            status = f"connected to '{self._selected_mailbox}'"
        elif self.connection: # Might be connected but mailbox select failed
            status = "connected (no mailbox)"

        return {
            "connector_id": self.connector_id,
            "type": "imap",
            "server": self.config.get("server"),
            "port": self.config.get("port"),
            "username": self.config.get("username"),
            "status": status
            # Could add mailbox count from connection if stored
        }

    def _decode_header(self, header_text):
        """Decodes email header text, handling different encodings."""
        if header_text is None:
            return ""
        try:
            # Use email.header.make_header to handle decoding and joining parts
            decoded_header = make_header(decode_header(str(header_text)))
            return str(decoded_header)
        except Exception:
            # Fallback for unexpected errors or non-standard headers
            try:
                return str(header_text).encode('raw_unicode_escape').decode('utf-8', 'ignore')
            except:
                return str(header_text) # Last resort


    def query_data(self, query_params=None):
        """
        Fetches basic headers (Subject, From, Date) for recent emails.
        Returns data structured as standard Data Items.
        """
        if not self._is_connected or not self.connection or not self._selected_mailbox:
            print(f"Error: IMAP connector '{self.connector_id}' is not connected to a mailbox.")
            if not self.connect(): # Attempt reconnect
                 print("Error: Reconnect failed.")
                 return []
            if not self._is_connected: # Check again after connect attempt
                 return []

        data_items = []
        fetch_count = self.config.get('fetch_count', self.DEFAULT_FETCH_COUNT)
        print(f"IMAP Connector '{self.connector_id}': Fetching headers for last {fetch_count} emails...")

        try:
            # Import protocol utilities here
            from protocol import create_iso_timestamp, generate_item_id

            # 1. Search for all message UIDs in the current mailbox
            status, messages = self.connection.search(None, 'ALL')
            if status != 'OK':
                print(f"Error searching mailbox: {' '.join(m.decode() for m in messages if isinstance(m, bytes))}")
                return []

            # UIDs are returned as a space-separated string in bytes
            if not messages or not messages[0]:
                print("No messages found in mailbox.")
                return []
            uids_bytes = messages[0].split()

            # 2. Get the UIDs for the most recent messages
            recent_uids = uids_bytes[-fetch_count:]
            if not recent_uids:
                print("No UIDs selected for fetching.")
                return []

            print(f"Found {len(uids_bytes)} total emails. Fetching details for {len(recent_uids)} UIDs: {[u.decode() for u in recent_uids]}")

            # 3. Fetch headers for each UID
            for uid_bytes in recent_uids:
                uid = uid_bytes.decode() # Use string representation of UID
                try:
                    # Fetch specific header fields. BODY.PEEK avoids marking as read.
                    fetch_command = f'(BODY.PEEK[HEADER.FIELDS (Subject From Date)])'
                    status, msg_data = self.connection.fetch(uid_bytes, fetch_command)

                    if status != 'OK':
                        print(f"Error fetching headers for UID {uid}: Status {status}")
                        continue

                    # Check if data was actually returned for this UID
                    if not msg_data or msg_data[0] is None:
                         print(f"Warning: No header data returned for UID {uid}. Skipping.")
                         continue

                    # msg_data is usually [(b'UID 123 (RFC822 {size}', b'Header Content...'), b')']
                    # We need the header content part
                    header_bytes = None
                    for part in msg_data:
                        if isinstance(part, tuple) and len(part) > 1 and isinstance(part[1], bytes):
                            header_bytes = part[1]
                            break # Found the header bytes

                    if not header_bytes:
                         print(f"Warning: Could not parse header bytes from fetch response for UID {uid}. Response: {msg_data}")
                         continue

                    # 4. Parse headers using email module
                    headers = email.message_from_bytes(header_bytes)

                    subject = self._decode_header(headers['Subject'])
                    sender = self._decode_header(headers['From'])
                    email_date_str = headers['Date'] # Keep as string for now, parsing can be complex

                    # 5. Construct Data Item
                    item = {
                        "item_id": generate_item_id(),
                        "connector_id": self.connector_id,
                        "source_uri": f"imap://{self.config['username']}@{self.config['server']}/{self._selected_mailbox};UID={uid}",
                        "retrieved_at": create_iso_timestamp(),
                        "metadata": {
                            "type": "message/rfc822-headers", # Indicate it's only headers
                            "uid": uid,
                            "mailbox": self._selected_mailbox,
                            # Add more metadata if needed
                        },
                        "payload": {
                            # For headers-only fetch, put them directly in payload for easy access
                            "subject": subject,
                            "from": sender,
                            "date_str": email_date_str,
                            # In a full fetch, 'content' might hold body text/html
                        }
                    }
                    data_items.append(item)
                    # print(f"  - Processed UID {uid}: Subject='{subject[:50]}...'") # Optional debug

                except Exception as e_fetch:
                    print(f"Error processing UID {uid}: {e_fetch}")
                    traceback.print_exc() # Print details for debugging
                    continue # Move to next UID

            print(f"Finished fetching headers. Retrieved {len(data_items)} items.")
            return data_items

        except imaplib.IMAP4.error as e:
             print(f"IMAP error during query_data: {e}")
             # Connection might be dead, attempt disconnect/reset state
             self.disconnect()
             return []
        except Exception as e:
             print(f"Unexpected error during IMAP query_data: {e}")
             traceback.print_exc()
             self.disconnect() # Disconnect on unexpected errors too
             return []

# --- Connector Registry and Factory ---

# Ensure the connector class is in the registry dictionary
_connector_types = {
    "local_files": LocalFilesConnector,
    "imap": ImapConnector # Make sure this line exists
}

# (Keep get_available_connector_types, get_connector_class, create_connector_instance functions below this)
# (Keep the __main__ block as it is)

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