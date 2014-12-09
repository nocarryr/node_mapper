from kivy.base import EventLoop
from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from node_mapper.kivyui.menu import MenuBar
from node_mapper.kivyui.node import NodeButton

class MainWin(FloatLayout):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        self._init_complete = False
        self._nodes_built = False
        super(MainWin, self).__init__(**kwargs)
        EventLoop.bind(on_start=self.on_event_loop_start)
        self.menu_bar = MenuBar()
        self.add_widget(self.menu_bar)
        self.debug_label = Label()
        self.add_widget(self.debug_label)
        if self.root_node is not None:
            self.build_nodes()
    @property
    def root_node(self):
        return self._root_node
    @root_node.setter
    def root_node(self, value):
        if self._root_node is not None:
            if self.root_button is not None:
                self.root_button.node_selection.unbind(selected=self.on_node_selected)
                self.root_button.unlink()
        self._root_node = value
        if value is not None:
            self.build_nodes()
    def build_nodes(self):
        if self._nodes_built:
            return
        if self.root_node is None:
            self._nodes_built = True
            return
        self._nodes_built = True
        w = self.root_button = NodeButton(node=self.root_node, root_widget=self)
        w.node_selection.bind(selected=self.on_node_selected)
        w.build_all()
        self._trigger_layout()
    def on_node_selected(self, **kwargs):
        obj = kwargs.get('node')
        if kwargs.get('value'):
            self.debug_label.text = obj.build_debug_text()
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
    

    
class BlahApp(App):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        super(BlahApp, self).__init__(**kwargs)
    def build(self):
        root = MainWin(root_node=self._root_node)
        return root

def launch(interactive=False, **kwargs):
    if interactive:
        a = InteractiveLauncher(BlahApp(**kwargs))
    else:
        a = BlahApp(**kwargs)
    a.run()
    return a
if __name__ == '__main__':
    BlahApp().run()
