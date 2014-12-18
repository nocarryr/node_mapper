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
        self.stage = kwargs.get('stage')
        self.node = kwargs.get('node')
        self.container = Clutter.Actor.new()
        self.text = Clutter.Text.new()
        self.text.set_font_name('Mono 10')
        self.text.set_color(color_to_clutter(self.node.colors['normal'].colors['text']))
        self.container.background_color = color_to_clutter(self.node.colors['normal'].colors['background'])
        self.stage.add_child(self.container)
        self.update_geom()
        self.container.add_child(self.text)
    def update_geom(self, *args, **kwargs):
        for attr in ['x', 'y', 'width', 'height']:
            val = getattr(self.node, attr)
            setattr(self.container, attr, val)
        
