from PyQt5.QtWidgets import QDial
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QPointF
from math import pi, sin, cos


class QSuperDial(QDial):
    """Overload QDial with correct stylesheet support

    QSuperDial support background-color and color stylesheet
    properties and do NOT add "shadow"

    QSuperDial draw ellipse if width and height are different
    """

    _degree270 = 1.5 * pi
    _degree225 = 1.25 * pi

    def __init__(self, parent, knobRadius=5, knobMargin=5):
        super(QSuperDial, self).__init__(parent)
        self.knobRadius = knobRadius
        self.knobMargin = knobMargin
        self.setRange(0, 100)

    def paintEvent(self, event):
        # From Peter, thanks !
        # http://thecodeinn.blogspot.fr/2015/02/customizing-qdials-in-qt-part-1.html

        painter = QPainter(self)

        # So that we can use the background color
        painter.setBackgroundMode(1)

        # Smooth out the circle
        painter.setRenderHint(QPainter.Antialiasing)

        # Use background color
        painter.setBrush(painter.background())

        # Store color from stylesheet, pen will be overriden
        pointColor = QColor(painter.pen().color())

        # No border
        painter.setPen(QPen(Qt.NoPen))

        # Draw first circle
        painter.drawEllipse(0, 0, self.width(), self.height())

        # Reset color to pointColor from stylesheet
        painter.setBrush(QBrush(pointColor))

        # Get ratio between current value and maximum to calculate angle
        ratio = self.value() / self.maximum()

        # The maximum amount of degrees is 270, offset by 225
        angle = ratio * self._degree270 - self._degree225

        # Radius of background circle
        rx = self.width() / 2
        ry = self.height() / 2

        # Add r to have (0,0) in center of dial
        y = sin(angle) * (ry - self.knobRadius - self.knobMargin) + ry
        x = cos(angle) * (rx - self.knobRadius - self.knobMargin) + rx

        # Draw the ellipse
        painter.drawEllipse(QPointF(x, y),
                            self.knobRadius,
                            self.knobRadius)
