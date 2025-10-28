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
from PyQt5.QtWidgets import QPushButton

"""
To Do List:
- Cards in a stack can be taken out into the foundation
- Cards are not picked up as a group from tableau
- Dragging cards does not have a function
- Animation
- Sound effects
- Win detection
- Fun Facts
- waste shows more cards
"""


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

        self.Z_Value = 0
        self.State = "faceup"  # or "facedown"
        self.Index = 0
        self.position = QPointF(0, 0)
        self.container = None

        self._dragging = False
        self._last_scene_pos = QPointF()

        self.updateState()
        self.updatePlace()

    def updateState(self):
        if self.State == "faceup":
            self.setPixmap(self.image)
            self._drag_enabled = True
        else:
            self.setPixmap(self.backside)
            self._drag_enabled = False

    def validMove(self, destination=None) -> bool:
        if self.container is not None:
            self.container.validateMove(self, destination)
            return True
        return False

    def updatePlace(self):
        self.setPos(self.position)
        self.setZValue(self.Z_Value)

    def setDragEnabled(self, draggable: bool):
        self._drag_enabled = draggable

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self._dragging = getattr(self, "_drag_enabled", True)
        if self._dragging:
            self._last_scene_pos = event.scenePos()
            self.grabMouse()
            self.setZValue(100)
        else:
            pass

    def mouseMoveEvent(self, event):
        if self._dragging:
            new_scene_pos = event.scenePos()
            delta = new_scene_pos - self._last_scene_pos
            self.setPos(self.pos() + delta)
            self._last_scene_pos = new_scene_pos

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if self._dragging:
            self._dragging = False
            self.ungrabMouse()
        else:
            pass

        self.setZValue(self.Z_Value)
        self.validMove()
        self.updatePlace()

    def __str__(self):
        return f"Card: {self.value} of {self.symbol}"

    def __repr__(self):
        return f"Card({self.value}, {self.symbol}, {self.State})"

class CardContainer:
    def __init__(self, startPos: QPointF, parent):
        self.startpos = startPos
        self.x_offset = 0
        self.y_offset = 0
        self.parent = parent
        self.cards = [[]]
    
    def addCard(self, card: Card, faceup=True, index: int=0):
        self.cards[index].append(card)
        card.Z_Value = len(self.cards[index])
        card.State = "faceup" if faceup else "facedown"
        card.position = self.cardPosition(index)
        card.container = self
        card.Index = index
        card.updatePlace()
        card.updateState()

    def removeCard(self, card: Card):
        index = card.Index
        if card in self.cards[index]:
            self.cards[index].remove(card)
            card.container = None

    def cardPosition(self, index: int=0) -> QPointF:
        x = self.startpos.x() + index * self.x_offset
        y = self.startpos.y() + (len(self.cards[index])-1) * self.y_offset
        return QPointF(x, y)
        
    def validateMove(self, card: Card, destination=None) -> bool:
        self.parent.CheckAutomaticMoves(card)
        if self.parent.CheckWin():
            print("Congratulations! You've won the game.")
        return True

    def reset(self):
        self.cards = [[]]

