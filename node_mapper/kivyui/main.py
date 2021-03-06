import os

from kivy.base import EventLoop
from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from node_mapper.node_tree.node import REGISTRY as NODE_REGISTRY
from node_mapper.kivyui.menu import MenuBar
from node_mapper.kivyui.node import NodeButton
from node_mapper.kivyui.node_actions import NodeBubble

class MainWin(FloatLayout):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        self._init_complete = False
        self._nodes_built = False
        self.root_button = None
        super(MainWin, self).__init__(**kwargs)
        EventLoop.bind(on_start=self.on_event_loop_start)
        self.menu_bar = MenuBar()
        self.add_widget(self.menu_bar)
        self.debug_label = Label()
        self.add_widget(self.debug_label)
        self.node_bubble = NodeBubble()
        self.menu_bar.file_menu.bind(on_new_file=self.do_file_new, 
                                     on_open_file=self.do_file_open, 
                                     on_save_file=self.do_file_save)
        if self.root_node is not None:
            self.build_nodes()
    @property
    def root_node(self):
        return self._root_node
    @root_node.setter
    def root_node(self, value):
        if self._root_node is not None:
            self._root_node.node_tree.unlink()
            if self.root_button is not None:
                self.root_button.node_selection.unbind(self.on_node_selected)
                self.root_button.unlink()
                self.root_button = None
                self._nodes_built = False
        self._root_node = value
        if value is not None and self._nodes_built:
            self.build_nodes()
    def build_nodes(self):
        if self._nodes_built:
            return
        if self.root_node is None:
            self.do_file_new()
        self._nodes_built = True
        w = self.root_button = NodeButton(node=self.root_node, root_widget=self)
        w.node_selection.bind(selected=self.on_node_selected)
        w.build_all()
        self._trigger_layout()
    def on_node_selected(self, **kwargs):
        obj = kwargs.get('node')
        if kwargs.get('value'):
            self.debug_label.text = obj.build_debug_text()
    def show_node_bubble(self, node_button):
        self.node_bubble.node_button = node_button
        self.node_bubble.show(self)
    def on_size(self, instance, value):
        if self._init_complete or value == [1, 1]:
            return
        self._init_complete = True
        self.build_nodes()
    def do_layout(self, *args, **kwargs):
        for child in self.children:
            if hasattr(child, 'update_position'):
                child.update_position()
        self.debug_label.width = self.width
        self.debug_label.bottom = 0
        self.debug_label.left = 0
    def on_event_loop_start(self, *args, **kwargs):
        EventLoop.unbind(on_start=self.on_event_loop_start)
        if self._init_complete:
            return
        if self.size == [1, 1]:
            return
        self._init_complete = True
        self.build_nodes()
    def do_file_new(self, *args):
        self.root_node = None
        self.root_node = NODE_REGISTRY.get('TreeNode')(y_invert=True)
        if self.root_button is None:
            self._nodes_built = False
            self.build_nodes()
    def do_file_open(self, instance, path, fn):
        fn = os.path.join(path, fn)
        with open(fn, 'r') as f:
            s = f.read()
        cls = NODE_REGISTRY.get('TreeNodeTree')
        tree = cls.from_json(s)
        self.root_node = None
        self.root_node = tree.root_node
        if self.root_button is None:
            self._nodes_built = False
            self.build_nodes()
        self._trigger_layout()
    def do_file_save(self, instance, path, fn):
        fn = os.path.join(path, fn)
        s = self.root_node.node_tree.to_json(json_preset='pretty')
        with open(fn, 'w') as f:
            f.write(s)
    

    
class NodeApp(App):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        super(NodeApp, self).__init__(**kwargs)
    def build(self):
        root = MainWin(root_node=self._root_node)
        return root

def launch(interactive=False, **kwargs):
    if interactive:
        a = InteractiveLauncher(NodeApp(**kwargs))
    else:
        a = NodeApp(**kwargs)
    a.run()
    return a
if __name__ == '__main__':
    NodeApp().run()
