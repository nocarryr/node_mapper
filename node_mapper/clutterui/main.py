import threading
from nomadic_recording_lib.ui.gtk import gtkBaseUI
from nomadic_recording_lib.ui.gtk.bases import widgets
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
from nomadic_recording_lib.ui.gtk.bases.ui_modules import gtk
Clutter = clutter_bases.clutter

from node_mapper.clutterui.node import Node
from node_mapper.clutterui.free_node import FreeNode, Connector
from node_mapper.node_tree.node import REGISTRY as NODE_REGISTRY
from node_mapper.node_tree.free_node import test as free_node_test

class Application(gtkBaseUI.Application):
    def __init__(self, **kwargs):
        kwargs['mainwindow_cls'] = MainWindow
        super(Application, self).__init__(**kwargs)
    def on_mainwindow_close(self, *args, **kwargs):
        super(Application, self).on_mainwindow_close(*args, **kwargs)
        print 'mainwindow_close: ', args, kwargs
        print threading.enumerate()
        
    
class MainWindow(gtkBaseUI.BaseWindow):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        vbox = self.vbox = widgets.VBox()
        self.menu_bar = MenuBar()
        vbox.pack_start(self.menu_bar)
        self.scene = clutter_bases.Scene()
        self.stage = self.scene.embed.get_stage()
        self.stage.set_background_color(Clutter.Color(1, 1, 1, 255))
        vbox.pack_start(self.scene.embed)
        self.window.add(vbox)
        self.test_free_node()
        self.window.show_all()
    def test_draw(self):
        self.root_node = NODE_REGISTRY.get('TreeNode')(y_invert=True, name='root')
        self.root_actor = Node(stage=self.stage, node=self.root_node)
        self.root_actor.bind(click=self.on_node_click)
    def test_free_node(self):
        self.node_tree = free_node_test()
        self.node_widgets = {}
        self.connectors = {}
        center_y = self.stage.get_height() / 2.
        for node in self.node_tree.nodes.itervalues():
            node.y = center_y
            node_widget = FreeNode(stage=self.stage, node=node)
            self.node_widgets[node.id] = node_widget
        for c in self.node_tree.connectors.itervalues():
            self.connectors[c.id] = Connector(stage=self.stage, connector=c)
    def on_node_click(self, **kwargs):
        actor = kwargs.get('obj')
        click_type = kwargs.get('type')
        self.menu_bar.debug_label.set_text('%s: %s' % (actor.node.name, click_type))
        
class MenuBar(widgets.HBox):
    def __init__(self):
        super(MenuBar, self).__init__()
        self.dummy_btn = widgets.Button(label='Placeholder')
        self.pack_start(self.dummy_btn)
        self.debug_label = gtk.Label()
        self.pack_start(self.debug_label)
    
def main():
    app = Application()
    print app
    app.run()
    
if __name__ == '__main__':
    main()
