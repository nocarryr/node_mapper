from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

#from node_mapper.clutterui.node import color_to_clutter

class Line(BaseObject):
    _Properties = dict(
        start_pos = {'default':{'x':-1., 'y':-1.}}, 
        end_pos = {'default':{'x':-1., 'y':-1.}}, 
        start_x = {'default':-1.}, 
        start_y = {'default':-1.}, 
        end_x = {'default':-1.}, 
        end_y = {'default':-1.}, 
    )
    def __init__(self, **kwargs):
        self._props_updating = set()
        super(Line, self).__init__(**kwargs)
        self.parent_widget = kwargs.get('parent_widget')
        self.widget = LineCanvas(line=self)
        self.parent_widget.add_child(self.widget)
        self.widget.set_position(*self.parent_widget.get_position())
        self.widget.set_size(*self.parent_widget.get_size())
        c = Clutter.BindConstraint.new(self.parent_widget, 
                                       Clutter.BindCoordinate.ALL, 
                                       0.0)
        self.widget.add_constraint(c)
        self.bind(start_x=self.on_start_xy_changed, 
                  start_y=self.on_start_xy_changed, 
                  end_x=self.on_end_xy_changed, 
                  end_y=self.on_end_xy_changed, 
                  start_pos=self.on_start_pos_changed, 
                  end_pos=self.on_end_pos_changed)
        for attr in ['start_pos', 'end_pos']:
            if attr not in kwargs:
                continue
            for key, val in kwargs.get(attr).iteritems():
                getattr(self, attr)[key] = val
        for attr in ['start_x', 'start_y', 'end_x', 'end_y']:
            if attr in kwargs:
                setattr(self, attr, kwargs.get(attr))
    def on_start_xy_changed(self, **kwargs):
        if 'start_pos' in self._props_updating:
            return
        value = kwargs.get('value')
        prop = kwargs.get('Property')
        self._props_updating.add('start_xy')
        self.start_pos[prop.name.split('_')[1]] = value
        self._props_updating.discard('start_xy')
    def on_end_xy_changed(self, **kwargs):
        if 'end_pos' in self._props_updating:
            return
        value = kwargs.get('value')
        prop = kwargs.get('Property')
        self._props_updating.add('end_xy')
        self.end_pos[prop.name.split('_')[1]] = value
        self._props_updating.discard('end_xy')
    def on_start_pos_changed(self, **kwargs):
        if 'start_xy' in self._props_updating:
            return
        value = kwargs.get('value')
        old = kwargs.get('old')
        self._props_updating.add('start_pos')
        for key in ['x', 'y']:
            if value[key] == old[key]:
                continue
            setattr(self, '_'.join(['start', key]), value[key])
        self._props_updating.discard('start_pos')
        self.widget.queue_redraw()
    def on_end_pos_changed(self, **kwargs):
        if 'end_xy' in self._props_updating:
            return
        value = kwargs.get('value')
        old = kwargs.get('old')
        self._props_updating.add('end_pos')
        for key in ['x', 'y']:
            if value[key] == old[key]:
                continue
            setattr(self, '_'.join(['end', key]), value[key])
        self._props_updating.discard('end_pos')
        self.widget.queue_redraw()
        
class LineCanvas(Clutter.Actor):
    def __init__(self, **kwargs):
        super(LineCanvas, self).__init__()
        self.line = kwargs.get('line')
        self.canvas = Clutter.Canvas.new()
        self.set_content(self.canvas)
        self.canvas.connect('draw', self.on_canvas_draw)
    def queue_redraw(self):
        if min(self.line.start_pos.values()) < 0:
            return
        if min(self.line.end_pos.values()) < 0:
            return
        self.canvas.invalidate()
    def set_size(self, *args):
        super(LineCanvas, self).set_size(*args)
        self.canvas.set_size(*args)
    def on_canvas_draw(self, canvas, context, width, height):
        context.set_source_rgba(0., 0., 0., 0.)
        context.move_to(self.line.start_x, self.line.start_y)
        context.set_source_rgba(0., 0., 1., 1.)
        context.set_line_width(2)
        context.line_to(self.line.end_x, self.line.end_y)
        context.stroke()
        return True
