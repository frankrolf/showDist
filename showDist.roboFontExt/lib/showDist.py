# coding=utf-8

'''
Show horizontal and vertical distance between selected points.
If the points are not on a staight line, also show diagonal distance and angle.
2013-04 roughly adapt code from DJR
2013-06 larger rewrite
2014-02 add angle
2014-06 add keyUp event for select all
2015-09 add BCP length
2017-12 make selections in multiple windows possible
        make BCP length interactive
        minor code simplifications
2018-01 make RF3 compatible
2018-12 fix angle (90° is vertical), support rulers
2019-05 properly remove observers
2019-11 avoid deprecated methods

Released under MIT license.
'''

from vanilla import TextBox
from mojo.events import addObserver, removeObserver
from mojo.UI import getGlyphViewDisplaySettings
import math


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

    c_points = contour.points
    p_index = c_points.index(point)

    # XXX this can eventually be rewritten with modulo
    if p_index == 0:
        prev_BCP, next_BCP = c_points[-1], c_points[1]
    elif p_index == len(contour.points) - 1:
        prev_BCP, next_BCP = c_points[p_index - 1], c_points[0]
    else:
        prev_BCP, next_BCP = c_points[p_index - 1], c_points[p_index + 1]

    if prev_BCP.type.lower() != 'offcurve':
        prev_BCP = None

    if next_BCP.type.lower() != 'offcurve':
        next_BCP = None

    return prev_BCP, next_BCP


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


class ShowDistTextBox(TextBox):

    def __init__(self, parent_view, *args, **kwargs):
        super(ShowDistTextBox, self).__init__(*args, **kwargs)
        self.notifications = [
            'mouseUp',
            'mouseDragged',
            'keyUp', 'selectAll',
            'viewDidChangeGlyph'
        ]
        for notification_name in self.notifications:
            addObserver(
                self, 'update_info_callback', notification_name)

        addObserver(self, 'kill_observers', 'glyphWindowWillClose')
        self.parent_view = parent_view

    def get_BCP_indicator(self, point_pair):
        '''Draw a tack in the direction of the BCP'''
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

    def make_BCP_info(self, point_pair):
        '''String to display in the info box'''
        bcp_indicator = self.get_BCP_indicator(point_pair)
        point_a, point_b = point_pair.coord_list
        if point_pair.angle in [0, 90]:
            info = u'{} {:.0f}'.format(
                bcp_indicator, point_pair.dist)
        else:
            info = u'{} {:.0f} ∡ {}°'.format(
                bcp_indicator, point_pair.dist,
                point_pair.nice_angle)
        return info

    def set_text(self, selection):
        if len(selection) == 1:
            point = selection[0]
            info_list = []

            if point.type.lower() == 'offcurve':
                # only a BCP is selected
                bc_point = point
                base_point = get_BCP_base(bc_point)
                point_pair = SelectedPoints([bc_point, base_point])
                info = self.make_BCP_info(point_pair)
                info_list.append(info)

            else:
                # a single point with one or two BCPs is selected
                prev_BCP, next_BCP = get_prev_and_next_BCP(point)

                if prev_BCP:
                    prev_point_pair = SelectedPoints([prev_BCP, point])
                    info = self.make_BCP_info(prev_point_pair)
                    info_list.append(info)

                if next_BCP:
                    next_point_pair = SelectedPoints([next_BCP, point])
                    info = self.make_BCP_info(next_point_pair)
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

        self.set(text)

    def update_info_callback(self, info):
        view = info['view']
        glyph = info['glyph']
        if self._check_view(view) is True:
            self.update_info(glyph)

    def update_info(self, glyph):
        if glyph is not None:
            selection = glyph.selectedPoints
        else:
            selection = []
        self.set_text(selection)

    def _check_view(self, view):
        return view == self.parent_view

    def kill_observers(self, info):
        for notification_name in self.notifications:
            removeObserver(self, notification_name)
        removeObserver(self, 'glyphWindowWillClose')


class ShowDist(object):

    def __init__(self):
        addObserver(self, 'show_dist_textbox', 'glyphWindowDidOpen')

    def show_dist_textbox(self, info):
        window = info['window']
        if getGlyphViewDisplaySettings().get('Rulers'):
            offset = (20, 22, 120, 22),
        else:
            offset = (10, 12, 120, 22),
        view = window.getGlyphView()
        vanillaView = ShowDistTextBox(
            view,
            *offset,
            '',
            alignment='left',
            sizeStyle='mini'
        )
        window.addGlyphEditorSubview(vanillaView)


if __name__ == '__main__':
    ShowDist()
