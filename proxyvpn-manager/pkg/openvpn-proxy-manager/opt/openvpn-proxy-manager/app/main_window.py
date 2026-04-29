import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QTextEdit, 
                             QMessageBox, QLineEdit, QCheckBox, QStackedWidget,
                             QSpinBox, QComboBox, QFormLayout, QFileDialog, 
                             QFrame, QListWidgetItem, QAbstractItemView, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QCursor
from app.storage import ProfileStorage
from app.profile_manager import ProfileManager
from app.vpn_runner import VPNRunner
from app.styles import get_stylesheet, YELLOW, TEXT_DIM, RED, GREEN, BG_CARD

class ProfileItemWidget(QWidget):
    def __init__(self, pid, name, parent_window, parent=None):
        super().__init__(parent)
        self.pid = pid
        self.parent_window = parent_window
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.lbl_name = QLabel(name)
        self.lbl_name.setStyleSheet("font-weight: bold; font-size: 15px;")
        
        self.btn_edit = QPushButton("✎")
        self.btn_edit.setObjectName("btn_icon")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.clicked.connect(self._on_edit)
        
        self.btn_del = QPushButton("🗑")
        self.btn_del.setObjectName("btn_icon")
        self.btn_del.setStyleSheet("color: #EF4444;")
        self.btn_del.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_del.clicked.connect(self._on_del)
        
        layout.addWidget(self.lbl_name)
        layout.addStretch()
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_del)

    def _on_edit(self):
        self.parent_window._action_edit_profile(self.pid)
        
    def _on_del(self):
        self.parent_window._delete_profile(self.pid)

