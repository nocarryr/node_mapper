from node_mapper.nomadic_recording_lib.Bases import BaseObject
from node_mapper.nomadic_recording_lib.Bases.misc import setID

class NodeBase(BaseObject):
    _Properties = dict(
        id={'ignore_type':True, 'fvalidate':'_fvalidate_id'}, 
        name={'default':''}, 
        init_complete={'default':False}, 
    )
    _saved_attributes = ['id', 'name']
    signals_to_register = ['pre_delete']
    def __init__(self, **kwargs):
        super(NodeBase, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            self.id = setID(kwargs.get('id'))
            self.name = kwargs.get('name', '')
        self.node_tree = kwargs.get('node_tree')
        if self.node_tree is None:
            self.node_tree = self.build_node_tree(**kwargs)
        self.node_tree.add_node(self)
        self.node_tree.nodes.bind(child_update=self.on_node_tree_nodes_update)
    def unlink(self):
        self.node_tree.remove_node(self)
        super(NodeBase, self).unlink()
    def build_node_tree(self, **kwargs):
        cls = getattr(self, 'node_tree_class', None)
        if cls is None:
            cls = NodeTree
        return cls(**kwargs)
    def _fvalidate_id(self, value):
        prop = self.Properties['id']
        if prop.value is not None:
            return False
        if value is None:
            return False
        return True
    def on_node_tree_nodes_update(self, **kwargs):
        pass
    def __repr__(self):
        try:
            return '%s %s' % (self.__class__.__name__, self)
        except:
            return super(NodeBase, self).__repr__()
    def __str__(self):
        if not self.name:
            s = self.id
        else:
            s = self.name
        if type(s) != str:
            s = 'Node'
        return s
    
class NodeTree(BaseObject):
    _Properties = dict(
        node_class_name={'type':str}, 
    )
    _ChildGroups = dict(
        nodes = {'ignore_index':True, 'deserialize_callback':'_deserialize_node'}, 
    )
    _saved_attributes = ['node_class_name']
    _saved_child_objects = ['nodes']
    _saved_class_name = 'NodeTree'
    def __init__(self, **kwargs):
        super(NodeTree, self).__init__(**kwargs)
        self.nodes.bind(child_update=self.on_nodes_ChildGroup_update)
    def _deserialize_node(self, d):
        cls = REGISTRY.get(self.node_class_name)
        return cls(deserialize=d, node_tree=self)
    def add_node(self, node=None, **kwargs):
        if node is not None:
            return self.nodes.add_child(existing_object=node)
        kwargs.setdefault('node_tree', self)
        return self.nodes.add_child(**kwargs)
    def remove_node(self, node):
        self.nodes.del_child(node)
    def on_nodes_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        obj = kwargs.get('obj')
        if mode == 'add':
            if self.nodes.child_class is None and obj is not None:
                self.nodes.child_class = obj.__class__
                self.node_class_name = obj.__class__.__name__

class Registry(object):
    def __init__(self):
        self.node_classes = {}
        self.tree_classes = {}
    def add_node_class(self, cls):
        self.node_classes[cls.__name__] = cls
        if hasattr(cls, 'node_tree_class'):
            self.add_tree_class(cls.node_tree_class)
    def add_tree_class(self, cls):
        self.tree_classes[cls.__name__] = cls
    def get(self, name):
        if name in self.node_classes:
            return self.node_classes[name]
        if name in self.tree_classes:
            return self.tree_classes[name]
        return None
REGISTRY = Registry()

    
