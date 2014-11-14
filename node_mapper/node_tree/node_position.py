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
        root = self.get_root()
        if root is self:
            self.position_collection = NodePositionCollection()
        else:
            self.position_collection = self.get_root().position_collection
    def get_root(self):
        raise NotImplementedError('must be implemented by subclasses')
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
    def iter_neighbors(self):
        for node in self.position_collection.iter_nodes(self.relative_x):
            if node is self:
                continue
            yield node
        
class NodePositionCollection(BaseObject):
    def __init__(self, **kwargs):
        super(NodePositionCollection, self).__init__(**kwargs)
        self.register_signal('node_added', 'node_removed')
        self.nodes_by_x = {}
        self.nodes_by_id = {}
    def iter_nodes(self, x=None):
        by_x = self.nodes_by_x
        if x is None:
            x_iter = sorted(by_x.keys())
        else:
            x_iter = [x]
        for x in x_iter:
            if x not in by_x:
                continue
            for node in by_x[x].itervalues():
                yield node
    def get_nodes(self, x=None):
        return [node for node in self.iter_nodes(x)]
    def add_node(self, node):
        x = node.relative_x
        if self.nodes_by_x.get(x) is None:
            self.nodes_by_x[x] = {}
        if self.nodes_by_x[x].get(node.id) == node:
            return
        if node.id not in self.nodes_by_id:
            self.nodes_by_id[node.id] = node
        self.nodes_by_x[x][node.id] = node
        node.bind(relative_x=self.on_node_relative_x)
        self.emit('node_added', node=node)
    def del_node(self, node):
        x = node.relative_x
        node.unbind(self)
        if node.id in self.nodes_by_x.get(x, {}):
            del self.nodes_by_x[x][node.id]
        elif node.id in self.nodes_by_id:
            for d in self.nodes_by_x.itervalues():
                if node.id in d:
                    del d[node.id]
        if node.id in self.nodes_by_id:
            del self.nodes_by_id[node.id]
        self.emit('node_removed', node=node)
    def on_node_relative_x(self, **kwargs):
        node = kwargs.get('obj')
        value = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
            if node.id in self.nodes_by_x.get(old, {}):
                del self.nodes_by_x[old][node.id]
        if value not in self.nodes_by_x:
            self.nodes_by_x[value] = {}
        self.nodes_by_x[value][node.id] = node
