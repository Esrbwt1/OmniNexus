# Local Files Connector (local_files)

The LocalFilesConnector is a built-in OmniNexus connector designed to access plain text files from a specified directory on the local filesystem.

## Functionality

*   Scans a designated directory for files.
*   Supports recursive scanning of subdirectories (optional).
*   Filters files based on specific extensions (currently .txt and .md).
*   Reads the content of supported text files using a configurable encoding (defaulting to utf-8).
*   Formats the retrieved file information and content into the [Standard Data Item Structure](../../protocol/data_item_structure.md).

## Configuration Parameters

The following parameters are used when adding an instance of the local_files connector via the CLI (add_connector command) or other configuration methods.

*   `type` (string, Internal)
    *   Must be set to "local_files" for this connector type. Handled automatically by the framework/CLI.

*   `path` (string, Required)
    *   Description: The absolute or relative path to the directory containing the text files you want OmniNexus to access. Relative paths are resolved based on the OmniNexus execution directory.
    *   Validation: The path must exist and be a readable directory.
    *   Example: C:\Users\MyUser\Documents\Notes or /home/myuser/projects/my_project/docs

*   `recursive` (boolean, Optional)
    *   Description: If set to true, the connector will search for files within the specified path and all its subdirectories. If false or omitted, it only searches the top-level directory specified by path.
    *   Default: false
    *   Example: true

*   `encoding` (string, Optional)
    *   Description: The character encoding to use when reading the content of the text files. Common values include utf-8, latin-1, cp1252.
    *   Validation: Must be a valid encoding recognized by Python.
    *   Default: utf-8
    *   Example: latin-1

## Data Item Output

When query_data is called, this connector returns a list of Data Items, one for each supported file found. Each item follows the standard structure:

*   `item_id`: Unique UUID for this fetch.
*   `connector_id`: ID of this connector instance (e.g., my_notes).
*   `source_uri`: File URI, e.g., file:///path/to/your/file.txt.
*   `retrieved_at`: ISO 8601 timestamp of fetch.
*   `metadata`:
    *   type: text/plain or text/markdown.
    *   filename: Base name of the file (e.g., file.txt).
    *   created_time: File creation timestamp (ISO 8601).
    *   modified_time: File last modification timestamp (ISO 8601).
    *   size_bytes: File size.
    *   encoding: The encoding used to read the file.
    *   full_path: The absolute path to the file.
*   `payload`:
    *   content: The full text content read from the file.

## Usage Example (CLI)

1.  Add Connector:
    
    OmniNexus> add_connector
    Enter connector type...: local_files
    Enter value for 'path'...: /path/to/my/text/files
    Enter value for 'recursive'...: true
    Enter value for 'encoding'...: utf-8 (or press Enter for default)
    Enter a unique ID...: my_text_files
    
2.  (Auto) Activate & Run Agent:
    
    OmniNexus> run_word_count my_text_files
    
    *(This will scan the directory, read files, and pass the content to the Word Count agent)*

## Notes

*   This connector does not require explicit connect or disconnect operations beyond verifying path access during initialization.
*   Error handling for file reading is basic; unreadable files or files with incorrect encoding (other than specified) will generate warnings and be skipped.
*   Currently only supports .txt and .md extensions.