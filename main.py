#main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from engine import JarvisEngine
from ui import FloatingAssistant

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
def main():
    app = QApplication(sys.argv)
    engine = JarvisEngine()
    assistant = FloatingAssistant(engine)
    assistant.show()
    assistant.chat_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()