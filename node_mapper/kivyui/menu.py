import os

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
DropDown = None

def load_dropdown():
    global DropDown
    if DropDown is None:
        from kivy.uix.dropdown import DropDown as _DropDown
        DropDown = _DropDown

class MenuBar(BoxLayout):
    def __init__(self, **kwargs):
        kwargs['height'] = 30
        super(MenuBar, self).__init__(**kwargs)
        self.file_menu = FileDropDown()
        self.add_widget(self.file_menu)
    def do_layout(self, *args):
        if self.parent:
            self.width = self.parent.width
            self.top = self.parent.top
            self.x = self.parent.x
        super(MenuBar, self).do_layout(*args)
        
class MenuDropDown(ToggleButton):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        kwargs.setdefault('text', self.name)
        self._dropdown_active = False
        super(MenuDropDown, self).__init__(**kwargs)
        self.register_event_type('on_select')
        load_dropdown()
        self.dropdown = DropDown()
        items = kwargs.get('items', [])
        for item in items:
            self.add_item(item)
        self.dropdown.bind(on_select=self.on_dropdown_select, 
                           on_dismiss=self.on_dropdown_dismiss)
    def add_item(self, item):
        btn = Button(text=item.title(), size_hint_y=None, height=44)
        btn.bind(on_release=lambda btn: self.dropdown.select(item))
        self.dropdown.add_widget(btn)
    def on_dropdown_select(self, instance, value):
        print 'select: %s' % (value)
        self.dispatch('on_select', value)
    def on_release(self):
        value = self.state
        if value == 'down' and not self._dropdown_active:
            self._dropdown_active = True
            self.dropdown.open(self)
        #elif value == 'normal' and self._dropdown_active:
        #    self._dropdown_active = False
            #self.dropdown.dismiss()
    def on_dropdown_dismiss(self, *args):
        self._dropdown_active = False
        return
    def on_select(self, *args):
        pass
    

class FileDropDown(MenuDropDown):
    path = ObjectProperty(None, allownone=True)
    file = ObjectProperty(None, allownone=True)
    def __init__(self, **kwargs):
        self.file_dialog = None
        self.popup = None
        kwargs.setdefault('name', 'File')
        kwargs.setdefault('items', ['New', 'Open', 'Save'])
        super(FileDropDown, self).__init__(**kwargs)
        self.current_mode = None
        if self.path is None:
            self.path = os.getcwd()
        self.register_event_type('on_new_file')
        self.register_event_type('on_open_file')
        self.register_event_type('on_save_file')
    def build_file_dialog(self):
        dlg = self.file_dialog = FileDialog(mode=self.current_mode, 
                                            path=self.path, 
                                            file=self.file)
        dlg.bind(on_cancel=self.on_file_dialog_cancel, 
                 on_submit=self.on_file_dialog_submit)
        self.popup = Popup(title=self.current_mode.title(), content=dlg, size_hint=(.9, .9))
        self.popup.open()
    def clear_file_dialog(self):
        self.file_dialog.unbind(on_cancel=self.on_file_dialog_cancel, 
                                on_submit=self.on_file_dialog_submit)
        self.popup.dismiss()
        self.file_dialog = None
        self.popup = None
    def on_file_dialog_cancel(self, *args):
        self.clear_file_dialog()
        self.current_mode = None
    def on_file_dialog_submit(self, *args):
        dlg = self.file_dialog
        self.path = dlg.path
        self.file = dlg.file
        self.clear_file_dialog()
        sig_name = '_'.join(['on', self.current_mode.lower(), 'file'])
        self.dispatch(sig_name, self.path, self.file)
        self.current_mode = None
    def on_select(self, value):
        self.current_mode = value
        if value == 'New':
            self.current_mode = None
            self.file = None
            self.dispatch('on_new_file')
        elif value == 'Open':
            self.build_file_dialog()
        elif value == 'Save':
            if self.file is not None:
                self.dispatch('on_save_file', self.path, self.file)
                self.current_mode = None
            else:
                self.build_file_dialog()
    def on_new_file(self, *args):
        pass
    def on_open_file(self, *args):
        pass
    def on_save_file(self, *args):
        pass
        
class FileDialog(FloatLayout):
    path = ObjectProperty(None)
    file = ObjectProperty(None)
    def __init__(self, **kwargs):
        self.mode = kwargs.get('mode')
        super(FileDialog, self).__init__(**kwargs)
        self.register_event_type('on_cancel')
        self.register_event_type('on_submit')
        vbox = self.vbox = BoxLayout(orientation='vertical')
        self.add_widget(vbox)
        self.chooser = FileChooserListView(path=self.path)
        vbox.add_widget(self.chooser)
        self.text_input = TextInput(size_hint_y=None, height=30, multiline=False)
        if self.file:
            self.text_input.text = self.file
        vbox.add_widget(self.text_input)
        hbox = BoxLayout(size_hint_y=None, height=30)
        vbox.add_widget(hbox)
        self.cancel_btn = Button(text='Cancel')
        hbox.add_widget(self.cancel_btn)
        self.confirm_btn = Button(text=self.mode.title())
        hbox.add_widget(self.confirm_btn)
        self.text_input.bind(text=self.on_text_input_text)
        self.chooser.bind(path=self.on_chooser_path, 
                          selection=self.on_chooser_selection, 
                          on_submit=self.on_chooser_submit)
        self.cancel_btn.bind(on_release=self.on_cancel_btn_release)
        self.confirm_btn.bind(on_release=self.on_confirm_btn_release)
    def do_layout(self, *args):
        if self.parent is not None:
            self.pos = self.parent.pos
            self.size = self.parent.size
            self.vbox.pos = self.parent.pos
            self.vbox.size = self.parent.size
        super(FileDialog, self).do_layout(*args)
    def on_text_input_text(self, instance, value):
        if not self.text_input.focus:
            return
        self.file = value
    def on_chooser_path(self, instance, value):
        self.path = value
    def on_chooser_selection(self, instance, value):
        self.file = value[0]
        self.text_input.text = self.file
    def on_chooser_submit(self, *args):
        self.dispatch('on_submit')
    def on_cancel_btn_release(self, *args):
        self.dispatch('on_cancel')
    def on_confirm_btn_release(self, *args):
        if self.file:
            self.dispatch('on_submit')
    def on_cancel(self, *args):
        pass
    def on_submit(self, *args):
        pass
