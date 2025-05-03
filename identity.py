# OmniNexus - identity.py
# Basic identity management - Generates/loads a password-protected local key pair.

import os
import json
import getpass # For securely prompting for password
import traceback
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes # Needed for PBE

# Configuration
KEY_FILE = "local_identity.json"
KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537

# Global variable to hold the loaded identity (simplification for PoC)
_local_identity = None

def prompt_for_password(confirm=False):
    """Securely prompts the user for a password."""
    while True:
        try:
            password = getpass.getpass("Enter password for identity key: ")
            if not password:
                print("Password cannot be empty. Please try again.")
                continue
            if confirm:
                password_confirm = getpass.getpass("Confirm password: ")
                if password == password_confirm:
                    return password.encode('utf-8') # Return bytes
                else:
                    print("Passwords do not match. Please try again.")
            else:
                 return password.encode('utf-8') # Return bytes
        except EOFError:
             print("\nPassword input cancelled.")
             return None
        except Exception as e:
            print(f"\nError reading password: {e}")
            return None

def generate_new_keys():
    """Generates a new RSA private/public key pair."""
    print("Generating new identity keys...")
    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=KEY_SIZE,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def serialize_keys(private_key, public_key, password_bytes):
    """Serializes keys into PEM format strings, encrypting the private key."""
    if not password_bytes:
         # Fallback to no encryption if password prompt somehow failed/cancelled
         # Consider raising an error instead for stricter security
         print("Warning: No password provided, saving private key UNENCRYPTED (INSECURE).")
         private_encryption_algorithm = serialization.NoEncryption()
    else:
         private_encryption_algorithm = serialization.BestAvailableEncryption(password_bytes)

    try:
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=private_encryption_algorithm
        )
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # Decode to strings for JSON storage
        return pem_private.decode('utf-8'), pem_public.decode('utf-8')
    except Exception as e:
        print(f"Error during key serialization: {e}")
        traceback.print_exc()
        return None, None


def deserialize_keys(pem_private_str, pem_public_str, password_bytes):
    """Deserializes keys from PEM format strings, decrypting private key."""
    try:
        private_key = serialization.load_pem_private_key(
            pem_private_str.encode('utf-8'),
            password=password_bytes, # Can be None if key wasn't encrypted
            backend=default_backend()
        )
        public_key = serialization.load_pem_public_key(
            pem_public_str.encode('utf-8'),
            backend=default_backend()
        )
        return private_key, public_key
    except TypeError as e:
        # Often indicates incorrect password (or trying password on unencrypted key)
        if "private key is encrypted" in str(e).lower() and password_bytes is None:
             print("Error: Private key is encrypted, but no password was provided.")
        elif "password was incorrect" in str(e).lower():
             print("Error: Incorrect password provided for private key.")
        else:
             print(f"Error deserializing private key (TypeError): {e}")
        return None, None
    except ValueError as e:
        # Often indicates key is *not* encrypted but password was provided,
        # or general format issues.
         if "private key is not encrypted" in str(e).lower() and password_bytes is not None:
              print("Warning: Password provided, but private key is not encrypted.")
              # Attempt to load without password
              try:
                   private_key = serialization.load_pem_private_key(
                       pem_private_str.encode('utf-8'),
                       password=None, # Try without password
                       backend=default_backend()
                   )
                   public_key = serialization.load_pem_public_key(
                       pem_public_str.encode('utf-8'),
                       backend=default_backend()
                   )
                   return private_key, public_key
              except Exception as inner_e:
                   print(f"Failed to load unencrypted key after password mismatch: {inner_e}")
                   return None, None
         else:
              print(f"Error deserializing key (ValueError): {e}")
         return None, None
    except Exception as e:
        print(f"Unexpected error during key deserialization: {e}")
        traceback.print_exc()
        return None, None


def save_identity_to_file(pem_private_str, pem_public_str, filename=KEY_FILE):
    """Saves the PEM strings to a JSON file."""
    identity_data = {
        "private_key_pem": pem_private_str,
        "public_key_pem": pem_public_str
    }
    try:
        with open(filename, 'w') as f:
            json.dump(identity_data, f, indent=4)
        print(f"Identity saved to {filename}")
        # Set restrictive permissions (works on Linux/macOS, ignored on Windows)
        try:
            os.chmod(filename, 0o600) # Read/write only for owner
            print(f"Set permissions for {filename} to 600.")
        except OSError:
             print(f"Could not set restrictive permissions for {filename} (may not be supported on this OS).")
        except Exception as e:
             print(f"An unexpected error occurred setting file permissions: {e}")

    except IOError as e:
        print(f"Error saving identity file: {e}")

