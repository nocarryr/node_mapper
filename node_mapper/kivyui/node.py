from kivy.clock import Clock
from kivy.graphics import Line as KvLine
from kivy.graphics import Color as KvColor
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button as KvButton
from kivy.uix.textinput import TextInput
from node_mapper.nomadic_recording_lib.Bases import BaseObject, Color

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
        if node is None:
            return
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
        self._adding_node_from_ui = False
        self.widget = None
        self.node_link = None
        self.with_editor = kwargs.get('with_editor', False)
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
                       pre_delete=self.on_node_pre_delete, 
                       x=self.refresh_geom, 
                       y=self.refresh_geom, 
                       width=self.refresh_geom, 
                       height=self.refresh_geom)
        for child_node in self.node.child_nodes.itervalues():
            self.add_child_node(child_node)
        self.node.child_nodes.bind(child_update=self.on_node_child_update)
    @property
    def id(self):
        return self.node.id
    def unlink(self):
        self.node.unbind(self)
        if self.node_link is not None:
            self.node_link.unlink()
        #for child in self.node.child_nodes.itervalues():
        #    child.unlink()
        if self.widget is not None and self.widget.parent is not None:
            self.widget.parent.remove_widget(self.widget)
        if self.node.is_root:
            self.node_selection.unlink()
            #self.node.unlink()
        super(NodeButton, self).unlink()
    def build_all(self):
        self._build_all()
    def _build_all(self, **kwargs):
        if self.widget is None:
            self.build_widget()
        if self.node_link is None and not self.node.is_root:
            self.node_link = NodeLink(node_button=self)
        for child in self.children.itervalues():
            child.build_all()
    def build_widget(self):
        self.widget = Button(node_button=self)
        if self.root_widget is not None:
            self.root_widget.add_widget(self.widget)
            if self.with_editor:
                self.add_editor()
        return self.widget
    def add_child_node(self, node_obj, **kwargs):
        kwargs.update(dict(node=node_obj, parent=self))
        child = NodeButton(**kwargs)
        self.children[child.id] = child
        if self.widget is not None:
            child.build_all()
        ## TODO: bind some events and stuff
        return child
    def build_debug_text(self):
        d = {'name':self.node.name}
        d['position'] = {}
        for key in ['x', 'y', 'relative_x', 'relative_y', 'y_offset']:
            d['position'][key] = getattr(self.node, key)
        d['bounds'] = dict(zip(['x', 'y'], [getattr(self.node, key) for key in ['x', 'y']]))
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
        if self.widget.parent is None:
            return
        ivalue = self.widget.node_pos_to_widget_pos(prop)
        if prop in ['x', 'y']:
            attr = '_'.join(['center', prop])
        else:
            attr = prop
        if getattr(self.widget, attr) == ivalue:
            return
        self.emit('refresh', type='geom')
        self.widget.needs_update = True
        setattr(self.widget, attr, ivalue)
    def add_editor(self):
        return NodeEditor(node_button=self)
    def on_node_child_update(self, **kwargs):
        mode = kwargs.get('mode')
        node = kwargs.get('obj')
        if mode == 'add':
            if not node.init_complete:
                node.bind(init_complete=self.on_child_node_init_complete)
                return
            ckwargs = {}
            if self._adding_node_from_ui:
                ckwargs['with_editor'] = True
                self._adding_node_from_ui = False
            self.add_child_node(node, **ckwargs)
    def on_child_node_init_complete(self, **kwargs):
        if not kwargs.get('value'):
            return
        node = kwargs.get('obj')
        node.unbind(self.on_child_node_init_complete)
        ckwargs = {}
        if self._adding_node_from_ui:
            ckwargs['with_editor'] = True
            self._adding_node_from_ui = False
        self.add_child_node(node, **ckwargs)
    def on_node_hidden(self, **kwargs):
        if self.widget is None:
            return
        if kwargs.get('value'):
            self.selected = False
            self.widget.parent.remove_widget(self.widget)
        else:
            self.root_widget.add_widget(self.widget)
    def on_node_pre_delete(self, **kwargs):
        self.emit('delete')
        self.unlink()
    def on_double_tap(self):
        self._adding_node_from_ui = True
        self.node.add_child()
    def on_single_tap(self):
        if not self.selected:
            self.selected = True
        else:
            self.node.collapsed = not self.node.collapsed
    def on_long_touch(self):
        #self.add_editor()
        self.root_widget.show_node_bubble(self)
    def on_other_node_selected(self, **kwargs):
        if kwargs.get('value') is False:
            return
        if kwargs.get('node') is self:
            return
        self.selected = False
        
