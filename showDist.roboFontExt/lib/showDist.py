# coding=utf-8

"""
Show horizontal and vertical distance between selected points.
If the points are not on a staight line, also show diagonal distance and angle.

2013-04 roughly adapt code from DJR
2013-06 larger rewrite
2014-02 add angle
2014-06 add keyUp event for select all
2015-09 add BCP length
2017-12 make selections in multiple windows possible

Released under MIT license.

"""

from vanilla import *
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver, removeObserver
from mojo.UI import CurrentGlyphWindow
import math


def return_prev_and_next_BCP(point):
    '''
    For a given point, return previous and next BCPs
    '''
    contour = point.getParent()
    if len(contour) == 1:
        return None, None

    c_points = contour.points
    point_index = c_points.index(point)

    if point_index == 0:
        prev_BCP, next_BCP = c_points[-1], c_points[1]
    elif point_index == len(contour.points) - 1:
        prev_BCP, next_BCP = c_points[point_index - 1], c_points[0]
    else:
        prev_BCP, next_BCP = c_points[point_index - 1], c_points[point_index + 1]

    if prev_BCP.type != 'offCurve':
        prev_BCP = None

    if next_BCP.type != 'offCurve':
        next_BCP = None

    return prev_BCP, next_BCP


class SelectedPoints(object):
    def __init__(self, coordList):
        self.coordList = coordList
        self.sel_box = self.sel_box()
        self.dist_x = self.sel_box[1][0] - self.sel_box[0][0]
        self.dist_y = self.sel_box[1][1] - self.sel_box[0][1]
        self.dist = math.sqrt(self.dist_x**2 + self.dist_y**2)
        self.angle = math.degrees(math.atan2(self.dist_x, self.dist_y))
        self.nice_angle = self.nice_angle_string()

    def sel_box(self):
        if self.coordList:
            xList = [point.x for point in self.coordList]
            yList = [point.y for point in self.coordList]

            return ((min(xList), min(yList)), (max(xList), max(yList)))
        else:
            return ((0, 0), (0, 0))

    def nice_angle_string(self):
        angleResultString = u'%.2f' % self.angle
        if angleResultString.endswith('.00'):
            angleResultString = angleResultString[0:-3]
        return angleResultString


class ShowDistTextBox(TextBox):

    def __init__(self, parent_view, *args, **kwargs):
        super(ShowDistTextBox, self).__init__(*args, **kwargs)
        self.notifications = ["mouseUp", "selectAll", "viewDidChangeGlyph"]
        for notification_name in self.notifications:
            addObserver(
                self, "update_info_callback", notification_name)
        self.parent_view = parent_view

    def set_text(self, selection):
        if len(selection) == 1:
            point = selection[0]

            if point.type == 'offCurve':
                return

            else:
                prev_BCP, next_BCP = return_prev_and_next_BCP(point)
                textData = []

                if prev_BCP:
                    pPointPair = SelectedPoints([prev_BCP, point])

                    if pPointPair.angle > 45:
                        if prev_BCP.x - point.x < 0:
                            bcpIndicator = u'⟝'
                        else:
                            bcpIndicator = u'⟞'
                    else:
                        if prev_BCP.y - point.y < 0:
                            bcpIndicator = u'⟘'
                        else:
                            bcpIndicator = u'⟙'

                    if pPointPair.angle in [0, 90]:
                        textString = u"%s %.0f" % (
                            bcpIndicator, pPointPair.dist)
                    else:
                        textString = u"%s %.0f ∡ %s°" % (
                            bcpIndicator, pPointPair.dist,
                            pPointPair.nice_angle)
                    textData.append(textString)

                if next_BCP:
                    nPointPair = SelectedPoints([next_BCP, point])

                    if nPointPair.angle > 45:
                        if next_BCP.x - point.x < 0:
                            bcpIndicator = u'⟝'
                            pos = 0
                        else:
                            bcpIndicator = u'⟞'
                            pos = -1
                    else:
                        if next_BCP.y - point.y < 0:
                            bcpIndicator = u'⟘'
                            pos = -1
                        else:
                            bcpIndicator = u'⟙'
                            pos = 0

                    if nPointPair.angle in [0, 90]:
                        textString = u"%s %.0f" % (
                            bcpIndicator, nPointPair.dist)
                    else:
                        textString = u"%s %.0f ∡ %s°" % (
                            bcpIndicator, nPointPair.dist,
                            nPointPair.nice_angle)
                    if pos == 0:
                        textData.insert(pos, textString)
                    else:
                        textData.append(textString)

                text = '\n'.join(textData)

        else:

            sp = SelectedPoints(selection)

            if [sp.angle, sp.dist_x, sp.dist_y] == [0, 0, 0]:
                text = ''
            elif sp.angle in [0, 90] and sp.dist in [sp.dist_x, sp.dist_y]:
                text = u"↦ %.0f ↥ %.0f\n∡ %s°" % (
                    sp.dist_x, sp.dist_y, sp.nice_angle)
            else:
                text = u"↦ %.0f ↥ %.0f \n∡ %s° ⤢ %.2f" % (
                    sp.dist_x, sp.dist_y, sp.nice_angle, sp.dist)

        self.set(text)

    def update_info_callback(self, info):
        view = info['view']
        glyph = info['glyph']
        if self._check_view(view) is True:
            self.update_info(glyph)

    def update_info(self, glyph):
        if glyph is not None:
            selection = glyph.selection
        else:
            selection = []
        self.set_text(selection)

    def _check_view(self, view):
        return view == self.parent_view

    def _breakCycles(self):
        for notification_name in self.notifications:
            removeObserver(self, notification_name)


class ShowDist(BaseWindowController):

    def __init__(self):
        addObserver(self, "show_dist_textbox", "glyphWindowDidOpen")

    def show_dist_textbox(self, info):
        window = CurrentGlyphWindow()
        view = window.getGlyphView()
        vanillaView = ShowDistTextBox(
            view,
            (20, 22, 120, 22),
            "",
            alignment="left",
            sizeStyle="mini"
        )
        window.addGlyphEditorSubview(vanillaView)


ShowDist()
