import os
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt

class SVGManager:
    def __init__(self):
        self.svgs = {}
        self.cache = {}
        ownpath = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(ownpath, "images_svg")
        for svg in os.listdir(path):
            if svg.endswith(".svg"):
                name = os.path.splitext(svg)[0]
                self.loadSVG(name, os.path.join(path, svg))

    def loadSVG(self, name, path):
        renderer = QSvgRenderer(path)
        self.svgs[name] = renderer

    def getSVG(self, name: str, size: tuple) -> QPixmap:
        key = (name, size)
        if key in self.cache:
            return self.cache[key]

        if name in self.svgs:
            image = QPixmap(size[0], size[1])
            image.fill(Qt.transparent)
            self.svgs[name].render(QPainter(image))
            self.cache[key] = image
            return image

        raise ValueError(f"SVG '{name}' not found.")

    def shutdown(self):
        self.svgs.clear()
        self.cache.clear()