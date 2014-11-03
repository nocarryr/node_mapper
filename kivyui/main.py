from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout

from node_mapper.node_tree.node import Node, test
from node_mapper.kivyui.node import NodeButton

class MainWin(FloatLayout):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        super(MainWin, self).__init__(**kwargs)
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
        self.root_button = NodeButton(node=self.root_node, root_widget=self)
        self.root_button.build_all()
    def do_layout(self, *args, **kwargs):
        for child in self.children:
            child.update_position()
    
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
