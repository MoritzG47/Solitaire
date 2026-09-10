from PyQt6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                            QGraphicsRectItem, QGraphicsPixmapItem, QFrame)
from PyQt6.QtGui import (QPainter, QColor, QPen, QPixmap, QIcon, QPainterPath, QBrush)
from PyQt6.QtCore import (Qt, QPointF, QPoint, QTimer, QEventLoop)

from screeninfo import get_monitors
import os
import random
from .SVGManager import SVGManager
from .miscObjects import WinScreen, Clock, FunFacts, RoundedRect
from .card import Card
from .containers import Foundation, Tableau, Stock, Waste

monitor = get_monitors()[0]
scale = 0.0026 * monitor.width
C_WIDTH = int(25 * scale)
C_HEIGHT = int(35 * scale)
PAD = 30

class MainWindow(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.initUI()
        self.initScene()
        self.initCards()

    def initUI(self):
        self.monitor = get_monitors()[0]
        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWindowTitle("Premium Solitaire")

        self.WindowWidth = int(self.monitor.width*0.7)
        self.WindowHeight = int(self.monitor.height*0.7)
        self.center = QPoint(int(self.monitor.width/2), int(self.monitor.height/2))
        self.topleft = QPoint((self.center.x() - int(self.WindowWidth/2)), (self.center.y() - int(self.WindowHeight/2)))
        self.setGeometry(self.topleft.x(), self.topleft.y(), self.WindowWidth, self.WindowHeight)
        self.setFixedSize(self.WindowWidth, self.WindowHeight)

        self.svg = SVGManager()
        image = self.svg.getSVG("win_icon_black", (128, 128))
        icon = QIcon(image)
        self.setWindowIcon(icon)

        self.WinWindow = WinScreen(self, self.monitor)
        self.Clock = Clock(width=self.WindowWidth, height=self.WindowHeight, padding=PAD, parent=self)
        self.FunFact = FunFacts(width=self.WindowWidth, height=self.WindowHeight)

    def initScene(self):
        background = QPixmap(os.path.join("images", "bg1.png"))
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.WindowWidth, self.WindowHeight)
        self.scene.setBackgroundBrush(QBrush(background))
        self.setScene(self.scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.foundationcards = []
        self.basecards = []
        for i in range(7):
            rect = QGraphicsRectItem(0, 0, C_WIDTH, C_HEIGHT)
            rect.setPos(50 + i * (C_WIDTH + 10), C_HEIGHT + 100)
            rect.setBrush(QColor(255, 255, 255, 0))
            rect.setPen(QPen(Qt.PenStyle.NoPen))
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
        FunFactBG.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(FunFactBG)

        pad = 5
        x, y = self.Clock.pos().x()-pad, self.Clock.pos().y()
        w, h = self.Clock.text_width+pad*3, self.Clock.text_height+pad*2
        ClockBG = RoundedRect(x, y, w, h, radius=12)
        color = "#00392B"
        ClockBG.setBrush(QColor(color))
        ClockBG.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(ClockBG)

        w, h = self.Clock.text_width+pad*3, self.Clock.text_height+pad*2
        x, y = self.Clock.pos().x()-pad, self.Clock.pos().y() + h + pad*2
        self.Autocompletable = False
        self.AutoCompleteBtn = RoundedRect(x, y, w, h, radius=12, action=self.AutoComplete, text="Press to\nAuto Complete")
        color = "#000000"
        self.AutoCompleteBtn.setBrush(QColor(color))
        self.AutoCompleteBtn.setPen(QPen(Qt.PenStyle.NoPen))
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
        self.Foundation = Foundation(startPos=QPointF(PAD, PAD),                                  card_width=C_WIDTH, card_height=C_HEIGHT, parent=self)
        self.Tableau = Tableau(      startPos=QPointF(PAD, C_HEIGHT+PAD*2),                       card_width=C_WIDTH, card_height=C_HEIGHT, parent=self)
        self.Stock = Stock(          startPos=QPointF(self.WindowWidth - C_WIDTH - PAD, PAD),     card_width=C_WIDTH, card_height=C_HEIGHT, parent=self)
        self.Waste = Waste(          startPos=QPointF(self.WindowWidth - C_WIDTH*2 - PAD*2, PAD), card_width=C_WIDTH, card_height=C_HEIGHT, parent=self)

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
            _loop.exec()
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