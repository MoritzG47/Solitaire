from PyQt6.QtCore import (QPointF, QObject, pyqtProperty)


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