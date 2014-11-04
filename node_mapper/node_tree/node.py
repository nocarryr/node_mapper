from node_mapper.nomadic_recording_lib.Bases import BaseObject
from node_mapper.nomadic_recording_lib.Bases.misc import setID

class Node(BaseObject):
    _Properties = dict(
        name={'default':''}, 
        attributes={'type':dict}, 
        collapsed={'default':False}, 
        hidden={'default':False}, 
        parent={'ignore_type':True, 'fvalidate':'fvalidate_parent'}, 
        updating_child_positions={'default':False}, 
    )
    _ChildGroups = dict(child_nodes={'child_class':'__self__'})
    signals_to_register = ['position_changed', 'pre_delete']
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.id = setID(kwargs.get('id'))
        self.name = kwargs.get('name', '')
        pkwargs = kwargs.get('position', {})
        pkwargs.setdefault('node', self)
        self.bind(parent=self.on_parent_changed, collapsed=self.on_collapsed_changed)
        p = kwargs.get('parent')
        if p is None and getattr(self, 'ChildGroup_parent', None) is not None:
            p = self.ChildGroup_parent.parent_obj
        self.parent = p
        self.is_root = self.parent is None
        if self.is_root:
            self.nodes_flat = {}
        else:
            self.nodes_flat = self.root_node.nodes_flat
        self.nodes_flat[self.id] = self
        self.position = NodePosition(**pkwargs)
        self.bounds = self.position.bounds
        self.child_nodes.bind(child_update=self.on_child_nodes_update)
        self.position.bind(x=self.on_position_changed, 
                           y=self.on_position_changed, 
                           relative_y=self.on_relative_position_changed)
    @property
    def root_node(self):
        if self.is_root:
            return self
        return self.parent.root_node
    def unlink(self):
        self.emit('pre_delete')
        if self.id in self.nodes_flat:
            del self.nodes_flat[self.id]
        self.child_nodes.clear()
        self.position.unlink()
        super(Node, self).unlink()
    def add_child(self, **kwargs):
        kwargs.setdefault('parent', self)
        return self.child_nodes.add_child(**kwargs)
    def del_child(self, child):
        self.child_nodes.del_child(child)
    def fvalidate_parent(self, value):
        if not hasattr(self, 'is_root'):
            return True
        if self.is_root and value is not None:
            return False
        return True
    def on_parent_changed(self, **kwargs):
        p = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
            old.unbind(self)
            old.child_nodes.detach_child(self)
            if self.id not in p.child_nodes:
                p.child_nodes.add_child(existing_object=self)
        self.hidden = p.hidden or p.collapsed
        p.bind(hidden=self.on_parent_hidden)
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
    def on_child_nodes_update(self, **kwargs):
        mode = kwargs.get('mode')
        child = kwargs.get('obj')
        if mode == 'add':
            child.bind(position_changed=self.on_child_node_position_changed)
            self.update_child_positions_relative()
        elif mode == 'remove':
            child.unbind(self)
    def update_child_positions_relative(self):
        if self.updating_child_positions:
            return
        self.updating_child_positions = True
        pos_changed = False
        for child in self.child_nodes.itervalues():
            d = child.position.calc_relative()
            if d['y']:
                pos_changed = True
        self.updating_child_positions = False
        if pos_changed:
            #self.emit('position_changed', type='relative')
            self.root_node.update_child_positions_absolute()
    def update_child_positions_absolute(self):
        if self.updating_child_positions:
            return
        self.updating_child_positions = True
        self.position.calc_absolute()
        for child in self.child_nodes.itervalues():
            child.update_child_positions_absolute()
        self.updating_child_positions = False
    def on_position_changed(self, **kwargs):
        self.emit('position_changed', position=self.position, type='absolute')
    def on_relative_position_changed(self, **kwargs):
        self.emit('position_changed', position=self.position, type='relative')
    def on_child_node_position_changed(self, **kwargs):
        if self.updating_child_positions:
            return
        if self.is_root:
            self.update_child_positions_absolute()
    def __repr__(self):
        return 'Node: %s' % (self)
    def __str__(self):
        if not self.name:
            return self.id
        return self.name
    
