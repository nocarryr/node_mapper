import math

from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

from node_mapper.clutterui.node import color_to_clutter, TextBox
from node_mapper.clutterui import actions
from node_mapper.clutterui.line_drawing import Line

class NodeContainer(Clutter.Actor):
    def __init__(self, **kwargs):
        super(NodeContainer, self).__init__()
        self.set_background_color(Clutter.Color(0, 0, 0, 0))
        self.set_x_align(Clutter.ActorAlign.FILL)
        self.set_y_align(Clutter.ActorAlign.FILL)
        self.set_x_expand(True)
        self.set_y_expand(True)
        
class FreeNode(BaseObject):
    def __init__(self, **kwargs):
        super(FreeNode, self).__init__(**kwargs)
        n = self.node = kwargs.get('node')
        self.container = kwargs.get('container')
        self.widget = FreeNodeActor(ui_node=self)
        self.container.add_child(self.widget)
        self.widget.update_geom()
        self.connections = {}
        for cg in [n.input_connections, n.output_connections]:
            for c in cg.itervalues():
                self.add_connection(c)
    def add_connection(self, c):
        obj = Connection(parent=self, connection=c)
        self.connections[c.id] = obj
    def on_widget_action(self, **kwargs):
        print kwargs
        
class FreeNodeActor(Clutter.Actor, actions.Dragable):
    def __init__(self, **kwargs):
        super(FreeNodeActor, self).__init__()
        self.init_actions(**kwargs)
        self.ui_node = kwargs.get('ui_node')
        self.node = self.ui_node.node
        self.set_background_color(color_to_clutter(self.node.colors['normal'].background))
    def update_geom(self):
        n = self.node
        self.set_position(n.x, n.y)
        self.set_size(n.width, n.height)
    def _on_drop_can_drop(self, *args):
        return False
    def trigger_action(self, **kwargs):
        self.ui_node.on_widget_action(**kwargs)
        
class Connection(BaseObject):
    #_Properties = dict(
        
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent')
        super(Connection, self).__init__(**kwargs)
        self.connection = kwargs.get('connection')
        self.widget = ConnectionActor(ui_connection=self)
    def on_widget_action(self, **kwargs):
        print kwargs
        
class ConnectionActor(Clutter.Actor, actions.Clickable):
    def __init__(self, **kwargs):
        super(ConnectionActor, self).__init__()
        self.init_actions(**kwargs)
        self.ui_connection = kwargs.get('ui_connection')
        self.connection = self.ui_connection.connection
        layout = Clutter.BoxLayout()
        self.set_layout_manager(layout)
        self.ui_connection.parent.widget.add_child(self)
        self.update_geom()
        if 'input' in self.connection.ChildGroup_parent.name:
            x_align = 'start'
        else:
            x_align = 'end'
        self.text_box = TextBox(text=self.connection.label, 
                                color=self.connection.parent.colors['normal'].text, 
                                x_align=x_align)
        self.add_child(self.text_box.widget)
        self.connection_point = ConnectionPointActor(ui_connection=self)
        self.add_child(self.connection_point)
    def update_geom(self):
        c = self.connection
        self.set_position(c.relative_x, c.relative_y)
        self.set_size(c.width, c.height)
    def trigger_action(self, **kwargs):
        self.ui_connection.on_widget_action(**kwargs)
        
class ConnectionPointActor(Clutter.Actor, actions.Dragable):
    def __init__(self, **kwargs):
        super(ConnectionPointActor, self).__init__()
        self.ui_connection = kwargs.get('ui_connection')
        self.set_x_align(Clutter.ActorAlign.END)
        self.set_y_align(Clutter.ActorAlign.CENTER)
        self.set_size(8, 8)
        self.canvas = Clutter.Canvas.new()
        self.set_content(self.canvas)
        self.canvas.connect('draw', self.on_canvas_draw)
        self.canvas.set_size(8, 8)
        self.init_actions(**kwargs)
    def on_canvas_draw(self, canvas, cr, width, height):
        cr.move_to(width/2., 0)
        cr.set_source_rgb(.7, .7, .7)
        r = min([width, height]) / 2.
        cr.arc(width/2., height/2., r, 0, 2* math.pi)
        cr.fill()
        
    def trigger_action(self, **kwargs):
        self.ui_connection.trigger_action(**kwargs)
        
class Connector(BaseObject):
    def __init__(self, **kwargs):
        super(Connector, self).__init__(**kwargs)
        self.container = kwargs.get('container')
        self.connector = kwargs.get('connector')
        wkwargs = self.build_line_coords()
        wkwargs['parent_widget'] = self.container
        self.line = Line(**wkwargs)
        self.connector.bind(position_changed=self.on_connector_pos_changed)
    def build_line_coords(self, connection_type=None):
        if connection_type is None:
            connection_type = ['source', 'dest']
        else:
            connection_type = [connection_type]
        d = {}
        if 'source' in connection_type:
            c = self.connector.source
            if c is None:
                d['start_pos'] = {'x':0., 'y':0.}
            else:
                d['start_pos'] = {'x':c.x, 'y':c.y}
        if 'dest' in connection_type:
            c = self.connector.dest
            if c is None:
                d['end_pos'] = {'x':0., 'y':0.}
            else:
                d['end_pos'] = {'x':c.x, 'y':c.y}
        return d
    def on_connector_pos_changed(self, **kwargs):
        connection_type = {'input':'dest', 'output':'source'}.get(kwargs.get('connection_type'))
        d = self.build_line_coords(connection_type)
        for key, val in d.iteritems():
            setattr(self.line, key, val)
