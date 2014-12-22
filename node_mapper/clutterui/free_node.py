from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

from node_mapper.clutterui.node import color_to_clutter, TextBox

class FreeNode(BaseObject):
    def __init__(self, **kwargs):
        super(FreeNode, self).__init__(**kwargs)
        n = self.node = kwargs.get('node')
        self.stage = kwargs.get('stage')
        w = self.widget = Clutter.Actor.new()
        w.set_background_color(color_to_clutter(self.node.colors['normal'].background))
        self.stage.add_child(w)
        self.update_geom()
        self.connections = {}
        for cg in [n.input_connections, n.output_connections]:
            for c in cg.itervalues():
                self.add_connection(c)
    def add_connection(self, c):
        obj = Connection(parent=self, connection=c)
        self.connections[c.id] = obj
    def update_geom(self):
        w = self.widget
        n = self.node
        w.set_position(n.x, n.y)
        w.set_size(n.width, n.height)
        
class Connection(BaseObject):
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent')
        super(Connection, self).__init__(**kwargs)
        self.connection = kwargs.get('connection')
        self.widget = Clutter.Actor.new()
        layout = Clutter.BoxLayout.new()
        self.widget.set_layout_manager(layout)
        self.parent.widget.add_child(self.widget)
        self.update_geom()
        if 'input' in self.connection.ChildGroup_parent.name:
            x_align = 'start'
        else:
            x_align = 'end'
        self.text_box = TextBox(text=self.connection.label, 
                                color=self.connection.parent.colors['normal'].text, 
                                x_align=x_align)
        self.widget.add_child(self.text_box.widget)
    def update_geom(self):
        c = self.connection
        w = self.widget
        w.set_position(c.relative_x, c.relative_y)
        w.set_size(c.width, c.height)
