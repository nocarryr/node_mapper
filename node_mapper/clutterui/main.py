import threading
from nomadic_recording_lib.ui.gtk import gtkBaseUI
from nomadic_recording_lib.ui.gtk.bases import widgets
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
from nomadic_recording_lib.ui.gtk.bases.ui_modules import gtk
Clutter = clutter_bases.clutter

from node_mapper.clutterui.grid import GridController
from node_mapper.clutterui.line_drawing import LineContainer
from node_mapper.clutterui.node import Node
from node_mapper.clutterui.free_node import NodeContainer, FreeNode, Connector
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
        #self.stage.connect('allocation-changed', self.on_stage_allocation)
        self.stage.set_background_color(Clutter.Color(1, 1, 1, 255))
        self.mouse_pos = {'stage':[0, 0], 'connector':[0, 0]}
        #self.stage.connect('motion-event', self.on_stage_motion)
        vbox.pack_start(self.scene.embed)
        self.window.add(vbox)
        self.test_free_node()
        self.window.show_all()
    def test_draw(self):
        self.root_node = NODE_REGISTRY.get('TreeNode')(y_invert=True, name='root')
        self.root_actor = Node(stage=self.stage, node=self.root_node)
        self.root_actor.bind(click=self.on_node_click)
    def test_free_node(self):
        layout = Clutter.BinLayout()
        self.stage.set_layout_manager(layout)
        self.grid_controller = GridController(stage=self.stage)
        self.line_container = LineContainer()
        self.node_container = NodeContainer()
        self.stage.add_child(self.line_container)
        self.stage.add_child(self.node_container)
        self.node_tree = free_node_test()
        self.node_tree.bind(connector_added=self.on_node_tree_connector_added)
        self.node_widgets = {}
        self.connectors = {}
        center_y = self.stage.get_height() / 2.
        for node in self.node_tree.nodes.itervalues():
            node.y = center_y
            node_widget = FreeNode(node=node, container=self.node_container)
            self.node_widgets[node.id] = node_widget
        for c in self.node_tree.connectors.itervalues():
            self.connectors[c.id] = Connector(connector=c, container=self.line_container)
        #self.connectors.values()[0].line.widget.connect('motion-event', self.on_connector_motion)
    def on_node_tree_connector_added(self, **kwargs):
        c = kwargs.get('connector')
        self.connectors[c.id] = Connector(connector=c, container=self.line_container)
    def on_stage_allocation(self, stage, box, flags):
        print 'stage size: ', stage.get_size()
        w = box.x2 - box.x1
        h = box.y2 - box.y1
        print 'box size: ', (w, h)
        if hasattr(self, 'line_container'):
            print 'line_container: ', self.line_container.get_size()
        if hasattr(self, 'node_container'):
            print 'node_container', self.node_container.get_size()
        if hasattr(self, 'connectors'):
            w = self.connectors.values()[0].line.widget
            print 'connector: ', w.get_size()
            print 'canvas: ', (w.canvas.get_property('width'), w.canvas.get_property('height'))
    def on_stage_motion(self, stage, e):
        d = self.mouse_pos['stage']
        d[0] = e.x
        d[1] = e.y
        self.update_debug()
    def on_connector_motion(self, c, e):
        d = self.mouse_pos['connector']
        d[0] = e.x
        d[1] = e.y
        self.update_debug()
    def update_debug(self):
        self.menu_bar.debug_label.set_text('stage: %s, connector: %s' % (self.mouse_pos['stage'], self.mouse_pos['connector']))
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
