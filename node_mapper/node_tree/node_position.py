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
        pass
    def _fset_left(self, value):
        pass
    def _fget_top(self):
        pass
    def _fset_top(self, value):
        pass
    
