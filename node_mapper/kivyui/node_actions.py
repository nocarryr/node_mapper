from kivy.uix.bubble import Bubble, BubbleButton

class Action(object):
    def __init__(self, **kwargs):
        self.bubble = kwargs.get('bubble')
        if not hasattr(self, 'name'):
            self.name = kwargs.get('name')
            if self.name is None:
                self.name = self.__class__.__name__.split('Action')[0]
        if not hasattr(self, 'text'):
            self.text = self.name.title()
        self.button = self.add_button()
    def add_button(self, **kwargs):
        kwargs.setdefault('name', self.name)
        kwargs.setdefault('text', self.text)
        btn = NodeBubbleButton(**kwargs)
        btn.bind(on_release=self.on_button_release)
        self.bubble.add_widget(btn)
        return btn
    def do_action(self, node_button):
        raise NotImplementedError('method must be defined by subclass')
    def on_button_release(self, *args):
        node_button = self.bubble.node_button
        self.do_action(node_button)
        self.bubble._dispatch_action(self)
        
class EditAction(Action):
    def do_action(self, node_button):
        node_button.add_editor()
        
class MoveAction(Action):
    def do_action(self, node_button):
        ## TODO: make nodes move
        pass
        
class DeleteAction(Action):
    def do_action(self, node_button):
        node = node_button.node
        if node.is_root:
            return
        node.unlink()
        
ACTIONS = [EditAction, MoveAction, DeleteAction]

class NodeBubble(Bubble):
    def __init__(self, **kwargs):
        self._node_button = None
        kwargs.update(dict(
            size_hint=(None, None), 
            size=(160, 30), 
            pos_hint={'center_x': .5, 'y': .6}, 
        ))
        super(NodeBubble, self).__init__(**kwargs)
        self.register_event_type('on_action')
        self.actions = {}
        for cls in ACTIONS:
            self.add_action(cls)
    @property
    def node_button(self):
        return self._node_button
    @node_button.setter
    def node_button(self, value):
        if value == self._node_button:
            return
        self._node_button = value
        if value is None:
            self.hide()
    def add_action(self, cls, **kwargs):
        kwargs['bubble'] = self
        action = cls(**kwargs)
        self.actions[action.name] = action
        return action
    def _dispatch_action(self, action):
        self.dispatch('on_action', action.name, self.node_button)
        self.node_button = None
    def set_pos_from_node_button(self):
        widget = self.node_button.widget
        self.center_x = widget.center_x
        self.y = widget.top + 10
    def show(self, widget):
        if self.parent is not None:
            return
        self.set_pos_from_node_button()
        widget.add_widget(self)
    def hide(self):
        if self.parent is None:
            return
        self.parent.remove_widget(self)
    def on_action(self, action, node_button):
        pass
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            self.node_button = None
            return True
        return super(NodeBubble, self).on_touch_down(touch)
        
class NodeBubbleButton(BubbleButton):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        kwargs.setdefault('text', self.name.title())
        super(NodeBubbleButton, self).__init__(**kwargs)
        