class MainWindow(QMainWindow):
    profiles_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProxyVPN Manager")
        self.setMinimumSize(400, 750)
        self.setStyleSheet(get_stylesheet())
        
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        
        self.storage = ProfileStorage()
        self.profile_manager = ProfileManager(self.storage)
        self.vpn_runner = VPNRunner()
        
        self.active_profile_id = None
        self.editing_profile_id = None
        
        self._blink_state = False
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_blink)
        
        self.conn_time = 0
        self.conn_timer = QTimer(self)
        self.conn_timer.timeout.connect(self._update_time)
        
        self.assigned_ip = "---.---.---.---"
        
        self.setup_ui()
        self.connect_signals()
        self.load_profiles_list()
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        
    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        self._setup_page_dashboard()
        self._setup_page_logs()
        self._setup_page_profiles()
        self._setup_page_edit()
        
        self.stack.setCurrentIndex(0)
        
    def _setup_page_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel("🛡")
        icon_lbl.setStyleSheet("font-size: 24px; color: #3B82F6;")
        title_lbl = QLabel("ProxyVPN")
        title_lbl.setObjectName("label_title")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        
        btn_settings = QPushButton("⚙")
        btn_settings.setObjectName("btn_icon")
        btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        header.addWidget(btn_settings)
        layout.addLayout(header)
        
        # Connection Card
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        
        self.lbl_current_profile_title = QLabel("Perfil Actual")
        self.lbl_current_profile_title.setObjectName("label_dim")
        
        self.cb_profile = QComboBox()
        self.cb_profile.setStyleSheet("border: none; background-color: transparent; font-size: 16px; font-weight: bold; padding: 0;")
        self.cb_profile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cb_profile.currentIndexChanged.connect(self._on_dashboard_profile_changed)
        
        btn_container = QWidget()
        btn_container.setFixedSize(160, 160)
        btn_container.setStyleSheet("background: transparent;")

        self.btn_connect = QPushButton(btn_container)
        self.btn_connect.setFixedSize(160, 160)
        self.btn_connect.setStyleSheet(
            "QPushButton { background-color: #3B82F6; border-radius: 80px; border: none; }"
            "QPushButton:pressed { background-color: #2563EB; }"
        )
        self.btn_connect.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_connect.setProperty("state", "disconnected")

        from PyQt6.QtSvgWidgets import QSvgWidget
        from PyQt6.QtCore import QByteArray
        power_svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>'
        self.svg_power = QSvgWidget(btn_container)
        self.svg_power.load(QByteArray(power_svg))
        self.svg_power.setGeometry(48, 48, 64, 64)
        self.svg_power.setStyleSheet("background: transparent;")
        self.svg_power.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.lbl_connect_hint = QLabel("Toca para conectar")
        self.lbl_connect_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_connect_hint.setStyleSheet("font-size: 16px; font-weight: 500; margin-top: 16px;")
        
        self.lbl_status = QLabel("Estado: Desconectado")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setObjectName("label_dim")
        self.lbl_status.setStyleSheet("margin-top: 8px;")
        
        card_layout.addWidget(self.lbl_current_profile_title)
        card_layout.addWidget(self.cb_profile)
        card_layout.addStretch()
        card_layout.addWidget(btn_container, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_connect_hint, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addStretch()
        card_layout.addWidget(self.lbl_status)
        
        # Logs Button under status
        lyt_logs_btn = QHBoxLayout()
        btn_logs = QPushButton("Ver Logs")
        btn_logs.setObjectName("btn_secondary")
        btn_logs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_logs.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        lyt_logs_btn.addStretch()
        lyt_logs_btn.addWidget(btn_logs)
        lyt_logs_btn.addStretch()
        card_layout.addLayout(lyt_logs_btn)
        
        layout.addWidget(card, stretch=1)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        stat_ip = QFrame()
        stat_ip.setObjectName("card")
        stat_ip_lyt = QVBoxLayout(stat_ip)
        lbl_ip_title = QLabel("IP Asignada")
        lbl_ip_title.setObjectName("label_dim")
        self.lbl_ip_val = QLabel("---.---.---.---")
        self.lbl_ip_val.setStyleSheet("font-size: 14px; font-weight: bold;")
        stat_ip_lyt.addWidget(lbl_ip_title)
        stat_ip_lyt.addWidget(self.lbl_ip_val)
        
        stat_time = QFrame()
        stat_time.setObjectName("card")
        stat_time_lyt = QVBoxLayout(stat_time)
        lbl_time_title = QLabel("Duración")
        lbl_time_title.setObjectName("label_dim")
        self.lbl_time_val = QLabel("00:00:00")
        self.lbl_time_val.setStyleSheet("font-size: 14px; font-weight: bold;")
        stat_time_lyt.addWidget(lbl_time_title)
        stat_time_lyt.addWidget(self.lbl_time_val)
        
        stats_layout.addWidget(stat_ip)
        stats_layout.addWidget(stat_time)
        layout.addLayout(stats_layout)
        
        self.stack.addWidget(page)
        
    def _setup_page_logs(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QHBoxLayout()
        btn_back = QPushButton("⬅")
        btn_back.setObjectName("btn_icon")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        title = QLabel("Logs")
        title.setObjectName("label_title")
        btn_clear = QPushButton("Limpiar")
        btn_clear.setObjectName("btn_icon")
        btn_clear.setStyleSheet("color: #EF4444;")
        btn_clear.clicked.connect(lambda: self.log_view.clear())
        
        header.addWidget(btn_back)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_clear)
        layout.addLayout(header)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_view)
        
        self.stack.addWidget(page)
        
    def _setup_page_profiles(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QHBoxLayout()
        btn_back = QPushButton("⬅")
        btn_back.setObjectName("btn_icon")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        title = QLabel("Gestionar Perfiles")
        title.setObjectName("label_title")
        
        btn_add_top = QPushButton("⊕")
        btn_add_top.setObjectName("btn_circle_plus")
        btn_add_top.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add_top.clicked.connect(self._action_new_profile)
        
        header.addWidget(btn_back)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_add_top)
        layout.addLayout(header)
        
        self.list_profiles = QListWidget()
        self.list_profiles.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_profiles.itemDoubleClicked.connect(self._on_profile_double_clicked)
        layout.addWidget(self.list_profiles)
        
        self.stack.addWidget(page)
        
    def _setup_page_edit(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QHBoxLayout()
        btn_back = QPushButton("⬅")
        btn_back.setObjectName("btn_icon")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.lbl_edit_title = QLabel("Editar Perfil")
        self.lbl_edit_title.setObjectName("label_title")
        self.btn_save_profile = QPushButton("Guardar")
        self.btn_save_profile.setObjectName("btn_icon")
        self.btn_save_profile.setStyleSheet("color: #3B82F6;")
        self.btn_save_profile.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save_profile.clicked.connect(self._save_profile)
        
        header.addWidget(btn_back)
        header.addWidget(self.lbl_edit_title)
        header.addStretch()
        header.addWidget(self.btn_save_profile)
        layout.addLayout(header)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        # Name
        lbl_name = QLabel("Nombre del Perfil")
        lbl_name.setObjectName("label_dim")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ej. VPN Trabajo")
        form_layout.addWidget(lbl_name)
        form_layout.addWidget(self.name_input)
        
        # File
        lbl_file = QLabel("Archivo .ovpn")
        lbl_file.setObjectName("label_dim")
        file_lyt = QHBoxLayout()
        self.config_path_input = QLineEdit()
        self.config_path_input.setPlaceholderText("Seleccionar...")
        btn_browse = QPushButton("📁")
        btn_browse.setObjectName("btn_icon")
        btn_browse.clicked.connect(self._browse_file)
        file_lyt.addWidget(self.config_path_input)
        file_lyt.addWidget(btn_browse)
        form_layout.addWidget(lbl_file)
        form_layout.addLayout(file_lyt)
        
        # VPN Creds
        lbl_vuser = QLabel("Usuario VPN")
        lbl_vuser.setObjectName("label_dim")
        self.vpn_user_input = QLineEdit()
        form_layout.addWidget(lbl_vuser)
        form_layout.addWidget(self.vpn_user_input)
        
        lbl_vpass = QLabel("Contraseña VPN")
        lbl_vpass.setObjectName("label_dim")
        pass_lyt = QHBoxLayout()
        self.vpn_pass_input = QLineEdit()
        self.vpn_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        btn_toggle_pass = QPushButton("👁")
        btn_toggle_pass.setObjectName("btn_icon")
        btn_toggle_pass.clicked.connect(lambda: self.vpn_pass_input.setEchoMode(
            QLineEdit.EchoMode.Normal if self.vpn_pass_input.echoMode() == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        ))
        pass_lyt.addWidget(self.vpn_pass_input)
        pass_lyt.addWidget(btn_toggle_pass)
        form_layout.addWidget(lbl_vpass)
        form_layout.addLayout(pass_lyt)
        
        # Proxy Section
        proxy_hdr = QHBoxLayout()
        lbl_proxy = QLabel("Usar Proxy")
        lbl_proxy.setStyleSheet("color: #3B82F6; font-weight: 600;")
        self.proxy_check = QCheckBox()
        self.proxy_check.setObjectName("switch")
        self.proxy_check.toggled.connect(self._toggle_proxy)
        proxy_hdr.addWidget(lbl_proxy)
        proxy_hdr.addStretch()
        proxy_hdr.addWidget(self.proxy_check)
        form_layout.addLayout(proxy_hdr)
        
        self.proxy_container = QWidget()
        pxy_lyt = QVBoxLayout(self.proxy_container)
        pxy_lyt.setContentsMargins(0, 0, 0, 0)
        
        lbl_phost = QLabel("Servidor Proxy")
        lbl_phost.setObjectName("label_dim")
        self.proxy_host_input = QLineEdit()
        pxy_lyt.addWidget(lbl_phost)
        pxy_lyt.addWidget(self.proxy_host_input)
        
        lbl_pport = QLabel("Puerto")
        lbl_pport.setObjectName("label_dim")
        self.proxy_port_input = QSpinBox()
        self.proxy_port_input.setRange(1, 65535)
        pxy_lyt.addWidget(lbl_pport)
        pxy_lyt.addWidget(self.proxy_port_input)
        
        req_cred_lyt = QHBoxLayout()
        lbl_req_cred = QLabel("Requiere Credenciales")
        lbl_req_cred.setObjectName("label_dim")
        self.proxy_req_cred = QCheckBox()
        self.proxy_req_cred.setObjectName("switch")
        self.proxy_req_cred.toggled.connect(self._toggle_proxy_creds)
        req_cred_lyt.addWidget(lbl_req_cred)
        req_cred_lyt.addStretch()
        req_cred_lyt.addWidget(self.proxy_req_cred)
        pxy_lyt.addLayout(req_cred_lyt)
        
        self.proxy_creds_container = QWidget()
        pcred_lyt = QVBoxLayout(self.proxy_creds_container)
        pcred_lyt.setContentsMargins(0, 0, 0, 0)
        
        lbl_pauth = QLabel("Tipo de Autenticación")
        lbl_pauth.setObjectName("label_dim")
        self.proxy_auth_input = QComboBox()
        self.proxy_auth_input.addItems(["ntlm", "basic"])
        pcred_lyt.addWidget(lbl_pauth)
        pcred_lyt.addWidget(self.proxy_auth_input)
        
        lbl_puser = QLabel("Usuario proxy")
        lbl_puser.setObjectName("label_dim")
        self.proxy_user_input = QLineEdit()
        pcred_lyt.addWidget(lbl_puser)
        pcred_lyt.addWidget(self.proxy_user_input)
        
        lbl_ppass = QLabel("Contraseña proxy")
        lbl_ppass.setObjectName("label_dim")
        self.proxy_pass_input = QLineEdit()
        self.proxy_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        pcred_lyt.addWidget(lbl_ppass)
        pcred_lyt.addWidget(self.proxy_pass_input)
        
        pxy_lyt.addWidget(self.proxy_creds_container)
        form_layout.addWidget(self.proxy_container)
        
        form_layout.addStretch() # Previene que los elementos "salten" ocupando todo el espacio al ocultar partes
        
        # ScrollArea to contain everything in Edit form
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_content.setLayout(form_layout)
        scroll.setWidget(scroll_content)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; }")
        scroll_content.setStyleSheet("background-color: transparent;")
        
        layout.addWidget(scroll)
        
        self.stack.addWidget(page)
        
    def connect_signals(self):
        self.vpn_runner.state_changed.connect(self._on_state_changed)
        self.vpn_runner.log_updated.connect(self._append_log)
        self.vpn_runner.dns_detected.connect(self._on_dns_detected)
        self.btn_connect.clicked.connect(self._on_connect_clicked)

    def load_profiles_list(self):
        self.list_profiles.clear()
        
        # Update ComboBox
        self.cb_profile.blockSignals(True)
        self.cb_profile.clear()
        
        profiles = self.profile_manager.get_all()
        for idx, (pid, pdata) in enumerate(profiles.items()):
            name = pdata.get("name", "Sin nombre")
            
            # List Widget Custom Item
            item = QListWidgetItem()
            self.list_profiles.addItem(item)
            item_widget = ProfileItemWidget(pid, name, self)
            item.setSizeHint(item_widget.sizeHint())
            self.list_profiles.setItemWidget(item, item_widget)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            
            # ComboBox update
            self.cb_profile.addItem(name, pid)
            
            if self.active_profile_id == pid:
                self.cb_profile.setCurrentIndex(idx)
        
        self.cb_profile.blockSignals(False)
            
        current_pid = self.active_profile_id if self.active_profile_id else (self._get_selected_profile_id() if self.list_profiles.count() > 0 else None)
        if not current_pid and profiles:
            pid0 = list(profiles.keys())[0]
            self.active_profile_id = pid0
            self.cb_profile.setCurrentIndex(0)
        elif current_pid and current_pid in profiles:
            pass # combo is already handled inline above
            
        self.profiles_changed.emit(profiles)
        
    def _on_dashboard_profile_changed(self, index):
        pid = self.cb_profile.itemData(index)
        if pid:
            self.active_profile_id = pid

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar configuración OpenVPN", "", "OpenVPN Files (*.ovpn)")
        if path:
            self.config_path_input.setText(path)

    def _toggle_proxy(self, checked):
        self.proxy_container.setVisible(checked)
        
    def _toggle_proxy_creds(self, checked):
        self.proxy_creds_container.setVisible(checked)

    def _get_selected_profile_id(self):
        items = self.list_profiles.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def _on_profile_double_clicked(self, item):
        pid = item.data(Qt.ItemDataRole.UserRole)
        self.active_profile_id = pid
        # Set combo box to the clicked profile
        idx = self.cb_profile.findData(pid)
        if idx >= 0:
            self.cb_profile.setCurrentIndex(idx)
        self.stack.setCurrentIndex(0)

    def _action_new_profile(self):
        self.editing_profile_id = None
        self.lbl_edit_title.setText("Nuevo Perfil")
        self.btn_save_profile.setText("Crear")
        self._populate_edit_form({})
        self.stack.setCurrentIndex(3)
        
    def _action_edit_profile(self, pid):
        if not pid: return
        self.editing_profile_id = pid
        self.lbl_edit_title.setText("Editar Perfil")
        self.btn_save_profile.setText("Guardar")
        pdata = self.profile_manager.get(pid)
        self._populate_edit_form(pdata)
        self.stack.setCurrentIndex(3)

    def _delete_profile(self, pid):
        if not pid: return
        pdata = self.profile_manager.get(pid)
        rep = QMessageBox.question(self, "Eliminar", "¿Eliminar perfil '" + pdata.get("name", "") + "'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if rep == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete(pid)
            if self.active_profile_id == pid:
                self.active_profile_id = None
            self.load_profiles_list()

    def _populate_edit_form(self, pdata):
        self.name_input.setText(pdata.get("name", ""))
        self.config_path_input.setText(pdata.get("config_path", ""))
        self.vpn_user_input.setText(pdata.get("vpn_username", ""))
        self.vpn_pass_input.setText(pdata.get("vpn_password", ""))
        
        use_proxy = pdata.get("use_proxy", False)
        self.proxy_check.setChecked(use_proxy)
        self.proxy_host_input.setText(pdata.get("proxy_host", "10.0.0.1"))
        self.proxy_port_input.setValue(int(pdata.get("proxy_port", 8080)))
        
        proxy_user = pdata.get("proxy_username", "")
        has_creds = bool(proxy_user)
        self.proxy_req_cred.setChecked(has_creds)
        self.proxy_user_input.setText(proxy_user)
        self.proxy_pass_input.setText(pdata.get("proxy_password", ""))
        
        auth = pdata.get("proxy_auth", "ntlm")
        self.proxy_auth_input.setCurrentText(auth if auth in ["ntlm", "basic"] else "ntlm")
        
        self._toggle_proxy(use_proxy)
        self._toggle_proxy_creds(has_creds)

    def _save_profile(self):
        data = {
            "name": self.name_input.text().strip(),
            "config_path": self.config_path_input.text().strip(),
            "vpn_username": self.vpn_user_input.text().strip(),
            "vpn_password": self.vpn_pass_input.text().strip(),
            "vpn_dns": "", 
            "use_proxy": self.proxy_check.isChecked(),
            "proxy_host": self.proxy_host_input.text().strip(),
            "proxy_port": self.proxy_port_input.value(),
            "proxy_auth": self.proxy_auth_input.currentText(),
            "proxy_username": self.proxy_user_input.text().strip() if self.proxy_req_cred.isChecked() else "",
            "proxy_password": self.proxy_pass_input.text().strip() if self.proxy_req_cred.isChecked() else ""
        }
        
        if self.editing_profile_id:
            self.profile_manager.update(self.editing_profile_id, data)
        else:
            self.editing_profile_id = self.profile_manager.add(data)
            self.active_profile_id = self.editing_profile_id
            
        self.load_profiles_list()
        self.stack.setCurrentIndex(2)

    def _on_state_changed(self, state: str):
        self._update_status_ui(state)
        
        if state in ["Disconnected", "Error"]:
            self.btn_connect.setStyleSheet("QPushButton { background-color: #3B82F6; border-radius: 80px; border: none; } QPushButton:pressed { background-color: #2563EB; }")
            self.btn_connect.setProperty("state", "disconnected")
            self.lbl_connect_hint.setText("Toca para conectar")
            self.blink_timer.stop()
            self.conn_timer.stop()
        elif state == "Connecting":
            self.btn_connect.setStyleSheet("QPushButton { background-color: #F59E0B; border-radius: 80px; border: none; } QPushButton:pressed { background-color: #D97706; }")
            self.btn_connect.setProperty("state", "connecting")
            self.lbl_connect_hint.setText("Conectando...")
            self.blink_timer.start(600)
            self.conn_timer.stop()
            self.lbl_time_val.setText("00:00:00")
            self.conn_time = 0
        elif state == "Connected":
            self.btn_connect.setStyleSheet("QPushButton { background-color: #10B981; border-radius: 80px; border: none; } QPushButton:pressed { background-color: #059669; }")
            self.btn_connect.setProperty("state", "connected")
            self.lbl_connect_hint.setText("Toca para Desconectar")
            self.blink_timer.stop()
            self.conn_time = 0
            self.lbl_time_val.setText("00:00:00")
            self.conn_timer.start(1000)
            
    def _update_time(self):
        self.conn_time += 1
        hrs = self.conn_time // 3600
        mins = (self.conn_time % 3600) // 60
        secs = self.conn_time % 60
        self.lbl_time_val.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

    def _update_status_ui(self, state: str, blink_color=None):
        if state == "Connected":
            self.lbl_status.setText("Estado: Conectado")
            self.lbl_status.setStyleSheet("color: #10B981; margin-top: 8px;")
        elif state == "Connecting":
            self.lbl_status.setText("Estado: Conectando...")
            color = blink_color if blink_color else "#F59E0B"
            self.lbl_status.setStyleSheet(f"color: {color}; margin-top: 8px;")
            self.lbl_ip_val.setText("---.---.---.---")
        elif state == "Error":
            self.lbl_status.setText("Estado: Error en la conexión")
            self.lbl_status.setStyleSheet("color: #EF4444; margin-top: 8px;")
            self.lbl_ip_val.setText("---.---.---.---")
            self.conn_timer.stop()
        else:
            self.lbl_status.setText("Estado: Desconectado")
            self.lbl_status.setStyleSheet("color: #888888; margin-top: 8px;")
            self.lbl_ip_val.setText("---.---.---.---")
            self.conn_timer.stop()

    def _toggle_blink(self):
        self._blink_state = not self._blink_state
        color = "#F59E0B" if self._blink_state else "#888888"
        self._update_status_ui("Connecting", color)

    def _on_connect_clicked(self):
        state = self.btn_connect.property("state")
        if state == "connected" or state == "connecting":
            self.vpn_runner.disconnect_vpn()
        elif state in ["disconnected", "error"]:
            if not self.active_profile_id:
                QMessageBox.warning(self, "Atención", "Por favor, crea y selecciona un perfil primero.")
                return
                
            pdata = self.profile_manager.get(self.active_profile_id)
            if pdata is None: return
            
            errors = self.profile_manager.validate_profile(pdata)
            if errors:
                err_msg = "\n".join("- " + e for e in errors)
                QMessageBox.critical(self, "Perfil Inválido", "Corrige los siguientes errores:\n\n" + err_msg)
                return
                
            self.log_view.clear()
            self._append_log("Conectando con perfil: " + pdata.get('name', ''))
            self.vpn_runner.connect_vpn(pdata)

    def _on_dns_detected(self, dns: str):
        if self.active_profile_id:
            self.profile_manager.update_dns(self.active_profile_id, dns)

    def _append_log(self, text: str):
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] {text}") # Log a consola
        
        if "ifconfig" in text and "netmask" in text:
            import re
            m = re.search(r"ifconfig (\d+\.\d+\.\d+\.\d+)", text)
            if m:
                self.lbl_ip_val.setText(m.group(1))
                
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
