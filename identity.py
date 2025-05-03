# OmniNexus - identity.py
# Basic identity management for PoC - Generates/loads a simple local key pair.

import os
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Configuration (simple for now)
KEY_FILE = "local_identity.json"
KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537

# Global variable to hold the loaded identity (simplification for PoC)
_local_identity = None

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

def serialize_keys(private_key, public_key):
    """Serializes keys into PEM format strings."""
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()  # WARNING: Not password protected for PoC
    )
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Decode to strings for JSON storage
    return pem_private.decode('utf-8'), pem_public.decode('utf-8')

def deserialize_keys(pem_private_str, pem_public_str):
    """Deserializes keys from PEM format strings."""
    private_key = serialization.load_pem_private_key(
        pem_private_str.encode('utf-8'),
        password=None, # No password used in serialization
        backend=default_backend()
    )
    public_key = serialization.load_pem_public_key(
        pem_public_str.encode('utf-8'),
        backend=default_backend()
    )
    return private_key, public_key

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
    except IOError as e:
        print(f"Error saving identity file: {e}")

def load_identity_from_file(filename=KEY_FILE):
    """Loads the identity (keys) from a JSON file."""
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

        private_key, public_key = deserialize_keys(pem_private_str, pem_public_str)
        _local_identity = {
            "private_key": private_key,
            "public_key": public_key,
            "public_key_pem": pem_public_str # Keep PEM string for easy sharing/display
        }
        print(f"Identity loaded successfully from {filename}")
        return _local_identity
    except (IOError, json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"Error loading or parsing identity file {filename}: {e}")
        return None # Return None if loading fails

def get_or_create_identity():
    """
    Loads identity from file if it exists, otherwise generates a new one
    and saves it. Returns the identity dictionary.
    """
    global _local_identity
    if _local_identity:
        return _local_identity

    loaded_identity = load_identity_from_file(KEY_FILE)
    if loaded_identity:
        return loaded_identity
    else:
        print(f"No existing identity found at {KEY_FILE}. Creating a new one.")
        private_key, public_key = generate_new_keys()
        pem_private_str, pem_public_str = serialize_keys(private_key, public_key)
        save_identity_to_file(pem_private_str, pem_public_str, KEY_FILE)
        # Reload from file to ensure consistency and set global state
        return load_identity_from_file(KEY_FILE)

def get_public_key_pem():
    """Returns the PEM formatted public key string of the current identity."""
    identity = get_or_create_identity()
    if identity:
        return identity.get("public_key_pem")
    return None

# Example of how to use it (will be called from main.py later)
if __name__ == "__main__":
    # This block runs only when the script is executed directly
    print("Running identity module directly for testing...")
    my_identity = get_or_create_identity()

    if my_identity:
        print("\nIdentity Details:")
        # print("Private Key Object:", my_identity['private_key']) # Don't usually print private key object
        print("Public Key Object:", my_identity['public_key'])
        print("\nPublic Key (PEM Format):")
        print(get_public_key_pem())
    else:
        print("\nFailed to get or create identity.")