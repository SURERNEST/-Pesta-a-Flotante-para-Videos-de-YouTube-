import sys
import re
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout,
    QColorDialog, QDialog, QDialogButtonBox, QSpinBox, QFormLayout, QGroupBox,
    QSlider, QCheckBox, QComboBox, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile, QWebEnginePage
from PyQt5.QtCore import Qt, QUrl, QPoint, QSettings, QObject, QEvent
from PyQt5.QtGui import QFont
import re

# Diagnostics: capture JS console and log
class DiagnosticWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, linenumber, sourceid):
        logging.debug(f"JS console ({level}) {sourceid}:{linenumber} - {msg}")

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setFixedSize(550, 650)
        self.setStyleSheet("""
            QDialog {
                background: #232946;
                color: #fffffe;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 15px;
            }
            QPushButton {
                background: #eebbc3;
                color: #232946;
                border: none;
                border-radius: 8px;
                padding: 12px 0;
                font-size: 15px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background: #b8c1ec;
                color: #232946;
            }
            QGroupBox {
                border: 2px solid #b8c1ec;
                border-radius: 10px;
                margin-top: 20px;
                padding: 15px 10px;
                font-weight: bold;
                font-size: 16px;
                color: #eebbc3;
            }
            QSpinBox, QComboBox {
                background: #121629;
                color: #fffffe;
                border: 2px solid #b8c1ec;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 15px;
                min-width: 120px;
            }
            QSlider::groove:horizontal {
                background: #121629;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #eebbc3;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #b8c1ec;
                border-radius: 4px;
                background: #121629;
            }
            QCheckBox::indicator:checked {
                background: #eebbc3;
            }
            QLabel#contact {
                font-size: 14px;
                color: #b8c1ec;
                margin: 8px 0;
                line-height: 1.6;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Grupo para apariencia
        appearance_group = QGroupBox("Personalización Visual")
        appearance_layout = QVBoxLayout(appearance_group)
        
        color_btn = QPushButton("Cambiar color de fondo principal")
        color_btn.clicked.connect(self.change_bg_color)
        appearance_layout.addWidget(color_btn)
        
        # Opacidad
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacidad de ventana:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(self.parent().windowOpacity() * 100))
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        opacity_layout.addWidget(self.opacity_label)
        appearance_layout.addLayout(opacity_layout)
        
        layout.addWidget(appearance_group)

        # Grupo para tamaño
        size_group = QGroupBox("Tamaño del Reproductor")
        size_layout = QVBoxLayout(size_group)
        
        size_form = QFormLayout()
        size_form.setSpacing(15)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 1920)
        self.width_spin.setValue(self.parent().video_width)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(150, 1080)
        self.height_spin.setValue(self.parent().video_height)
        
        # Presets de tamaño
        self.size_preset = QComboBox()
        self.size_preset.addItems(["Personalizado", "Pequeño (480x270)", "Mediano (640x360)", 
                                   "Grande (854x480)", "HD (1280x720)"])
        self.size_preset.currentTextChanged.connect(self.apply_preset)
        
        size_form.addRow("Preset:", self.size_preset)
        size_form.addRow("Ancho (px):", self.width_spin)
        size_form.addRow("Alto (px):", self.height_spin)
        size_layout.addLayout(size_form)

        apply_size_btn = QPushButton("Aplicar nuevo tamaño")
        apply_size_btn.clicked.connect(self.apply_size)
        size_layout.addWidget(apply_size_btn)
        
        layout.addWidget(size_group)

        # Grupo para comportamiento
        behavior_group = QGroupBox("Comportamiento")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.autoplay_check = QCheckBox("Reproducción automática")
        self.autoplay_check.setChecked(self.parent().autoplay)
        
        self.save_history_check = QCheckBox("Guardar historial de videos")
        self.save_history_check.setChecked(self.parent().save_history)
        
        behavior_layout.addWidget(self.autoplay_check)
        behavior_layout.addWidget(self.save_history_check)
        
        layout.addWidget(behavior_group)

        # Grupo para contacto
        contact_group = QGroupBox("Soporte y Contacto")
        contact_layout = QVBoxLayout(contact_group)
        
        contact = QLabel(
            "✉️ Correo electrónico: not.boris.yt@gmail.com\n"
            "🟣 Discord: bochisline\n"
            "📷 Instagram: @bochislineeeee\n\n"
            "¿Necesitas ayuda? Contáctanos para soporte técnico"
        )
        contact.setObjectName("contact")
        contact.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        contact_layout.addWidget(contact)
        
        layout.addWidget(contact_group)

        # Botones
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar configuración")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_preset(self, preset):
        presets = {
            "Pequeño (480x270)": (480, 270),
            "Mediano (640x360)": (640, 360),
            "Grande (854x480)": (854, 480),
            "HD (1280x720)": (1280, 720)
        }
        if preset in presets:
            w, h = presets[preset]
            self.width_spin.setValue(w)
            self.height_spin.setValue(h)

    def change_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.parent().bg_color = color.name()
            self.parent().update_style()


    
    def change_opacity(self, value):
        self.opacity_label.setText(f"{value}%")
        self.parent().setWindowOpacity(value / 100.0)

    def apply_size(self):
        self.parent().video_width = self.width_spin.value()
        self.parent().video_height = self.height_spin.value()

    def save_config(self):
        self.parent().video_width = self.width_spin.value()
        self.parent().video_height = self.height_spin.value()
        self.parent().autoplay = self.autoplay_check.isChecked()
        self.parent().save_history = self.save_history_check.isChecked()
        self.parent().save_settings()
        QMessageBox.information(self, "Configuración", "¡Configuración guardada exitosamente!")

class VideoWindow(QWidget):
    def __init__(self, url, width=480, height=270, autoplay=True):
        super().__init__()
        self.setWindowTitle("Reproductor Flotante")
        self.normal_size = (width, height)
        self.resize(*self.normal_size)
        self.setMinimumSize(200, 150)
        self.setWindowFlags(self.windowFlags() | 
                            Qt.WindowStaysOnTopHint | 
                            Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QWidget {
                background: #000000;
                border: 2px solid #b8c1ec;
                border-radius: 8px;
            }
        """)
        self._drag_active = False
        self._drag_position = QPoint()
        self.fullscreen = False
        self.is_pinned = True

        # Layout principal sin márgenes
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # WebView ocupa todo
        self.webview = QWebEngineView()
        self.layout.addWidget(self.webview, stretch=1)
        self.setLayout(self.layout)
        
        # No necesitamos event filter para webview - los botones estarán flotantes encima

        # Botones de control como overlay (widget flotante encima del video)
        # Contenedor para los botones - debe ser descendiente de self para que tenga coordenadas correctas
        self.buttons_container = QWidget(self)
        self.buttons_container.setGeometry(0, 0, self.width(), 45)
        self.buttons_container.setStyleSheet("background: transparent;")
        self.buttons_container.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.buttons_container.raise_()
        
        control_bar = QHBoxLayout(self.buttons_container)
        control_bar.setSpacing(5)
        control_bar.setContentsMargins(5, 5, 5, 5)
        
        # Botón de pin/despin
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.6);
                color: white;
                border: none;
                font-size: 16px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #3498db;
            }
        """)
        self.pin_btn.setToolTip("Mantener siempre visible")
        self.pin_btn.clicked.connect(self.toggle_pin)
        
        # Botón de minimizar
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.6);
                color: white;
                border: none;
                font-size: 20px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #f39c12;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        
        # Botón de cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.6);
                color: white;
                border: none;
                font-size: 18px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background: #e74c3c;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        control_bar.addStretch()
        control_bar.addWidget(self.pin_btn)
        control_bar.addWidget(minimize_btn)
        control_bar.addWidget(self.close_btn)

        # Configurar perfil personalizado
        profile = self.webview.page().profile()
        try:
            # Preferir almacenamiento persistente para cookies/credenciales
            profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
            cache_dir = os.path.join(os.path.expanduser("~"), ".youtube_floater_cache")
            os.makedirs(cache_dir, exist_ok=True)
            profile.setCachePath(cache_dir)
            profile.setPersistentStoragePath(cache_dir)
        except Exception:
            logging.debug("No se pudo configurar almacenamiento persistente del perfil")

        # Configurar User Agent moderno
        try:
            profile.setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        except Exception:
            logging.debug("No se pudo establecer User Agent en el perfil")

        # Usar página diagnóstica para capturar mensajes de consola
        page = DiagnosticWebPage(profile, self.webview)
        self.webview.setPage(page)

        # Configurar settings del navegador
        settings = self.webview.settings()
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        # Permitir que contenido local cargue recursos remotos (para setHtml baseUrl)
        try:
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        except Exception:
            logging.debug("Some LocalContent settings not available on this Qt version")

        # Conectores para diagnóstico
        self._fallback_attempted = False
        self.webview.loadStarted.connect(lambda: logging.info("WebView loadStarted"))
        self.webview.loadProgress.connect(lambda p: logging.info(f"WebView loadProgress: {p}%"))
        self.webview.loadFinished.connect(self.on_load_finished)

        # Permitir automáticamente permisos solicitados por la página (audio, cámara, geolocation)
        try:
            def _grant_permission(url, feature):
                try:
                    page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
                    logging.info(f"Granted feature permission {feature} for {url.toString()}")
                except Exception:
                    logging.debug("Could not set feature permission")

            self.webview.page().featurePermissionRequested.connect(_grant_permission)
        except Exception:
            logging.debug("featurePermissionRequested not available in this Qt version")

        embed_url = self.youtube_embed_url(url, autoplay)
        self.webview.setStyleSheet("background: #000;")

        # Cargar mediante HTML con iframe para forzar atributos 'allow' y 'allowfullscreen'
        # El webview ocupa toda la ventana, iframe al 100% sin recorte
        iframe_html = f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8"> 
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <style>
            html,body {{ height:100%; margin:0; background:#000; padding:0; }}
            .player-wrapper {{ 
              width:100%; height:100%; 
              overflow:hidden;
              position:relative;
            }}
            .player-wrapper iframe {{
              width:100%; height:100%;
              border:0; display:block;
              background:#000;
            }}
          </style>
        </head>
        <body>
          <div class="player-wrapper">
            <iframe src="{embed_url}" allow="autoplay; encrypted-media; fullscreen; picture-in-picture" allowfullscreen></iframe>
          </div>
        </body>
        </html>
        """

        # Usar baseUrl para que el iframe herede el dominio y cookies
        try:
            self.webview.setHtml(iframe_html, QUrl(embed_url))
        except Exception:
            logging.exception("setHtml failed, falling back to load()")
            self.webview.load(QUrl(embed_url))

        if hasattr(self.webview, "fullScreenRequested"):
            self.webview.fullScreenRequested.connect(self.handle_fullscreen)

        self.setMouseTracking(True)

    def on_load_finished(self, ok: bool):
        url = self.webview.url().toString()
        logging.info(f"loadFinished: {ok} -> {url}")
        if not ok:
            # Capturar HTML para diagnóstico
            try:
                def _save_html(html):
                    fname = os.path.join(os.path.expanduser("~"), "youtube_floater_error.html")
                    with open(fname, "w", encoding="utf-8") as f:
                        f.write(html)
                    logging.error(f"Página cargada mal. HTML guardado en: {fname}")
                self.webview.page().toHtml(_save_html)
            except Exception as e:
                logging.exception("Error capturando HTML de la página")

            # Intentar fallback entre dominios (nocookie <-> www)
            if not getattr(self, "_fallback_attempted", False):
                self._fallback_attempted = True
                if "youtube-nocookie.com" in url:
                    new_url = url.replace("youtube-nocookie.com", "www.youtube.com")
                else:
                    new_url = url.replace("www.youtube.com", "www.youtube-nocookie.com")
                logging.info(f"Intentando fallback a: {new_url}")
                self.webview.load(QUrl(new_url))
            else:
                QMessageBox.warning(self, "Error de carga", "No se pudo cargar el video (error 153). Revisa consola y actualiza PyQt5/QtWebEngine.")

    def youtube_embed_url(self, url, autoplay=True):
        patterns = [
            r"youtu\.be/([a-zA-Z0-9_-]+)",
            r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
            r"youtube\.com/embed/([a-zA-Z0-9_-]+)",
            r"youtube\.com/shorts/([a-zA-Z0-9_-]+)"
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                video_id = m.group(1)
                autoplay_param = "1" if autoplay else "0"
                return f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay={autoplay_param}&rel=0&modestbranding=1&controls=1&playsinline=1&fs=1"
        return url

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        if self.is_pinned:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.pin_btn.setText("📌")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.pin_btn.setText("📍")
        self.show()

    def handle_fullscreen(self, request):
        if request.toggleOn():
            self.fullscreen = True
            self.close_btn.hide()
            self.pin_btn.hide()
            self.showFullScreen()
        else:
            self.fullscreen = False
            self.close_btn.show()
            self.pin_btn.show()
            self.showNormal()
        request.accept()

    def resizeEvent(self, event):
        """Actualizar posición del contenedor de botones al redimensionar"""
        super().resizeEvent(event)
        if hasattr(self, 'buttons_container'):
            self.buttons_container.setGeometry(0, 0, self.width(), 45)

    def mousePressEvent(self, event):
        """Maneja clicks de mouse para drag o interacción con botones"""
        if self.fullscreen:
            return
        
        # Verificar si el click es en la zona de botones (derecha, arriba)
        if event.y() < 45 and event.x() > self.width() - 150:
            # Dejar que los botones manejen el evento
            return
        
        # Si es click izquierdo en la zona de drag (parte superior/izquierda)
        if event.button() == Qt.LeftButton and event.y() < 45:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            return
        
        event.ignore()

    def mouseMoveEvent(self, event):
        """Mover la ventana mientras se arrastra"""
        if not self.fullscreen and self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        """Detener el dragging"""
        self._drag_active = False
        event.accept()

class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reproductor Flotante para Videos de YouTube")
        self.setFixedSize(600, 500)
        
        # Configuración por defecto
        self.settings = QSettings("BochisLine", "YouTubeFloater")
        self.video_width = self.settings.value("video_width", 480, type=int)
        self.video_height = self.settings.value("video_height", 270, type=int)
        self.autoplay = self.settings.value("autoplay", True, type=bool)
        self.save_history = self.settings.value("save_history", True, type=bool)
        self.bg_color = self.settings.value("bg_color", "#232946")
        self.video_history = self.settings.value("video_history", [])
        if not isinstance(self.video_history, list):
            self.video_history = []
        
        self.update_style()

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Encabezado
        header = QHBoxLayout()
        title = QLabel("🎬 Reproductor Flotante para Videos")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.addWidget(title, 1)
        
        config_btn = QPushButton("⚙ Configuración")
        config_btn.setFixedHeight(36)
        config_btn.setStyleSheet("""
            QPushButton {
                background: #b8c1ec; 
                color: #232946; 
                border: none; 
                border-radius: 8px; 
                font-size: 14px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #eebbc3;
            }
        """)
        config_btn.clicked.connect(self.open_config)
        header.addWidget(config_btn, alignment=Qt.AlignRight)
        layout.addLayout(header)

        # Información del creador
        creator = QLabel("Desarrollado por bochisline | Contacto: not.boris.yt@gmail.com")
        creator.setObjectName("creator")
        creator.setWordWrap(True)
        layout.addWidget(creator)

        # Instrucción
        instruction = QLabel("📝 Pega tu enlace de YouTube aquí:")
        instruction.setFont(QFont("Segoe UI", 12))
        layout.addWidget(instruction)

        # Entrada de URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ejemplo: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.url_input.returnPressed.connect(self.open_video)
        layout.addWidget(self.url_input)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.open_btn = QPushButton("▶ Abrir video en ventana flotante")
        self.open_btn.clicked.connect(self.open_video)
        button_layout.addWidget(self.open_btn)
        
        clear_btn = QPushButton("🗑 Limpiar")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #121629;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #e74c3c;
                color: white;
            }
        """)
        clear_btn.clicked.connect(self.url_input.clear)
        button_layout.addWidget(clear_btn)
        layout.addLayout(button_layout)

        # Historial de videos
        if self.save_history and self.video_history:
            history_label = QLabel("📚 Historial reciente:")
            history_label.setFont(QFont("Segoe UI", 11))
            layout.addWidget(history_label)
            
            self.history_list = QListWidget()
            self.history_list.setMaximumHeight(120)
            self.history_list.setStyleSheet("""
                QListWidget {
                    background: #121629;
                    border: 2px solid #b8c1ec;
                    border-radius: 8px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-radius: 4px;
                    color: #fffffe;
                }
                QListWidget::item:hover {
                    background: #2d3561;
                }
                QListWidget::item:selected {
                    background: #b8c1ec;
                    color: #232946;
                }
            """)
            self.history_list.itemDoubleClicked.connect(self.open_from_history)
            self.update_history_list()
            layout.addWidget(self.history_list)

        layout.addStretch()
        self.setLayout(layout)
        self.floating_windows = []

    def update_style(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {self.bg_color};
                color: #fffffe;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 15px;
            }}
            QLineEdit {{
                background: #121629;
                color: #fffffe;
                border: 2px solid #b8c1ec;
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
            }}
            QPushButton {{
                background: #eebbc3;
                color: #232946;
                border: none;
                border-radius: 8px;
                padding: 12px 0;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background: #b8c1ec;
                color: #232946;
            }}
            QLabel#title {{
                font-size: 24px;
                font-weight: bold;
                color: #eebbc3;
                margin-bottom: 5px;
            }}
            QLabel#creator {{
                font-size: 12px;
                color: #b8c1ec;
                padding: 8px;
                background: rgba(0,0,0,0.2);
                border-radius: 5px;
            }}
        """)

    def update_history_list(self):
        if hasattr(self, 'history_list'):
            self.history_list.clear()
            for url in reversed(self.video_history[-10:]):  # Mostrar últimos 10
                item = QListWidgetItem(f"🎥 {url[:60]}...")
                item.setData(Qt.UserRole, url)
                self.history_list.addItem(item)

    def add_to_history(self, url):
        if self.save_history:
            if url in self.video_history:
                self.video_history.remove(url)
            self.video_history.append(url)
            self.video_history = self.video_history[-20:]  # Mantener últimos 20
            self.save_settings()
            self.update_history_list()

    def open_from_history(self, item):
        url = item.data(Qt.UserRole)
        self.url_input.setText(url)
        self.open_video()

    def open_config(self):
        dlg = ConfigDialog(self)
        dlg.exec_()

    def open_video(self):
        url = self.url_input.text().strip()
        if url and url.startswith("http"):
            video_window = VideoWindow(url, self.video_width, self.video_height, self.autoplay)
            video_window.show()
            self.floating_windows.append(video_window)
            self.add_to_history(url)
            QMessageBox.information(self, "¡Éxito!", "Video abierto en ventana flotante\n\n💡 Puedes arrastrarla y moverla libremente")
        else:
            QMessageBox.warning(self, "Error", "Por favor ingresa una URL válida de YouTube")

    def save_settings(self):
        self.settings.setValue("video_width", self.video_width)
        self.settings.setValue("video_height", self.video_height)
        self.settings.setValue("autoplay", self.autoplay)
        self.settings.setValue("save_history", self.save_history)
        self.settings.setValue("bg_color", self.bg_color)
        self.settings.setValue("video_history", self.video_history)

if __name__ == "__main__":
    # Environment adjustments and logging for diagnostics
    logging.basicConfig(level=logging.INFO)
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    # Chromium flags: disable gpu for compatibility on some systems
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")

    app = QApplication(sys.argv)
    app.setApplicationName("Reproductor Flotante YouTube")
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())
