from PyQt6.QtWidgets import QApplication
import sys
from src.mainWindow import MainWindow
import os
"""
To Do List:
- Sound effects
- scoring
- undo/redo
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec())