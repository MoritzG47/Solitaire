from PyQt6.QtWidgets import (QWidget, QLabel, QGraphicsRectItem, QPushButton, QGraphicsTextItem)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QTextOption
from PyQt6.QtCore import Qt, QPoint, QTimer, QTime
import random

class WinScreen(QWidget):    
    def __init__(self, parent=None, monitor=None):
        super().__init__()
        self.setWindowTitle("Win!")
        self.WinWidth = 400
        self.WinHeight = 200
        self.parent = parent
        self.x = int((monitor.width - self.WinWidth) / 2)
        self.y = int((monitor.height - self.WinHeight) / 2)
        self.setGeometry(self.x, self.y, self.WinWidth, self.WinHeight)

        self.label = QLabel("Congratulations! You've won the game!", self)
        self.label.setGeometry(0, 30, self.WinWidth, 40)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button = QPushButton("Restart", self)
        button.setFixedSize(140, 40)
        button.move((self.width() - button.width()) // 2, ((self.height() - button.height()) // 2) + 10)
        button.clicked.connect(self.restart)

    def restart(self):
        self.parent.ShuffleCards()
        self.hide()

    def popUp(self, pos: QPoint, width, height):
        x = int(pos.x() + (width - self.WinWidth) / 2)
        y = int(pos.y() + (height - self.WinHeight) / 2)
        self.move(x, y)
        self.show()

class Clock(QGraphicsTextItem):
    def __init__(self, width: int=0, height: int=0, padding: int=30, parent=None):
        super().__init__()
        self.parent = parent
        text = "00:00"
        self.setPlainText(text)
        color = "#FFFFFF"
        self.setDefaultTextColor(QColor(color))
        font = QFont("Consolas", 24)
        self.setFont(font)
        font_metrics = QFontMetrics(font)
        self.text_width = font_metrics.horizontalAdvance(text)
        self.text_height = font_metrics.height()
        x = int((width - self.text_width)/2)
        y = padding/2
        self.setPos(x, y)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.elapsed_time = QTime(0, 0, 0)

    def start(self):
        if not self.timer.isActive():
            self.timer.start(1000)  # update every 1 second

    def stop(self):
        self.timer.stop()

    def reset(self):
        self.timer.stop()
        self.elapsed_time = QTime(0, 0, 0)
        self.setPlainText("00:00")

    def update_time(self):
        self.elapsed_time = self.elapsed_time.addSecs(1)
        if self.elapsed_time.second() % 15 == 0:
            self.parent.FunFact.update_fact()
        time_str = self.elapsed_time.toString("mm:ss")
        self.setPlainText(time_str)

class FunFacts(QGraphicsTextItem):
    def __init__(self, width: int = 0, height: int = 0):
        super().__init__()
        self.width = width
        self.height = height

        with open("funfacts.txt", "r", encoding="utf-8") as f:
            self.facts = f.readlines()
        random.shuffle(self.facts)
        self.index = 0
        fact = self.facts[self.index].strip()

        self.setPlainText(fact)
        self.setDefaultTextColor(QColor(0, 0, 0))
        font = QFont("Consolas", 9)
        self.setFont(font) 
        self.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignCenter))

        self.setPosition()

    def update_fact(self):
        self.index = (self.index + 1) % len(self.facts)
        fact = self.facts[self.index].strip()
        self.setPlainText(fact)
        self.setPosition()
        
    def setPosition(self):
        pad = 20
        size = 100
        w = self.width - size - pad
        self.setTextWidth(w*0.9)

        text_rect = self.boundingRect()
        x = (w - text_rect.width())/2 + pad
        y = self.height - text_rect.height()/2 - pad - size/2
        self.setPos(x, y)

class RoundedRect(QGraphicsRectItem):
    def __init__(self, x, y, w, h, radius=12, action=None, text=""):
        super().__init__(x, y, w, h)
        self._radius = radius
        self._action = action
        self._text = text

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), self._radius, self._radius)
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)

    def mousePressEvent(self, event):
        if self._action:
            self._action()
        return super().mousePressEvent(event)