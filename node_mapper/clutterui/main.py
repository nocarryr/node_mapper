import threading

from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.ui.gtk import gtkBaseUI
from nomadic_recording_lib.ui.gtk.bases import widgets
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
from nomadic_recording_lib.ui.gtk.bases.ui_modules import gtk, gdk, clutter
Clutter = clutter_bases.clutter

from node_mapper.clutterui.menu import MenuBar, ContextMenus
from node_mapper.clutterui.grid import GridController
from node_mapper.clutterui.line_drawing import LineContainer
from node_mapper.clutterui.node import Node
from node_mapper.clutterui.free_node import NodeContainer, FreeNode, Connector
from node_mapper.node_tree.node import REGISTRY as NODE_REGISTRY
from node_mapper.node_tree.free_node import test as free_node_test

class Application(gtkBaseUI.Application):
    def __init__(self, **kwargs):
        self.menu_context_obj = None
        kwargs['mainwindow_cls'] = MainWindow
        super(Application, self).__init__(**kwargs)
    def on_mainwindow_close(self, *args, **kwargs):
        super(Application, self).on_mainwindow_close(*args, **kwargs)
        print 'mainwindow_close: ', args, kwargs
        print threading.enumerate()
        
    
class InputDevices(BaseObject):
    def __init__(self, **kwargs):
        super(InputDevices, self).__init__(**kwargs)
        keys = ['master', 'slave', 'floating']
        self.device_type_map = dict(zip(keys, [getattr(gdk.DeviceType, key.upper()) for key in keys]))
        self.devices_by_type = {}
        self.window = kwargs.get('window')
        display = self.window.window.get_display()
        self.device_manager = display.get_device_manager()
        self.update_devices()
        #self.device_manager.connect('
    def find_by_name(self, name):
        by_type = self.devices_by_type
        for key in ['master', 'slave', 'floating']:
            if key not in by_type:
                continue
            device = by_type[key].get(name)
            if device is not None:
                return device
    def update_devices(self, *args, **kwargs):
        #by_id = self.devices_by_id
        by_type = self.devices_by_type
        for key, device_type in self.device_type_map.iteritems():
            if key not in by_type:
                by_type[key] = {}
            for device in self.device_manager.list_devices(device_type):
                name = device.get_name()
                if name not in by_type[key]:
                    by_type[key][name] = device
            
class MainWindow(gtkBaseUI.BaseWindow):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.input_devices = InputDevices(window=self)
        vbox = self.vbox = widgets.VBox()
        self.menu_bar = MenuBar()
        self.menu_bar.bind(activate=self.on_menuitem_activate)
        vbox.pack_start(self.menu_bar.widget)
        self.scene = clutter_bases.Scene()
        self.stage = self.scene.embed.get_stage()
        self.context_menus = ContextMenus(stage=self.stage)
        #self.stage.connect('allocation-changed', self.on_stage_allocation)
        self.stage.set_background_color(Clutter.Color(1, 1, 1, 255))
        self.mouse_pos = {'stage':[0, 0], 'connector':[0, 0]}
        #self.stage.connect('motion-event', self.on_stage_motion)
        a = Clutter.ClickAction.new()
        self.stage.add_action(a)
        a.connect('clicked', self.on_stage_click)
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
        self.node_tree.bind(node_update=self.on_node_tree_node_update, 
                            connector_added=self.on_node_tree_connector_added)
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
    def add_node(self, **kwargs):
        if None in [kwargs.get(key) for key in ['x', 'y']]:
            position = kwargs.get('position')
            kwargs.update(dict(zip(['x', 'y'], position)))
        self.node_tree.add_node(**kwargs)
    def on_node_tree_connector_added(self, **kwargs):
        c = kwargs.get('connector')
        self.connectors[c.id] = Connector(connector=c, container=self.line_container)
    def on_node_tree_node_update(self, **kwargs):
        mode = kwargs.get('mode')
        node = kwargs.get('obj')
        if mode == 'add':
            node_widget = FreeNode(node=node, container=self.node_container)
            self.node_widgets[node.id] = node_widget
        elif mode == 'remove':
            node_widget = self.node_widgets[node.id]
            node_widget.unlink()
            del self.node_widgets[node.id]
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
    def on_stage_click(self, action, actor):
        btn = action.get_button()
        if btn == 1:
            return
        if self.Application.menu_context_obj is not None:
            return
        self.trigger_context_menu(id='window', btn=btn)
    def trigger_context_menu(self, **kwargs):
        menu_id = kwargs.get('id')
        event_kwargs = kwargs.get('event_kwargs', {})
        e = kwargs.get('event')
        btn = kwargs.get('btn')
        if e is None:
            e = clutter.get_current_event()
        if btn is None:
            btn = e.get_button()
        ts = e.get_time()
        position = kwargs.get('position', e.get_coords())
        event_kwargs['position'] = position
        e_device = e.get_device()
        d_name = e_device.get_device_name()
        g_device = self.input_devices.find_by_name(d_name)
        self.context_menus.trigger_menu(id=menu_id, 
                                        btn=btn, 
                                        device=g_device, 
                                        timestamp=ts, 
                                        event_kwargs=event_kwargs)
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
    def on_menuitem_activate(self, **kwargs):
        pass
        

    
def main():
    app = Application()
    print app
    app.run()
    
if __name__ == '__main__':
    main()
