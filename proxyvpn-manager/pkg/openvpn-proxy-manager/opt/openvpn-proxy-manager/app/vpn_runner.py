import os
import stat
import tempfile
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
        self.proxy_creds_path = None
        self.up_script_path = None
        self.down_script_path = None
        self._original_gateway = "192.168.1.1"
        self._original_dns = "8.8.8.8"

        self._state = "Disconnected"

    def _get_default_gateway(self) -> str:
        """Parsea 'ip route' y retorna el gateway actual antes de conectar."""
        try:
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if line.startswith("default"):
                    parts = line.split()
                    if "via" in parts:
                        via_idx = parts.index("via")
                        return parts[via_idx + 1]
        except Exception as e:
            self.log_updated.emit(f"Error detectando gateway: {e}")
        return "192.168.1.1"  # fallback real

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

    def _check_openssl_legacy(self):
        """Verifica que el provider legacy de OpenSSL esté activo."""
        try:
            with open('/etc/ssl/openssl.cnf', 'r') as f:
                content = f.read()
                if '[legacy_sect]' in content:
                    section = content.split('[legacy_sect]')[1].split('[')[0]
                    if 'activate = 1' not in section and 'activate=1' not in section:
                        self.log_updated.emit("ADVERTENCIA: proxy NTLM requiere OpenSSL legacy provider activo. Ver /etc/ssl/openssl.cnf sección [legacy_sect]")
                else:
                    self.log_updated.emit("ADVERTENCIA: proxy NTLM requiere OpenSSL legacy provider activo. Ver /etc/ssl/openssl.cnf sección [legacy_sect]")
        except Exception as e:
            self.log_updated.emit(f"ADVERTENCIA: No se pudo verificar /etc/ssl/openssl.cnf: {e}")

    def set_state(self, new_state: str):
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(self._state)

    def _write_secure_temp_file(self, content: str) -> str:
        fd, path = tempfile.mkstemp(prefix="pvpn_", text=True)
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR) # 600
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path

    def connect_vpn(self, profile: dict):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_updated.emit("Error: VPN is already running.")
            return

        self.set_state("Connecting")
        self.log_updated.emit("Starting VPN connection process...")

        self._original_gateway = self._get_default_gateway()
        self._original_dns = self._get_current_dns()
        
        self.log_updated.emit(f"Detected fallback gateway: {self._original_gateway} / DNS: {self._original_dns}")

        # Create temporary credential files
        vpn_creds = profile.get('vpn_username', '') + "\n" + profile.get('vpn_password', '') + "\n"
        self.vpn_creds_path = self._write_secure_temp_file(vpn_creds)
        
        args = [
            "openvpn",
            "--config", profile.get("config_path", ""),
            "--auth-user-pass", self.vpn_creds_path,
            "--script-security", "2",
            "--setenv", "OPENSSL_CONF", "/etc/ssl/openssl.cnf",
        ]

        # DNS scripts
        dns_ip = profile.get("vpn_dns", "").strip()
        if not dns_ip:
            self.log_updated.emit(
                "ADVERTENCIA: DNS VPN no configurado. "
                "Usando 10.98.0.1 por defecto. "
                "Edita el perfil para configurarlo manualmente."
            )
            dns_ip = "10.98.0.1"

        # Crear scripts temporales para up/down
        up_script_content = "#!/bin/sh\necho nameserver " + dns_ip + " > /etc/resolv.conf\n"
        down_script_content = "#!/bin/sh\necho nameserver " + self._original_dns + " > /etc/resolv.conf\n"
        
        self.up_script_path = self._write_secure_temp_file(up_script_content)
        self.down_script_path = self._write_secure_temp_file(down_script_content)
        
        # Hacer los scripts ejecutables
        os.chmod(self.up_script_path, 0o755)
        os.chmod(self.down_script_path, 0o755)
        
        args.extend([
            "--up-restart",
            "--up", self.up_script_path,
            "--down", self.down_script_path
        ])

        # Proxy settings
        if profile.get("use_proxy", False):
            proxy_auth = profile.get("proxy_auth", "ntlm")
            if proxy_auth == "ntlm":
                self._check_openssl_legacy()
                
            proxy_creds = profile.get('proxy_username', '') + "\n" + profile.get('proxy_password', '') + "\n"
            self.proxy_creds_path = self._write_secure_temp_file(proxy_creds)
            args.extend([
                "--http-proxy", profile.get("proxy_host", "10.0.0.1"), str(profile.get("proxy_port", "8080")), self.proxy_creds_path, proxy_auth
            ])

        self.log_updated.emit(f"Running: sudo {' '.join(args)}")
        self.process.start("sudo", args)

    def disconnect_vpn(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.log_updated.emit("Sending SIGTERM to openvpn...")
            os.system("sudo killall -SIGTERM openvpn")
            self.process.waitForFinished(5000)
            if self.process.state() != QProcess.ProcessState.NotRunning:
                self.log_updated.emit("Force killing openvpn...")
                os.system("sudo killall -SIGKILL openvpn")
                self.process.kill()

        self._cleanup_temp_files()
        self.set_state("Disconnected")

    def _cleanup_temp_files(self):
        for path in [self.vpn_creds_path, self.proxy_creds_path,
                     self.up_script_path, self.down_script_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        self.vpn_creds_path = None
        self.proxy_creds_path = None
        self.up_script_path = None
        self.down_script_path = None

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
        self._cleanup_temp_files()
        if exitStatus == QProcess.ExitStatus.CrashExit:
            self.log_updated.emit("VPN Process crashed.")
            self.set_state("Error")
        else:
            self.log_updated.emit(f"VPN Process exited with code {exitCode}.")
            self.set_state("Disconnected")

    def _handle_error(self, err):
        self.log_updated.emit(f"Process error: {err}")
        self._cleanup_temp_files()
        self.set_state("Error")
