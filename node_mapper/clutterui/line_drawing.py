from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

#from node_mapper.clutterui.node import color_to_clutter

class LineContainer(Clutter.Actor):
    def __init__(self, **kwargs):
        self._parent_allocation_signal_id = None
        super(LineContainer, self).__init__()
        self.set_x_align(Clutter.ActorAlign.FILL)
        self.set_y_align(Clutter.ActorAlign.FILL)
        self.set_x_expand(True)
        self.set_y_expand(True)
        layout = Clutter.BinLayout()
        self.set_layout_manager(layout)
        
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
        self.widget.queue_canvas_redraw()
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
        self.widget.queue_canvas_redraw()
        
class LineCanvas(Clutter.Actor):
    def __init__(self, **kwargs):
        self._parent_allocation_signal_id = None
        self._setting_canvas_size = False
        super(LineCanvas, self).__init__()
        self.set_x_align(Clutter.ActorAlign.FILL)
        self.set_y_align(Clutter.ActorAlign.FILL)
        self.set_x_expand(True)
        self.set_y_expand(True)
        self.set_reactive(True)
        self.line = kwargs.get('line')
        self.canvas = Clutter.Canvas.new()
        self.canvas.set_size(*self.get_size())
        self.set_content(self.canvas)
        self.canvas.connect('draw', self.on_canvas_draw)
        self.connect('notify::size', self.on_size_property_changed)
    def on_size_property_changed(self, *args):
        self.canvas.set_size(*self.get_size())
    def queue_canvas_redraw(self, *args):
        #if min(self.line.start_pos.values()) < 0:
        #    return
        #if min(self.line.end_pos.values()) < 0:
        #    return
        #r = self.canvas.set_size(*self.get_size())
        #if not r:
        if self._setting_canvas_size:
            return
        self.canvas.invalidate()
    def on_canvas_draw(self, canvas, context, width, height):
        if min(self.line.start_pos.values()) < 0:
            return
        if min(self.line.end_pos.values()) < 0:
            return
        #print 'parent size=(%s, %s), actor size=(%s, %s), canvas size=(%s, %s), start_pos=%s, end_pos=%s' % (
        #    self.get_parent().get_width(), self.get_parent().get_height(), 
        #    self.get_width(), self.get_height(), width, height, 
        #    self.line.start_pos, self.line.end_pos)
        context.set_source_rgba(0., 0., 0., 0.)
        context.move_to(self.line.start_x, self.line.start_y)
        context.set_source_rgba(0., 0., 1., 1.)
        context.set_line_width(2)
        context.line_to(self.line.end_x, self.line.end_y)
        context.stroke()
        return True
