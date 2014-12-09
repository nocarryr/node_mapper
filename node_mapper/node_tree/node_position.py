from node_mapper.node_tree import NodeBase, NodeTree, REGISTRY

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
    _saved_attributes = [
        'x', 
        'y', 
        'width', 
        'height', 
        'v_padding', 
        'h_padding', 
    ]
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
        absolute_pos_set={'default':False}, 
        y_offset={'default':0.}, 
        in_collision={'default':False}, 
    )
    def __init__(self, **kwargs):
        self._updating_position_relative = False
        self._updating_position_absolute = False
        self._adjusting_y_offset_from_children = False
        super(TreeNodePosition, self).__init__(**kwargs)
        self.bind(property_changed=self.on_own_property_changed, 
                  init_complete=self.on_init_complete)
        self.node_tree.bind(x_invert=self.on_node_tree_x_invert, 
                            y_invert=self.on_node_tree_y_invert)
    def get_y_path(self):
        if self.is_root:
            return [0]
        y_path = self.parent.get_y_path()
        y_path.append(self.relative_y)
        return y_path
    def __eq__(self, other):
        if not isinstance(other, TreeNodePosition):
            return False
        return id(self) == id(other)
    def __ne__(self, other):
        return not self.__eq__(other)
    def __lt__(self, other):
        if not self.init_complete:
            return NotImplemented
        if not isinstance(other, TreeNodePosition) or other.init_complete is False:
            return NotImplemented
        return self._cmp_node(other) == -1
    def __le__(self, other):
        if not self.init_complete:
            return NotImplemented
        if not isinstance(other, TreeNodePosition) or other.init_complete is False:
            return NotImplemented
        return self._cmp_node(other) <= 0
    def __gt__(self, other):
        if not self.init_complete:
            return NotImplemented
        if not isinstance(other, TreeNodePosition) or other.init_complete is False:
            return NotImplemented
        return self._cmp_node(other) == 1
    def __ge__(self, other):
        if not self.init_complete:
            return NotImplemented
        if not isinstance(other, TreeNodePosition) or other.init_complete is False:
            return NotImplemented
        return self._cmp_node(other) >= -1
    def _cmp_node(self, other):
        if other == self:
            return 0
        if other not in self.node_tree.nodes_by_x[self.x].values():
            print self.x, other.x
            raise TypeError('cannot compare nodes with different x values')
        y_path = self.get_y_path()
        other_y_path = other.get_y_path()
        for my_y, other_y in zip(y_path, other_y_path):
            #if my_y < 0:
            #    my_y *= -1.
            #if other_y < 0:
            #    other_y *= -1.
            if my_y < other_y:
                return -1
            if my_y > other_y:
                return 1
        return 0
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
    def get_child_nodes_center(self):
        child_len = len(self.child_nodes)
        if not child_len:
            return []
        if child_len == 1:
            return [self.child_nodes.values()[0]]
        children = sorted(self.child_nodes.values())
        if child_len / 2. == child_len / 2:
            return [
                children[(child_len / 2) - 1], 
                children[child_len / 2], 
            ]
        else:
            return [children[child_len / 2]]
    def bind_parent(self, parent):
        self.y_invert = parent.y_invert
        self.x_invert = parent.x_invert
        parent.bind(relative_y=self.update_position_absolute, 
                    x=self.update_position_absolute, 
                    y=self.update_position_absolute)
        parent.child_nodes.bind(child_update=self.on_siblings_childgroup_update)
        if self.init_complete:
            self.update_position_relative()
            self.update_position_absolute()
    def unbind_parent(self, parent):
        self.absolute_pos_set = False
        parent.unbind(self.update_position_absolute)
        parent.child_nodes.unbind(self.on_siblings_childgroup_update)
    def on_child_node_position_changed(self, **kwargs):
        if self.is_root:
            return
        child = kwargs.get('obj')
        ptype = kwargs.get('type')
        if ptype != 'y_offset':
            return
        if self._adjusting_y_offset_from_children:
            return
        if child._updating_position_absolute:
            return
        child_y = None
        center_nodes = self.get_child_nodes_center()
        if len(center_nodes) == 1:
            child_y = center_nodes[0].y
        else:
            l = [n.y for n in center_nodes]
            child_y = min(l) + ((max(l) - min(l)) / 2.)
        if child_y is not None:
            self._adjusting_y_offset_from_children = True
            self.y_offset = (self.y - self.y_offset) + child_y
            self._adjusting_y_offset_from_children = False
    def update_position_relative(self, **kwargs):
        if self.node_tree._deserializing:
            return
        if self._updating_position_relative:
            return
        if self._unlinking:
            return
        if self.parent and self.parent._unlinking:
            return
        self._updating_position_relative = True
        y = self.get_zero_centered_index()
        if self.y_invert:
            y *= -1.
        self.relative_y = float(y)
        self._updating_position_relative = False
    def update_position_absolute(self, **kwargs):
        if self.node_tree._deserializing:
            return
        if self._updating_position_absolute:
            return
        if self.parent is None:
            return
        if self.relative_y is None:
            return
        if self._unlinking or self.parent._unlinking:
            return
        if self.parent._adjusting_y_offset_from_children:
            self.y_offset = 0.
        self._updating_position_absolute = True
        p = self.parent
        w = (self.width + self.h_padding) / 2.
        pw = (p.width + p.h_padding) / 2.
        self.x = p.x + w + pw
        h = self.height + self.v_padding
        self.y = p.y + (h * self.relative_y) + self.y_offset
        self._updating_position_absolute = False
        self.absolute_pos_set = True
    def check_collisions(self, **kwargs):
        single_pass = kwargs.get('single_pass', False)
        resolve = kwargs.get('resolve', True)
        if not self.init_complete:
            return
        if not self.absolute_pos_set:
            return
        in_collision = set()
        for node in sorted(self.node_tree.nodes_by_x[self.x].values()):
            if node is self:
                continue
            if not node.init_complete:
                continue
            if not node.absolute_pos_set:
                continue
            if self.check_collision(node):
                in_collision.add(node)
                if resolve:
                    r = self.resolve_collision(node)
                    if r:
                        in_collision.discard(node)
                if single_pass:
                    break
        self.in_collision == len(in_collision) > 0
    def resolve_collision(self, node):
        y_offset = node.height + node.v_padding
        if node < self:
            if self.y_invert:
                self.y_offset += y_offset
            else:
                self.y_offset -= y_offset
        elif node > self:
            if self.y_invert:
                self.y_offset -= y_offset
            else:
                self.y_offset += y_offset
        return self.check_collision(node) is False
    def on_siblings_childgroup_update(self, **kwargs):
        self.update_position_relative()
    def on_node_tree_x_invert(self, **kwargs):
        self.x_invert = kwargs.get('value')
    def on_node_tree_y_invert(self, **kwargs):
        self.y_invert = kwargs.get('value')
    def on_init_complete(self, **kwargs):
        if kwargs.get('value'):
            self.update_position_relative()
            self.update_position_absolute()
    def on_own_property_changed(self, **kwargs):
        prop = kwargs.get('Property')
        value = kwargs.get('value')
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
        elif prop.name in ['x_invert', 'y_invert']:
            if getattr(self.node_tree, prop.name) != value:
                setattr(self.node_tree, prop.name, value)
            self.update_position_relative()
        super(TreeNodePosition, self).on_own_property_changed(**kwargs)
        
