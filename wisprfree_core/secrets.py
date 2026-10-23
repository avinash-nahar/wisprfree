"""Store user-provided API keys in macOS Keychain via keyring."""
import os
SERVICE_NAME = "WisprFree"
ACCOUNT_NAME = "gemini-api-key"
class SecretStoreError(RuntimeError):
    """Keychain could not be accessed."""
def get_api_key(*, allow_environment=False):
    if allow_environment:
        value = os.environ.get("GEMINI_API_KEY")
        if value and value.strip():
            return value.strip()
    try:
        import keyring
        value = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
    except Exception as exc:
        raise SecretStoreError("Unable to access macOS Keychain. Configure the API key in Settings.") from exc
    return value.strip() if isinstance(value, str) and value.strip() else None
def set_api_key(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("API key must not be empty")
    try:
        import keyring
        keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, value.strip())
    except Exception as exc:
        raise SecretStoreError("Unable to save the API key to macOS Keychain.") from exc
def delete_api_key():
    try:
        import keyring
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except Exception as exc:
        raise SecretStoreError("Unable to remove the API key from macOS Keychain.") from exc
