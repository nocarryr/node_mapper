from kivy.clock import Clock
from kivy.uix.button import Button as KvButton
from node_mapper.nomadic_recording_lib.Bases import BaseObject

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
        self.node.bind(name=self.refresh_text, 
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
            self.node.collapsed = True
    def on_long_touch(self):
        pass
        
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
    def on_touch_down(self, touch):
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
        return super(Button, self).on_touch_up(touch)
    def long_touch(self, dt):
        self.node_button.on_long_touch()
