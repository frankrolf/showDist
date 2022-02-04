'''
Show horizontal and vertical distance between selected points.
If the points are not on a staight line, also show diagonal distance and angle.

Released under MIT license.
'''

import math
import vanilla
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber


def get_BCP_base(bcp):
    '''
    For a given BCP, return the point it is attached to.
    '''
    contour = bcp.contour
    if len(contour) == 1:
        return None, None

    c_points = contour.points
    p_index = c_points.index(bcp)
    prev_index = p_index - 1
    next_index = p_index + 1
    # the previous point for a given BCP must always exist:
    prev_point = c_points[prev_index]

    # the next point doesn’t necessarily have to:
    if p_index == len(c_points) - 1:
        next_point = c_points[0]
    else:
        next_point = c_points[next_index]

    point = prev_point
    if prev_point.type.lower() == 'offcurve':
        point = next_point

    return point


def get_prev_and_next_BCP(point):
    '''
    For a given point, return previous and next BCPs.
    '''
    contour = point.contour
    if contour and len(contour) == 1:
        return None, None

    c_points = contour.points  # including off-curve
    p_index = c_points.index(point)
    prev_BCP = c_points[(p_index - 1) % len(c_points)]
    next_BCP = c_points[(p_index + 1) % len(c_points)]

    if prev_BCP.type.lower() != 'offcurve':
        prev_BCP = None

    if next_BCP.type.lower() != 'offcurve':
        next_BCP = None

    return prev_BCP, next_BCP


def get_BCP_indicator(point_pair):
    '''
    Draw a tack in the direction of the BCP
    '''
    point_a, point_b = point_pair.coord_list
    if point_pair.angle < 45:
        if point_a.x - point_b.x < 0:
            bcp_indicator = u'⊢'
        else:
            bcp_indicator = u'⊣'
    else:
        if point_a.y - point_b.y < 0:
            bcp_indicator = u'⊥'
        else:
            bcp_indicator = u'⊤'
    return bcp_indicator


def make_BCP_info(point_pair):
    '''
    String to display in the info box
    '''
    bcp_indicator = get_BCP_indicator(point_pair)
    point_a, point_b = point_pair.coord_list
    if point_pair.angle in [0, 90]:
        info = u'{} {:.0f}'.format(
            bcp_indicator, point_pair.dist)
    else:
        info = u'{} {:.0f} ∡ {}°'.format(
            bcp_indicator, point_pair.dist,
            point_pair.nice_angle)
    return info


class SelectedPoints(object):
    def __init__(self, coord_list):
        self.coord_list = coord_list
        self.sel_box = self.sel_box()
        self.dist_x = self.sel_box[1][0] - self.sel_box[0][0]
        self.dist_y = self.sel_box[1][1] - self.sel_box[0][1]
        self.dist = math.hypot(self.dist_x, self.dist_y)
        self.angle = math.degrees(math.atan2(self.dist_y, self.dist_x))
        self.nice_angle = self.nice_angle_string()

    def sel_box(self):
        if self.coord_list:
            xList = [point.x for point in self.coord_list]
            yList = [point.y for point in self.coord_list]

            return ((min(xList), min(yList)), (max(xList), max(yList)))
        return ((0, 0), (0, 0))

    def nice_angle_string(self):
        nice_angle = u'{:.2f}'.format(self.angle)
        if nice_angle.endswith('.00'):
            return u'{:.0f}'.format(self.angle)
        return nice_angle


class ShowDistSubscriber(Subscriber):

    debug = False

    def build(self):
        glyphEditor = self.getGlyphEditor()

        self.showDist = vanilla.TextBox((10, 12, 120, 22))

        glyphEditor.addGlyphEditorSubview(
            self.showDist, identifier="de.frgr.showDist")

    def glyphDidChangeSelection(self, info):
        self.setTextForSelection(info["glyph"].selectedPoints)

    def glyphEditorDidMouseDrag(self, info):
        self.setTextForSelection(info["glyph"].selectedPoints)

    def setTextForSelection(self, selection):
        if len(selection) == 1:
            point = selection[0]
            info_list = []

            if point.type.lower() == 'offcurve':
                # only a BCP is selected
                bc_point = point
                base_point = get_BCP_base(bc_point)
                point_pair = SelectedPoints([bc_point, base_point])
                info = make_BCP_info(point_pair)
                info_list.append(info)

            else:
                # a single point with one or two BCPs is selected
                prev_BCP, next_BCP = get_prev_and_next_BCP(point)

                if prev_BCP:
                    prev_point_pair = SelectedPoints([prev_BCP, point])
                    info = make_BCP_info(prev_point_pair)
                    info_list.append(info)

                if next_BCP:
                    next_point_pair = SelectedPoints([next_BCP, point])
                    info = make_BCP_info(next_point_pair)
                    info_list.append(info)

            # make sure the BCP list is always displayed in same order:
            if info_list:
                if info_list[0][0] == u'⊣':
                    info_list.reverse()
                if info_list[0][0] == u'⊥':
                    info_list.reverse()

            text = '\n'.join(info_list)

        else:
            # multiple points are selected
            sp = SelectedPoints(selection)

            if [sp.angle, sp.dist_x, sp.dist_y] == [0, 0, 0]:
                text = ''
            elif sp.angle in [0, 90] and sp.dist in [sp.dist_x, sp.dist_y]:
                text = u'↦ {:.0f} ↥ {:.0f}\n∡ {}°'.format(
                    sp.dist_x, sp.dist_y, sp.nice_angle)
            else:
                text = u'↦ {:.0f} ↥ {:.0f} \n∡ {}° ⤢ {:.2f}'.format(
                    sp.dist_x, sp.dist_y, sp.nice_angle, sp.dist)

        self.showDist.set(text)


registerGlyphEditorSubscriber(ShowDistSubscriber)
