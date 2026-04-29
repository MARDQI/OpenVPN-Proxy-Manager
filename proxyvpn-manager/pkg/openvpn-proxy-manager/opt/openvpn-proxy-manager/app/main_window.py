import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QTextEdit, 
                             QMessageBox, QDialog, QLineEdit, QCheckBox, 
                             QSpinBox, QComboBox, QFormLayout, QFileDialog, 
                             QFrame, QDialogButtonBox, QListWidgetItem, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from app.storage import ProfileStorage
from app.profile_manager import ProfileManager
from app.vpn_runner import VPNRunner
from app.styles import get_stylesheet, YELLOW, TEXT_DIM, RED, GREEN

class ProfileDialog(QDialog):
    def __init__(self, parent=None, profile_data=None):
        super().__init__(parent)
        self.setWindowTitle("Perfil VPN")
        self.setMinimumWidth(400)
        self.profile_data = profile_data or {}
        self.setup_ui()
        self.populate_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        form_layout.addRow("Nombre:", self.name_input)
        
        self.config_path_input = QLineEdit()
        btn_browse = QPushButton("Buscar")
        btn_browse.clicked.connect(self._browse_file)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.config_path_input)
        path_layout.addWidget(btn_browse)
        form_layout.addRow("Archivo .ovpn:", path_layout)
        
        self.vpn_user_input = QLineEdit()
        form_layout.addRow("Usuario VPN:", self.vpn_user_input)
        
        self.vpn_pass_input = QLineEdit()
        self.vpn_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        # Mostrar/Ocultar
        btn_toggle_pass = QPushButton("👁")
        btn_toggle_pass.setFixedWidth(30)
        btn_toggle_pass.clicked.connect(lambda: self.vpn_pass_input.setEchoMode(
            QLineEdit.EchoMode.Normal if self.vpn_pass_input.echoMode() == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        ))
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(self.vpn_pass_input)
        pass_layout.addWidget(btn_toggle_pass)
        form_layout.addRow("Contraseña VPN:", pass_layout)

        self.vpn_dns_input = QLineEdit()
        self.vpn_dns_input.setPlaceholderText("Se detecta automáticamente")
        form_layout.addRow("DNS VPN:", self.vpn_dns_input)
        
        layout.addLayout(form_layout)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)
        
        self.proxy_check = QCheckBox("Usar proxy institucional")
        self.proxy_check.toggled.connect(self._toggle_proxy)
        layout.addWidget(self.proxy_check)
        
        # Proxy Section
        self.proxy_container = QWidget()
        proxy_layout = QFormLayout(self.proxy_container)
        
        self.proxy_host_input = QLineEdit("10.0.0.1")
        proxy_layout.addRow("Host proxy:", self.proxy_host_input)
        
        self.proxy_port_input = QSpinBox()
        self.proxy_port_input.setRange(1, 65535)
        self.proxy_port_input.setValue(8080)
        proxy_layout.addRow("Puerto proxy:", self.proxy_port_input)
        
        self.proxy_auth_input = QComboBox()
        self.proxy_auth_input.addItems(["ntlm", "basic"])
        proxy_layout.addRow("Autenticación:", self.proxy_auth_input)
        
        self.proxy_user_input = QLineEdit()
        proxy_layout.addRow("Usuario proxy:", self.proxy_user_input)
        
        self.proxy_pass_input = QLineEdit()
        self.proxy_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        proxy_layout.addRow("Contraseña proxy:", self.proxy_pass_input)
        
        layout.addWidget(self.proxy_container)
        self.proxy_container.setVisible(False)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar configuración OpenVPN", "", "OpenVPN Files (*.ovpn)")
        if path:
            self.config_path_input.setText(path)

    def _toggle_proxy(self, checked):
        self.proxy_container.setVisible(checked)
        self.adjustSize()

    def populate_data(self):
        if not self.profile_data: return
        self.name_input.setText(self.profile_data.get("name", ""))
        self.config_path_input.setText(self.profile_data.get("config_path", ""))
        self.vpn_user_input.setText(self.profile_data.get("vpn_username", ""))
        self.vpn_pass_input.setText(self.profile_data.get("vpn_password", ""))
        self.vpn_dns_input.setText(self.profile_data.get("vpn_dns", ""))
        
        use_proxy = self.profile_data.get("use_proxy", False)
        self.proxy_check.setChecked(use_proxy)
        self.proxy_host_input.setText(self.profile_data.get("proxy_host", "10.0.0.1"))
        self.proxy_port_input.setValue(int(self.profile_data.get("proxy_port", 8080)))
        auth = self.profile_data.get("proxy_auth", "ntlm")
        self.proxy_auth_input.setCurrentText(auth if auth in ["ntlm", "basic"] else "ntlm")
        self.proxy_user_input.setText(self.profile_data.get("proxy_username", ""))
        self.proxy_pass_input.setText(self.profile_data.get("proxy_password", ""))
        
        self._toggle_proxy(use_proxy)

    def get_data(self) -> dict:
        data = self.profile_data.copy()
        data["name"] = self.name_input.text().strip()
        data["config_path"] = self.config_path_input.text().strip()
        data["vpn_username"] = self.vpn_user_input.text().strip()
        data["vpn_password"] = self.vpn_pass_input.text().strip()
        data["vpn_dns"] = self.vpn_dns_input.text().strip()
        data["use_proxy"] = self.proxy_check.isChecked()
        data["proxy_host"] = self.proxy_host_input.text().strip()
        data["proxy_port"] = self.proxy_port_input.value()
        data["proxy_auth"] = self.proxy_auth_input.currentText()
        data["proxy_username"] = self.proxy_user_input.text().strip()
        data["proxy_password"] = self.proxy_pass_input.text().strip()
        return data

