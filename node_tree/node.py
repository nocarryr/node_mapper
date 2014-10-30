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
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        self.id = setID(kwargs.get('id'))
        self.name = kwargs.get('name', '')
        self.bind(parent=self.on_parent_changed, collapsed=self.on_collapsed_changed)
        self.parent = kwargs.get('parent')
        self.is_root = self.parent is None
    def on_parent_changed(self, **kwargs):
        p = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
            old.unbind(self)
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
