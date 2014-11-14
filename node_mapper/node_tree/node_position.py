from node_mapper.node_tree import NodeBase, NodeTree

class NodePositionBase(NodeBase):
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
    )
    signals_to_register = ['position_changed']
    def __init__(self, **kwargs):
        super(NodePositionBase, self).__init__(**kwargs)
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
        
class TreeNodePosition(NodePositionBase):
    _Properties = dict(
        relative_x={'default', 1.}, 
        relative_y={'default', 0.}, 
    )
    def __init__(self, **kwargs):
        super(TreeNodePosition, self).__init__(**kwargs)
        self.bind(relative_y=self.update_position_absolute)
    def get_zero_centered_index(self):
        raise NotImplementedError('must be implemented by subclasses')
    def iter_neighbors(self):
        for node in self.node_tree.iter_nodes_by_x(self.x):
            if node is self:
                continue
            yield node
    def bind_parent(self, parent):
        super(TreeNodePosition, self).bind_parent(parent)
        parent.bind(relative_y=self.update_position_absolute, 
                    x=self.update_position_absolute, 
                    y=self.update_position_absolute)
        parent.child_nodes.bind(child_update=self.update_position_relative)
        self.update_position_relative()
    def unbind_parent(self, parent):
        parent.unbind(self.update_position_absolute)
        parent.child_nodes.unbind(self.update_position_relative)
        super(TreeNodePosition, self).unbind_parent(parent)
    def update_position_relative(self, **kwargs):
        self.relative_y = self.get_zero_centered_index()
    def update_position_absolute(self, **kwargs):
        pass
        
class TreeNodeTree(NodeTree):
    def __init__(self, **kwargs):
        super(TreeNodeTree, self).__init__(**kwargs)
        self.nodes_by_x = {}
    def iter_nodes_by_x(self, x=None):
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
        return [node for node in self.iter_nodes_by_x(x)]
    def on_nodes_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        node = kwargs.get('obj')
        if mode == 'add':
            x = node.x
            if self.nodes_by_x.get(x) is None:
                self.nodes_by_x[x] = {}
            if self.nodes_by_x[x].get(node.id) == node:
                return
            self.nodes_by_x[x][node.id] = node
            node.bind(x=self.on_node_x_changed)
        elif mode == 'remove':
            x = node.x
            node.unbind(self.on_node_x_changed)
            if node.id in self.nodes_by_x.get(x, {}):
                del self.nodes_by_x[x][node.id]
    def on_node_x_changed(self, **kwargs):
        node = kwargs.get('obj')
        value = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
            if node.id in self.nodes_by_x.get(old, {}):
                del self.nodes_by_x[old][node.id]
        if value not in self.nodes_by_x:
            self.nodes_by_x[value] = {}
        self.nodes_by_x[value][node.id] = node

TreeNodePosition.node_tree_class = TreeNodeTree
