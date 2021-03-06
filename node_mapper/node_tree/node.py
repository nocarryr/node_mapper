from node_mapper.node_tree import REGISTRY
from node_mapper.node_tree.node_position import TreeNodePosition

class TreeNode(TreeNodePosition):
    _Properties = dict(
        parent={'ignore_type':True, 'fvalidate':'_fvalidate_parent'}, 
        attributes={'type':dict}, 
        collapsed={'default':False}, 
        hidden={'default':False}, 
        updating_child_positions={'default':False}, 
    )
    _ChildGroups = dict(child_nodes={'child_class':'__self__', 
                                     'zero_centered':True})
    _saved_attributes = ['Index', 'parent_id', 'attributes', 'collapsed']
    _saved_class_name = 'TreeNode'
    def __init__(self, **kwargs):
        self._unlinking = False
        self._parent_id = None
        p = kwargs.get('parent')
        if p is not None:
            kwargs.setdefault('node_tree', p.node_tree)
        super(TreeNode, self).__init__(**kwargs)
        self.bind(parent=self.on_parent_changed, 
                  collapsed=self.on_collapsed_changed, 
                  hidden=self.on_hidden_changed)
        self.child_nodes.bind(child_update=self.on_child_nodes_update)
        if 'deserialize' not in kwargs:
            parent = kwargs.get('parent')
            self.is_root = parent is None
            self.parent = parent
        else:
            if self.parent_id is None:
                self.is_root = True
                self.parent = None
            else:
                self.is_root = False
                p = self.node_tree.nodes.get(self.parent_id)
                if p is not None:
                    self.parent = p
        if self.is_root:
            self.init_complete = True
    @property
    def root_node(self):
        if self.is_root:
            return self
        return self.parent.root_node
    @property
    def parent_id(self):
        return self._parent_id
    @parent_id.setter
    def parent_id(self, value):
        self._parent_id = value
    def get_zero_centered_index(self):
        if self.parent is None:
            return 0.
        i = self.parent.child_nodes.get_zero_centered(child=self)
        return float(i)
    def unlink(self):
        self._unlinking = True
        self.emit('pre_delete')
        self.child_nodes.unbind(self)
        for child in self.child_nodes.values()[:]:
            child.unlink()
        if self.parent:
            self.parent = None
        super(TreeNode, self).unlink()
    def _fvalidate_parent(self, value):
        if not hasattr(self, 'is_root'):
            return True
        if self.is_root and value is not None:
            return False
        return True
    def add_child(self, **kwargs):
        kwargs.setdefault('parent', self)
        return self.child_nodes.add_child(**kwargs)
    def del_child(self, child):
        self.child_nodes.del_child(child)
    def bind_parent(self, parent):
        if self.id not in parent.child_nodes:
            parent.child_nodes.add_child(existing_object=self)
        self.hidden = parent.hidden or parent.collapsed
        parent.bind(hidden=self.on_parent_hidden)
        super(TreeNode, self).bind_parent(parent)
        if not self.init_complete:
            self.init_complete = True
    def unbind_parent(self, parent):
        super(TreeNode, self).unbind_parent(parent)
        parent.unbind(self)
        parent.child_nodes.detach_child(self)
        self.init_complete = False
    def on_parent_changed(self, **kwargs):
        p = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
           self.unbind_parent(old)
        if p is not None:
            self.parent_id = p.id
            self.bind_parent(p)
        elif self.init_complete:
            self.parent_id = None
    def iter_siblings(self):
        if self.is_root:
            s_iter = []
        else:
            s_iter = self.parent.child_nodes.itervalues()
        for sibling in s_iter:
            if sibling == self:
                continue
            yield sibling
    def walk_nodes(self):
        self_yielded = False
        if len(self.child_nodes):
            child_iter = self.child_nodes.itervalues()
        else:
            child_iter = None
        node_iter = None
        walking_children = True
        while walking_children:
            if not self_yielded:
                _node = self
                self_yielded = True
            elif node_iter is None:
                if child_iter is None:
                    walking_children = False
                    node_iter = None
                    _node = None
                else:
                    try:
                        child = child_iter.next()
                        node_iter = child.walk_nodes()
                    except StopIteration:
                        walking_children = False
                        node_iter = None
                        _node = None
            if node_iter is not None:
                try:
                    _node = node_iter.next()
                except StopIteration:
                    _node = None
                    node_iter = None
            if _node is not None:
                yield _node
            
    def check_collision(self, node):
        if self.hidden:
            return False
        if node.hidden:
            return False
        return super(TreeNode, self).check_collision(node)
    def on_parent_hidden(self, **kwargs):
        value = kwargs.get('value')
        if value:
            self.hidden = True
        elif not self.parent.collapsed:
            self.hidden = False
    def on_collapsed_changed(self, **kwargs):
        if kwargs.get('value') or self.hidden:
            hidden = True
        else:
            hidden = False
        for c in self.child_nodes.itervalues():
            c.hidden = hidden
        self.y_offset = 0.
        self.node_tree.check_collisions()
    def on_hidden_changed(self, **kwargs):
        if kwargs.get('value') is False:
            self.in_collision = False
        self.y_offset = 0.
        self.node_tree.check_collisions()
    def on_child_nodes_update(self, **kwargs):
        mode = kwargs.get('mode')
        child = kwargs.get('obj')
        if mode == 'add':
            self.y_offset = 0.
            child.bind(position_changed=self.on_child_node_position_changed)
            self.node_tree.check_collisions()
        elif mode == 'remove':
            self.y_offset = 0.
            child.unbind(self.on_child_node_position_changed)
            self.node_tree.check_collisions()

REGISTRY.add_node_class(TreeNode)

def test(**kwargs):
    kwargs.setdefault('name', 'root')
    p = TreeNode(**kwargs)
    c1 = p.add_child(name='child1')
    c2 = p.add_child(name='child2')
    p.add_child(name='child3')
    for i in range(3):
        c1.add_child(name='grandchild%d' % (i+1))
    c2.add_child(name='grandchildb1')
    return p
    
def test_serialization(**kwargs):
    root1 = test(**kwargs)
    s = root1.node_tree.to_json(json_preset='pretty')
    print REGISTRY.node_classes
    print REGISTRY.tree_classes
    with open('test.json', 'w') as f:
        f.write(s)
    cls = root1.node_tree_class
    tree2 = cls.from_json(s)
    with open('test2.json', 'w') as f:
        f.write(tree2.to_json(json_preset='pretty'))
    return root1, tree2, s
    

if __name__ == '__main__':
    r = test()
