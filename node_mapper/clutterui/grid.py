from nomadic_recording_lib.Bases import BaseObject, Color
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

class GridController(BaseObject):
    _Properties = dict(
        min_size = {'default':4}, 
        num_subdivisions = {'default':8}, 
        total_size = {'default':{'x':640, 'y':480}}, 
    )
    _ChildGroups = dict(
        h_lines = {}, 
        v_lines = {}, 
    )
    signals_to_register = ['lines_built']
    def __init__(self, **kwargs):
        self._stage = None
        super(GridController, self).__init__(**kwargs)
        for key in ['min_size', 'num_subdivisions', 'total_size']:
            if key in kwargs:
                setattr(self, key, kwargs.get(key))
        self.background_color = Color(hue=0., sat=0., val=0.)
        self.line_color = Color(hue=0., sat=0., val=.5)
        self.build_lines()
        self.bind(property_changed=self.on_own_property_changed)
        self.widget = GridCanvas(controller=self)
        self.stage = kwargs.get('stage')
    @property
    def stage(self):
        return self._stage
    @stage.setter
    def stage(self, value):
        if value == self._stage:
            return
        self._stage = value
        if value is not None:
            size = value.get_size()
            self.total_size.update(dict(zip(['x', 'y'], size)))
            value.add_child(self.widget)
            value.connect('notify::size', self.on_stage_size)
    def build_lines(self):
        self.h_lines.clear()
        self.v_lines.clear()
        def iter_grid():
            i = 0
            sub_count = self.num_subdivisions
            count_down = True
            max_i = max(self.total_size.values())
            while i <= max_i:
                yield i, sub_count
                i += self.min_size
                if count_down:
                    sub_count -= 1
                    if sub_count < 0:
                        sub_count = 0
                    if sub_count == 0:
                        count_down = False
                else:
                    sub_count += 1
                    if sub_count > self.num_subdivisions:
                        sub_count = self.num_subdivisions
                    if sub_count == self.num_subdivisions:
                        count_down = True
        for i, size in iter_grid():
            if i <= self.total_size['x']:
                self.v_lines.add_child(GridLine, 
                                       controller=self, 
                                       position=i, 
                                       width=size)
            if i <= self.total_size['y']:
                self.h_lines.add_child(GridLine, 
                                       controller=self, 
                                       position=i, 
                                       width=size)
        self.emit('lines_built')
    def on_stage_size(self, *args):
        size = dict(zip(['x', 'y'], self.stage.get_size()))
        self.total_size.update(size)
    def on_own_property_changed(self, **kwargs):
        prop = kwargs.get('Property')
        print prop.name, prop.value
        if prop.name in ['min_size', 'num_subdivisions', 'total_size']:
            self.build_lines()
        
class GridLine(BaseObject):
    _Properties = dict(
        position = {'type':int}, 
        width = {'type':int}, 
    )
    def __init__(self, **kwargs):
        super(GridLine, self).__init__(**kwargs)
        self.controller = kwargs.get('controller')
        self.position = kwargs.get('position')
        self.id = self.position
        self.width = kwargs.get('width')

def build_color_args(color, alpha):
    l = [getattr(color, k) for k in ['red', 'green', 'blue']]
    l.append(alpha)
    return l
    
class GridCanvas(Clutter.Actor):
    def __init__(self, **kwargs):
        super(GridCanvas, self).__init__()
        self.controller = kwargs.get('controller')
        size = [self.controller.total_size[key] for key in ['x', 'y']]
        self.set_size(*size)
        self.canvas = Clutter.Canvas.new()
        self.canvas.connect('draw', self.on_canvas_draw)
        self.canvas.set_size(*size)
        self.controller.bind(lines_built=self.queue_grid_draw, 
                             total_size=self.on_total_size)
    def queue_grid_draw(self, *args, **kwargs):
        self.canvas.invalidate()
    def on_total_size(self, **kwargs):
        value = kwargs.get('value')
        size = [value[key] for key in ['x', 'y']]
        self.set_size(*size)
        self.canvas.set_size(*size)
    def on_canvas_draw(self, canvas, cr, width, height):
        print 'grid draw: ', width, height
        alpha_scale = 1. / self.controller.num_subdivisions
        base_color = self.controller.line_color
        for h_line in self.controller.h_lines.itervalues():
            cr.move_to(h_line.position, 0)
            cargs = build_color_args(base_color, h_line.width*alpha_scale)
            cr.set_source_rgba(*cargs)
            cr.line_to(h_line.position, height)
        for v_line in self.controller.v_lines.itervalues():
            cr.move_to(0, v_line.position)
            cargs = build_color_args(base_color, v_line.width*alpha_scale)
            cr.set_source_rgba(*cargs)
            cr.line_to(width, v_line.position)
        cr.stroke()
