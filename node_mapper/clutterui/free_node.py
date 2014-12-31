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
    _Properties = dict(
        has_touch={'default':False}, 
        dragging={'default':False}, 
    )
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
        action = kwargs.get('action')
        action_type = kwargs.get('type')
        if action == 'drop' and action_type == 'can_drop':
            return False
        
class Connection(BaseObject):
    _Properties = dict(
        has_touch={'default':False}, 
        dragging={'default':False}, 
    )
    def __init__(self, **kwargs):
        self.parent = kwargs.get('parent')
        super(Connection, self).__init__(**kwargs)
        self.connection = kwargs.get('connection')
        self.widget = ConnectionActor(ui_connection=self)
        self.connection_point = ConnectionPoint(ui_connection=self)
        self.connection_point.bind(dragging=self.on_connection_point_dragging, 
                                   drag_motion=self.on_connection_point_drag_motion, 
                                   drop=self.on_connection_point_drop)
        self.widget.add_child(self.connection_point.widget)
        self.widget.text_box.bind(text=self.on_text_widget_text_set, 
                                  enable_edit=self.on_text_widget_enable_edit_set)
    def on_text_widget_text_set(self, **kwargs):
        if not kwargs.get('obj').enable_edit:
            return
        self.connection.label = kwargs.get('value')
    def on_text_widget_enable_edit_set(self, **kwargs):
        value = kwargs.get('value')
        if not value:
            self.has_touch = False
    def on_connection_point_dragging(self, **kwargs):
        pass
    def on_connection_point_drag_motion(self, **kwargs):
        pass
    def on_connection_point_drop(self, **kwargs):
        pass
    def on_widget_action(self, **kwargs):
        action = kwargs.get('action')
        action_type = kwargs.get('type')
        btn = kwargs.get('btn')
        actor = kwargs.get('actor')
        if action == 'drop':
            drop_actor = kwargs.get('drop_actor')
            drag_actor = kwargs.get('drag_actor')
            if not isinstance(drag_actor, ConnectionPointActor):
                return False
            if not isinstance(drop_actor, ConnectionPointActor):
                return False
            if not isinstance(drop_actor, ConnectionActor):
                return False
            can_connect = self.connection.can_connect_to(drag_actor.connection)
            if action_type == 'can_drop':
                return can_connect
            elif action_type == 'drop':
                self.connection.connect_to(drag_actor.connection)
            return
        if not isinstance(actor, ConnectionActor):
            return
        if self.connection_point.has_touch:
            return
        if action == 'click':
            if action_type == 'long_press':
                state = kwargs.get('state')
                if state == 'query':
                    return btn == 'left'
                elif state == 'activate':
                    self.has_touch = True
                    self.widget.text_box.enable_edit = True
            
class ConnectionPoint(BaseObject):
    _Properties = dict(
        has_touch={'default':False}, 
        dragging={'default':False}, 
    )
    signals_to_register = ['drop', 'drag_motion']
    def __init__(self, **kwargs):
        super(ConnectionPoint, self).__init__(**kwargs)
        self.ui_connection = kwargs.get('ui_connection')
        self.connection = self.ui_connection.connection
        self.widget = ConnectionPointActor(connection_point=self)
    def on_widget_action(self, **kwargs):
        action = kwargs.get('action')
        action_type = kwargs.get('type')
        actor = kwargs.get('actor')
        if not isinstance(actor, ConnectionPointActor):
            return
        if action == 'drag':
            if action_type == 'begin':
                self.dragging = True
                self.has_touch = True
                self.widget.highlighted = True
                return True
            elif action_type == 'motion':
                kwargs['connection_point'] = self
                kwargs['connection'] = self.connection
                self.emit('drag_motion', **kwargs)
            elif action_type == 'end':
                self.dragging = False
                self.has_touch = False
                self.widget.highlighted = False
        elif action == 'drop':
            drop_actor = kwargs.get('drop_actor')
            drag_actor = kwargs.get('drag_actor')
            if drop_actor is not self.widget:
                return False
            if not isinstance(drag_actor, ConnectionPointActor):
                return False
            drop_source = drag_actor.ui_connection
            ekwargs = dict(source=drop_source, dest=self)
            can_connect = self.connection.can_connect_to(drop_source.connection)
            if action_type == 'drop':
                self.emit('drop', **ekwargs)
                self.connection.connect_to(drop_source.connection)
                self.widget.highlighted = False
            elif action_type == 'can_drop':
                return can_connect
            elif action_type == 'over_in' and can_connect:
                self.widget.highlighted = True
            elif action_type == 'over_out' and drop_source is not self:
                self.widget.highlighted = False
            

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
    def trigger_action(self, **kwargs):
        return self.ui_node.on_widget_action(**kwargs)
    def __str__(self):
        return 'NodeActor: %s' % (self.node)
        
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
            layout.set_pack_start(True)
        else:
            x_align = 'end'
        self.text_box = TextBox(text=self.connection.label, 
                                color=self.connection.parent.colors['normal'].text, 
                                x_align=x_align)
        self.add_child(self.text_box.widget)
    def update_geom(self):
        c = self.connection
        self.set_position(c.relative_x, c.relative_y)
        self.set_size(c.width, c.height)
    def trigger_action(self, **kwargs):
        return self.ui_connection.on_widget_action(**kwargs)
    def __str__(self):
        return 'ConnectionActor: %s' % (self.connection)
        
class ConnectionPointActor(Clutter.Actor, actions.Dragable):
    def __init__(self, **kwargs):
        super(ConnectionPointActor, self).__init__()
        self._highlighted = False
        self.connection_point = kwargs.get('connection_point')
        self.ui_connection = self.connection_point.ui_connection
        self.connection = self.ui_connection.connection
        if 'input' in self.connection.ChildGroup_parent.name:
            self.set_x_align(Clutter.ActorAlign.START)
        else:
            self.set_x_align(Clutter.ActorAlign.END)
        self.set_y_align(Clutter.ActorAlign.CENTER)
        self.set_size(8, 8)
        self.canvas = Clutter.Canvas.new()
        self.set_content(self.canvas)
        self.canvas.connect('draw', self.on_canvas_draw)
        self.canvas.set_size(8, 8)
        self.init_actions(**kwargs)
    @property
    def highlighted(self):
        return self._highlighted
    @highlighted.setter
    def highlighted(self, value):
        if value == self._highlighted:
            return
        self._highlighted = value
        self.canvas.invalidate()
    def on_canvas_draw(self, canvas, cr, width, height):
        cr.move_to(width/2., 0)
        if self.highlighted:
            cr.set_source_rgb(1, 1, 1)
        else:
            cr.set_source_rgb(.7, .7, .7)
        r = min([width, height]) / 2.
        cr.arc(width/2., height/2., r, 0, 2* math.pi)
        cr.fill()
    def trigger_action(self, **kwargs):
        return self.connection_point.on_widget_action(**kwargs)
    def __str__(self):
        return 'ConnectionPointActor: %s' % (self.connection)
        
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
