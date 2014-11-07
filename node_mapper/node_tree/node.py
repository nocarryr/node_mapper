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
        init_complete={'default':False}, 
    )
    _ChildGroups = dict(child_nodes={'child_class':'__self__', 
                                     'zero_centered':True})
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
            self.init_complete = True
        else:
            self.nodes_flat = self.root_node.nodes_flat
        self.nodes_flat[self.id] = self
        self.position = NodePosition(**pkwargs)
        self.bounds = self.position.bounds
        self.child_nodes.bind(child_update=self.on_child_nodes_update)
        self.position.bind(x=self.on_position_changed, 
                           y=self.on_position_changed, 
                           relative_y=self.on_relative_position_changed, 
                           working=self.on_position_working_changed)
    @property
    def root_node(self):
        if self.is_root:
            return self
        return self.parent.root_node
    @property
    def zero_centered_index(self):
        if self.parent is None:
            return 0.
        i = self.parent.child_nodes.get_zero_centered(child=self)
        return float(i)
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
            self.init_complete = False
            if self.id not in p.child_nodes:
                p.child_nodes.add_child(existing_object=self)
        self.hidden = p.hidden or p.collapsed
        p.bind(hidden=self.on_parent_hidden)
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
        if True:#pos_changed or (self.init_complete and len(self.child_nodes) == 1):
            #self.emit('position_changed', type='relative')
            self.root_node.update_child_positions_absolute()
    def update_child_positions_absolute(self):
        if self.updating_child_positions:
            return
        #if self.is_root and self.position.working:
        #    return
        self.updating_child_positions = True
        self.position.calc_absolute()
        for child in self.child_nodes.itervalues():
            child.update_child_positions_absolute()
        if self.is_root:
            self.position.working = False
        elif not self.root_node.position.working:
            self.position.working = False
            self.init_complete = True
        self.updating_child_positions = False
    def on_position_changed(self, **kwargs):
        self.emit('position_changed', position=self.position, type='absolute')
    def on_relative_position_changed(self, **kwargs):
        self.emit('position_changed', position=self.position, type='relative')
    def on_position_working_changed(self, **kwargs):
        value = kwargs.get('value')
        if not value and not self.position.in_conflict and not self.init_complete:
            self.init_complete = True
            print self, 'init_complete'
    def on_child_node_position_changed(self, **kwargs):
        if self.updating_child_positions:
            return
        if self.is_root and kwargs.get('type') == 'relative':
            self.update_child_positions_absolute()
        else:
            self.emit('position_changed', **kwargs)
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
        y_offset={'default':0.}, 
        in_conflict={'default':False}, 
        working={'default':False}, 
        y_size={'default':1.}, 
        y_size_max={'default':1.}, 
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
        self.y_offset = kwargs.get('y_offset', 0.)
        self.conflicting_positions = set()
        self.bind(property_changed=self.on_own_property_changed)
        if self.node.is_root:
            self.all_positions = set()
            self.all_positions_xy = {}
        else:
            self.all_positions = self.parent_position.all_positions
            self.all_positions_xy = self.parent_position.all_positions_xy
            self.bind(in_conflict=self.parent_position.on_child_conflict, 
                      y_size=self.on_y_size, 
                      y_size_max=self.parent_position.on_child_y_size_max, 
                      working=self.parent_position.on_child_working, 
                      x=self.on_x_changed)
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
    @property
    def root_position(self):
        if self.node.is_root:
            return self
        return self.parent_position.root_position
    def unlink(self):
        self.all_positions.discard(self)
        self.in_conflict = False
        p = self.parent_position
        if p is not None:
            self.unbind(p)
        super(NodePosition, self).unlink()
    def iter_children(self):
        for n in self.node.child_nodes.itervalues():
            yield n.position
    def iter_siblings(self):
        for n in self.node.iter_siblings():
            yield n.position
    def walk_positions(self):
        for node in self.node.walk_nodes():
            yield node.position
    def calc_relative(self):
        n = self.node
        if n.is_root:
            x = 0.
            y = 0.
        else:
            x = 1.
            y = n.zero_centered_index
            if y != 0:
                y = y * -1.
            y = float(y)
        d = {}
        d['x'] = self.relative_x != x
        d['y'] = self.relative_y != y
        #print '%s x: %s, y: %s' % (self.node.name, x, y)
        self.relative_x = x
        self.relative_y = y
        return d
    def calc_y_size(self):
        self.y_size_max = 0.
        self.y_size = float(len(self.node.child_nodes.values()))
        if self.y_size == 0.:
            self.y_offset = 0.
            return
        for pos in self.walk_positions():
            pos.calc_y_size()
        y_offset = (self.y_size + 1) / 2.
        if self.relative_y < 0:
            y_offset *= -1.
        self.y_offset = y_offset
    def calc_absolute(self):
        p = self.parent_position
        if p is None:
            return
        self.working = True
        self.x = p.x + self.relative_x
        self.calc_y_size()
        self.y = p.y + self.relative_y + self.y_offset
        #print 'calc_absolute: ', str(self)
        r = self.check_conflicts()
        self.working = False
        return r
    def on_sibling_in_conflict(self, **kwargs):
        pass
    def check_conflicts(self, full_check=False):
        return
        x = self.x
        y = self.y
        in_conflict = False
        for pos in self.all_positions:
            if full_check:
                r = pos._check_conflicts()
                if r:
                    in_conflict = True
            else:
                if pos == self:
                    continue
                if pos.x == x and pos.y == y:
                    self.conflicting_positions.add(pos)
                    #pos.conflicting_positions.add(self)
                    #pos.in_conflict = True
                    self.in_conflict = True
                    in_conflict = True
                else:
                    self.conflicting_positions.discard(pos)
                    #pos.conflicting_positions.discard(self)
        self.in_conflict = len(self.conflicting_positions) == 0
        return in_conflict
    def _check_conflicts(self):
        x = self.x
        y = self.y
        for pos in self.all_positions:
            if pos == self:
                continue
            if pos.x == x and pos.y == y:
                self.conflicting_positions.add(pos)
                #pos.conflicting_positions.add(self)
                #pos.in_conflict = True
                self.in_conflict = True
            else:
                self.conflicting_positions.discard(pos)
                #pos.conflicting_positions.discard(self)
                #if not len(pos.conflicting_positions):
                #    pos.in_conflict = False
        if not len(self.conflicting_positions):
            self.in_conflict = False
        return self.in_conflict
    def on_y_size(self, **kwargs):
        value = kwargs.get('value')
        if value > self.y_size_max:
            self.y_size_max = value
    def on_child_y_size_max(self, **kwargs):
        self.y_size_max = kwargs.get('value')
    def on_x_changed(self, **kwargs):
        x = kwargs.get('value')
        old = kwargs.get('old')
        old_set = self.all_positions_xy.get(old, set())
        old_set.discard(self)
        if x not in self.all_positions_xy:
            self.all_positions_xy[x] = set()
        self.all_positions_xy[x].add(self)
    def on_child_conflict(self, **kwargs):
        return
        child = kwargs.get('obj')
        if not kwargs.get('value'):
            return
            
    def on_child_working(self, **kwargs):
        child = kwargs.get('obj')
        if kwargs.get('value'):
            return
        if child.in_conflict:
            pass
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
#            for n in p.child_nodes.itervalues():
#                if n == self.node:
#                    continue
#                break
            self.bind(in_conflict=p.position.on_child_conflict, 
                      y_size_max=p.position.on_child_y_size_max, 
                      working=p.position.on_child_working)
    def on_own_property_changed(self, **kwargs):
        prop = kwargs.get('Property')
        if prop.name in ['in_conflict', 'working']:
            print '%s: %s=%s' % (self.node.name, prop.name, kwargs.get('value'))
    def __repr__(self):
        return '%s Position (%s)' % (self.node.name, self)
    def __str__(self):
        attrs = ['relative_x', 'relative_y', 'x', 'y']
        return ', '.join(['%s: %s' % (attr, getattr(self, attr)) for attr in attrs])
    
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
        print repr(self)
    def on_position_changed(self, **kwargs):
        if self.position.in_conflict:
            return
        self.refresh()
    def on_position_conflict_changed(self, **kwargs):
        if kwargs.get('value') is False:
            self.refresh()
    def __repr__(self):
        return 'Bounds (%s)' % (self)
    def __str__(self):
        attrs = ['x', 'y', 'width', 'height']
        return ', '.join(['%s: %s' % (attr, getattr(self, attr)) for attr in attrs])
        
def test():
    p = Node(name='root')
    c = p.add_child(name='child1')
    p.add_child(name='child2')
    p.add_child(name='child3')
    for i in range(3):
        c.add_child(name='grandchild%d' % (i+1))
    return p

if __name__ == '__main__':
    r = test()
