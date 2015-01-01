from nomadic_recording_lib.Bases import BaseObject, Color
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

class GridController(BaseObject):
    _Properties = dict(
        min_size = {'default':32}, 
        num_subdivisions = {'default':2}, 
        width = {'default':640}, 
        height = {'default':480}, 
    )
    _ChildGroups = dict(
        h_lines = {}, 
        v_lines = {}, 
    )
    signals_to_register = ['lines_built']
    def __init__(self, **kwargs):
        self._stage = None
        super(GridController, self).__init__(**kwargs)
        for key in ['min_size', 'num_subdivisions', 'width', 'height']:
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
            self.width = size[0]
            self.height = size[1]
            value.add_child(self.widget)
            value.connect('notify::size', self.on_stage_size)
    def build_lines(self):
        self.h_lines.clear()
        self.v_lines.clear()
        def iter_grid():
            i = 0
            sub_count = self.num_subdivisions
            count_down = True
            max_i = max([self.width, self.height])
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
            if i <= self.width:
                self.v_lines.add_child(GridLine, 
                                       controller=self, 
                                       position=i, 
                                       width=size)
            if i <= self.height:
                self.h_lines.add_child(GridLine, 
                                       controller=self, 
                                       position=i, 
                                       width=size)
        self.emit('lines_built')
    def on_stage_size(self, *args):
        size = self.stage.get_size()
        self.width = size[0]
        self.height = size[1]
    def on_own_property_changed(self, **kwargs):
        prop = kwargs.get('Property')
        if prop.name in ['min_size', 'num_subdivisions', 'width', 'height']:
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
    def __repr__(self):
        return '<GridLine: %s>' % (self)
    def __str__(self):
        return 'position=%s, width=%s' % (self.position, self.width)

def build_color_args(color, alpha):
    l = [getattr(color, k) for k in ['red', 'green', 'blue']]
    l.append(alpha)
    return l
    
class GridCanvas(Clutter.Actor):
    def __init__(self, **kwargs):
        super(GridCanvas, self).__init__()
        self.set_background_color(Clutter.Color(0, 0, 255, 255))
        self.controller = kwargs.get('controller')
        size = [self.controller.width, self.controller.height]
        self.set_size(*size)
        self.canvas = Clutter.Canvas.new()
        self.set_content(self.canvas)
        self.canvas.connect('draw', self.on_canvas_draw)
        self.canvas.set_size(*size)
        #self.connect('notify::size', self.on_own_size_changed)
        self.controller.bind(lines_built=self.queue_grid_draw, 
                             width=self.on_controller_size, 
                             height=self.on_controller_size)
    def on_own_size_changed(self, *args):
        pass
    def queue_grid_draw(self, *args, **kwargs):
        self.canvas.invalidate()
    def on_controller_size(self, **kwargs):
        size = [self.controller.width, self.controller.height]
        self.set_size(*size)
        self.canvas.set_size(*size)
    def on_canvas_draw(self, canvas, cr, width, height):
        c = self.controller
        cr.save()
        cr.set_source_rgba(0., 0., 0., 0.)
        cr.set_operator(0)
        cr.paint()
        cr.restore()
        def calc_alpha(line):
            return (.5 / c.num_subdivisions * line.width) + .5
        base_color = c.line_color
        for h_line in c.h_lines.itervalues():
            cr.move_to(0, h_line.position)
            cargs = build_color_args(base_color, calc_alpha(h_line))
            cr.set_source_rgba(*cargs)
            cr.line_to(width, h_line.position)
            cr.stroke()
        for v_line in c.v_lines.itervalues():
            cr.move_to(v_line.position, 0)
            cargs = build_color_args(base_color, calc_alpha(v_line))
            cr.set_source_rgba(*cargs)
            cr.line_to(v_line.position, height)
            cr.stroke()
