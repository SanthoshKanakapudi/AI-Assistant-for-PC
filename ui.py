from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QHBoxLayout, QMenu, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint, QTimer, QPropertyAnimation
from PyQt6.QtGui import QAction, QPainter, QColor, QFont
import speech_recognition as sr
import functions as fun
from engine import EngineWorker


# ---------------- VOICE WORKER ---------------- #

class VoiceWorker(QThread):
    heard_text = pyqtSignal(str)
    state_signal = pyqtSignal(str)

    def __init__(self, max_length=20, pause_duration=1.0):
        super().__init__()
        self.running = True
        self.pause_listening = False
        self.max_length = max_length
        self.pause_duration = pause_duration
        self.current_state = None

    def emit_state(self, state):
        if self.current_state != state:
            self.current_state = state
            self.state_signal.emit(state)

    def run(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            recognizer.pause_threshold = self.pause_duration

        while self.running:
            if self.pause_listening:
                self.msleep(200)
                continue

            try:
                self.emit_state("listening")

                with mic as source:
                    audio = recognizer.listen(
                        source,
                        timeout=None,
                        phrase_time_limit=self.max_length
                    )

                self.emit_state("processing")

                try:
                    text = recognizer.recognize_google(audio)
                    if text.strip():
                        self.heard_text.emit(text)
                except:
                    pass

                self.emit_state("idle")

            except:
                self.emit_state("idle")

    def stop_listening(self):
        self.pause_listening = True

    def resume_listening(self):
        self.pause_listening = False

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


# ---------- MESSAGE BUBBLE ---------- #

class MessageBubble(QFrame):
    def __init__(self, text, is_user=True):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 10))
        label.setMaximumWidth(300)

        if is_user:
            self.setStyleSheet("""
                QFrame { background-color: #2563eb; border-radius: 12px; }
                QLabel { color: white; padding: 8px; }
            """)
            layout.addStretch()
            layout.addWidget(label)
        else:
            self.setStyleSheet("""
                QFrame { background-color: #1f2937; border-radius: 12px; }
                QLabel { color: #e5e7eb; padding: 8px; }
            """)
            layout.addWidget(label)
            layout.addStretch()

        self.setLayout(layout)


# ---------- CHAT WINDOW ---------- #

class ChatWindow(QWidget):

    def __init__(self, engine, assistant):
        super().__init__()
        self.engine = engine
        self.assistant = assistant
        self.engine_worker = None
        self.init_ui()
        
    def smooth_scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        self.animation = QPropertyAnimation(scrollbar, b"value")
        self.animation.setDuration(300)  # smoothness
        self.animation.setStartValue(scrollbar.value())
        self.animation.setEndValue(scrollbar.maximum())
        self.animation.start()

    def init_ui(self):
        self.setWindowTitle("JARVIS")
        self.setGeometry(300, 200, 420, 600)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.container = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.container.setLayout(self.chat_layout)
        self.scroll.setWidget(self.container)

        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Message Jarvis...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                color: white;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        self.input_box.returnPressed.connect(self.handle_query)

        self.send_button = QPushButton("➤")
        self.send_button.setFixedWidth(40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                border-radius: 10px;
                color: black;
                font-weight: bold;
            }
        """)
        self.send_button.clicked.connect(self.handle_query)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(self.scroll)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #020617;")

    def add_message(self, text, is_user):
        bubble = MessageBubble(text, is_user)
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(0, self.smooth_scroll_to_bottom)

    def handle_query(self):
        query = self.input_box.text().strip()
        if not query:
            return

        self.assistant.is_busy = True
        self.assistant.voice_worker.stop_listening()
        self.assistant.update_state("executing")

        self.add_message(query, True)
        self.input_box.clear()

        self.engine_worker = EngineWorker(self.engine, query)
        self.engine_worker.finished_signal.connect(self.handle_response)
        self.engine_worker.start()

    def handle_response(self, result):
        response = result.get("response", "")
        step_msgs = result.get("steps_messages", [])

        # Show final response
        self.add_message(response, False)

        self.assistant.update_state("executing")

        # Speak step-by-step (natural feel)
        def speak_steps(index=0):
            if index < len(step_msgs):
                fun.speak(
                    step_msgs[index],
                    on_complete=lambda: speak_steps(index + 1)
                )
            else:
                # After all steps done
                self.on_speech_done()

        if step_msgs:
            speak_steps()
        else:
            fun.speak(response, on_complete=self.on_speech_done)

    def on_speech_done(self):
        QTimer.singleShot(0, self.finish_task)

    def finish_task(self):
        self.assistant.is_busy = False
        self.assistant.voice_worker.resume_listening()
        self.assistant.update_state("listening")

    def add_voice_text(self, text):
        self.assistant.is_busy = True
        self.assistant.voice_worker.stop_listening()
        self.assistant.update_state("executing")

        self.add_message(text, True)

        self.engine_worker = EngineWorker(self.engine, text)
        self.engine_worker.finished_signal.connect(self.handle_response)
        self.engine_worker.start()


# ---------------- FLOATING ASSISTANT ---------------- #

class FloatingAssistant(QWidget):

    def __init__(self, engine):
        super().__init__()

        self.engine = engine
        self.chat_window = ChatWindow(self.engine, self)
        self.voice_worker = VoiceWorker()

        self.is_busy = False

        self.setFixedSize(80, 80)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.color = QColor("#ef4444")
        self.offset = QPoint()

        self.wave_radius = 20
        self.wave_step = 2
        self.max_radius = 35
        self.animating = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_wave)

        self.voice_worker.heard_text.connect(self.handle_voice)
        self.voice_worker.state_signal.connect(
            self.update_state,
            Qt.ConnectionType.QueuedConnection
        )

        self.voice_worker.start()

        # Initial state
        self.update_state("listening")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = self.width() // 2

        if self.animating:
            wave_color = QColor(self.color)
            wave_color.setAlpha(80)
            painter.setBrush(wave_color)
            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(
                center - self.wave_radius,
                center - self.wave_radius,
                self.wave_radius * 2,
                self.wave_radius * 2
            )

        painter.setBrush(self.color)
        painter.drawEllipse(center - 15, center - 15, 30, 30)

    def animate_wave(self):
        self.wave_radius += self.wave_step
        if self.wave_radius > self.max_radius:
            self.wave_radius = 20
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        show_action = QAction("Show Window", self)
        hide_action = QAction("Hide Window", self)
        exit_action = QAction("Exit", self)

        show_action.triggered.connect(self.chat_window.show)
        hide_action.triggered.connect(self.chat_window.hide)
        exit_action.triggered.connect(self.close_all)

        menu.addAction(show_action)
        menu.addAction(hide_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        menu.exec(event.globalPos())

    def handle_voice(self, text):
        if self.is_busy:
            return
        self.chat_window.add_voice_text(text)

    def update_state(self, state):

        def safe_update():

            if self.is_busy and state in ["listening", "processing"]:
                return

            if state == "listening":
                self.color = QColor("#22c55e")
                self.animating = True
                self.timer.start(30)

            elif state == "processing":
                self.color = QColor("#facc15")
                self.animating = False
                self.timer.start(60)

            elif state == "executing":
                self.color = QColor("#f97316")
                self.animating = False
                self.timer.start(50)

            else:
                self.color = QColor("#ef4444")
                self.animating = False
                self.timer.stop()

            self.update()

        QTimer.singleShot(0, safe_update)

    def close_all(self):
        self.voice_worker.stop()
        self.chat_window.close()
        self.close()