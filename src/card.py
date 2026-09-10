from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QPointF, QPropertyAnimation, QEasingCurve
from .animator import ItemAnimator
from .containers import Tableau

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
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

        self._animation = anim
        self.setZValue(self.Z_Value)

    def setDragEnabled(self, draggable: bool):
        self._drag_enabled = draggable

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
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
        if event.button() != Qt.MouseButton.LeftButton:
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