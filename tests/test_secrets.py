import sys
import types
import pytest
from wisprfree_core import secrets

class FakeKeyring(types.ModuleType):
    def __init__(self):
        super().__init__("keyring")
        self.values = {}
    def get_password(self, service, account):
        return self.values.get((service, account))
    def set_password(self, service, account, value):
        self.values[(service, account)] = value
    def delete_password(self, service, account):
        del self.values[(service, account)]

def test_environment_is_ignored_unless_explicit(monkeypatch):
    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring())
    monkeypatch.setenv("GEMINI_API_KEY", "dev-key")
    assert secrets.get_api_key() is None
    assert secrets.get_api_key(allow_environment=True) == "dev-key"

def test_keychain_round_trip(monkeypatch):
    monkeypatch.setitem(sys.modules, "keyring", FakeKeyring())
    secrets.set_api_key("  sample-key  ")
    assert secrets.get_api_key() == "sample-key"
    secrets.delete_api_key()
    assert secrets.get_api_key() is None

def test_empty_key_rejected():
    with pytest.raises(ValueError):
        secrets.set_api_key("  ")
