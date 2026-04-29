import json
import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ProfileStorage:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "proxyvpn-manager"
        self.profiles_file = self.config_dir / "profiles.json"
        self.key_file = self.config_dir / ".key"
        self._ensure_config_dir()
        self.fernet = self._init_crypto()

    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Ensure secure permissions for the config directory
        os.chmod(self.config_dir, 0o700)

    def _init_crypto(self):
        """Initializes the encryption key or generates a new one if it doesn't exist."""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)
        else:
            with open(self.key_file, "rb") as f:
                key = f.read()
        return Fernet(key)

    def encrypt_password(self, password: str) -> str:
        if not password:
            return ""
        return self.fernet.encrypt(password.encode()).decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        if not encrypted_password:
            return ""
        try:
            return self.fernet.decrypt(encrypted_password.encode()).decode()
        except Exception:
            return ""

    def load_profiles(self) -> dict:
        """Loads profiles from JSON, decrypts passwords on the fly."""
        if not self.profiles_file.exists():
            return {}
        try:
            with open(self.profiles_file, "r") as f:
                data = json.load(f)
                # Decrypt passwords
                for profile_id, profile in data.items():
                    if "vpn_password" in profile:
                        profile["vpn_password"] = self.decrypt_password(profile["vpn_password"])
                    if "proxy_password" in profile:
                        profile["proxy_password"] = self.decrypt_password(profile["proxy_password"])
                return data
        except Exception as e:
            print(f"Error loading profiles: {e}")
            return {}

    def save_profiles(self, profiles: dict):
        """Encrypts passwords and saves profiles to JSON."""
        save_data = {}
        for profile_id, profile in profiles.items():
            save_profile = profile.copy()
            if "vpn_password" in save_profile:
                save_profile["vpn_password"] = self.encrypt_password(save_profile.get("vpn_password", ""))
            if "proxy_password" in save_profile:
                save_profile["proxy_password"] = self.encrypt_password(save_profile.get("proxy_password", ""))
            save_data[profile_id] = save_profile

        with open(self.profiles_file, "w") as f:
            json.dump(save_data, f, indent=4)
        os.chmod(self.profiles_file, 0o600)