class TreeNodeTree(NodeTree):
    _Properties = dict(
        x_invert={'default':False}, 
        y_invert={'default':False}, 
    )
    _saved_attributes = ['x_invert', 'y_invert']
    _saved_child_objects = ['nodes_by_path']
    def __init__(self, **kwargs):
        self._unlinking = False
        self.unparented_nodes = {}
        self._checking_collisions = False
        self._nodes_in_collision = set()
        self.nodes_by_x = {}
        super(TreeNodeTree, self).__init__(**kwargs)
    @property
    def root_node(self):
        by_x = self.nodes_by_x.get(0., {})
        if not len(by_x):
            return None
        if len(by_x) > 1:
            r = None
            for node in by_x.values():
                if node.parent is None:
                    if r is not None:
                        return None
                    r = node
            return r
        return by_x.values()[0]
    @property
    def nodes_by_path(self):
        d = {}
        i = 0
        for node in self.root_node.walk_nodes():
            d[i] = node
            i += 1
        return d
    @nodes_by_path.setter
    def nodes_by_path(self, value):
        return
    def unlink(self):
        self._unlinking = True
        root = self.root_node
        if root is not None and not root._unlinking:
            root.unlink()
        super(TreeNodeTree, self).unlink()
    def _load_saved_attr(self, d, **kwargs):
        if 'nodes' in d['saved_children']:
            d['saved_children']['nodes'].clear()
        super(TreeNodeTree, self)._load_saved_attr(d, **kwargs)
    def _deserialize_child(self, d):
        node = super(TreeNodeTree, self)._deserialize_child(d)
        for attr in ['x_invert', 'y_invert']:
            setattr(node, attr, getattr(self, attr))
        self.bind_node(node)
        if not node.is_root and node.parent is None:
            if node.parent_id not in self.unparented_nodes:
                self.unparented_nodes[node.parent_id] = set()
            self.unparented_nodes[node.parent_id].add(node)
        if node.id in self.unparented_nodes:
            for other in self.unparented_nodes[node.id]:
                other.parent = node
            del self.unparented_nodes[node.id]
        return node
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
    def add_node(self, node=None, **kwargs):
        node = super(TreeNodeTree, self).add_node(node, **kwargs)
        self.bind_node(node)
        return node
    def remove_node(self, node):
        self.unbind_node(node)
        super(TreeNodeTree, self).remove_node(node)
    def bind_node(self, node):
        x = node.x
        if self.nodes_by_x.get(x) is None:
            self.nodes_by_x[x] = {}
        if self.nodes_by_x[x].get(node.id) == node:
            return
        self.nodes_by_x[x][node.id] = node
        node.bind(x=self.on_node_x_changed, 
                  y=self.on_node_y_changed, 
                  in_collision=self.on_node_in_collision, 
                  init_complete=self.on_node_init_complete)
    def unbind_node(self, node):
        x = node.x
        node.unbind(self.on_node_x_changed)
        if node.id in self.nodes_by_x.get(x, {}):
            del self.nodes_by_x[x][node.id]
    def on_node_x_changed(self, **kwargs):
        if self._unlinking:
            return
        node = kwargs.get('obj')
        value = kwargs.get('value')
        old = kwargs.get('old')
        if old == value:
            return
        if old is not None:
            if node.id in self.nodes_by_x.get(old, {}):
                del self.nodes_by_x[old][node.id]
            if not len(self.nodes_by_x[old]):
                del self.nodes_by_x[old]
        if value not in self.nodes_by_x:
            self.nodes_by_x[value] = {}
        self.nodes_by_x[value][node.id] = node
        if node.init_complete:
            self.check_collisions()
    def on_node_y_changed(self, **kwargs):
        if self._unlinking:
            return
        node = kwargs.get('obj')
        if node.init_complete:
            self.check_collisions()
    def on_node_in_collision(self, **kwargs):
        if self._unlinking:
            return
        node = kwargs.get('obj')
        if kwargs.get('value'):
            self._nodes_in_collision.add(node)
            self.check_collisions()
        else:
            self._nodes_in_collision.discard(node)
    def on_node_init_complete(self, **kwargs):
        if self._unlinking:
            return
        if kwargs.get('value'):
            self.check_collisions()
    def check_collisions(self):
        try:
            self._check_collisions()
        except TypeError:
            self._checking_collisions = False
    def _check_collisions(self):
        if self._unlinking:
            return
        if self._checking_collisions:
            return
        if self._deserializing:
            return
        if len(self.unparented_nodes):
            return
        self._checking_collisions = True
        def do_check(node):
            node.check_collisions(single_pass=True)
            if node.in_collision:
                self._nodes_in_collision.add(node)
        for x in reversed(sorted(self.nodes_by_x.keys())):
            if False in [n.init_complete for n in self.nodes_by_x[x].values()]:
                break
            nodes = sorted(self.nodes_by_x[x].values())
            if len(nodes) / 2 == len(nodes) / 2.:
                center_node = None
            else:
                center_node = nodes[len(nodes) / 2]
            nodes_plus = nodes[len(nodes) / 2:]
            nodes_minus = nodes[:len(nodes) / 2]
            nodes_minus.reverse()
            for node_plus, node_minus in zip(nodes_plus, nodes_minus):
                if center_node is not node_minus:
                    do_check(node_minus)
                if center_node is not node_plus:
                    do_check(node_plus)
        self._checking_collisions = False
        if len(self._nodes_in_collision):
            self.check_collisions()

TreeNodePosition.node_tree_class = TreeNodeTree
REGISTRY.add_tree_class(TreeNodeTree)
TreeNodePosition.node_tree_class = TreeNodeTree
