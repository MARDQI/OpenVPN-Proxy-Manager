import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app.main_window import MainWindow
from app.tray import SystemTray

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ProxyVPN Manager")
    app.setQuitOnLastWindowClosed(False)  # Mantener vivo en tray al cerrar ventana

    window = MainWindow()

    tray = SystemTray(app, window)
    tray.show()

    # Conectar señales del vpn_runner al tray
    window.vpn_runner.state_changed.connect(tray.update_state)

    # Conectar recarga de perfiles en tray cuando cambie la lista
    window.profiles_changed.connect(tray.refresh_profiles)

    # Carga inicial para el tray
    tray.refresh_profiles(window.profile_manager.get_all())

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