class MainWindow(QMainWindow):
    profiles_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProxyVPN Manager")
        self.setMinimumSize(500, 700)
        self.setStyleSheet(get_stylesheet())
        
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        
        self.storage = ProfileStorage()
        self.profile_manager = ProfileManager(self.storage)
        self.vpn_runner = VPNRunner()
        
        self.active_profile_id = None
        self._blink_state = False
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_blink)
        
        self.setup_ui()
        self.connect_signals()
        self.load_profiles_list()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Profile List
        self.list_profiles = QListWidget()
        self.list_profiles.setFixedHeight(180)
        self.list_profiles.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_profiles.itemSelectionChanged.connect(self._on_profile_selected)
        main_layout.addWidget(self.list_profiles)
        
        # Profile Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("+ Agregar")
        self.btn_edit = QPushButton("✎ Editar")
        self.btn_delete = QPushButton("🗑 Eliminar")
        self.btn_edit.setEnabled(False)
        self.btn_delete.setEnabled(False)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        main_layout.addLayout(btn_layout)
        
        # Status Card
        card_frame = QFrame()
        card_frame.setObjectName("card")
        card_layout = QVBoxLayout(card_frame)
        
        status_layout = QHBoxLayout()
        self.label_profile_name = QLabel("Perfil: Ninguno")
        self.label_status_dot = QLabel("●")
        self.label_status_dot.setObjectName("label_status")
        self.label_status_text = QLabel("Desconectado")
        self.label_status_text.setObjectName("label_status")
        
        self._update_status_ui("Disconnected")
        
        status_layout.addWidget(self.label_profile_name)
        status_layout.addStretch()
        status_layout.addWidget(self.label_status_dot)
        status_layout.addWidget(self.label_status_text)
        card_layout.addLayout(status_layout)
        
        self.btn_connect = QPushButton("CONECTAR")
        self.btn_connect.setObjectName("btn_connect")
        self.btn_connect.setProperty("state", "disconnected")
        card_layout.addWidget(self.btn_connect)

        self.btn_cancel = QPushButton("CANCELAR")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setStyleSheet(
            "QPushButton { background-color: #e0af68; color: #1a1b2e; font-weight: bold; border-radius: 8px; padding: 8px 16px; }"
        )
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        card_layout.addWidget(self.btn_cancel)
        
        main_layout.addWidget(card_frame)
        
        # Log
        main_layout.addWidget(QLabel("Log:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(200)
        main_layout.addWidget(self.log_view)

    def connect_signals(self):
        self.vpn_runner.state_changed.connect(self._on_state_changed)
        self.vpn_runner.log_updated.connect(self._append_log)
        self.vpn_runner.dns_detected.connect(self._on_dns_detected)
        
        self.btn_add.clicked.connect(lambda: self._open_profile_dialog())
        self.btn_edit.clicked.connect(lambda: self._open_profile_dialog(self._get_selected_profile_id()))
        self.btn_delete.clicked.connect(self._delete_profile)
        self.btn_connect.clicked.connect(self._on_connect_clicked)

    def load_profiles_list(self):
        self.list_profiles.clear()
        profiles = self.profile_manager.get_all()
        for pid, pdata in profiles.items():
            item = QListWidgetItem(pdata.get("name", "Sin nombre"))
            item.setData(Qt.ItemDataRole.UserRole, pid)
            self.list_profiles.addItem(item)
            
        self._on_profile_selected()
        self.profiles_changed.emit(self.profile_manager.get_all())

    def _get_selected_profile_id(self):
        items = self.list_profiles.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def _on_profile_selected(self):
        selected_id = self._get_selected_profile_id()
        has_selection = selected_id is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        if has_selection:
            pdata = self.profile_manager.get(selected_id)
            self.label_profile_name.setText("Perfil: " + pdata.get("name", ""))
        else:
            self.label_profile_name.setText("Perfil: Ninguno")

    def _open_profile_dialog(self, profile_id=None):
        pdata = self.profile_manager.get(profile_id) if profile_id else None
        dlg = ProfileDialog(self, pdata)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_data = dlg.get_data()
            if profile_id:
                self.profile_manager.update(profile_id, new_data)
            else:
                self.profile_manager.add(new_data)
            self.load_profiles_list()

    def _delete_profile(self):
        pid = self._get_selected_profile_id()
        if not pid: return
        pdata = self.profile_manager.get(pid)
        rep = QMessageBox.question(self, "Eliminar", "¿Eliminar perfil '" + pdata.get("name", "") + "'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete(pid)
            self.load_profiles_list()

    def _on_state_changed(self, state: str):
        self._update_status_ui(state)
        
        if state in ["Disconnected", "Error"]:
            self.btn_connect.setVisible(True)
            self.btn_cancel.setVisible(False)
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("CONECTAR")
            self.btn_connect.setProperty("state", "disconnected")
            self.blink_timer.stop()
            self.list_profiles.setEnabled(True)
        elif state == "Connecting":
            self.btn_connect.setVisible(False)
            self.btn_cancel.setVisible(True)
            self.btn_connect.setText("CONECTANDO...")
            self.btn_connect.setProperty("state", "connecting")
            self.btn_connect.setEnabled(False)
            self.blink_timer.start(600)
            self.list_profiles.setEnabled(False)
        elif state == "Connected":
            self.btn_connect.setVisible(True)
            self.btn_cancel.setVisible(False)
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("DESCONECTAR")
            self.btn_connect.setProperty("state", "connected")
            self.blink_timer.stop()
            self.list_profiles.setEnabled(False)
            
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)

    def _on_cancel_clicked(self):
        self.vpn_runner.disconnect_vpn()
        self.btn_cancel.setVisible(False)
        self.btn_connect.setVisible(True)

    def _update_status_ui(self, state: str, blink_color=None):
        self.label_status_text.setText(state)
        if blink_color:
            color = blink_color
        else:
            if state == "Connected": color = GREEN
            elif state == "Connecting": color = YELLOW
            elif state == "Error": color = RED
            else: color = TEXT_DIM
            
        self.label_status_dot.setStyleSheet("color: " + color + ";")

    def _toggle_blink(self):
        self._blink_state = not self._blink_state
        color = YELLOW if self._blink_state else TEXT_DIM
        self._update_status_ui("Connecting", color)

    def _on_connect_clicked(self):
        state = self.btn_connect.property("state")
        if state == "connected":
            self.vpn_runner.disconnect_vpn()
        elif state in ["disconnected", "error"]:
            pid = self._get_selected_profile_id()
            if not pid:
                QMessageBox.warning(self, "Atención", "Selecciona un perfil primero.")
                return
                
            pdata = self.profile_manager.get(pid)
            errors = self.profile_manager.validate_profile(pdata)
            if errors:
                err_msg = "\n".join("- " + e for e in errors)
                QMessageBox.critical(self, "Perfil Inválido", "Corrige los siguientes errores:\n\n" + err_msg)
                return
                
            self.active_profile_id = pid
            self.log_view.clear()
            self._append_log("Conectando con perfil: " + pdata.get('name', ''))
            self.vpn_runner.connect_vpn(pdata)

    def _on_dns_detected(self, dns: str):
        if self.active_profile_id:
            self.profile_manager.update_dns(self.active_profile_id, dns)

    def _append_log(self, text: str):
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] {text}") # Imprimir por consola
        color = TEXT_DIM
        if "ERROR" in text:
            color = RED
        elif "ADVERTENCIA" in text:
            color = YELLOW
        elif "Initialization Sequence Completed" in text:
            color = GREEN
            
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)
        self.log_view.insertHtml(
            "<span style='color: " + color + "'>[" + time_str + "] " 
            + text.replace("<", "&lt;").replace(">", "&gt;") 
            + "</span><br>"
        )
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )
