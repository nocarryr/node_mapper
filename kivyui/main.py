from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from node_mapper.node_tree.node import Node, test
from node_mapper.kivyui.node import NodeButton

class MainWin(FloatLayout):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        super(MainWin, self).__init__(**kwargs)
        self.debug_label = Label()
        self.add_widget(self.debug_label)
        if self.root_node is not None:
            self.build_nodes()
    @property
    def root_node(self):
        return self._root_node
    @root_node.setter
    def root_node(self, value):
        self._root_node = value
        if value is not None:
            self.build_nodes()
    def build_nodes(self):
        w = self.root_button = NodeButton(node=self.root_node, root_widget=self)
        w.node_selection.bind(selected=self.on_node_selected)
        w.build_all()
    def on_node_selected(self, **kwargs):
        obj = kwargs.get('node')
        if kwargs.get('value'):
            self.debug_label.text = obj.build_debug_text()
    def do_layout(self, *args, **kwargs):
        for child in self.children:
            if hasattr(child, 'update_position'):
                child.update_position()
        self.debug_label.width = self.width
        self.debug_label.bottom = 0
        self.debug_label.left = 0
        
    
class NodeApp(App):
    def build(self):
        root_node = test()
        root = MainWin(root_node=root_node)
        return root

def launch(interactive=False):
    if interactive:
        a = InteractiveLauncher(NodeApp())
    else:
        a = NodeApp()
    a.run()
    return a
if __name__ == '__main__':
    NodeApp().run()
