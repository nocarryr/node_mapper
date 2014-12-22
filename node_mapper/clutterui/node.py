from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

def color_to_clutter(color):
    l = [int(getattr(color, k)*255) for k in ['red', 'green', 'blue']]
    l.append(255)
    return Clutter.Color.new(*l)
    
class Node(BaseObject):
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.register_signal('click')
        self.stage = kwargs.get('stage')
        self.node = kwargs.get('node')
        self.container = Clutter.Actor.new()
        self.container.set_reactive(True)
        layout = Clutter.BoxLayout.new()
        self.container.set_layout_manager(layout)
        self.text = TextBox(text=self.node.name, color=self.node.colors['normal'].colors['text'])
        self.container.set_background_color(color_to_clutter(self.node.colors['normal'].colors['background']))
        self.stage.add_child(self.container)
        self.update_geom()
        self.container.add_child(self.text.widget)
        self.actions = {}
        a = Clutter.ClickAction.new()
        self.container.add_action(a)
        a.connect('clicked', self.on_clicked)
        self.actions['click'] = a
    def update_geom(self, *args, **kwargs):
        c = self.container
        n = self.node
        x = n.x + (self.stage.get_width() / 2.)
        y = n.y + (self.stage.get_height() / 2.)
        c.set_position(x, y)
        c.set_size(n.width, n.height)
    def on_clicked(self, *args):
        a = self.actions['click']
        btn = a.get_button()
        if btn == 1:
            click_type = 'left'
        else:
            click_type = 'right'
        self.emit('click', obj=self, type=click_type)
        
        
class TextBox(BaseObject):
    _Properties = dict(
        text = {'default':''}, 
    )
    def __init__(self, **kwargs):
        super(TextBox, self).__init__(**kwargs)
        w = self.widget = Clutter.Text.new()
        w.set_reactive(False)
        w.set_x_align(Clutter.ActorAlign.CENTER)
        w.set_y_align(Clutter.ActorAlign.CENTER)
        w.set_x_expand(True)
        w.set_y_expand(True)
        w.set_font_name('Mono 10')
        w.set_color(color_to_clutter(kwargs.get('color')))
        self.bind(text=self.on_text_set)
        self.text = kwargs.get('text')
    def on_text_set(self, **kwargs):
        value = kwargs.get('value')
        if self.widget.get_text() == value:
            return
        self.widget.set_text(value)