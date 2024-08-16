import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class Crosshair(QtWidgets.QWidget):
    def __init__(self, parent=None, windowSize=10, penWidth=2):
        QtWidgets.QWidget.__init__(self, parent)
        self.ws = windowSize
        self.resize(windowSize, windowSize)
        self.pen = QtGui.QPen(QtGui.QColor(0, 255, 0, 255))                
        self.pen.setWidth(penWidth)                                            
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        screen_geometry = QtWidgets.QApplication.desktop().screenGeometry()
        screen_center = screen_geometry.center()
        widget_center = self.rect().center()
        
        # Adjust the offset to move the crosshair slightly upwards
        offset_y = 0  # Adjust this value to fine-tune the vertical position
        self.move(screen_center - widget_center + QtCore.QPoint(0, offset_y))

    def paintEvent(self, event):
        ws = self.ws
        d = 4
        painter = QtGui.QPainter(self)
        painter.setPen(self.pen)
        painter.drawLine(ws/2, 0, ws/2, ws/2 - ws/d)   # Top
        painter.drawLine(ws/2, ws/2 + ws/d, ws/2, ws)   # Bottom
        painter.drawLine(0, ws/2, ws/2 - ws/d, ws/2)   # Left
        painter.drawLine(ws/2 + ws/d, ws/2, ws, ws/2)   # Right

app = QtWidgets.QApplication(sys.argv) 

widget = Crosshair(windowSize=24, penWidth=1)
widget.show()

sys.exit(app.exec_())
