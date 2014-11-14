from node_mapper.node_tree.node_position import TreeNodePosition

class TreeNode(TreeNodePosition):
    _Properties = dict(
        parent={'ignore_type':True, 'fvalidate':'_fvalidate_parent'}, 
        attributes={'type':dict}, 
        collapsed={'default':False}, 
        hidden={'default':False}, 
        updating_child_positions={'default':False}, 
        init_complete={'default':False}, 
    )
    _ChildGroups = dict(child_nodes={'child_class':'__self__', 
                                     'zero_centered':True})
    def __init__(self, **kwargs):
        super(TreeNode, self).__init__(**kwargs)
        self.bind(parent=self.on_parent_changed, 
                  collapsed=self.on_collapsed_changed)
        self.parent = kwargs.get('parent')
        self.is_root = self.parent is None
        self.child_nodes.bind(child_update=self.on_child_nodes_update)
    @property
    def root_node(self):
        if self.is_root:
            return self
        return self.parent.root_node
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
        if self.id not in parent.child_nodes:
            parent.child_nodes.add_child(existing_object=self)
        self.hidden = parent.hidden or parent.collapsed
        parent.bind(hidden=self.on_parent_hidden)
    def unbind_parent(self, parent):
        parent.unbind(self)
        parent.child_nodes.detach_child(self)
        self.init_complete = False
    def on_parent_changed(self, **kwargs):
        p = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
           self.unbind_parent(old)
        if p is not None:
            self.bind_parent(p)
        self.update_position_relative()
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
        self.root_node.update_child_positions_absolute()
    def on_child_nodes_update(self, **kwargs):
        mode = kwargs.get('mode')
        child = kwargs.get('obj')
        if mode == 'add':
            child.bind(position_changed=self.on_child_node_position_changed)
            self.update_child_positions_relative()
        elif mode == 'remove':
            child.unbind(self)
        elif mode == 'Index':
            self.update_child_positions_relative()
    def __repr__(self):
        return 'Node: %s' % (self)
    def __str__(self):
        if not self.name:
            return self.id
        return self.name
    

def test():
    p = TreeNode(name='root')
    c = p.add_child(name='child1')
    p.add_child(name='child2')
    p.add_child(name='child3')
    for i in range(3):
        c.add_child(name='grandchild%d' % (i+1))
    return p

if __name__ == '__main__':
    r = test()
