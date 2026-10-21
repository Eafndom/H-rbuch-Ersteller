from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QHBoxLayout)
from PyQt6.QtCore import QSettings

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("NovelToAudio", "App")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.settings.value("api_key", ""))
        form_layout.addRow("OpenCode Go API Key:", self.api_key_input)

        # Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setText(self.settings.value("base_url", "https://opencode.ai/zen/go/v1"))
        form_layout.addRow("Base URL:", self.base_url_input)

        # Model
        self.model_input = QLineEdit()
        self.model_input.setText(self.settings.value("model", "deepseek"))
        form_layout.addRow("Model ID:", self.model_input)

        # TTS Engine
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(["Edge-TTS", "Kokoro-TTS"])
        current_tts = self.settings.value("tts_engine", "Edge-TTS")
        self.tts_engine_combo.setCurrentText(current_tts)
        form_layout.addRow("TTS Engine:", self.tts_engine_combo)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Modern", "Cyberpunk/Neon", "Clean White", "Fusion (Default)"])
        current_theme = self.settings.value("theme", "Fusion (Default)")
        self.theme_combo.setCurrentText(current_theme)
        form_layout.addRow("UI Theme:", self.theme_combo)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        self.settings.setValue("api_key", self.api_key_input.text())
        self.settings.setValue("base_url", self.base_url_input.text())
        self.settings.setValue("model", self.model_input.text())
        self.settings.setValue("tts_engine", self.tts_engine_combo.currentText())
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.accept()
