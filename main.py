from PyQt5.QtWidgets import QWidget, QApplication, QSystemTrayIcon, QMenu, QAction, QToolBar
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPixmap, QFontMetrics, QIcon, QTransform, QPainterPath, QPalette, QBrush
from PyQt5.QtCore import QRectF, Qt, QPointF, QPoint
from PyQt5.QtCore import QTimer, QElapsedTimer, QRect, QUrl
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem
from screeninfo import get_monitors
import sys
import math
import os
import random
import pprint
import copy
import csv
from SVGManager import SVGManager

C_WIDTH = 25 * 6
C_HEIGHT = 35 * 6

class Card(QGraphicsPixmapItem):
    def __init__(self, value: int, symbol: str, image: QPixmap, backside: QPixmap, parent=None):
        super().__init__()
        self.image = image
        self.backside = backside
        self.value = value
        self.symbol = symbol
        self.parent = parent

        self.setFlag(QGraphicsPixmapItem.ItemIsMovable, True)

        self.Z_Value = 0
        self.State = "faceup"  # or "facedown"
        self.Place = "Tableau"    # "Foundation", "Tableau", "Stock", "Waste"
        self.position = QPointF(0, 0)
        self.updateState()
        self.updatePlace()
        
    def updateState(self):
        if self.State == "faceup":
            self.setPixmap(self.image)
        else:
            self.setPixmap(self.backside)

    def updatePlace(self):
        self.setPos(self.position)
        self.setZValue(self.Z_Value)
        if self.State == "faceup":
            if self.Place == "Foundation":
                self.Z_Value = self.value
            elif self.Place == "Tableau":
                pass

    def mousePressEvent(self, event):
        self.setZValue(100)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setZValue(self.Z_Value)
        self.updatePlace()
        super().mouseReleaseEvent(event)

    def __str__(self):
        return f"Card: {self.value} of {self.symbol}"

    def __repr__(self):
        return f"Card: {self.value} of {self.symbol}"
        #return f"Card: {self.value} of {self.symbol}, State: {self.State}, Place: {self.Place}"

class CardContainer:
    def __init__(self, startPos: QPointF, parent):
        self.startpos = startPos
        self.x_offset = 0
        self.y_offset = 0
        self.cards = [[]]
    
    def addCard(self, card: Card, faceup=True, index: int=0):
        self.cards[index].append(card)
        card.Z_Value = len(self.cards[index])
        card.State = "faceup" if faceup else "facedown"
        card.position = self.cardPosition(index)
        card.updatePlace()
        card.updateState()

    def cardPosition(self, index: int=0) -> QPointF:
        x = self.startpos.x() + index * self.x_offset
        y = self.startpos.y() + (len(self.cards[index])-1) * self.y_offset
        return QPointF(x, y)
        

class Foundation(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = C_WIDTH + 10
        self.y_offset = 0
        self.cards = [[] for _ in range(4)]
class Tableau(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = C_WIDTH + 10
        self.y_offset = C_HEIGHT / 6
        self.cards = [[] for _ in range(7)]
class Stock(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = 0
        self.y_offset = 0
class Waste(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = C_WIDTH / 4
        self.y_offset = 0


class MainWindow(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initScene()
        self.initCards()

    def initUI(self):
        self.monitor = get_monitors()[0]
        self.setMouseTracking(True)
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWindowTitle("Premium Solitaire")

        self.path = os.path.dirname(os.path.abspath(__file__))

        self.svg = SVGManager()
        image = self.svg.getSVG("win_icon_black", (128, 128))
        icon = QIcon(image)
        self.setWindowIcon(icon)

        self.WindowWidth = int(self.monitor.width*0.7)
        self.WindowHeight = int(self.monitor.height*0.7)
        self.center = QPoint(int(self.monitor.width/2), int(self.monitor.height/2))
        self.topleft = QPoint((self.center.x() - int(self.WindowWidth/2)), (self.center.y() - int(self.WindowHeight/2)))
        self.setGeometry(self.topleft.x(), self.topleft.y(), self.WindowWidth, self.WindowHeight)
        self.setFixedSize(self.WindowWidth, self.WindowHeight)

    def initScene(self):
        background = QPixmap(self.path + r"\images\bg1.png")
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.WindowWidth, self.WindowHeight)
        self.scene.setBackgroundBrush(QBrush(background))
        self.setScene(self.scene)

    def initCards(self):
        background = QPixmap(self.path + r"\images\bg1.png")

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.WindowWidth, self.WindowHeight)
        self.scene.setBackgroundBrush(QBrush(background))
        self.setScene(self.scene)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        suits = ["spades", "hearts", "diamonds", "clubs"]
        self.Foundation = Foundation(QPointF(50, 50), self)
        self.Tableau = Tableau(QPointF(50, C_HEIGHT+100), self)
        self.Stock = Stock(QPointF(self.WindowWidth - C_WIDTH - 50, 50), self)
        self.Waste = Waste(QPointF(self.WindowWidth - C_WIDTH*2 - 100, 50), self)

        KingImg = self.svg.getSVG("KingWhite", (C_WIDTH, C_HEIGHT))
        backside = self.svg.getSVG("backside", (C_WIDTH, C_HEIGHT))
        for i, suit in enumerate(suits):
            for rank in range(1, 14):
                image_path = f"{self.path}/images/cards/{rank}_of_{suit}.png"
                card = Card(rank, suit, KingImg, backside, self)
                self.scene.addItem(card)

        self.ShuffleCards()


    def ShuffleCards(self):
        all_cards = self.scene.items()
        random.shuffle(all_cards)
        for i in range(24):
            self.Stock.addCard(all_cards[i], faceup=False)
        n = 24
        for i in range(7):
            for j in range(i+1):
                faceup = (i == j)
                self.Tableau.addCard(all_cards[n], faceup=faceup, index=i)
                n += 1

if __name__ == "__main__":    
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())

    