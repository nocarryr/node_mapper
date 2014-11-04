from kivy.clock import Clock
from kivy.uix.button import Button as KvButton
from kivy.uix.textinput import TextInput
from node_mapper.nomadic_recording_lib.Bases import BaseObject

class NodeSelection(BaseObject):
    signals_to_register = ['selected', 'node_added']
    def __init__(self, **kwargs):
        super(NodeSelection, self).__init__(**kwargs)
        self.all_nodes = {}
        self.node_selected = None
    def add_node(self, node):
        self.all_nodes[node.id] = node
        self.emit('node_added', node=node)
        #self.bind(node_added=node.on_new_node)
        self.bind(selected=node.on_other_node_selected)
        node.bind(selected=self.on_node_selected, 
                  delete=self.on_node_delete)
    def on_node_selected(self, **kwargs):
        node = kwargs.get('obj')
        value = kwargs.get('value')
        changed = False
        if value and node != self.node_selected:
            self.node_selected = node
            changed = True
        elif node == self.node_selected:
            self.node_selected = None
            node = None
            changed = True
        if changed:
            self.emit('selected', node=node, value=value)
    def on_node_delete(self, **kwargs):
        node = kwargs.get('obj')
        self.unbind(node)
        node.unbind(self)
        if node.id in self.all_nodes:
            del self.all_nodes[node.id]
        if node == self.node_selected:
            self.node_selected = None
            self.emit('selected', node=None, value=False)
        
        
class NodeButton(BaseObject):
    _Properties = dict(
        selected={'default':False}, 
    )
    signals_to_register = ['refresh', 'delete']
    def __init__(self, **kwargs):
        self.widget = None
        self.children = {}
        self.parent = kwargs.get('parent')
        rw = kwargs.get('root_widget')
        if rw is None and self.parent is not None:
            rw = self.parent.root_widget
            
        self.root_widget = rw
        super(NodeButton, self).__init__(**kwargs)
        self.node = kwargs.get('node')
        if self.node.is_root:
            self.node_selection = NodeSelection()
        else:
            self.node_selection = self.parent.node_selection
        self.node_selection.add_node(self)
        self.node.bind(name=self.refresh_text, 
                       hidden=self.on_node_hidden, 
                       pre_delete=self.on_node_pre_delete)
        self.node.bounds.bind(x=self.refresh_geom, 
                              y=self.refresh_geom, 
                              width=self.refresh_geom, 
                              height=self.refresh_geom)
        for child_node in self.node.child_nodes.itervalues():
            self.add_child_node(child_node)
    @property
    def id(self):
        return self.node.id
    def build_all(self):
        if self.widget is None:
            self.build_widget()
        for child in self.children.itervalues():
            child.build_all()
    def build_widget(self):
        self.widget = Button(node_button=self)
        if self.root_widget is not None:
            self.root_widget.add_widget(self.widget)
        return self.widget
    def add_child_node(self, node_obj):
        child = NodeButton(node=node_obj, parent=self)
        self.children[child.id] = child
        ## TODO: bind some events and stuff
        return child
    def build_debug_text(self):
        d = {}
        d['position'] = {}
        for key in ['x', 'y', 'relative_x', 'relative_y']:
            d['position'][key] = getattr(self.node.position, key)
        d['bounds'] = dict(zip(['x', 'y'], [getattr(self.node.bounds, key) for key in ['x', 'y']]))
        d['index'] = self.node.Index
        return str(d)
    def refresh_text(self, **kwargs):
        if self.widget is None:
            return
        self.widget.text = kwargs.get('value')
        self.emit('refresh', type='text')
    def refresh_geom(self, **kwargs):
        if self.widget is None:
            return
        prop = kwargs.get('Property').name
        ivalue = self.widget.node_pos_to_widget_pos(prop)
        if prop in ['x', 'y']:
            attr = '_'.join(['center', prop])
        else:
            attr = prop
        if getattr(self.widget, attr) == ivalue:
            return
        self.emit('refresh', type='geom')
        setattr(self.widget, attr, ivalue)
    def on_node_hidden(self, **kwargs):
        if self.widget is None:
            return
        if kwargs.get('value'):
            self.selected = False
            self.widget.parent.remove_widget(self.widget)
        else:
            self.parent.widget.add_widget(self.widget)
    def on_node_pre_delete(self, **kwargs):
        self.node.unbind(self)
        self.node.bounds.unbind(self)
        self.emit('delete')
    def on_double_tap(self):
        pass
    def on_single_tap(self):
        if not self.selected:
            self.selected = True
        else:
            self.node.collapsed = not self.node.collapsed
    def on_long_touch(self):
        editor = NodeEditor(node_button=self)
    def on_other_node_selected(self, **kwargs):
        if kwargs.get('value') is False:
            return
        if kwargs.get('node') == self:
            return
        self.selected = False
        
class Button(KvButton):
    def __init__(self, **kwargs):
        self._touch_count = 0
        self.node_button = kwargs.get('node_button')
        node = self.node_button.node
        bounds = node.bounds
        kwargs.update(dict(
            size_hint=(None, None), 
            width=int(round(bounds.width)), 
            height=int(round(bounds.height)), 
            text=node.name, 
        ))
        super(Button, self).__init__(**kwargs)
        self.node_button.bind(selected=self.on_node_selected)
    def node_pos_to_widget_pos(self, attr=None):
        if attr is None:
            attr = ['x', 'y']
        if isinstance(attr, basestring):
            attr = [attr]
        bounds = self.node_button.node.bounds
        center = dict(zip(['x', 'y'], self.parent.center))
        d = {}
        for _attr in attr:
            d['_'.join(['center', _attr])] = int(round(getattr(bounds, _attr))) + center[_attr]
        if len(d) == 1:
            return d.values()[0]
        return d
    def update_position(self):
        for key, val in self.node_pos_to_widget_pos().iteritems():
            setattr(self, key, val)
    def on_node_selected(self, **kwargs):
        self.state = {True:'down', False:'normal'}.get(kwargs.get('value'))
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self._touch_count += 1
        if not touch.is_double_tap:
            Clock.schedule_once(self.long_touch, .5)
        return True
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self._touch_count -= 1
            Clock.unschedule(self.long_touch)
            if touch.is_double_tap:
                self.node_button.on_double_tap()
            else:
                self.node_button.on_single_tap()
            touch.ungrab(self)
            return True
        return False
    def long_touch(self, dt):
        self.node_button.on_long_touch()
    
class NodeEditor(TextInput):
    def __init__(self, **kwargs):
        self.node_button = kwargs.get('node_button')
        node = self.node_button.node
        button = self.node_button.widget
        kwargs.setdefault('center_x', button.center_x)
        kwargs.setdefault('center_y', button.center_y)
        kwargs.setdefault('width', button.width)
        kwargs.setdefault('height', button.height)
        kwargs.setdefault('text', node.name)
        kwargs.setdefault('focus', True)
        kwargs.setdefault('multiline', False)
        super(NodeEditor, self).__init__(**kwargs)
        self.node_button.root_widget.add_widget(self)
    def on_text_validate(self):
        self.node_button.node.text = self.text
    def on_focus(self, instance, value, *args):
        super(NodeEditor, self).on_focus(instance, value, *args)
        if value is False:
            self.parent.remove_widget(self)
            
