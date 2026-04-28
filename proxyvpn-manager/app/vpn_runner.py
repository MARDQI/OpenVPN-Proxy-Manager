import os
import subprocess
import re
from PyQt6.QtCore import QObject, pyqtSignal, QProcess

class VPNRunner(QObject):
    # Signals
    state_changed = pyqtSignal(str) # "Disconnected", "Connecting", "Connected", "Error"
    log_updated = pyqtSignal(str)
    dns_detected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)
        self.process.errorOccurred.connect(self._handle_error)
        
        self.vpn_creds_path = None
        self._original_gateway = "192.168.1.1"
        self._original_dns = "8.8.8.8"

        self._state = "Disconnected"

    def _get_current_dns(self) -> str:
        """Lee el DNS actual desde /etc/resolv.conf antes de conectar."""
        try:
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('nameserver') and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1]
        except Exception:
            pass
        return self._original_gateway  # fallback al gateway si no encuentra DNS

    def set_state(self, new_state: str):
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(self._state)

    def _generate_script(self, profile: dict) -> str:
        from pathlib import Path
        import stat as stat_mod
        import tempfile

        config_dir = Path.home() / ".config" / "proxyvpn-manager"
        config_dir.mkdir(parents=True, exist_ok=True)

        script_path = config_dir / "connect.sh"
        proxy_creds_path = config_dir / "proxy.txt"

        dns_ip = profile.get("vpn_dns", "").strip() or "10.98.0.1"

        # Archivo temporal de credenciales VPN
        fd, vpn_creds_path = tempfile.mkstemp(prefix="pvpn_vpn_")
        os.chmod(vpn_creds_path, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(profile.get("vpn_username", "") + "\n")
            f.write(profile.get("vpn_password", "") + "\n")
        self.vpn_creds_path = vpn_creds_path

        lines = [
            "#!/bin/bash",
            'echo "[*] Conectando: ' + profile.get("name", "") + '"',
            "sudo openvpn \\",
            '  --config "' + profile.get("config_path", "") + '" \\',
            "  --auth-user-pass " + vpn_creds_path + " \\",
            "  --script-security 2 \\",
            "  --up-restart \\",
            "  --setenv OPENSSL_CONF /etc/ssl/openssl.cnf \\",
            "  --up \"/bin/sh -c 'echo nameserver " + dns_ip + " > /etc/resolv.conf'\" \\",
            "  --down \"/bin/sh -c 'echo nameserver " + self._original_dns + " > /etc/resolv.conf'\"",
        ]

        if profile.get("use_proxy", False):
            # Escribir credenciales proxy en archivo separado
            with open(proxy_creds_path, "w") as f:
                f.write(profile.get("proxy_username", "") + "\n")
                f.write(profile.get("proxy_password", "") + "\n")
            os.chmod(proxy_creds_path, 0o600)

            proxy_host = profile.get("proxy_host", "10.0.0.1")
            proxy_port = str(profile.get("proxy_port", 8080))
            proxy_auth = profile.get("proxy_auth", "ntlm")

            lines[-1] += " \\"
            lines.append(
                "  --http-proxy " + proxy_host + " " + proxy_port +
                " " + str(proxy_creds_path) + " " + proxy_auth
            )

        try:
            with open(script_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            os.chmod(script_path, 0o700)
            self.log_updated.emit("Script listo: " + str(script_path))
            return str(script_path)
        except Exception as e:
            self.log_updated.emit("ERROR generando script: " + str(e))
            return ""

    def connect_vpn(self, profile: dict):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_updated.emit("Error: VPN already running.")
            return

        self._original_dns = self._get_current_dns()
        
        script = self._generate_script(profile)
        if not script:
            self.set_state("Error")
            return

        self.set_state("Connecting")
        self.log_updated.emit("Ejecutando script: " + script)
        self.process.start("bash", [script])

    def disconnect_vpn(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_updated.emit("Sending SIGTERM to openvpn...")
            os.system("sudo killall -SIGTERM openvpn")
            self.process.waitForFinished(5000)
            if self.process.state() != QProcess.ProcessState.NotRunning:
                os.system("sudo killall -SIGKILL openvpn")
                self.process.kill()
        self._cleanup()
        # Restaurar DNS
        try:
            with open('/etc/resolv.conf', 'w') as f:
                f.write("nameserver " + self._original_dns + "\n")
        except Exception:
            pass
        self.set_state("Disconnected")

    def _cleanup(self):
        for path in [self.vpn_creds_path]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass
        self.vpn_creds_path = None

    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode(errors='replace')
        for line in data.splitlines():
            line = line.strip()
            if not line: continue
            self.log_updated.emit(line)
            
            # Detect success state
            if "Initialization Sequence Completed" in line:
                self.set_state("Connected")
            
            # Detect DNS configuration from PUSH_REPLY
            dns_match = re.search(r'dhcp-option\s+DNS\s+([\d.]+)', line)
            if dns_match:
                detected_dns = dns_match.group(1)
                self.log_updated.emit(f"DNS detectado automáticamente: {detected_dns}")
                self.dns_detected.emit(detected_dns)
            
            # Detect common errors
            if "AUTH_FAILED" in line:
                self.log_updated.emit("ERROR: VPN Authentication Failed!")
                self.set_state("Error")
            elif "HTTP proxy authenticate failed" in line:
                self.log_updated.emit("ERROR: Proxy Authentication Failed!")
                self.set_state("Error")
            elif "MD4" in line:
                self.log_updated.emit("ERROR: OpenSSL legacy provider no activo. Ejecuta: sudo nano /etc/ssl/openssl.cnf y activa [legacy_sect]")
                self.set_state("Error")
            elif "HTTP proxy returned: 'HTTP/1.1 407'" in line:
                self.log_updated.emit("ERROR: Credenciales del proxy incorrectas")
                self.set_state("Error")
            elif "TLS Error" in line:
                self.log_updated.emit("ERROR: Fallo en handshake TLS con el servidor VPN")
                self.set_state("Error")
            elif "RESOLVE: Cannot resolve host address" in line:
                self.log_updated.emit("ERROR: No se puede resolver el servidor VPN. Verifica tu conexión")
                self.set_state("Error")

    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode(errors='replace')
        for line in data.splitlines():
            line = line.strip()
            if not line: continue
            self.log_updated.emit(f"STDERR: {line}")

    def _handle_finished(self, exitCode, exitStatus):
        self._cleanup()
        if exitStatus == QProcess.ExitStatus.CrashExit:
            self.log_updated.emit("VPN Process crashed.")
            self.set_state("Error")
        else:
            self.log_updated.emit(f"VPN Process exited with code {exitCode}.")
            self.set_state("Disconnected")

    def _handle_error(self, err):
        self.log_updated.emit(f"Process error: {err}")
        self._cleanup()
        self.set_state("Error")
