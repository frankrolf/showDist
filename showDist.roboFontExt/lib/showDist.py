#coding=utf-8

"""
Show horizontal and vertical distance between selected points. 
If the points are not on a staight line, also show diagonal distance and angle.

2013-04 roughly adapt code from DJR
2013-06 larger rewrite
2014-02 add angle
2014-06 add keyUp event for select all

Released under MIT license.

"""

from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver
import math


class SelectedPoints(object):
    def __init__(self, coordList):
        self.coordList = coordList
        self.selBox = self.selBox()
        self.xDist = self.selBox[1][0] - self.selBox[0][0]
        self.yDist = self.selBox[1][1] - self.selBox[0][1]
        self.dist = math.sqrt(self.xDist**2 + self.yDist**2)
        self.angle = math.degrees(math.atan2(self.xDist, self.yDist))
        self.niceAngle = self.niceAngleString()

    def selBox(self):
        if self.coordList:
            xList = [point.x for point in self.coordList]
            yList = [point.y for point in self.coordList]

            return ((min(xList), min(yList)), (max(xList), max(yList)))
        else:
            return ((0,0), (0,0))

    def niceAngleString(self):
        angleResultString = u'%.2f' % self.angle
        if angleResultString.endswith('.00'):
            angleResultString = angleResultString[0:-3]
        return angleResultString



class ShowDistTextBox(TextBox):

    def __init__(self, *args, **kwargs):
        super(ShowDistTextBox, self).__init__(*args, **kwargs)
        addObserver(self, "mouseUpCallback", "mouseUp")
        addObserver(self, "keyUpCallback", "keyUp")
    

    def setText(self, glyph):
        s = glyph.selection
        sp = SelectedPoints(s)

        if [sp.angle, sp.xDist, sp.yDist] == [0, 0, 0]:
            text = ''
        elif sp.angle in [0, 90] and sp.dist in [sp.xDist, sp.yDist]:
            text = u"↦ %.0f ↥ %.0f\n∡ %s°" % (sp.xDist, sp.yDist, sp.niceAngle)
        else:
            text = u"↦ %.0f ↥ %.0f \n∡ %s° ⤢ %.2f" % (sp.xDist, sp.yDist, sp.niceAngle, sp.dist)

        self.set(text)


    def mouseUpCallback(self, info):
        self.setText(CurrentGlyph())


    def keyUpCallback(self, info):
        if info["event"].characters() == "a":
            self.setText(CurrentGlyph())


    def _breakCycles(self):
        super(ShowDistTextBox, self)._breakCycles()

        removeObserver(self, "mouseUp")
        removeObserver(self, "keyUp")



class ShowDist(BaseWindowController):
    """
    Attach a vanilla text box to a window.
    """

    def __init__(self):
        addObserver(self, "glyphWindowDidOpen", "glyphWindowDidOpen")


    def glyphWindowDidOpen(self, info):
        window = info["window"]
        vanillaView = ShowDistTextBox((20, 22, 120, 22), "", alignment="left", sizeStyle="mini")
        superview = window.editGlyphView.enclosingScrollView().superview()
        view = vanillaView.getNSTextField()
        frame = superview.frame()
        vanillaView._setFrame(frame)
        superview.addSubview_(view)
                

    def windowCloseCallback(self, sender):
        super(ShowDistTextBox, self).windowCloseCallback(sender)
        removeObserver(self, "glyphWindowDidOpen")


ShowDist()
