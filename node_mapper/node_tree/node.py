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
    _saved_attributes = ['parent_id', 'attributes', 'collapsed']
    #_saved_child_objects = ['child_nodes']
    _saved_class_name = 'TreeNode'
    def __init__(self, **kwargs):
        self._parent_id = None
        p = kwargs.get('parent')
        if p is not None:
            kwargs.setdefault('node_tree', p.node_tree)
        super(TreeNode, self).__init__(**kwargs)
        self.bind(parent=self.on_parent_changed, 
                  collapsed=self.on_collapsed_changed, 
                  hidden=self.on_hidden_changed)
        if 'deserialize' not in kwargs:
            self.parent = kwargs.get('parent')
            self.is_root = self.parent is None
        elif self.parent_id is None:
            self.is_root = True
            self.parent = None
        else:
            self.is_root = False
            p = self.node_tree.nodes.get(self.parent_id)
            if p is not None:
                self.parent = p
        self.child_nodes.bind(child_update=self.on_child_nodes_update)
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
        self.emit('pre_delete')
        self.child_nodes.clear()
        self.position.unlink()
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
        if self.init_complete and self.id not in parent.child_nodes:
            parent.child_nodes.add_child(existing_object=self)
        self.hidden = parent.hidden or parent.collapsed
        parent.bind(hidden=self.on_parent_hidden)
        super(TreeNode, self).bind_parent(parent)
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
        node_iter = None
        for node in self.child_nodes.itervalues():
            if node_iter is None:
                node_iter = [node]
            else:
                node_iter = node.walk_nodes()
            for _node in node_iter:
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
    
def test_serialization(filename=None, **kwargs):
    import json
    root1 = test(**kwargs)
    s = root1.node_tree.to_json(json_preset='pretty')
    print REGISTRY.node_classes
    print REGISTRY.tree_classes
    if filename is not None:
        with open(filename, 'w') as f:
            f.write(s)
    cls = root1.node_tree_class
    tree2 = cls(deserialize=json.loads(s))
    return root1, tree2, s
    

if __name__ == '__main__':
    r = test()
