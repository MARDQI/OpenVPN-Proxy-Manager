from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import Qt
from app.styles import TEXT_DIM, YELLOW, GREEN, RED

class SystemTray(QSystemTrayIcon):
    def __init__(self, app, main_window):
        super().__init__()
        self.app = app
        self.main_window = main_window
        
        self.setIcon(self._make_icon(TEXT_DIM))
        self.setToolTip("ProxyVPN Manager — Desconectado")
        
        self.menu = QMenu()
        self.setContextMenu(self.menu)
        self.menu.aboutToShow.connect(self._update_visibility_action)
        
        self.activated.connect(self._on_activated)
        self.refresh_profiles({})

    def _make_icon(self, color: str) -> QIcon:
        pixmap = QPixmap(22, 22)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 18, 18)
        painter.end()
        
        return QIcon(pixmap)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _update_visibility_action(self):
        if hasattr(self, '_toggle_action'):
            if self.main_window.isVisible() and not self.main_window.isMinimized():
                self._toggle_action.setText("Ocultar")
            else:
                self._toggle_action.setText("Mostrar")

    def _toggle_window(self):
        if self.main_window.isVisible() and not self.main_window.isMinimized():
            self.main_window.hide()
        else:
            self.main_window.showNormal()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def update_state(self, state: str):
        if state == "Connected":
            self.setIcon(self._make_icon(GREEN))
            self.setToolTip("ProxyVPN Manager — Conectado")
        elif state == "Connecting":
            self.setIcon(self._make_icon(YELLOW))
            self.setToolTip("ProxyVPN Manager — Conectando...")
        elif state == "Error":
            self.setIcon(self._make_icon(RED))
            self.setToolTip("ProxyVPN Manager — Error")
        else:
            self.setIcon(self._make_icon(TEXT_DIM))
            self.setToolTip("ProxyVPN Manager — Desconectado")

    def refresh_profiles(self, profiles: dict):
        self.menu.clear()
        
        title_action = QAction("ProxyVPN Manager", self.menu)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)
        self.menu.addSeparator()
        
        for pid, pdata in profiles.items():
            action = QAction(pdata.get("name", "Unknown"), self.menu)
            action.triggered.connect(lambda checked, _pid=pid: self._select_profile(_pid))
            self.menu.addAction(action)
            
        self.menu.addSeparator()
        
        self._toggle_action = QAction("Mostrar", self.menu)
        self._toggle_action.triggered.connect(self._toggle_window)
        self.menu.addAction(self._toggle_action)
        
        exit_action = QAction("Salir", self.menu)
        exit_action.triggered.connect(self._exit_app)
        self.menu.addAction(exit_action)

    def _select_profile(self, profile_id: str):
        self._show_window()
        # Find item in the list and select it
        list_widget = self.main_window.list_profiles
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == profile_id:
                list_widget.setCurrentItem(item)
                break

    def _show_window(self):
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def _exit_app(self):
        runner = self.main_window.vpn_runner
        if runner.process.state() != runner.process.ProcessState.NotRunning:
            reply = QMessageBox.question(
                None, "Salir",
                "La VPN está conectada.\\n¿Seguro que deseas desconectar y salir?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                runner.disconnect_vpn()
                self.app.quit()
        else:
            self.app.quit()
