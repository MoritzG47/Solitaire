import os
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import Qt

class SVGManager:
    def __init__(self):
        self.svgs = {}
        self.cache = {}
        #base_path = os.path.join("..", "images_svg")
        base_path = ("images_svg")
        for svg in os.listdir(base_path):
            if svg.endswith(".svg"):
                name = os.path.splitext(svg)[0]
                self.loadSVG(name, os.path.join(base_path, svg))
        cards_path = os.path.join(base_path, "Cards")
        for folder in os.listdir(cards_path):
            folder_path = os.path.join(cards_path, folder)
            if os.path.isdir(folder_path):
                for svg in os.listdir(folder_path):
                    if svg.endswith(".svg"):
                        name = f"{folder}{os.path.splitext(svg)[0]}"
                        self.loadSVG(name, os.path.join(folder_path, svg))

    def loadSVG(self, name, path):
        renderer = QSvgRenderer(path)
        self.svgs[name] = renderer

    def getSVG(self, name: str, size: tuple) -> QPixmap:
        key = (name, size)
        if key in self.cache:
            return self.cache[key]

        if name in self.svgs:
            image = QPixmap(size[0], size[1])
            image.fill(Qt.GlobalColor.transparent)
            self.svgs[name].render(QPainter(image))
            self.cache[key] = image
            return image

        raise ValueError(f"SVG '{name}' not found.")

    def shutdown(self):
        self.svgs.clear()
        self.cache.clear()