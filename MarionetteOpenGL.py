from OpenGL.GL import *
from OpenGL.GLU import *

from MatrixUtil import *
from Marionette import *
from ReferenceSpace import *

class MarionetteOpenGL:
    def __init__(self):
        display = (650, 650)
        gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        zoom = 0.001
        glScale(zoom, zoom, zoom)
        # Matrix to apply to the marionette points to get them in view space:
        # xView = Right
        # yView = Up
        # zView = Front
        glRotatef(-90, 1, 0, 0)
        glRotatef(-90, 0, 0, 1)
        # Add a slight angular tilt
        glRotatef(-3, 0, 1, 0)
        # Translate to center marionette on view
        glTranslatef(0, 0, 900)

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

    def drawWorldRef(self, size):
        glColor3f(1.0, 1.0, 1.0)
        origin = (0, 0, 0)
        x = (size, 0, 0)
        y = (0, size, 0)
        z = (0, 0, size)
        self.drawLine(1, origin, x)
        self.drawLine(1, origin, y)
        self.drawLine(1, origin, z)

        # Draw transparent ceiling
        glColor4f(1.0, 1.0, 1.0, 0.5)
        glPushMatrix()
        glScale(500, 500, 500)
        glBegin(GL_QUADS)
        glVertex3f(-1, -1, 0)
        glVertex3f(-1,  1, 0)
        glVertex3f( 1,  1, 0)
        glVertex3f( 1, -1, 0)
        glEnd()
        glPopMatrix()

    def drawMarionette(self, marionette):
        ref = ReferenceSpace(marionette)
        pointRadius = 0.05
        lineWidth = 5

        # Draw Head points
        pHR = ref.activePointInWorld(marionette.motor['HR'])
        glColor3f(0.0, 1.0, 0.0)
        self.drawPoint(pointRadius, pHR)
        pHL = ref.activePointInWorld(marionette.motor['HL'])
        glColor3f(1.0, 0.0, 0.0)
        self.drawPoint(pointRadius, pHL)
        glColor3f(1.0, 0.0, 1.0) # Magenta
        self.drawLine(lineWidth, pHL, pHR)

        # Draw Shoulder points
        pSR = ref.activePointInWorld(marionette.motor['SR'])
        glColor3f(0.0, 1.0, 0.0)
        self.drawPoint(pointRadius, pSR)
        pSL = ref.activePointInWorld(marionette.motor['SL'])
        glColor3f(1.0, 0.0, 0.0)
        self.drawPoint(pointRadius, pSL)
        glColor3f(1.0, 1.0, 0.0) #Yellow
        self.drawLine(lineWidth, pSL, pSR)

        # Draw Arm points
        pAR = ref.activePointInWorld(marionette.motor['AR'])
        glColor3f(0.0, 1.0, 0.0)
        self.drawPoint(pointRadius, pAR)
        pAL = ref.activePointInWorld(marionette.motor['AL'])
        glColor3f(1.0, 0.0, 0.0)
        self.drawPoint(pointRadius, pAL)

        # Draw Wrist points
        pWR = ref.activePointInWorld(marionette.motor['WR'])
        glColor3f(1.0, 0.0, 0.0)
        self.drawPoint(pointRadius, pWR)
        pWL = ref.activePointInWorld(marionette.motor['WL'])
        glColor3f(1.0, 0.0, 0.0)
        self.drawPoint(pointRadius, pWL)

        # Draw Arms
        glColor3f(1.0, 1.0, 1.0) # White
        self.drawLine(lineWidth * 5, pSL, pAL)
        self.drawLine(lineWidth * 5, pAL, pWL)
        self.drawLine(lineWidth * 5, pSR, pAR)
        self.drawLine(lineWidth * 5, pAR, pWR)

        # Draw Foot points
        pFR = ref.activePointInWorld(marionette.motor['FR'])
        glColor3f(0.0, 1.0, 0.0)
        self.drawPoint(pointRadius, pFR)
        pFL = ref.activePointInWorld(marionette.motor['FL'])
        glColor3f(1.0, 0.0, 0.0)
        self.drawPoint(pointRadius, pFL)

    def drawMotors(self, marionette):
        ref = ReferenceSpace(marionette)
        motorRadius = 0.1
        lineWidth = 10

        glColor3f(1.0, 1.0, 1.0)

        # Draw all motors
        for motor in marionette.motorList:
            motorToWorld = ref.motorToWorld(motor)
            pos = GetMatrixOrigin(motorToWorld)
            self.drawPoint(motorRadius, pos)

        # Draw Head rod
        motorHRToWorld = ref.motorToWorld(marionette.motor['HR'])
        mHR = GetMatrixOrigin(motorHRToWorld)
        motorHLToWorld = ref.motorToWorld(marionette.motor['HL'])
        mHL = GetMatrixOrigin(motorHLToWorld)
        self.drawLine(lineWidth, mHL, mHR)

        # Draw Shoulder rod
        motorSRToWorld = ref.motorToWorld(marionette.motor['SR'])
        mSR = GetMatrixOrigin(motorSRToWorld)
        motorSLToWorld = ref.motorToWorld(marionette.motor['SL'])
        mSL = GetMatrixOrigin(motorSLToWorld)
        self.drawLine(lineWidth, mSL, mSR)

        # Draw supporting rod (Origin - H)
        motorHToWorld = ref.motorToWorld(marionette.motor['H'])
        mH = GetMatrixOrigin(motorHToWorld)
        self.drawLine(lineWidth, (0, 0, 0), mH)

    def drawStrings(self, marionette):
        ref = ReferenceSpace(marionette)
        glColor3f(1.0, 1.0, 1.0)
        lineWidth = 1

        for motor in marionette.motorList:
            if motor.isStatic:
                # Draw string
                motorToWorld = ref.motorToWorld(motor)
                motorCenter = GetMatrixOrigin(motorToWorld)
                attachmentPoint = ref.activePointInWorld(motor)
                self.drawLine(lineWidth, motorCenter, attachmentPoint)

    def draw(self, marionette):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        # World Reference
        glColor3f(1.0, 1.0, 1.0)
        self.drawWorldRef(10)

        self.drawMarionette(marionette)
        self.drawMotors(marionette)
        self.drawStrings(marionette)


if __name__ == '__main__':
    marionette = Marionette()

    import pygame
    from pygame.locals import *

    pygame.init()
    display = (650, 650)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

    marionetteOpenGL = MarionetteOpenGL()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Rotates continously
        glRotatef(1, 0, 0, 1)

        glPushMatrix()
        # Angles the marionette 45 degrees around z axis
        glRotatef(45, 0, 0, 1)
        marionetteOpenGL.draw(marionette)
        glPopMatrix()

        pygame.display.flip()
        pygame.time.wait(10)
