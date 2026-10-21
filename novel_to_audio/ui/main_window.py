import os
import json
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QLineEdit,
                             QTextEdit, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from core.file_extractor import FileExtractor
from core.memory_manager import ProfileManager
from core.llm_client import LLMClient
from core.tts_engine import EdgeTTSEngine
from core.audio_processor import AudioProcessor
from ui.settings_dialog import SettingsDialog

class ScriptGenerationWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, profile_manager, profile_name, llm_client):
        super().__init__()
        self.profile_manager = profile_manager
        self.profile_name = profile_name
        self.llm_client = llm_client

    def run(self):
        try:
            config = self.profile_manager.load_config(self.profile_name)
            memory = self.profile_manager.load_memory(self.profile_name)

            profile_path = self.profile_manager.get_profile_path(self.profile_name)
            source_file = os.path.join(profile_path, "source.txt")

            if not os.path.exists(source_file):
                self.error.emit("Source file not found in profile.")
                return

            with open(source_file, 'r', encoding='utf-8') as f:
                text = f.read()

            # Normally we chunk properly, but let's assume it was chunked or we chunk it here
            extractor = FileExtractor()
            chunks = extractor.chunk_text(text)

            total_chunks = len(chunks)
            config["total_chunks"] = total_chunks
            self.profile_manager.save_config(self.profile_name, config)

            start_idx = config.get("current_chunk", 0)

            for i in range(start_idx, total_chunks):
                self.log.emit(f"Processing chunk {i+1}/{total_chunks}...")
                chunk = chunks[i]

                updated_memory, audio_script = self.llm_client.process_chunk(chunk, memory)

                self.profile_manager.save_memory(self.profile_name, updated_memory)
                self.profile_manager.append_script(self.profile_name, audio_script)

                config["current_chunk"] = i + 1
                self.profile_manager.save_config(self.profile_name, config)

                memory = updated_memory
                self.progress.emit(i + 1, total_chunks)

            self.log.emit("Script generation complete!")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

class AudioGenerationWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, profile_manager, profile_name, tts_engine):
        super().__init__()
        self.profile_manager = profile_manager
        self.profile_name = profile_name
        self.tts_engine = tts_engine
        self.audio_processor = AudioProcessor()

    def run(self):
        try:
            script = self.profile_manager.load_script(self.profile_name)
            if not script:
                self.error.emit("No script found. Generate script first.")
                return

            profile_path = self.profile_manager.get_profile_path(self.profile_name)
            output_dir = os.path.join(profile_path, "audio_output")

            total_lines = len(script)
            generated_files = []

            for i, line_item in enumerate(script):
                self.log.emit(f"Generating audio for line {i+1}/{total_lines}...")

                raw_audio_path = os.path.join(output_dir, f"raw_{i}.mp3")
                final_audio_path = os.path.join(output_dir, f"line_{i}.mp3")

                text = line_item.get("text", "")
                if not text.strip():
                    continue

                # Generate raw TTS
                self.tts_engine.generate_audio(text, raw_audio_path, line_item)

                # Apply post-processing
                effect = line_item.get("effect", "none")
                self.audio_processor.apply_effect(raw_audio_path, final_audio_path, effect)

                generated_files.append(final_audio_path)
                self.progress.emit(i + 1, total_lines)

            self.log.emit("Stitching final audio...")
            final_output = os.path.join(output_dir, "final_audiobook.mp3")
            self.audio_processor.stitch_audio(generated_files, final_output)

            self.log.emit(f"Audio generation complete! Saved to {final_output}")
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Novel to Audio Drama")
        self.resize(800, 600)

        self.profile_manager = ProfileManager()
        self.settings = QSettings("NovelToAudio", "App")

        self.init_ui()
        self.apply_theme()

    def apply_theme(self):
        theme = self.settings.value("theme", "Fusion (Default)")
        if theme == "Dark Modern":
            self.setStyleSheet("""
                QMainWindow { background-color: #121212; color: #FFFFFF; }
                QPushButton { background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #333333; padding: 5px; }
                QLabel, QLineEdit, QTextEdit { color: #FFFFFF; background-color: #1E1E1E; }
            """)
        elif theme == "Cyberpunk/Neon":
            self.setStyleSheet("""
                QMainWindow { background-color: #0d0221; color: #00ff41; }
                QPushButton { background-color: #1e093e; color: #00ff41; border: 1px solid #ff003c; padding: 5px; font-weight: bold; }
                QLabel, QLineEdit, QTextEdit { color: #00ff41; background-color: #0d0221; border: 1px solid #ff003c; }
            """)
        elif theme == "Clean White":
            self.setStyleSheet("""
                QMainWindow { background-color: #FFFFFF; color: #000000; }
                QPushButton { background-color: #F0F0F0; color: #000000; border: 1px solid #CCCCCC; padding: 5px; }
                QLabel, QLineEdit, QTextEdit { color: #000000; background-color: #FFFFFF; border: 1px solid #CCCCCC; }
            """)
        else:
            self.setStyleSheet("")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Top Bar (Settings)
        top_layout = QHBoxLayout()
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.open_settings)
        top_layout.addStretch()
        top_layout.addWidget(settings_btn)
        layout.addLayout(top_layout)

        # Profile Creation
        profile_layout = QHBoxLayout()
        self.profile_name_input = QLineEdit()
        self.profile_name_input.setPlaceholderText("Profile Name (e.g. Space Monster)")

        create_profile_btn = QPushButton("Create Profile & Load File")
        create_profile_btn.clicked.connect(self.create_profile)

        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_name_input)
        profile_layout.addWidget(create_profile_btn)
        layout.addLayout(profile_layout)

        # Actions
        action_layout = QHBoxLayout()
        self.gen_script_btn = QPushButton("Generate Audio Script")
        self.gen_script_btn.clicked.connect(self.generate_script)

        self.gen_audio_btn = QPushButton("Generate Audio")
        self.gen_audio_btn.clicked.connect(self.generate_audio)

        action_layout.addWidget(self.gen_script_btn)
        action_layout.addWidget(self.gen_audio_btn)
        layout.addLayout(action_layout)

        # Progress and Logs
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.apply_theme()

    def log(self, message: str):
        self.log_output.append(message)

    def create_profile(self):
        profile_name = self.profile_name_input.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "Select Novel File", "", "All Supported Files (*.txt *.epub *.pdf *.docx *.html *.md)")
        if not filepath:
            return

        try:
            extractor = FileExtractor()
            text = extractor.extract_text(filepath)

            profile_path = self.profile_manager.create_profile(profile_name)

            # Save extracted source text
            with open(os.path.join(profile_path, "source.txt"), 'w', encoding='utf-8') as f:
                f.write(text)

            self.log(f"Profile '{profile_name}' created successfully. Extracted {len(text)} characters.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create profile: {str(e)}")

    def generate_script(self):
        profile_name = self.profile_name_input.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        api_key = self.settings.value("api_key", "")
        if not api_key:
            QMessageBox.warning(self, "Warning", "API Key is not set in Settings.")
            return

        base_url = self.settings.value("base_url", "https://opencode.ai/zen/go/v1")
        model = self.settings.value("model", "deepseek")

        llm_client = LLMClient(api_key=api_key, base_url=base_url, model=model)

        self.gen_script_btn.setEnabled(False)
        self.script_worker = ScriptGenerationWorker(self.profile_manager, profile_name, llm_client)
        self.script_worker.progress.connect(self.update_progress)
        self.script_worker.log.connect(self.log)
        self.script_worker.error.connect(self.worker_error)
        self.script_worker.finished.connect(self.worker_finished)
        self.script_worker.start()

    def generate_audio(self):
        profile_name = self.profile_name_input.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        engine_type = self.settings.value("tts_engine", "Edge-TTS")
        if engine_type == "Edge-TTS":
            tts_engine = EdgeTTSEngine()
        else:
            QMessageBox.warning(self, "Warning", "Kokoro-TTS not yet fully supported. Falling back to Edge-TTS.")
            tts_engine = EdgeTTSEngine()

        self.gen_audio_btn.setEnabled(False)
        self.audio_worker = AudioGenerationWorker(self.profile_manager, profile_name, tts_engine)
        self.audio_worker.progress.connect(self.update_progress)
        self.audio_worker.log.connect(self.log)
        self.audio_worker.error.connect(self.worker_error)
        self.audio_worker.finished.connect(self.worker_finished)
        self.audio_worker.start()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def worker_error(self, err_msg):
        self.log(f"ERROR: {err_msg}")
        QMessageBox.critical(self, "Error", err_msg)
        self.gen_script_btn.setEnabled(True)
        self.gen_audio_btn.setEnabled(True)

    def worker_finished(self):
        self.gen_script_btn.setEnabled(True)
        self.gen_audio_btn.setEnabled(True)
