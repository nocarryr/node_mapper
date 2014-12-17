from gi.repository import GtkClutter, Clutter
from node_mapper.nomadic_recording_lib.ui.gtk import gtkBaseUI
from node_mapper.nomadic_recording_lib.ui.gtk.bases import widgets

class Application(gtkBaseUI.Application):
    def __init__(self, **kwargs):
        kwargs['mainwindow_cls'] = MainWindow
        super(Application, self).__init__(**kwargs)
    def _build_mainwindow(self, **kwargs):
        GtkClutter.init()
        return super(Application, self)._build_mainwindow(**kwargs)
    
class MainWindow(gtkBaseUI.BaseWindow):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        vbox = self.vbox = widgets.VBox()
        self.menu_bar = MenuBar()
        vbox.pack_start(self.menu_bar)
        self.embed = GtkClutter.Embed()
        vbox.pack_start(self.embed)
        self.add(vbox)
        self.test_draw()
        
    def test_draw(self):
        c = Clutter.Color.new(0, 0, 255, 100)
        rect = Clutter.Rectangle.new_with_color(c)
        rect.set_size(150, 50)
        rect.set_position(200, 200)
        self.embed.get_stage().add_child(rect)
        
        
class MenuBar(widgets.HBox):
    def __init__(self):
        super(MenuBar, self).__init__()
        self.dummy_btn = widgets.Button(label='Placeholder')
        self.pack_start(self.dummy_btn)
    
def main():
    app = Application()
    app.run()
    
if __name__ == '__main__':
    main()
