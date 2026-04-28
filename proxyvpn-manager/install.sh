#!/usr/bin/env bash
set -e

echo "==> Instalando dependencias..."
sudo pacman -S --needed --noconfirm python-pyqt6 python-cryptography openvpn

echo "==> Creando directorios de configuración..."
mkdir -p "$HOME/.config/proxyvpn-manager"
chmod 700 "$HOME/.config/proxyvpn-manager"

echo "==> Configurando sudoers para openvpn sin password..."
SUDOERS_FILE="/etc/sudoers.d/proxyvpn-manager"
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/openvpn, /usr/bin/killall" | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 440 "$SUDOERS_FILE"
sudo visudo -c -f "$SUDOERS_FILE" && echo "Sudoers OK" || (sudo rm "$SUDOERS_FILE" && echo "ERROR en sudoers, revertido")

echo "==> Instalando .desktop file..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > "$DESKTOP_DIR/proxyvpn-manager.desktop" << DESKTOP
[Desktop Entry]
Name=ProxyVPN Manager
Comment=Gestiona conexiones OpenVPN con proxy institucional
Exec=bash -c "cd $SCRIPT_DIR && python main.py"
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Network;VPN;
Keywords=vpn;proxy;openvpn;protonvpn;
StartupNotify=false
DESKTOP

chmod +x "$DESKTOP_DIR/proxyvpn-manager.desktop"

echo "==> Actualizando base de datos de aplicaciones..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "✓ Instalación completa."
echo "  Puedes lanzar la app desde el menú de inicio o con:"
echo "  cd $SCRIPT_DIR && python main.py"
