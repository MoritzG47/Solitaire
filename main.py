from PyQt5.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMenu, QAction, QToolBar
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap, QFontMetrics, QIcon, QTransform, QPainterPath, QPalette, QBrush
from PyQt5.QtCore import QRectF, Qt, QPointF, QPoint
from PyQt5.QtCore import QTimer, QElapsedTimer, QRect, QUrl
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
from screeninfo import get_monitors
import sys
import math
import os
import pprint
import copy
import csv
from SVGManager import SVGManager

class Card(QGraphicsRectItem):
    def __init__(self, x, y, w=100, h=150, text="A♠"):
        super().__init__(0, 0, w, h)
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setPos(x, y)
        self.text = text

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setFont(QFont("Arial", 24))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

class MainWindow(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initCards()

    def initUI(self):
        self.monitor = get_monitors()[0]
        self.setMouseTracking(True)
        self.setWindowTitle("Premium Solitaire")

        self.path = os.path.dirname(os.path.abspath(__file__))

        self.svg = SVGManager()
        image = self.svg.getSVG("win_icon_black", (128, 128))
        icon = QIcon(image)
        self.setWindowIcon(icon)

        self.WindowWidth = int(self.monitor.width*0.6)
        self.WindowHeight = int(self.monitor.height*0.6)
        self.center = QPoint(int(self.monitor.width/2), int(self.monitor.height/2))
        self.topleft = QPoint((self.center.x() - int(self.WindowWidth/2)), (self.center.y() - int(self.WindowHeight/2)))
        self.setGeometry(self.topleft.x(), self.topleft.y(), self.WindowWidth, self.WindowHeight)

        background = QPixmap(self.path + r"\images\bg1.png")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(background))
        self.setPalette(palette)

    def initCards(self):
        # Scene setup
        scene = QGraphicsScene(self)
        scene.setSceneRect(0, 0, 800, 600)
        self.setScene(scene)
        # Create many cards
        suits = ["♠", "♥", "♦", "♣"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        x, y = 50, 50

        for i, suit in enumerate(suits):
            for j, rank in enumerate(ranks):
                card = Card(x + j * 15, y + i * 25, text=f"{rank}{suit}")
                scene.addItem(card)

        self.setScene(scene)
        self.resize(900, 700)
        #scale = 5
        #King_image = self.svg.getSVG("KingWhite", (25*scale, 35*scale))
        #self.KingCard = Card(King_image, "KH")

if __name__ == "__main__":    
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())

    