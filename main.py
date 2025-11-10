from PyQt5.QtWidgets import (QWidget, QApplication, QLabel, QGraphicsView, QGraphicsScene, \
                            QGraphicsRectItem, QGraphicsPixmapItem, QPushButton, QGraphicsTextItem)
from PyQt5.QtGui import (QPainter, QColor, QPen, QFont, QPixmap, QFontMetrics, QIcon, \
                        QTextOption, QPainterPath, QBrush)
from PyQt5.QtCore import (Qt, QPointF, QPoint, QObject, QTimer, QTime, QPropertyAnimation, \
                        QEasingCurve, QEventLoop, pyqtProperty)
from screeninfo import get_monitors
import sys
import math
import os
import random
from SVGManager import SVGManager

"""
To Do List:
- Sound effects
- scoring
- undo/redo
"""


C_WIDTH = 25 * 6
C_HEIGHT = 35 * 6
PAD = 30


class ItemAnimator(QObject):
    """A QObject that exposes a QGraphicsItem's position as an animatable property."""
    def __init__(self, item):
        super().__init__()
        self.item = item

    def getPos(self):
        return self.item.pos()

    def setPos(self, pos):
        self.item.setPos(pos)

    pos = pyqtProperty(QPointF, fget=getPos, fset=setPos)

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
        self.Stacklist = []
        self.container = None

        self._dragging = False
        self.Drag = False
        self._last_scene_pos = QPointF()
        self.start_pos = QPointF()
        self.drag_threshold = 20  # Minimum distance in pixels to start a drag
        self._animation = None

        self.updateState()
        self.setPos(self.position)
        self.setZValue(self.Z_Value)

    def updateState(self):
        if self.State == "faceup":
            self.setPixmap(self.image)
            self._drag_enabled = True
        else:
            self.setPixmap(self.backside)
            self._drag_enabled = False

    def validMove(self, destination=None) -> bool:
        if self.container is not None:
            if self.container.validateMove(self, destination):
                self.parent.Clock.start()
            return True
        return False

    def updatePlace(self, duration=300):
        """Smoothly move the card to its target position."""
        if duration <= 0:
            self.setPos(self.position)
            self.setZValue(self.Z_Value)
            return

        # Create or reuse the animator
        if not hasattr(self, "_animator"):
            self._animator = ItemAnimator(self)

        # Stop any old animation
        if hasattr(self, "_animation") and self._animation is not None:
            self._animation.stop()

        # Animate via the QObject wrapper
        anim = QPropertyAnimation(self._animator, b'pos')
        anim.setDuration(duration)
        anim.setStartValue(self.pos())
        anim.setEndValue(self.position)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

        self._animation = anim
        self.setZValue(self.Z_Value)

    def setDragEnabled(self, draggable: bool):
        self._drag_enabled = draggable

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self._dragging = getattr(self, "_drag_enabled", True)
        if self._dragging:
            self.Drag = False
            self._last_scene_pos = event.scenePos()
            self.start_pos = event.scenePos()
            self.grabMouse()
            self.Stacklist = []
            if isinstance(self.container, Tableau):
                for c in self.container.cards[self.Index][::-1]:
                    if c == self:
                        break
                    self.Stacklist.append(c)
            self.Stacklist.append(self)
            self.Stacklist = self.Stacklist[::-1]
            for c in self.Stacklist:
                c.setZValue(100 + c.Z_Value)
        else:
            pass

    def mouseMoveEvent(self, event):
        if self._dragging:
            if (event.scenePos() - self.start_pos).manhattanLength() > self.drag_threshold:
                self.Drag = True
            new_scene_pos = event.scenePos()
            delta = new_scene_pos - self._last_scene_pos
            self.moveStack(delta)
            self._last_scene_pos = new_scene_pos

    def moveStack(self, delta: QPointF):
        for c in self.Stacklist:
            c.setPos(c.pos() + delta)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        destination_card = None
        if self.Drag:
            mousepos = event.scenePos()
            destination_card = self.parent.releaseCard(self, mousepos)
            print("Dragged", self)
        else:
            pass
        self._dragging = False
        self.Drag = False
        self.ungrabMouse()

        for c in self.container.cards[self.Index]:
            c.setZValue(c.Z_Value)
        if destination_card != -1:
            self.validMove(destination_card)
        for c in self.Stacklist:
            c.updatePlace()
        self.Stacklist = []

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
        moved = False
        if destination is None:
            moved = self.parent.CheckAutomaticMoves(card)
        else:
            moved = self.parent.CheckMove(card, destination)
        self.parent.CheckAutoComplete()
        if self.parent.CheckWin():
            return False
        return moved

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
            self.parent.foundationcards.append(bgcard)
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
        return super().validateMove(card, destination)
    
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
        self.parent.Waste.addCard(card)
        self.parent.Waste.updateOrder()
        return True

