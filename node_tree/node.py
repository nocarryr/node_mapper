from . import Bases
BaseObject = Bases.BaseObject
setID = Bases.misc.setID

class Node(BaseObject):
    _Properties = dict(
        name={}, 
        attributes={'type':dict}, 
        collapsed={'default':False}, 
        hidden={'default':False}, 
        parent={'ignore_type':True}, 
    )
    _ChildGroups = dict(child_nodes={'child_class':'__self__'})
    signals_to_register = ['position_changed']
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.id = setID(kwargs.get('id'))
        self.name = kwargs.get('name', '')
        self.position = NodePosition(**kwargs.get('position', {}))
        self.bind(parent=self.on_parent_changed, collapsed=self.on_collapsed_changed)
        p = kwargs.get('parent')
        if p is None and getattr(self, 'ChildGroup_parent', None) is not None:
            p = self.ChildGroup_parent.parent_obj
        self.parent = p
        self.is_root = self.parent is None
        self.child_nodes.bind(child_update=self.on_child_nodes_update)
        self.position.bind(x=self.on_position_changed, y=self.on_position_changed)
    def add_child(self, **kwargs):
        kwargs.setdefault('parent', self)
        return self.child_nodes.add_child(**kwargs)
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
        elif mode == 'remove':
            child.unbind(self)
    def on_position_changed(self, **kwargs):
        self.emit('position_changed', position=self.position)
    def on_child_node_position_changed(self, **kwargs):
        pass
    
class NodePosition(BaseObject):
    _Properties = dict(
        x={'default':0}, 
        y={'default':0}, 
    )
    def __init__(self, **kwargs):
        super(NodePosition, self).__init__(**kwargs)
        self.node = kwargs.get('node')
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
