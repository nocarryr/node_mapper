from nomadic_recording_lib.Bases import BaseObject, Color
from nomadic_recording_lib.Bases.misc import setID, iterbases


class NodeColorProps(BaseObject):
    _saved_child_objects = ['colors']
    _saved_child_classes = [Color]
    _color_defaults = ['background', 'border', 'text']
    _saved_class_name = 'NodeColorProps'
    def __init__(self, **kwargs):
        self.color_defaults = {}
        for cls in iterbases(self):
            _defaults = getattr(cls, '_color_defaults', None)
            if isinstance(_defaults, list):
                for key in _defaults:
                    if key in self.color_defaults:
                        continue
                    self.color_defaults[key] = dict(zip(['hue', 'sat', 'val'], [0., 0., .8]))
            if not isinstance(_defaults, dict):
                continue
            self.color_defaults.update(_defaults)
        super(NodeColorProps, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            self.colors = {}
            for key, cdict in self.color_defaults.iteritems():
                self.colors[key] = Color(**cdict)
    def __repr__(self):
        return '%s: %s' % (self.__class__, self)
    def __str__(self):
        return str(self.colors)
        
class NodeColorPropsNormal(NodeColorProps):
    _color_defaults = dict(
        background={'hue':0., 'sat':0., 'val':.5}, 
        border={'hue':0., 'sat':0., 'val':.8}, 
        text={'hue':0., 'sat':0., 'val':1.}, 
    )
    _saved_class_name = 'NodeColorPropsNormal'
    
class NodeColorPropsSelected(NodeColorProps):
    _color_defaults = dict(
        background={'hue':.667, 'sat':.4, 'val':1.}, 
        border={'hue':0., 'sat':0., 'val':1.}, 
        text={'hue':0., 'sat':0., 'val':1.}, 
    )
    _saved_class_name = 'NodeColorPropsSelected'
    
class NodeBase(BaseObject):
    _Properties = dict(
        id={'ignore_type':True, 'fvalidate':'_fvalidate_id'}, 
        name={'default':'', 'type':str}, 
        init_complete={'default':False}, 
    )
    _saved_attributes = ['id', 'name']
    _saved_child_objects = ['colors']
    _saved_child_classes = [NodeColorProps, NodeColorPropsNormal, NodeColorPropsSelected]
    signals_to_register = ['pre_delete', 'post_delete']
    def __init__(self, **kwargs):
        super(NodeBase, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            self.id = setID(kwargs.get('id'))
            self.name = kwargs.get('name', '')
            self.colors = {
                'normal':NodeColorPropsNormal(), 
                'selected':NodeColorPropsSelected(), 
            }
        self.node_tree = kwargs.get('node_tree')
        if self.node_tree is None:
            self.node_tree = self.build_node_tree(**kwargs)
        self.node_tree.add_node(self)
        self.node_tree.bind(node_update=self.on_node_tree_nodes_update)
    def unlink(self):
        self.node_tree.remove_node(self)
        self.emit('post_delete')
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
        node_class_name={'ignore_type':True}, 
    )
    _saved_attributes = ['node_class_name']
    _saved_child_objects = ['nodes']
    _saved_class_name = 'NodeTree'
    signals_to_register = ['node_update']
    def __init__(self, **kwargs):
        self.node_class = None
        super(NodeTree, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            self.nodes = {}
    @property
    def nodes(self):
        nodes = getattr(self, '_nodes', None)
        if nodes is None:
            nodes = self._nodes = {}
        return nodes
    @nodes.setter
    def nodes(self, value):
        if hasattr(self, '_nodes'):
            return
        self._nodes = value
    def _deserialize_child(self, d):
        cls = REGISTRY.get(self.node_class_name)
        if self.node_class is None:
            self.node_class = cls
            self.saved_child_classes.add(cls)
        return cls(deserialize=d, node_tree=self)
    def add_node(self, node=None, **kwargs):
        if node is not None:
            if self.node_class is None:
                self.node_class = node.__class__
                self.node_class_name = node.__class__.__name__
        else:
            kwargs.setdefault('node_tree', self)
            node = self.node_class(**kwargs)
        self.nodes[node.id] = node
        self.emit('node_update', mode='add', obj=node)
        return node
    def remove_node(self, node):
        if node.id in self.nodes:
            del self.nodes[node.id]
        self.emit('node_update', mode='remove', obj=node)

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

    