class Button(KvButton):
    def __init__(self, **kwargs):
        self.needs_update = True
        self._touch_count = 0
        self._long_touch = False
        self.node_button = kwargs.get('node_button')
        node = self.node_button.node
        kwargs.update(dict(
            size_hint=(None, None), 
            width=int(round(node.width)), 
            height=int(round(node.height)), 
            text=node.name, 
        ))
        super(Button, self).__init__(**kwargs)
        self.node_button.bind(selected=self.on_node_selected)
    def node_pos_to_widget_pos(self, attr=None):
        if attr is None:
            attr = ['x', 'y']
        if isinstance(attr, basestring):
            attr = [attr]
        node = self.node_button.node
        center = {'x': 100, 'y':self.parent.center[1]}
        d = {}
        for _attr in attr:
            d['_'.join(['center', _attr])] = int(round(getattr(node, _attr))) + center[_attr]
        if len(d) == 1:
            return d.values()[0]
        return d
    def update_position(self):
        if self.parent is None:
            return
        for key, val in self.node_pos_to_widget_pos().iteritems():
            setattr(self, key, val)
        self.needs_update = False
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
        if not self.collide_point(*touch.pos):
            return False
        if touch.grab_current is self:
            self._touch_count -= 1
            Clock.unschedule(self.long_touch)
            if touch.is_double_tap:
                Clock.unschedule(self.test_single_tap)
                self.node_button.on_double_tap()
            elif not self._long_touch and self._touch_count == 0:
                Clock.schedule_once(self.test_single_tap, .25)
            self._long_touch = False
            touch.ungrab(self)
            return True
        return False
    def test_single_tap(self, dt):
        self.node_button.on_single_tap()
    def long_touch(self, dt):
        self._long_touch = True
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
        button.bind(pos=self.on_button_pos)
        button.bind(size=self.on_button_size)
    def on_text_validate(self):
        self.node_button.node.name = self.text
    def on_focus(self, instance, value, *args):
        super(NodeEditor, self).on_focus(instance, value, *args)
        if value is False:
            self.parent.remove_widget(self)
    def on_button_pos(self, instance, value):
        self.pos = value
    def on_button_size(self, instance, value):
        self.size = value

class DummyWidget(FloatLayout):
    def __init__(self, **kwargs):
        self._layout_cb = kwargs.get('layout_cb')
        super(DummyWidget, self).__init__(**kwargs)
    def do_layout(self, *args, **kwargs):
        self.update_geom()
        if self._layout_cb:
            self._layout_cb(*args, **kwargs)
    def update_position(self):
        self._trigger_layout()
    def on_parent(self, instance, value):
        if self.parent is None:
            return
        self.update_geom()
        self.parent.bind(pos=self.update_geom, size=self.update_geom)
    def update_geom(self, *args, **kwargs):
        if self.parent is None:
            return
        self.pos = self.parent.pos
        self.size = self.parent.size
        
class NodeLink(BaseObject):
    _Properties = dict(
        line_width={'default':1}, 
    )
    def __init__(self, **kwargs):
        self.needs_update = True
        self.line = None
        super(NodeLink, self).__init__(**kwargs)
        self.color = Color()
        cprops = kwargs.get('color')
        if not cprops:
            cprops = {'hue':0., 'sat':0., 'val':.8}
        for prop, val in cprops.iteritems():
            setattr(self.color, prop, val)
        self.node_button = kwargs.get('node_button')
        self.root_widget = self.node_button.root_widget
        self.dummy_widget = DummyWidget(layout_cb=self.trigger_draw)
        self.root_widget.add_widget(self.dummy_widget)
        self.color.bind(rgb=self.trigger_draw)
        self.bind(line_width=self.trigger_draw)
        self.node_button.node.bind(hidden=self.trigger_draw)
        self.node_button.widget.bind(pos=self.trigger_draw, 
                                     size=self.trigger_draw)
        self.node_button.widget.parent.bind(pos=self.trigger_draw, 
                                            size=self.trigger_draw)
        self.dummy_widget.bind(size=self.trigger_draw, pos=self.trigger_draw)
        ## TODO: allow reparenting
        self.trigger_draw()
    def unlink(self):
        self.root_widget.remove_widget(self.dummy_widget)
        self.node_button.node.unbind(self)
        self.node_button.widget.unbind(pos=self.trigger_draw, 
                                       size=self.trigger_draw)
        self.node_button.widget.parent.unbind(pos=self.trigger_draw, 
                                              size=self.trigger_draw)
        super(NodeLink, self).unlink()
    def calc_points(self):
        widget1 = self.node_button.widget
        widget2 = self.node_button.parent.widget
        return [
            widget1.x, widget1.center_y, 
            widget2.right, widget2.center_y, 
        ]
    def draw(self):
        self.dummy_widget.canvas.clear()
        if self.node_button.node.hidden:
            return
        with self.dummy_widget.canvas:
            KvColor(rgb=self.color.rgb_seq)
            KvLine(points=self.calc_points(), width=self.line_width)
        self.needs_update = False
    def trigger_draw(self, *args, **kwargs):
        self.draw()
    def on_color_rgb(self, **kwargs):
        self.trigger_draw()
