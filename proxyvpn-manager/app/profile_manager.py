import os
import uuid
from typing import Dict, Optional, List
from app.storage import ProfileStorage

class ProfileManager:
    def __init__(self, storage: ProfileStorage):
        self.storage = storage
        self.profiles = self.storage.load_profiles()

    def get_all(self) -> Dict[str, dict]:
        """Retorna todos los perfiles cargados en memoria."""
        return self.profiles

    def get(self, profile_id: str) -> Optional[dict]:
        """Retorna un perfil específico según su ID."""
        return self.profiles.get(profile_id)

    def add(self, profile_data: dict) -> str:
        """
        Aplica valores por defecto, genera un UUID (si no tiene),
        y añade el perfil. Retorna el ID asignado.
        """
        profile_id = profile_data.get("id")
        if not profile_id:
            profile_id = str(uuid.uuid4())
            profile_data["id"] = profile_id

        # Defaults requeridos
        profile_data.setdefault("vpn_dns", "")
        profile_data.setdefault("use_proxy", False)
        profile_data.setdefault("proxy_host", "10.0.0.1")
        profile_data.setdefault("proxy_port", 8080)
        profile_data.setdefault("proxy_auth", "ntlm")

        self.profiles[profile_id] = profile_data
        self.storage.save_profiles(self.profiles)
        
        return profile_id

    def update(self, profile_id: str, updated_data: dict) -> bool:
        """
        Actualiza los campos de un perfil mediante un merge con los datos
        existentes, protegiendo el ID. Retorna True si existía.
        """
        if profile_id not in self.profiles:
            return False

        # Prevenir alteración del ID
        filtered_data = {k: v for k, v in updated_data.items() if k != "id"}
        
        self.profiles[profile_id].update(filtered_data)
        self.storage.save_profiles(self.profiles)
        return True

    def delete(self, profile_id: str) -> bool:
        """Elimina el perfil especificado y retorna True en caso de éxito."""
        if profile_id in self.profiles:
            del self.profiles[profile_id]
            self.storage.save_profiles(self.profiles)
            return True
        return False

    def update_dns(self, profile_id: str, dns: str) -> None:
        """Shortcut para actualizar exclusivamente el campo de DNS vía el log runner."""
        if profile_id in self.profiles:
            self.profiles[profile_id]["vpn_dns"] = dns
            self.storage.save_profiles(self.profiles)

    def validate_profile(self, profile_data: dict) -> List[str]:
        """
        Valida los campos obligatorios del perfil y retorna 
        una lista de errores encontrados (lista vacía = perfil válido).
        """
        errors = []

        if not profile_data.get("name"):
            errors.append("El nombre del perfil no puede estar vacío.")

        config_path = profile_data.get("config_path", "").strip()
        if not config_path:
            errors.append("Debes seleccionar una configuración OpenVPN (.ovpn) para este perfil.")
        elif not os.path.exists(config_path):
            errors.append("El archivo .ovpn no existe: " + config_path)

        if not profile_data.get("vpn_username"):
            errors.append("El usuario de VPN no puede estar vacío.")

        return errors