class Foundation(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = C_WIDTH + 10
        self.y_offset = 0
        self.cards = [[] for _ in range(4)]
        self.bgCards()
        
    def bgCards(self):
        imageAS = self.parent.svg.getSVG("AS", (C_WIDTH, C_HEIGHT))
        imageAH = self.parent.svg.getSVG("AH", (C_WIDTH, C_HEIGHT))
        imageAD = self.parent.svg.getSVG("AD", (C_WIDTH, C_HEIGHT))
        imageAC = self.parent.svg.getSVG("AC", (C_WIDTH, C_HEIGHT))
        imagelist = [imageAS, imageAH, imageAD, imageAC]
        for i, image in enumerate(imagelist):
            bgcard = QGraphicsPixmapItem()
            bgcard.setPixmap(image)
            bgcard.setPos(self.startpos.x() + i * self.x_offset, self.startpos.y())
            bgcard.setOpacity(0.5)
            self.parent.scene.addItem(bgcard)

    def reset(self):
        self.cards = [[] for _ in range(4)]

class Tableau(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = C_WIDTH + 10
        self.y_offset = C_HEIGHT / 6
        self.cards = [[] for _ in range(7)]

    def validateMove(self, card, destination=None):
        if card.State == "facedown":
            return False
        super().validateMove(card, destination)
        return True
    
    def removeCard(self, card: Card):
        index = card.Index
        if card in self.cards[index]:
            self.cards[index].remove(card)
            card.container = None
        else:
            Warning.print(card.__repr__(), "not in", self.cards[index])


        if self.cards[index]:
            self.cards[index][-1].State = "faceup"
            self.cards[index][-1].updateState()

    def reset(self):
        self.cards = [[] for _ in range(7)]

class Stock(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = 0
        self.y_offset = 0
        self.reloadCard()
        
    def reloadCard(self):
        imageReload = self.parent.svg.getSVG("reloadCard", (C_WIDTH, C_HEIGHT))
        bgcard = QGraphicsPixmapItem()
        bgcard.setPixmap(imageReload)
        bgcard.setPos(self.startpos.x(), self.startpos.y())
        bgcard.setOpacity(0.7)
        bgcard.mousePressEvent = self.reload
        self.parent.scene.addItem(bgcard)

    def reload(self, event):
        while self.parent.Waste.cards[0]:
            card = self.parent.Waste.cards[0].pop()
            self.addCard(card, faceup=False)

    def validateMove(self, card, destination=None):
        self.cards[0].remove(card)
        self.parent.Waste.addCard(card, faceup=True)

class Waste(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = C_WIDTH / 4
        self.y_offset = 0


class WinScreen(QWidget):    
    def __init__(self, parent=None, monitor=None):
        super().__init__()
        self.setWindowTitle("Win!")
        WinWidth = 400
        WinHeight = 200
        self.parent = parent
        self.x = int((monitor.width - WinWidth) / 2)
        self.y = int((monitor.height - WinHeight) / 2)
        self.setGeometry(self.x, self.y, WinWidth, WinHeight)

        self.label = QLabel("Congratulations! You've won the game!", self)
        self.label.setGeometry(0, 30, WinWidth, 40)
        self.label.setAlignment(Qt.AlignCenter)
        button = QPushButton("Restart", self)
        button.setFixedSize(140, 40)
        button.move((self.width() - button.width()) // 2, ((self.height() - button.height()) // 2) + 10)
        button.clicked.connect(self.restart)

    def restart(self):
        self.parent.ShuffleCards()
        self.hide()

    def popUp(self):
        self.move(self.x, self.y)
        self.show()

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

        self.WinWindow = WinScreen(self, self.monitor)

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

        background = QPixmap(self.path + r"\images\bg1.png")
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.WindowWidth, self.WindowHeight)
        self.scene.setBackgroundBrush(QBrush(background))
        self.setScene(self.scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        rsSize = 100
        rsPad = 20
        RestartImage = self.svg.getSVG("reload", (rsSize, rsSize))
        RestartButton = QGraphicsPixmapItem()
        RestartButton.setPixmap(RestartImage)
        RestartButton.setPos(self.WindowWidth - rsSize - rsPad, self.WindowHeight - rsSize - rsPad)
        RestartButton.setOpacity(1)
        path = QPainterPath()
        path.addRect(RestartButton.boundingRect())
        RestartButton.shape = lambda : path
        RestartButton.mousePressEvent = lambda event: self.ShuffleCards()
        self.scene.addItem(RestartButton)

    def initCards(self):
        self.all_cards = []

        suits = ["Spades", "Hearts", "Diamonds", "Clubs"]
        self.oppositeSuits = {"Spades": ["Hearts", "Diamonds"],
                              "Hearts": ["Spades", "Clubs"],
                              "Diamonds": ["Spades", "Clubs"],
                              "Clubs": ["Hearts", "Diamonds"]}
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.Foundation = Foundation(QPointF(50, 50), self)
        self.Tableau = Tableau(QPointF(50, C_HEIGHT+100), self)
        self.Stock = Stock(QPointF(self.WindowWidth - C_WIDTH - 50, 50), self)
        self.Waste = Waste(QPointF(self.WindowWidth - C_WIDTH*2 - 100, 50), self)

        backside = self.svg.getSVG("backside", (C_WIDTH, C_HEIGHT))
        for i, suit in enumerate(suits):
            for rank_numb, rank in enumerate(ranks):
                card_image = self.svg.getSVG(f"{rank}{suit[0]}", (C_WIDTH, C_HEIGHT))
                card = Card(rank_numb+1, suit, card_image, backside, self)
                self.scene.addItem(card)
                self.all_cards.append(card)

        self.ShuffleCards()

    def ShuffleCards(self):
        for container in [self.Foundation, self.Tableau, self.Stock, self.Waste]:
            container.reset()
        random.shuffle(self.all_cards)
        for i in range(24):
            self.Stock.addCard(self.all_cards[i], faceup=False)
        n = 24
        for i in range(7):
            for j in range(i+1):
                faceup = (i == j)
                self.Tableau.addCard(self.all_cards[n], faceup=faceup, index=i)
                n += 1

    def CheckWin(self):
        for stack in self.Foundation.cards:
            if len(stack) != 13:
                return False
        self.WinWindow.popUp()
        return True

    def CheckAutomaticMoves(self, card: Card):
        value = card.value
        symbol = card.symbol
        FoundationList = ["Spades", "Hearts", "Diamonds", "Clubs"]
        for i, Stack in enumerate(self.Foundation.cards):
            if card.container == self.Tableau:
                if self.Tableau.cards[card.Index][-1] != card:
                    break
            if Stack:
                top_card = Stack[-1]
                if top_card.value == value - 1 and top_card.symbol == symbol:
                    card.container.removeCard(card)
                    self.Foundation.addCard(card, faceup=True, index=i)
                    return True
            else:
                if value == 1 and symbol == FoundationList[i]:
                    card.container.removeCard(card)
                    self.Foundation.addCard(card, faceup=True, index=i)
                    return True
        for i, Stack in enumerate(self.Tableau.cards):
            if Stack:
                top_card = Stack[-1]
                if not(top_card.value - 1 == value and top_card.symbol in self.oppositeSuits[symbol]):
                    continue
            else:
                if value != 13:
                    continue
            cardgroup = []
            if card.container == self.Tableau:
                for c in self.Tableau.cards[card.Index][::-1]:
                    if c == card:
                        break
                    cardgroup.append(c)
            cardgroup.append(card)
            cardgroup = cardgroup[::-1]
            for c in cardgroup:
                c.container.removeCard(c)
                self.Tableau.addCard(c, faceup=True, index=i)
            return True
        return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())

    