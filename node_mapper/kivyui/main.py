import os
import json
from node_mapper.node_tree.node import TreeNode
from kivy.interactive import InteractiveLauncher
from kivy.app import App
from kivy.base import EventLoop
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

from node_mapper.kivyui.node import NodeButton
from node_mapper.kivyui.menubar import LoadDialog, SaveDialog

class MainWin(BoxLayout):
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    root_node = ObjectProperty(None)
    def cancel_file_dialog(self):
        self._popup.dismiss()
    def show_file_load(self):
        content = LoadDialog(load=self.load_file, cancel=self.cancel_file_dialog)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
    def show_file_save(self):
        content = SaveDialog(save=self.save_file, cancel=self.cancel_file_dialog)
        self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
    def new_file(self):
        self.clear_data()
        r = TreeNode(name='root')
        self.root_node = r
    def load_file(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            js = stream.read()
        d = json.loads(js)
        self.cancel_file_dialog()
        self.clear_data()
        r = TreeNode(deserialize=d)
        self.root_node = r
    def save_file(self, path, filename):
        js = self.root_node.to_json()
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write(js)
        self.cancel_file_dialog()
    def clear_data(self):
        if self.root_node is None:
            return
        self.root_node.unlink()
        self.root_node = None
    
class NodeWindow(FloatLayout):
    def __init__(self, **kwargs):
        self._root_node = kwargs.get('root_node')
        self._init_complete = False
        self._nodes_built = False
        super(NodeWindow, self).__init__(**kwargs)
        EventLoop.bind(on_start=self.on_event_loop_start)
        if self.root_node is not None:
            self.build_nodes()
    @property
    def root_node(self):
        p = self.parent
        if p is None:
            return None
        return p.root_node
    @root_node.setter
    def root_node(self, value):
        self._root_node = value
        if value is not None:
            self.build_nodes()
    def build_nodes(self):
        if self._nodes_built:
            return
        self._nodes_built = True
        w = self.root_button = NodeButton(node=self.root_node, root_widget=self)
        w.node_selection.bind(selected=self.on_node_selected)
        w.build_all()
        self._trigger_layout()
    def on_node_selected(self, **kwargs):
        obj = kwargs.get('node')
        if kwargs.get('value'):
            self.parent.debug_label.text = obj.build_debug_text()
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
