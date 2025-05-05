A3sh, [5/5/2025 3:07 PM]
# IMAP Email Connector (imap)

The ImapConnector allows OmniNexus to connect to an email account using the IMAP (Internet Message Access Protocol) standard. It can retrieve email headers and body content.

Security Note: This connector uses the system's secure credential manager (via the keyring library) to handle email passwords/tokens, avoiding storing them directly in the OmniNexus configuration files.

## Functionality

*   Connects to a specified IMAP server (e.g., imap.gmail.com, outlook.office365.com) using SSL/TLS by default.
*   Authenticates using a username and a password/token retrieved securely from the system keyring.
*   Selects a specified mailbox (e.g., INBOX).
*   Fetches a configurable number of the most recent emails from the selected mailbox.
*   Parses fetched emails to extract headers (Subject, From, To, Cc, Date, Message-ID) and the plain text body content.
*   Formats the retrieved email information into the [Standard Data Item Structure](../../protocol/data_item_structure.md).

## Configuration Parameters

*   `type` (string, Internal)
    *   Must be set to "imap".

*   `server` (string, Required)
    *   Description: The hostname or IP address of the IMAP server.
    *   Example: imap.gmail.com

*   `port` (integer, Optional)
    *   Description: The port number for the IMAP server. If omitted, defaults to 993 if use_ssl is true, or 143 if use_ssl is false.
    *   Example: 993

*   `username` (string, Required)
    *   Description: The full email address or username required to log in to the account.
    *   Example: myemail@example.com

*   `mailbox` (string, Optional)
    *   Description: The name of the mailbox (folder) to access. Case-sensitivity may depend on the server.
    *   Default: "INBOX"
    *   Example: "Sent", "Archive/2024"

*   `use_ssl` (boolean, Optional)
    *   Description: Whether to use an encrypted SSL/TLS connection (IMAP4_SSL). Set to false only if connecting to a server that explicitly requires a non-encrypted connection (rare and insecure).
    *   Default: true

*   `fetch_count` (integer, Optional)
    *   Description: The maximum number of *most recent* emails to fetch during each query_data call.
    *   Default: 5
    *   Example: 20

## Password/Token Handling (IMPORTANT)

This connector does not store your email password or access token in its configuration file (omnidata/connectors.json). Instead, it relies on the `keyring` library to securely interact with your operating system's credential manager (like Windows Credential Manager, macOS Keychain, or Linux Secret Service/KWallet).

Before you can activate an `imap` connector instance, you MUST manually store the password/token in the keyring.

1.  Install `keyring` CLI (if needed):
        pip install keyring
    
2.  Determine the `service name` and `username`:
    *   The service name used by OmniNexus is OmniNexus_IMAP:<server_address> (e.g., OmniNexus_IMAP:imap.gmail.com).
    *   The username is the value you configured for the connector instance.
3.  Run the `keyring set` command: Open a terminal and run:
        keyring set "OmniNexus_IMAP:<server_address>" "<your_username>"
    
    Replace <server_address> and <your_username> with the actual values from your connector config.
    *   Example for Gmail:
                keyring set "OmniNexus_IMAP:imap.gmail.com" "myemail@gmail.com"
        
4.  Enter Password/Token: The command will securely prompt you to enter the password.
    *   Gmail/Google Workspace: You must use a 16-character App Password. Generate one via your Google Account security settings (requires 2-Step Verification). Do NOT use your main Google account password.
    *   Other Providers: Use your regular email password or an equivalent app-specific password/token if provided by your email service.

OmniNexus will automatically use this stored credential when the connector's connect() method is called. If the credential is not found in the keyring, the connection will fail with an informative error message.

## Data Item Output

A3sh, [5/5/2025 3:07 PM]
When query_data is called, this connector returns a list of Data Items for the fetched emails:

*   `item_id`: Unique UUID for this fetch.
*   `connector_id`: ID of this connector instance (e.g., my_work_email).
*   `source_uri`: IMAP URI including UID, e.g., imap://user@server/INBOX;UID=12345.
*   `retrieved_at`: ISO 8601 timestamp of fetch.
*   `metadata`:
    *   type: message/rfc822.
    *   uid: IMAP Unique ID of the email.
    *   mailbox: Name of the mailbox it was fetched from.
    *   message_id: RFC standard Message-ID header value.
*   `payload`:
    *   subject: Decoded Subject header.
    *   from: Decoded From header.
    *   to: Decoded To header.
    *   cc: Decoded Cc header.
    *   date_str: Date header as a string.
    *   content: The extracted plain text body (body_text) if found, otherwise falls back to the subject. This is the primary field for text agents.
    *   body_text: The extracted plain text body (may be None if not found or decoding failed).

## Usage Example (CLI)

1.  Store Password in Keyring (Manual Step):
        # Example for Gmail App Password
    keyring set "OmniNexus_IMAP:imap.gmail.com" "myname@gmail.com"
    # (Enter the 16-character App Password when prompted)
    
2.  Add Connector in OmniNexus:
    
    OmniNexus> add_connector
    Enter connector type...: imap
    Enter value for 'server'...: imap.gmail.com
    Enter value for 'port'...: 993
    Enter value for 'username'...: myname@gmail.com
    Enter value for 'mailbox'...: INBOX (or press Enter for default)
    # ... configure other options ...
    Enter a unique ID...: gmail_inbox
    # (Note the IMPORTANT message about keyring)
    
3.  (Auto) Activate & Run Agent:
    
    OmniNexus> run_keyword_extractor gmail_inbox
    
    *(OmniNexus will retrieve the password from keyring, connect, fetch emails, and run the agent on the body/subject content.)*

## Notes

*   The connector attempts to select the mailbox in read-only mode first to avoid accidentally changing flags (like 'Seen').
*   Email body parsing currently extracts only the text/plain part. HTML parts and attachments are ignored.
*   Decoding of email bodies and headers attempts common charsets but might fail for unusual encodings. Warnings will be printed if decoding errors occur.
*   Error handling for IMAP operations (connection, login, fetch) is included, and the connector will attempt to disconnect cleanly if errors occur during query_data.