class NodePosition(BaseObject):
    _Properties = dict(
        x={'default':0.}, 
        y={'default':0.}, 
        relative_x={'default':0.}, 
        relative_y={'default':0.}, 
        center_y={'default':0.}, 
        in_conflict={'default':False}, 
    )
    def __init__(self, **kwargs):
        self._old_parent = None
        self.resolving_conflicts = False
        super(NodePosition, self).__init__(**kwargs)
        self.node = kwargs.get('node')
        self.x = kwargs.get('x', 0.)
        self.y = kwargs.get('y', 0.)
        self.relative_x = kwargs.get('relative_x', 0.)
        self.relative_y = kwargs.get('relative_y', 0.)
        self.offset_y = kwargs.get('offset_y', 0.)
        self.conflicting_positions = set()
        if self.node.is_root:
            self.all_positions = set()
        else:
            self.all_positions = self.parent_position.all_positions
            self.bind(in_conflict=self.parent_position.on_child_conflict)
        self.all_positions.add(self)
        self.bounds = NodeBounds(node=self.node, position=self)
        self.node.bind(parent=self.on_node_parent_changed)
    @property
    def parent_position(self):
        if self.node.is_root:
            return None
        p = self.node.parent
        if p is None:
            return None
        return p.position
    def unlink(self):
        self.all_positions.discard(self)
        self.in_conflict = False
        p = self.parent_position
        if p is not None:
            self.unbind(p)
        super(NodePosition, self).unlink()
    def calc_relative(self):
        n = self.node
        def calc_index():
            i = n.Index
            child_group = n.parent.child_nodes
            all_index = sorted(child_group.indexed_items.keys())
            all_index.reverse()
            i = all_index.index(i)
            child_len = len(all_index)
            mid_point = (child_len / 2.)
            self.center_y = mid_point
            return i - mid_point + .5
        if n.is_root:
            x = 0.
            y = 0.
        else:
            x = 1.
            y = calc_index()
        d = {}
        d['x'] = self.relative_x != x
        d['y'] = self.relative_y != y
        print '%s x: %s, y: %s, center_y: %s' % (self.node.name, x, y, self.center_y)
        self.relative_x = x
        self.relative_y = y
        return d
    def calc_absolute(self):
        p = self.parent_position
        if p is None:
            return
        offset_y = self.offset_y
        if offset_y > 0:
            if self.relative_y < self.center_y:
                offset_y = offset_y * -1.
        self.x = p.x + self.relative_x
        self.y = p.y + self.relative_y + offset_y
        print 'calc_absolute: ', str(self)
        self.check_conflicts()
    def check_conflicts(self):
        x = self.x
        y = self.y
        for pos in self.all_positions:
            if pos.x == x and pos.y == y:
                self.conflicting_positions.add(pos)
            else:
                self.conflicting_positions.discard(pos)
        self.in_conflict = len(self.conflicting_positions) == 0
    def on_child_conflict(self, **kwargs):
        if not self.node.is_root:
            self.parent_position.on_child_conflict(**kwargs)
            return
        def find_conflict_ancestor(obj):
            p = obj.parent_position
            if p is None:
                p = obj._old_position
            if p == self:
                return obj
            return find_conflict_ancestor(p)
        obj = find_conflict_ancestor(kwargs.get('obj'))
        if kwargs.get('value'):
            self.conflicting_positions.add(obj)
        else:
            self.conflicting_positions.discard(obj)
        if self.resolving_conflicts:
            return
        self.resolving_conflicts = True
        while len(self.resolving_conflicts):
            for node in self.node.child_nodes.itervalues():
                pos = node.position
                pos.offset_y += .5
                pos.calc_absolute()
        self.resolving_conflicts = False
    def on_node_parent_changed(self, **kwargs):
        p = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
            self.conflicting_positions.clear()
            self._old_parent = old
            self.in_conflict = False
            self.unbind(old.position)
            self.all_positions.discard(self)
            self._old_parent = None
        if p is not None:
            self.offset_y = 0.
            self.bind(in_conflict=p.on_child_conflict)
    def __repr__(self):
        return str(self)
    def __str__(self):
        return '%s position (%s, %s)' % (self.node, self.x, self.y)
    
class NodeBounds(BaseObject):
    _Properties = dict(
        left={'default':-50.}, 
        top={'default':25.}, 
        x={'default':0.}, 
        y={'default':0.}, 
        width={'default':100.}, 
        height={'default':50.}, 
        outer_bounds={'default':{'x':150., 'y':75.}}, 
    )
    def __init__(self, **kwargs):
        super(NodeBounds, self).__init__(**kwargs)
        self.node = kwargs.get('node')
        self.position = kwargs.get('position')
        self.position.bind(x=self.on_position_changed,
                           y=self.on_position_changed, 
                           in_conflict=self.on_position_conflict_changed)
        for attr in ['width', 'height', 'padding']:
            if attr in kwargs:
                if attr == 'padding':
                    for key, val in kwargs.get('padding').iteritems():
                        self.padding[key] = val
                setattr(self, attr, kwargs.get(attr))
        self.refresh()
    def refresh(self):
        pos = self.position
        p_pos = pos.parent_position
        if p_pos is None:
            return
        d = {}
        for key in ['x', 'y']:
            d[key] = self.outer_bounds[key] * getattr(pos, key)
            setattr(self, key, d[key])
        self.left = d['x'] - (self.width / 2)
        self.top = d['y'] + (self.height / 2)
        print self.x, self.y
    def on_position_changed(self, **kwargs):
        if self.position.in_conflict:
            return
        self.refresh()
    def on_position_conflict_changed(self, **kwargs):
        if kwargs.get('value') is False:
            self.refresh()
        
        
def test():
    p = Node(name='root')
    p.add_child(name='child1')
    p.add_child(name='child2')
    p.add_child(name='child3')
    p.add_child(name='child3')
    return p