class Waste(CardContainer):
    def __init__(self, startPos: QPointF, parent):
        super().__init__(startPos, parent)
        self.x_offset = -(C_WIDTH / 4)
        self.y_offset = 0
        self.cards = [[]]

    def updateOrder(self):
        for i, card in enumerate(self.cards[0][::-1]):
            card.Z_Value = len(self.cards[0]) - i
            card.position = self.cardPosition(min(i, 2))
            card._drag_enabled = False if i != 0 else True
            card.updatePlace()

    def cardPosition(self, index: int=0) -> QPointF:
        x = self.startpos.x() + index * self.x_offset
        y = self.startpos.y()
        return QPointF(x, y)

    def removeCard(self, card):
        super().removeCard(card)
        self.updateOrder()

    def reset(self):
        self.cards = [[]]


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
        self.label.setAlignment(Qt.AlignCenter)
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
    def __init__(self, width: int=0, height: int=0, parent=None):
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
        y = PAD/2
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
        self.document().setDefaultTextOption(QTextOption(Qt.AlignCenter))

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
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.rect(), self._radius, self._radius)
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)

    def mousePressEvent(self, event):
        if self._action:
            self._action()
        return super().mousePressEvent(event)


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

        self.WindowWidth = int(self.monitor.width*0.7)
        self.WindowHeight = int(self.monitor.height*0.7)
        self.center = QPoint(int(self.monitor.width/2), int(self.monitor.height/2))
        self.topleft = QPoint((self.center.x() - int(self.WindowWidth/2)), (self.center.y() - int(self.WindowHeight/2)))
        self.setGeometry(self.topleft.x(), self.topleft.y(), self.WindowWidth, self.WindowHeight)
        self.setFixedSize(self.WindowWidth, self.WindowHeight)

        self.path = os.path.dirname(os.path.abspath(__file__))

        self.svg = SVGManager()
        image = self.svg.getSVG("win_icon_black", (128, 128))
        icon = QIcon(image)
        self.setWindowIcon(icon)

        self.WinWindow = WinScreen(self, self.monitor)
        self.Clock = Clock(self.WindowWidth, self.WindowHeight, self)
        self.FunFact = FunFacts(self.WindowWidth, self.WindowHeight)

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

        self.foundationcards = []
        self.basecards = []
        for i in range(7):
            rect = QGraphicsRectItem(0, 0, C_WIDTH, C_HEIGHT)
            rect.setPos(50 + i * (C_WIDTH + 10), C_HEIGHT + 100)
            rect.setBrush(QColor(255, 255, 255, 0))
            rect.setPen(QPen(Qt.NoPen))
            self.basecards.append(rect)
            self.scene.addItem(rect)

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

        FunFactBG = RoundedRect(rsPad, self.WindowHeight - rsSize - rsPad, self.WindowWidth - rsSize - rsPad*3, rsSize, radius=12, action=self.FunFact.update_fact)
        color = "#FBF0DF"
        FunFactBG.setBrush(QColor(color))
        FunFactBG.setPen(QPen(Qt.NoPen))
        self.scene.addItem(FunFactBG)

        pad = 5
        x, y = self.Clock.pos().x()-pad, self.Clock.pos().y()
        w, h = self.Clock.text_width+pad*3, self.Clock.text_height+pad*2
        ClockBG = RoundedRect(x, y, w, h, radius=12)
        color = "#00392B"
        ClockBG.setBrush(QColor(color))
        ClockBG.setPen(QPen(Qt.NoPen))
        self.scene.addItem(ClockBG)

        w, h = self.Clock.text_width+pad*3, self.Clock.text_height+pad*2
        x, y = self.Clock.pos().x()-pad, self.Clock.pos().y() + h + pad*2
        self.Autocompletable = False
        self.AutoCompleteBtn = RoundedRect(x, y, w, h, radius=12, action=self.AutoComplete, text="Press to\nAuto Complete")
        color = "#000000"
        self.AutoCompleteBtn.setBrush(QColor(color))
        self.AutoCompleteBtn.setPen(QPen(Qt.NoPen))
        self.AutoCompleteBtn.hide()
        self.scene.addItem(self.AutoCompleteBtn)

        self.scene.addItem(RestartButton)
        self.scene.addItem(self.Clock)
        self.scene.addItem(self.FunFact)

    def initCards(self):
        self.all_cards = []

        self.suits = ["Spades", "Hearts", "Diamonds", "Clubs"]
        self.oppositeSuits = {"Spades": ["Hearts", "Diamonds"],
                              "Hearts": ["Spades", "Clubs"],
                              "Diamonds": ["Spades", "Clubs"],
                              "Clubs": ["Hearts", "Diamonds"]}
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.Foundation = Foundation(QPointF(PAD, PAD), self)
        self.Tableau = Tableau(QPointF(PAD, C_HEIGHT+PAD*2), self)
        self.Stock = Stock(QPointF(self.WindowWidth - C_WIDTH - PAD, PAD), self)
        self.Waste = Waste(QPointF(self.WindowWidth - C_WIDTH*2 - PAD*2, PAD), self)

        backside = self.svg.getSVG("backside", (C_WIDTH, C_HEIGHT))
        for i, suit in enumerate(self.suits):
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
        removes = 0
        n = 24+(7*removes-(sum(range(0, removes))))
        for i in range(n):
            self.Stock.addCard(self.all_cards[i], faceup=False)
        for i in range(7-removes):
            for j in range(i+1):
                faceup = (i == j)
                self.Tableau.addCard(self.all_cards[n], faceup=faceup, index=i)
                n += 1
        self.Clock.reset()

    def CheckWin(self):
        for stack in self.Foundation.cards:
            if len(stack) != 13:
                return False
        self.WinWindow.popUp(self.pos(), self.WindowWidth, self.WindowHeight)
        self.Clock.stop()
        return True

    def CheckAutoComplete(self):
        for card in self.all_cards:
            if card.State == "facedown" and card.container == self.Tableau:
                self.Autocompletable = False
                return False
        self.AutoCompleteBtn.show()
        self.Autocompletable = True

    def AutoComplete(self):
        if not self.Autocompletable:
            return
        Run = True
        self.AutoCompleteBtn.hide()
        topfountain = []
        self.Clock.start()
        for stack in self.Foundation.cards:
            if stack:
                topfountain.append(stack[-1].value)
            else:
                topfountain.append(0)
        while Run:
            Run = False
            toptableau = []
            for stack in self.Tableau.cards:
                if stack:
                    toptableau.append(stack[-1])
            for card in self.Waste.cards[0] + toptableau + self.Stock.cards[0]:
                if card.container != self.Foundation:
                    symbol_index = self.suits.index(card.symbol)
                    if card.value == topfountain[symbol_index] + 1:
                        card.container.removeCard(card)
                        self.Foundation.addCard(card, faceup=True, index=symbol_index)
                        topfountain[symbol_index] += 1
                        Run = True
                        break
            QApplication.processEvents()
            _loop = QEventLoop()
            QTimer.singleShot(100, _loop.quit)  # 100 ms delay (adjust as needed)
            _loop.exec_()
            QApplication.processEvents()

        self.Autocompletable = False
        self.CheckWin()

    def CheckAutomaticMoves(self, card: Card):
        value = card.value
        symbol = card.symbol
        FoundationList = ["Spades", "Hearts", "Diamonds", "Clubs"]
        if card.container == self.Waste and card.container.cards[0][-1] != card:
            return False
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

    def CheckMove(self, card: Card, destination: Card=None) -> bool:
        value = card.value
        symbol = card.symbol
        index = 0
        if isinstance(destination, Card):
            if destination.container == self.Foundation:
                if card.container == self.Tableau:
                    if self.Tableau.cards[card.Index][-1] != card:
                        return False
                if destination.value == value - 1 and destination.symbol == symbol:
                    card.container.removeCard(card)
                    self.Foundation.addCard(card, faceup=True, index=destination.Index)
                    return True
                return False
            elif destination.container == self.Tableau:
                if destination.value - 1 == value and destination.symbol in self.oppositeSuits[symbol]:
                    index = destination.Index
                else:
                    return False
        elif destination in range(7) and value == 13 and self.Tableau.cards[destination] == []:
            index = destination
        elif destination in range(10, 14):
            dest_index = destination - 10
            if card.container == self.Tableau:
                if self.Tableau.cards[card.Index][-1] != card:
                    return False
            if value == 1 and card.symbol == ["Spades", "Hearts", "Diamonds", "Clubs"][dest_index]:
                card.container.removeCard(card)
                self.Foundation.addCard(card, faceup=True, index=dest_index)
                return True
            return False
        else:
            return False
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
            self.Tableau.addCard(c, faceup=True, index=index)
        return True
            
    def releaseCard(self, dragcard: Card, mousepos: QPointF=None):
        items = self.scene.items(mousepos)
        for item in items:
            if item in self.basecards:
                return self.basecards.index(item)
            if item in self.foundationcards:
                return self.foundationcards.index(item) + 10
            if isinstance(item, Card) and item != dragcard and item == item.container.cards[item.Index][-1] \
                and item.container in [self.Tableau, self.Foundation] and item.State == "faceup":
                return item
        return -1

    def closeEvent(self, a0):
        self.WinWindow.close()
        return super().closeEvent(a0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec_())

    