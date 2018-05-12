import sys

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPoint
from PyQt5.QtOpenGL import *

from OpenGL.GL import *
from OpenGL.GLU import *

class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ImageWidget()
    sys.exit(app.exec_())
