from kivy.properties import ObjectProperty
from kivy.uix.actionbar import ActionBar
from kivy.uix.floatlayout import FloatLayout

    
class MenuBar(ActionBar):
    pass
    
class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
