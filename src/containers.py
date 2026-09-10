from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import QPointF
from .baseContainer import CardContainer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .card import Card

class Foundation(CardContainer):
    def __init__(self, startPos: QPointF, card_width: int, card_height: int, parent):
        super().__init__(startPos, parent)
        self.x_offset = card_width + 10
        self.y_offset = 0
        self.cards = [[] for _ in range(4)]
        self.card_width = card_width
        self.card_height = card_height
        self.bgCards()
        
    def bgCards(self):
        imagelist = ["AS", "AH", "AD", "AC"]
        for i, image_name in enumerate(imagelist):
            image = self.parent.svg.getSVG(image_name, (self.card_width, self.card_height))
            bgcard = QGraphicsPixmapItem()
            bgcard.setPixmap(image)
            bgcard.setPos(self.startpos.x() + i * self.x_offset, self.startpos.y())
            bgcard.setOpacity(0.5)
            self.parent.foundationcards.append(bgcard)
            self.parent.scene.addItem(bgcard)

    def reset(self):
        self.cards = [[] for _ in range(4)]

class Tableau(CardContainer):
    def __init__(self, startPos: QPointF, card_width: int, card_height: int, parent):
        super().__init__(startPos, parent)
        self.x_offset = card_width + 10
        self.y_offset = card_height / 6
        self.cards = [[] for _ in range(7)]

    def validateMove(self, card, destination=None):
        if card.State == "facedown":
            return False
        return super().validateMove(card, destination)
    
    def removeCard(self, card: "Card"):
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
    def __init__(self, startPos: QPointF, card_width: int, card_height: int, parent):
        super().__init__(startPos, parent)
        self.x_offset = 0
        self.y_offset = 0
        self.imageReload = self.parent.svg.getSVG("reloadCard", (card_width, card_height))
        self.reloadCard()

    def reloadCard(self):
        bgcard = QGraphicsPixmapItem()
        bgcard.setPixmap(self.imageReload)
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
    def __init__(self, startPos: QPointF, card_width: int, card_height: int, parent):
        super().__init__(startPos, parent)
        self.x_offset = -(card_width / 4)
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