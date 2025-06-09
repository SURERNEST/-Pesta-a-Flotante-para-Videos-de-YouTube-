import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout,
    QColorDialog, QDialog, QDialogButtonBox, QSpinBox, QFormLayout, QSpacerItem, QSizePolicy,
    QGroupBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QPoint
import re

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setFixedSize(500, 500)
        self.setStyleSheet("""
            QDialog {
                background: #232946;
                color: #fffffe;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 15px;
                border-radius: 10px;
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
            QSpinBox {
                background: #121629;
                color: #fffffe;
                border: 2px solid #b8c1ec;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 15px;
                min-width: 120px;
            }
            QFormLayout > QLabel {
                min-width: 100px;
                font-size: 14px;
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
        
        # Cambiar color de fondo
        color_btn = QPushButton("Cambiar color de fondo principal")
        color_btn.clicked.connect(self.change_bg_color)
        appearance_layout.addWidget(color_btn)
        
        layout.addWidget(appearance_group)

        # Grupo para tamaño
        size_group = QGroupBox("Tamaño del Reproductor")
        size_layout = QVBoxLayout(size_group)
        
        size_form = QFormLayout()
        size_form.setSpacing(15)
        size_form.setContentsMargins(10, 10, 10, 10)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 1920)
        self.width_spin.setValue(self.parent().video_width if hasattr(self.parent(), "video_width") else 480)
        self.width_spin.setToolTip("Ancho del reproductor de video en píxeles")
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(150, 1080)
        self.height_spin.setValue(self.parent().video_height if hasattr(self.parent(), "video_height") else 270)
        self.height_spin.setToolTip("Alto del reproductor de video en píxeles")
        
        size_form.addRow("Ancho (px):", self.width_spin)
        size_form.addRow("Alto (px):", self.height_spin)
        size_layout.addLayout(size_form)

        apply_size_btn = QPushButton("Aplicar nuevo tamaño")
        apply_size_btn.setToolTip("El nuevo tamaño se aplicará al próximo video que abras")
        apply_size_btn.clicked.connect(self.apply_size)
        size_layout.addWidget(apply_size_btn)
        
        layout.addWidget(size_group)

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

        # Botón de cerrar
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText("Cerrar configuración")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, alignment=Qt.AlignHCenter)

        self.setLayout(layout)

    def change_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.parent().setStyleSheet(self.parent().styleSheet() + f"background: {color.name()};")

    def apply_size(self):
        self.parent().video_width = self.width_spin.value()
        self.parent().video_height = self.height_spin.value()

def youtube_embed_url(url):
    patterns = [
        r"youtu\.be/([a-zA-Z0-9_-]+)",
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
        r"youtube\.com/embed/([a-zA-Z0-9_-]+)"
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            video_id = m.group(1)
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0&modestbranding=1&color=white&theme=dark"
    return url

class VideoWindow(QWidget):
    def __init__(self, url, width=480, height=270):
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
            }
        """)
        self._drag_active = False
        self._drag_position = QPoint()
        self.fullscreen = False

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Botón de cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,0.6);
                color: white;
                border: none;
                font-size: 20px;
                border-radius: 16px;
            }
            QPushButton:hover {
                background: #e74c3c;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(self.close_btn)
        close_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(close_layout)

        self.webview = QWebEngineView()
        embed_url = youtube_embed_url(url)
        self.webview.setStyleSheet("background: #000;")
        self.webview.load(QUrl(embed_url))
        self.layout.addWidget(self.webview, stretch=1)

        self.setLayout(self.layout)

        if hasattr(self.webview, "fullScreenRequested"):
            self.webview.fullScreenRequested.connect(self.handle_fullscreen)

        self.setMouseTracking(True)

    def handle_fullscreen(self, request):
        if request.toggleOn():
            self.fullscreen = True
            self.close_btn.hide()
            self.showFullScreen()
        else:
            self.fullscreen = False
            self.close_btn.show()
            self.showNormal()
        request.accept()

    def mousePressEvent(self, event):
        if not self.fullscreen and event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.fullscreen and self._drag_active and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False

class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reproductor Flotante para Videos de YouTube")
        self.setFixedSize(500, 300)
        self.setStyleSheet("""
            QWidget {
                background: #232946;
                color: #fffffe;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 15px;
                border-radius: 10px;
            }
            QLineEdit {
                background: #121629;
                color: #fffffe;
                border: 2px solid #b8c1ec;
                border-radius: 8px;
                padding: 8px;
                font-size: 15px;
            }
            QPushButton {
                background: #eebbc3;
                color: #232946;
                border: none;
                border-radius: 8px;
                padding: 10px 0;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #b8c1ec;
                color: #232946;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
                color: #eebbc3;
                margin-bottom: 5px;
            }
            QLabel#creator {
                font-size: 12px;
                color: #b8c1ec;
                padding: 8px;
                background: rgba(0,0,0,0.2);
                border-radius: 5px;
            }
        """)

        self.video_width = 480
        self.video_height = 270

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Encabezado
        header = QHBoxLayout()
        title = QLabel("Reproductor Flotante para Videos")
        title.setObjectName("title")
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
                padding: 5px 10px;
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
        instruction = QLabel("Pega tu enlace de YouTube aquí:")
        layout.addWidget(instruction)

        # Entrada de URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ejemplo: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        layout.addWidget(self.url_input)

        # Botón principal
        self.open_btn = QPushButton("Abrir video en ventana flotante")
        self.open_btn.clicked.connect(self.open_video)
        layout.addWidget(self.open_btn)

        self.setLayout(layout)
        self.floating_windows = []

    def open_config(self):
        dlg = ConfigDialog(self)
        dlg.exec_()

    def open_video(self):
        url = self.url_input.text()
        if url.startswith("http"):
            video_window = VideoWindow(url, self.video_width, self.video_height)
            video_window.show()
            self.floating_windows.append(video_window)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())