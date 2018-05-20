import sys

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPoint
from PyQt5.QtOpenGL import *

from OpenGL.GL import *
from OpenGL.GLU import *

from MarionetteOpenGL import *

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


class MarionetteWidget(QGLWidget):
    def __init__(self, marionette, parent=None):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(640, 480)
        self.marionetteView = None
        self.marionette = marionette
        self.angleZ = 0
        self.zoom = 1
        self.offsetZ = 0

    def paintGL(self):
        glPushMatrix()
        glRotatef(self.angleZ, 0, 0, 1)
        glScale(self.zoom, self.zoom, self.zoom)
        glTranslatef(0, 0, self.offsetZ)
        self.marionetteView.draw(self.marionette)
        glPopMatrix()

    def initializeGL(self):
        self.marionetteView = MarionetteOpenGL()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ImageWidget()

    widget = MarionetteWidget(Marionette())
    widget.show()

    sys.exit(app.exec_())
