from node_mapper.nomadic_recording_lib.Bases import BaseObject

class NodePosition(BaseObject):
    _Properties = dict(
        x_invert={'default':False}, 
        y_invert={'default':False}, 
        x={'default':0.}, 
        y={'default':0.}, 
        width={'default':100.}, 
        height={'default':30.}, 
        v_padding={'default':25.}, 
        h_padding={'default':25.}, 
        left={'type':float, 'fget':'_fget_left', 'fset':'_fset_left'}, 
        top={'type':float, 'fget':'_fget_top', 'fset':'_fset_top'}, 
        relative_x={'default', 0.}, 
        relative_y={'default', 0.}, 
    )
    def __init__(self, **kwargs):
        super(NodePosition, self).__init__(**kwargs)
    def _fget_left(self):
        w = self.width / 2.
        if self.x_invert:
            value = self.x + w
        else:
            value = self.x - w
        return value
    def _fset_left(self, value):
        w = self.width / 2.
        self.Properties['left'].set_value(value)
        if self.x_invert:
            self.x = value + w
        else:
            self.x = value - w
    def _fget_top(self):
        h = self.height / 2.
        if self.y_invert:
            value = self.y - h
        else:
            value = self.y + h
        return value
    def _fset_top(self, value):
        h = self.height / 2.
        self.Properties['top'].set_value(value)
        if self.y_invert:
            self.y = value + h
        else:
            self.y = value - h
        
    