def load_identity_from_file(filename=KEY_FILE):
    """
    Loads the identity (keys) from a JSON file.
    Prompts for password if the key appears encrypted.
    """
    global _local_identity
    if not os.path.exists(filename):
        return None # No identity file found

    try:
        with open(filename, 'r') as f:
            identity_data = json.load(f)

        pem_private_str = identity_data.get("private_key_pem")
        pem_public_str = identity_data.get("public_key_pem")

        if not pem_private_str or not pem_public_str:
            print(f"Error: Missing key data in {filename}")
            return None

        # Prompt for password - attempt decryption
        print(f"Loading identity from {filename}...")
        password_bytes = prompt_for_password(confirm=False)
        if password_bytes is None:
             print("Password entry cancelled. Cannot load identity.")
             return None # User cancelled password entry

        private_key, public_key = deserialize_keys(pem_private_str, pem_public_str, password_bytes)

        if private_key and public_key:
            _local_identity = {
                "private_key": private_key,
                "public_key": public_key,
                "public_key_pem": pem_public_str
            }
            print(f"Identity loaded and decrypted successfully.")
            return _local_identity
        else:
            # Error message already printed by deserialize_keys
            print("Failed to load identity.")
            return None

    except (IOError, json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Error loading or parsing identity file {filename}: {e}")
        return None # Return None if loading fails


def get_or_create_identity():
    """
    Loads identity from file if it exists (prompting for password),
    otherwise generates a new one (prompting for new password) and saves it.
    Returns the identity dictionary or None on failure/cancellation.
    """
    global _local_identity
    if _local_identity:
        return _local_identity

    if os.path.exists(KEY_FILE):
        # Attempt to load existing identity
        loaded_identity = load_identity_from_file(KEY_FILE)
        if loaded_identity:
            return loaded_identity
        else:
             print("Failed to load existing identity. Check password or file integrity.")
             # Optionally, offer to delete/recreate here, but for now just fail.
             return None # Failed to load
    else:
        # Create new identity
        print(f"No existing identity found at {KEY_FILE}. Creating a new one.")
        password_bytes = prompt_for_password(confirm=True)
        if password_bytes is None:
            print("Password entry cancelled. Cannot create identity.")
            return None # User cancelled password entry

        private_key, public_key = generate_new_keys()
        pem_private_str, pem_public_str = serialize_keys(private_key, public_key, password_bytes)

        if pem_private_str and pem_public_str:
            save_identity_to_file(pem_private_str, pem_public_str, KEY_FILE)
            # Need to reload to set global state correctly and ensure decryption works
            print("Attempting to reload newly created identity...")
            # We need the password again to reload immediately
            # In a real app, might store password temporarily or handle differently
            _local_identity = None # Clear global state before reload attempt
            reloaded_identity = load_identity_from_file(KEY_FILE)
            if reloaded_identity:
                 return reloaded_identity
            else:
                 print("Critical Error: Failed to reload the newly created identity!")
                 return None
        else:
             print("Error during key serialization. Identity not saved.")
             return None


def get_public_key_pem():
    """Returns the PEM formatted public key string of the current identity."""
    # Ensures identity is loaded/created before trying to access it
    identity_obj = get_or_create_identity()
    if identity_obj:
        # Check if it was loaded successfully, might have failed password
        if _local_identity:
             return _local_identity.get("public_key_pem")
        else:
             # Handle case where get_or_create_identity returned None previously
             print("Error: Identity could not be loaded or created.")
             return None
    else:
         # Handle case where get_or_create_identity failed and returned None now
         print("Error: Identity could not be loaded or created.")
         return None


# Example of how to use it (will be called from main.py later)
if __name__ == "__main__":
    # This block runs only when the script is executed directly
    print("Running identity module directly for testing...")

    # Ensure no old key file exists for a clean test
    if os.path.exists(KEY_FILE):
        print(f"Deleting existing key file '{KEY_FILE}' for fresh test...")
        try:
            os.remove(KEY_FILE)
        except OSError as e:
            print(f"Error deleting file: {e}")
            # Decide if you want to exit or continue
            # exit(1) # Exit if deletion fails and you need a clean state

    print("\nAttempting to get or create identity (will prompt for password):")
    my_identity = get_or_create_identity() # First run should create

    if my_identity:
        print("\nIdentity created/loaded successfully.")
        print("\nPublic Key (PEM Format):")
        print(get_public_key_pem())

        # Test loading again (should prompt for password)
        print("\nAttempting to load the identity again (clearing memory first):")
        _local_identity = None # Simulate app restart
        my_identity_reloaded = get_or_create_identity() # Should load existing

        if my_identity_reloaded:
             print("\nIdentity reloaded successfully.")
        else:
             print("\nFailed to reload identity (check password entered).")

    else:
        print("\nFailed to get or create identity (password entry might have been cancelled or failed).")