import threading
from nomadic_recording_lib.ui.gtk import gtkBaseUI
from nomadic_recording_lib.ui.gtk.bases import widgets
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

from node_mapper.clutterui.node import Node
from node_mapper.node_tree.node import REGISTRY as NODE_REGISTRY

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
        self.scene.embed.get_stage().set_color(Clutter.Color(0, 0, 0, 255))
        vbox.pack_start(self.scene.embed)
        self.window.add(vbox)
        self.test_draw()
        self.window.show_all()
        
    def test_draw(self):
        self.root_node = NODE_REGISTRY.get('TreeNode')(y_invert=True, name='root')
        self.root_actor = Node(stage=self.scene.embed.get_stage(), node=self.root_node)
        return
        
        c = Clutter.Color.new(0, 0, 255, 100)
        rect = Clutter.Rectangle.new_with_color(c)
        rect.set_size(150, 50)
        rect.set_position(200, 200)
        self.scene.embed.get_stage().add_child(rect)
        
        
class MenuBar(widgets.HBox):
    def __init__(self):
        super(MenuBar, self).__init__()
        self.dummy_btn = widgets.Button(label='Placeholder')
        self.pack_start(self.dummy_btn)
    
def main():
    app = Application()
    print app
    app.run()
    
if __name__ == '__main__':
    main()
