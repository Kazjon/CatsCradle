from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from MatrixUtil import *
from Marionette import *
from ReferenceSpace import *

class EyeOpenGL:
    def __init__(self):
        display = (650, 250)
        aspect = display[0] / display[1]
        gluPerspective(45, aspect, 0.1, 50.0)

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        zoom = 0.005
        glScale(zoom, zoom * aspect, zoom)
        # Matrix to apply to the marionette points to get them in view space:
        # xView = Right
        # yView = Up
        # zView = Front
        glRotatef(-90, 1, 0, 0)
        glRotatef(-90, 0, 0, 1)

    def drawPoint(self, radius, p):
        glPointSize(radius * 100)
        glBegin(GL_POINTS)
        glVertex3fv(tuple(p))
        glEnd()

    def drawLine(self, lineWidth, p1, p2):
        glLineWidth(lineWidth)
        glBegin(GL_LINES)
        glVertex3fv(tuple(p1))
        glVertex3fv(tuple(p2))
        glEnd()

    def drawSolidSphere(self, radius, center):
        glPushMatrix()
        glTranslatef(center[0], center[1], center[2])
        glutSolidSphere(radius * 100, 50, 50)
        glPopMatrix()

    def drawWireSphere(self, radius, center):
        glPushMatrix()
        glTranslatef(center[0], center[1], center[2])
        glutWireSphere(radius * 100, 50, 50)
        glPopMatrix()

    def drawWorldRef(self, size):
        glColor3f(1.0, 1.0, 1.0)
        origin = (0, 0, 0)
        x = (size, 0, 0)
        y = (0, size, 0)
        z = (0, 0, size)
        self.drawLine(1, origin, x)
        self.drawLine(1, origin, y)
        self.drawLine(1, origin, z)

    def drawEye(self, pos, angleY, angleZ):
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glRotatef(angleZ, 0, 0, 1)
        glRotatef(angleY, 0, 1, 0)

        # Draw white sphere
        glColor3f(1.0, 1.0, 1.0)
        self.drawSolidSphere(0.5, (0, 0, 0))

        # Draw blue pupil
        glColor3f(0.0, 0.0, 0.0) # Black
        self.drawSolidSphere(0.2, (50, 0, 0))

        glPopMatrix()

    def draw(self, marionette):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        # World Reference
        glColor3f(1.0, 1.0, 1.0)
        self.drawWorldRef(10)

        eye = marionette.eye['ER']
        distanceBetweenEyes = marionette.eyeOffset['EL'][1] - marionette.eyeOffset['ER'][1]
        self.drawEye((0, -distanceBetweenEyes, 0), eye.angleY, eye.angleZ)
        self.drawEye((0, distanceBetweenEyes, 0), eye.angleY, eye.angleZ)


if __name__ == '__main__':
    marionette = Marionette()

    import pygame
    from pygame.locals import *

    pygame.init()
    display = (650, 250)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

    eyeOpenGL = EyeOpenGL()
    angleZ = 0
    angleY = 0
    incrementZ = 1
    incrementY = 2

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Move eyes continously
        angleZ = angleZ + incrementZ
        angleY = angleY + incrementY
        if abs(angleY) > 19:
            incrementY = -incrementY
        if abs(angleZ) > 19:
            incrementZ = -incrementZ

        marionette.eye['ER'].angleZ = angleZ
        marionette.eye['ER'].angleY = angleY
        #glRotatef(1, 0, 0, 1)

        glPushMatrix()
        # Angles the marionette 45 degrees around z axis
        # glRotatef(45, 0, 0, 1)
        eyeOpenGL.draw(marionette)
        glPopMatrix()

        pygame.display.flip()
        pygame.time.wait(10)
