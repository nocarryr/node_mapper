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
    signals_to_register = ['connection_added']
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
        self.node.bind(x=self.on_node_pos_changed, 
                       y=self.on_node_pos_changed, 
                       width=self.on_node_size_changed, 
                       height=self.on_node_size_changed)
        self.node.input_connections.bind(child_update=self.on_node_connections_ChildGroup_update)
        self.node.output_connections.bind(child_update=self.on_node_connections_ChildGroup_update)
        self.widget.connect('notify::position', self.on_widget_pos_changed)
    @property
    def application(self):
        return self.GLOBAL_CONFIG['GUIApplication']
    @property
    def window(self):
        return self.application.mainwindow
    def unlink(self):
        self.node.unbind(self)
        self.node.input_connections.unbind(self)
        self.node.output_connections.unbind(self)
        for c in self.connections.itervalues():
            c.unlink()
        p = self.widget.get_parent()
        if p is not None:
            p.remove_child(self.widget)
        super(FreeNode, self).unlink()
    def add_connection(self, c):
        obj = Connection(parent=self, connection=c)
        self.connections[c.id] = obj
        self.emit('connection_added', node=self, connection=obj)
    def find_child_touches(self):
        for c in self.connections.itervalues():
            if c.has_touch:
                return c
            if c.connection_point.has_touch:
                return c.connection_point
        return None
    def on_node_pos_changed(self, **kwargs):
        if self.dragging:
            return
        self.widget.update_geom()
    def on_node_size_changed(self, **kwargs):
        self.widget.update_geom()
    def on_node_connections_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        obj = kwargs.get('obj')
        if mode == 'add':
            c = self.add_connection(obj)
        elif mode == 'remove':
            c = self.connections[obj.id]
            c.unlink()
            del self.connections[obj.id]
    def on_widget_pos_changed(self, *args):
        if not self.dragging:
            return
        pos = self.widget.get_position()
        self.node.x = pos[0]
        self.node.y = pos[1]
    def on_widget_action(self, **kwargs):
        action = kwargs.get('action')
        action_type = kwargs.get('type')
        if action == 'drop' and action_type == 'can_drop':
            return False
        elif action == 'click':
            btn = kwargs.get('btn')
            if action_type == 'long_press':
                state = kwargs.get('state')
                if state == 'query':
                    return btn == 'left'
                else:
                    return
                #elif state == 'activate':
                #    self.widget.text_box.enable_edit = True
                #elif state == 'cancel':
                #    self.widget.text_box.enable_edit = False
            elif action_type == 'click':
                if btn == 'right':
                    obj = self.find_child_touches()
                    if obj is not None:
                        return
                    self.has_touch = True
                    self.application.menu_context_obj = self
                    self.window.trigger_context_menu(id='node')
            elif action_type == 'double_click':
                self.has_touch = True
                self.widget.text_box.enable_edit = True
        elif action == 'drag':
            if not self.dragging:
                obj = self.find_child_touches()
                if obj is not None:
                    return
            if action_type == 'begin':
                self.drag_start_pos = kwargs.get('abs_pos')
                self.has_touch = True
                self.dragging = True
                return True
            elif action_type == 'motion':
                
                return True
            elif action_type == 'end':
                self.has_touch = False
                self.dragging = False
        
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
    def unlink(self):
        self.connection_point.unbind(self)
        self.connection_point.unlink()
        self.widget.text_box.unbind(self)
        self.widget.text_box.unlink()
        p = self.widget.get_parent()
        if p is not None:
            p.remove_child(self.widget)
        self.connection.unbind(self)
        super(Connection, self).unlink()
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
        if self.parent.has_touch:
            return
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
        self._unbound_connector = None
        super(ConnectionPoint, self).__init__(**kwargs)
        self.ui_connection = kwargs.get('ui_connection')
        self.connection = self.ui_connection.connection
        self.widget = ConnectionPointActor(connection_point=self)
    def unlink(self):
        p = self.widget.get_parent()
        if p is not None:
            p.remove_child(self.widget)
        super(ConnectionPoint, self).unlink()
    def find_line_container(self):
        stage = self.widget.get_stage()
        if hasattr(stage, '_line_container'):
            return stage._line_container
        for widget in stage.get_children():
            if widget.get_property('name') != 'line_container':
                continue
            stage._line_container = widget
            return widget
    def build_unbound_connector(self, **kwargs):
        kwargs['connection_point'] = self
        kwargs['container'] = self.find_line_container()
        self._unbound_connector = UnBoundConnector(**kwargs)
    def on_widget_action(self, **kwargs):
        action = kwargs.get('action')
        action_type = kwargs.get('type')
        actor = kwargs.get('actor')
        if self.ui_connection.parent.has_touch:
            return
        if not isinstance(actor, ConnectionPointActor):
            return
        if action == 'drag':
            ub_c = self._unbound_connector
            if action_type == 'begin':
                self.dragging = True
                self.has_touch = True
                self.widget.highlighted = True
                return True
            elif action_type == 'motion':
                abs_pos = kwargs.get('abs_pos')
                if ub_c is None:
                    ckwargs = dict(zip(['mouse_x', 'mouse_y'], abs_pos))
                    self.build_unbound_connector(**ckwargs)
                else:
                    ub_c.mouse_x = abs_pos[0]
                    ub_c.mouse_y = abs_pos[1]
                kwargs['connection_point'] = self
                kwargs['connection'] = self.connection
                self.emit('drag_motion', **kwargs)
            elif action_type == 'end':
                if ub_c is not None:
                    ub_c.unlink()
                    self._unbound_connector = None
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
        self.text_container = Clutter.Actor.new()
        self.text_container.set_reactive(True)
        self.add_child(self.text_container)
        self.text_container.set_size(self.node.width, self.node.padding_top)
        layout = Clutter.BoxLayout()
        self.text_container.set_layout_manager(layout)
        self.text_box = TextBox(text=self.node.name, 
                                color=self.node.colors['normal'].text, 
                                x_align='center')
        self.text_container.add_child(self.text_box.widget)
        self.text_box.bind(text=self.on_text_box_text_set)
        self.node.bind(name=self.on_node_name_set)
    def update_geom(self):
        n = self.node
        self.set_position(n.x, n.y)
        self.set_size(n.width, n.height)
        self.text_container.set_size(n.width, n.padding_top)
    def on_node_name_set(self, **kwargs):
        value = kwargs.get('value')
        if self.text_box.text == value:
            return
        self.text_box.text = value
    def on_text_box_text_set(self, **kwargs):
        value = kwargs.get('value')
        if self.node.name == value:
            return
        self.node.name = value
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
        if self.highlighted:
            cr.set_source_rgb(1, 1, 1)
        else:
            cr.set_source_rgb(.7, .7, .7)
        if self.get_x_align() == Clutter.ActorAlign.START:
            x = 0
        else:
            x = width
        r = min([width, height]) / 1.5
        cr.arc(x, height/2., r, 0, 2 * math.pi)
        cr.fill_preserve()
        cr.set_source_rgb(.2, .2, .2)
        cr.stroke()
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
            
