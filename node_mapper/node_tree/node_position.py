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
        right={'type':float, 'fget':'_fget_right', 'fset':'_fset_right'}, 
        top={'type':float, 'fget':'_fget_top', 'fset':'_fset_top'}, 
        bottom={'type':float, 'fget':'_fget_bottom', 'fset':'_fset_bottom'}, 
    )
    signals_to_register = ['position_changed']
    def __init__(self, **kwargs):
        super(NodePositionBase, self).__init__(**kwargs)
        self.x_invert = kwargs.get('x_invert', False)
        self.y_invert = kwargs.get('y_invert', False)
        self.bind(property_changed=self.on_own_property_changed)
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
    def _fget_right(self):
        w = self.width / 2.
        if self.x_invert:
            value = self.x - w
        else:
            value = self.x + w
        return value
    def _fset_right(self, value):
        w = self.width / 2.
        self.Properties['right'].set_value(value)
        if self.x_invert:
            self.x = value - w
        else:
            self.x = value + w
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
    def _fget_bottom(self):
        h = self.height / 2.
        if self.y_invert:
            value = self.y + h
        else:
            value = self.y - h
        return value
    def _fset_bottom(self, value):
        h = self.height / 2.
        self.Properties['bottom'].set_value(value)
        if self.y_invert:
            self.y = value - h
        else:
            self.y = value + h
    def check_collision(self, node):
        if self.x_invert:
            if node.left < self.right:
                return False
            if node.right > self.left:
                return False
        else:
            if node.left > self.right:
                return False
            if node.right < self.left:
                return False
        if self.y_invert:
            if node.top > self.bottom:
                return False
            if node.bottom < self.top:
                return False
        else:
            if node.top < self.bottom:
                return False
            if node.bottom > self.top:
                return False
        return True
    def on_other_node_x_invert(self, **kwargs):
        value = kwargs.get('value')
        if value == self.x_invert:
            return
        self.Properties['x_invert'].value = value
    def on_other_node_y_invert(self, **kwargs):
        value = kwargs.get('value')
        if value == self.y_invert:
            return
        self.Properties['y_invert'].value = value
    def on_node_tree_nodes_update(self, **kwargs):
        mode = kwargs.get('mode')
        node = kwargs.get('obj')
        if mode == 'add':
            node.bind(x_invert=self.on_other_node_x_invert, 
                      y_invert=self.on_other_node_y_invert)
        elif mode == 'remove':
            node.unbind(self.on_other_node_x_invert, 
                        self.on_other_node_y_invert)
    def on_own_property_changed(self, **kwargs):
        prop = kwargs.get('Property')
        if prop.name in ['x', 'y']:
            kwargs = kwargs.copy()
            kwargs['type'] = 'absolute'
            self.emit('position_changed', **kwargs)
        elif prop.name in ['x_invert', 'y_invert']:
            kwargs = kwargs.copy()
            kwargs['type'] = 'invert'
            self.emit('position_changed', **kwargs)
        elif prop.name in ['width', 'height', 'h_padding', 'v_padding']:
            kwargs = kwargs.copy()
            kwargs['type'] = 'size'
            self.emit('position_changed', **kwargs)
            
        
class TreeNodePosition(NodePositionBase):
    _Properties = dict(
        relative_x={'default':1.}, 
        relative_y={'type':float}, 
        y_offset={'default':0.}, 
    )
    def __init__(self, **kwargs):
        self._updating_position_relative = False
        self._updating_position_absolute = False
        super(TreeNodePosition, self).__init__(**kwargs)
        self.bind(property_changed=self.on_own_property_changed)
    def get_zero_centered_index(self):
        raise NotImplementedError('must be implemented by subclasses')
    def iter_neighbors(self):
        for node in self.node_tree.iter_nodes_by_x(self.x):
            if node is self:
                continue
            yield node
    def iter_siblings_outside_first(self):
        if self.is_root:
            key_iter = []
        else:
            cgroup = self.parent.child_nodes
            keys = cgroup.indexed_items.keys()
            zc_keys = [cgroup.get_zero_centered(index=key) for key in keys]
            key_iter = []
            while len(zc_keys):
                key = min(zc_keys)
                i = zc_keys.index(key)
                key_iter.append(keys[i])
                zc_keys.remove(key)
                if not len(zc_keys):
                    break
                key = max(zc_keys)
                i = zc_keys.index(key)
                key_iter.append(keys[i])
                zc_keys.remove(key)
        for key in key_iter:
            yield cgroup.indexed_items[key]
    def bind_parent(self, parent):
        self.y_invert = parent.y_invert
        self.x_invert = parent.x_invert
        parent.bind(relative_y=self.update_position_absolute, 
                    x=self.update_position_absolute, 
                    y=self.update_position_absolute)
        parent.child_nodes.bind(child_update=self.on_siblings_childgroup_update)
        self.update_position_relative()
    def unbind_parent(self, parent):
        parent.unbind(self.update_position_absolute)
        parent.child_nodes.unbind(self.on_siblings_childgroup_update)
    def on_child_node_position_changed(self, **kwargs):
        ptype = kwargs.get('type')
        if ptype == 'absolute':
            self.update_position_absolute()
    def update_position_relative(self, **kwargs):
        if self._updating_position_relative:
            return
        self._updating_position_relative = True
        y = self.get_zero_centered_index()
        if self.y_invert:
            y *= -1.
        self.relative_y = float(y)
        self._updating_position_relative = False
    def update_position_absolute(self, **kwargs):
        if self._updating_position_absolute:
            return
        if self.parent is None:
            return
        self._updating_position_absolute = True
        p = self.parent
        w = (self.width + self.h_padding) / 2.
        pw = (p.width + p.h_padding) / 2.
        self.x = p.x + w + pw
        h = self.height + self.v_padding
        self.y = p.y + (h * self.relative_y) + self.y_offset
        self._updating_position_absolute = False
    def check_neighbors(self):
        for node in self.iter_neighbors():
            if self.check_collision(node):
                self.resolve_collision(node)
    def resolve_collision(self, node):
        pass
    def on_siblings_childgroup_update(self, **kwargs):
        self.update_position_relative()
    def on_own_property_changed(self, **kwargs):
        prop = kwargs.get('Property')
        if prop.name in ['relative_x', 'relative_y']:
            kwargs = kwargs.copy()
            kwargs['type'] = 'relative'
            self.emit('position_changed', **kwargs)
            self.update_position_absolute()
        elif prop.name == 'y_offset':
            kwargs = kwargs.copy()
            kwargs['type'] = 'y_offset'
            self.emit('position_changed', **kwargs)
            self.update_position_absolute()
        super(TreeNodePosition, self).on_own_property_changed(**kwargs)
        
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
    def get_nodes_by_x(self, x=None):
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
