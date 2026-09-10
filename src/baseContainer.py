from PyQt6.QtCore import QPointF
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .card import Card

class CardContainer:
    def __init__(self, startPos: QPointF, parent):
        self.startpos = startPos
        self.x_offset = 0
        self.y_offset = 0
        self.parent = parent
        self.cards = [[]]
    
    def addCard(self, card: "Card", faceup=True, index: int=0):
        self.cards[index].append(card)
        card.Z_Value = len(self.cards[index])
        card.State = "faceup" if faceup else "facedown"
        card.position = self.cardPosition(index)
        card.container = self
        card.Index = index
        card.updatePlace()
        card.updateState()

    def removeCard(self, card: "Card"):
        index = card.Index
        if card in self.cards[index]:
            self.cards[index].remove(card)
            card.container = None

    def cardPosition(self, index: int=0) -> QPointF:
        x = self.startpos.x() + index * self.x_offset
        y = self.startpos.y() + (len(self.cards[index])-1) * self.y_offset
        return QPointF(x, y)
        
    def validateMove(self, card: "Card", destination=None) -> bool:
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