class UnBoundConnector(BaseObject):
    _Properties = dict(
        mouse_x = {'ignore_type':True}, 
        mouse_y = {'ignore_type':True}, 
    )
    signals_to_register = ['connected']
    def __init__(self, **kwargs):
        super(UnBoundConnector, self).__init__(**kwargs)
        self.mouse_x = kwargs.get('mouse_x')
        self.mouse_y = kwargs.get('mouse_y')
        self.connection_point = kwargs.get('connection_point')
        self.ui_connection = self.connection_point.ui_connection
        self.connection = self.ui_connection.connection
        self.container = kwargs.get('container')
        self.line = Line(parent_widget=self.container, 
                         start_pos={'x':self.connection.x, 'y':self.connection.y}, 
                         end_pos={'x':self.mouse_x, 'y':self.mouse_y})
        self.bind(mouse_x=self.on_mouse_pos, 
                  mouse_y=self.on_mouse_pos)
    def unlink(self):
        self.line.unlink()
        super(UnBoundConnector, self).unlink()
    def on_mouse_pos(self, **kwargs):
        prop = kwargs.get('Property')
        value = kwargs.get('value')
        key = prop.name.split('_')[1]
        self.line.end_pos[key] = value
    def on_cancelled(self, **kwargs):
        self.unlink()
    def on_connected(self, **kwargs):
        self.unlink()
        
