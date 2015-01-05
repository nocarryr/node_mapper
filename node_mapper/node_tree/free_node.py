from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.Bases.misc import setID

from node_mapper.node_tree import NodeTree, REGISTRY
from node_mapper.node_tree.node_position import NodePositionBase


class BaseNodeConnection(BaseObject):
    _Properties = dict(
        label={'default':''}, 
        parent={'ignore_type':True}, 
        relative_x={'default':0.}, 
        relative_y={'default':0.}, 
        width={'default':0.}, 
        height={'default':20.}, 
    )
    _saved_attributes = ['id', 'label', 'parent_id']
    signals_to_register = ['connector_added', 'pre_delete', 'position_changed']
    def __init__(self, **kwargs):
        self.node_tree = kwargs.get('node_tree')
        self.connectors = {}
        super(BaseNodeConnection, self).__init__(**kwargs)
        self.bind(parent=self.on_parent_changed)
        self.parent = kwargs.get('parent')
        if 'deserialize' not in kwargs:
            self.id = setID(kwargs.get('id'))
            self.label = kwargs.get('label', '')
    def unlink(self):
        self.emit('pre_delete', obj=self)
        super(BaseNodeConnection, self).unlink()
    @property
    def x(self):
        return self.get_x()
    @property
    def y(self):
        return self.get_y()
    @property
    def absolute_pos(self):
        return {'x':self.x, 'y':self.y}
    def get_x(self):
        p = self.parent
        if p is None:
            x = 0.
        else:
            x = p.x
        return x + self.relative_x
    def get_y(self):
        p = self.parent
        if p is None:
            y = 0.
        else:
            y = p.y
        return (y + self.relative_y) + (self.height / 2.)
    def can_connect_to(self, other):
        if not self._can_connect_to(other):
            return False
        if not other._can_connect_to(self):
            return False
        return True
    def _can_connect_to(self, other):
        for c in self.connectors.itervalues():
            if c.source is self and c.dest is other:
                return False
            if c.dest is self and c.source is other:
                return False
        return True
    def connect_to(self, other):
        return False
    def calc_geom(self):
        cg = self.ChildGroup_parent
        p = self.parent
        self.width = p.width / 2.
        y = p.padding_top
        for c in cg.itervalues():
            if c is self:
                break
            if c.Index > self.Index:
                break
            y = c.relative_y + c.height
        self.relative_y = y
    def bind_parent(self, parent):
        parent.bind(position_changed=self.on_parent_position_changed)
    def unbind_parent(self, parent):
        parent.unbind(self)
    def on_parent_changed(self, **kwargs):
        value = kwargs.get('value')
        old = kwargs.get('old')
        if old is not None:
            self.unbind_parent(old)
        if value is None:
            self.parent_id = None
            return
        if self.node_tree is None:
            self.node_tree = self.parent.node_tree
        self.bind_parent(value)
        if getattr(self, 'parent_id', None) != value.id:
            self.parent_id = value.id
        if self.parent._deserializing:
            return
        self.calc_geom()
    def on_parent_position_changed(self, **kwargs):
        kwargs['connection'] = self
        self.emit('position_changed', **kwargs)
    def __repr__(self):
        return '<%s> %s' % (self.__class__, self)
    def __str__(self):
        return '%s of Node %s' % (self.label, self.parent)
    
class InputNodeConnection(BaseNodeConnection):
    _saved_attributes = ['allow_multiple']
    _saved_class_name = 'InputNodeConnection'
    def __init__(self, **kwargs):
        super(InputNodeConnection, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            self.allow_multiple = kwargs.get('allow_multiple', False)
    def calc_geom(self):
        super(InputNodeConnection, self).calc_geom()
        self.relative_x = 0.
    def can_connect_to(self, other):
        if isinstance(other, InputNodeConnection):
            return False
        if not self.allow_multiple and len(self.connectors):
            return False
        return super(InputNodeConnection, self).can_connect_to(other)
    def connect_to(self, other):
        if not self.can_connect_to(other):
            return False
        c = NodeConnector(dest=self, source=other)
        self.emit('connector_added', connection=self, connector=c)
        return c
    def on_parent_position_changed(self, **kwargs):
        kwargs['connection_type'] = 'input'
        super(InputNodeConnection, self).on_parent_position_changed(**kwargs)
        
class OutputNodeConnection(BaseNodeConnection):
    _saved_class_name = 'OutputNodeConnection'
    def get_x(self):
        x = super(OutputNodeConnection, self).get_x()
        return x + self.width
    def calc_geom(self):
        super(OutputNodeConnection, self).calc_geom()
        self.relative_x = self.parent.width / 2.
    def can_connect_to(self, other):
        if isinstance(other, OutputNodeConnection):
            return False
        return super(OutputNodeConnection, self).can_connect_to(other)
    def connect_to(self, other):
        if not self.can_connect_to(other):
            return False
        c = NodeConnector(source=self, dest=other)
        self.emit('connector_added', connection=self, connector=c)
        return c
    def on_parent_position_changed(self, **kwargs):
        kwargs['connection_type'] = 'output'
        super(OutputNodeConnection, self).on_parent_position_changed(**kwargs)
    
class FreeNode(NodePositionBase):
    _Properties = dict(
        padding_top={'default':20.}, 
        padding_bottom={'default':0.}, 
    )
    _ChildGroups = dict(
        input_connections={'child_class':InputNodeConnection}, 
        output_connections={'child_class':OutputNodeConnection}, 
    )
    _saved_class_name = 'FreeNode'
    _saved_child_objects = ['input_connections', 'output_connections']
    signals_to_register = ['connector_added']
    def __init__(self, **kwargs):
        self._unlinking = False
        super(FreeNode, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            for attr in ['x', 'y', 'width', 'height']:
                if attr in kwargs:
                    setattr(self, attr, kwargs.get(attr))
        for cg in [self.input_connections, self.output_connections]:
            cg.bind(child_update=self.on_connections_ChildGroup_update)
        self.bind(padding_top=self.on_padding_changed, 
                  padding_bottom=self.on_padding_changed)
        self.bind(position_changed=self.on_own_position_changed)
    def unlink(self):
        self._unlinking = True
        self.emit('pre_delete', obj=self)
        self.input_connections.clear()
        self.output_connections.clear()
        super(FreeNode, self).unlink()
    def add_connection(self, **kwargs):
        connection_type = kwargs.get('type')
        c_kwargs = kwargs.copy()
        del c_kwargs['type']
        c_kwargs['parent'] = self
        cg = getattr(self, '_'.join([connection_type, 'connections']))
        return cg.add_child(**c_kwargs)
    def find_connection(self, **kwargs):
        connection_id = kwargs.get('id')
        label = kwargs.get('label')
        connection_type = kwargs.get('type')
        if connection_type is None:
            cgroups = [self.input_connections, self.output_connections]
        else:
            cgroups = [getattr(self, '_'.join([connection_type, 'connections']))]
        for cg in cgroups:
            if connection_id is not None:
                c = cg.get(connection_id)
                if c is not None:
                    return c
            else:
                for c in cg.itervalues():
                    if c.label == label:
                        return c
        return None
    def _deserialization_complete(self, **kwargs):
        self.update_connection_geom()
    def ChildGroup_prepare_child_instance(self, childgroup, cls, **kwargs):
        if 'connections' in childgroup.name:
            kwargs['parent'] = self
        return cls, kwargs
    def update_connection_geom(self, **kwargs):
        connection_types = kwargs.get('type')
        if connection_types is None:
            connection_types = ['input', 'output']
        elif isinstance(connection_types, basestring):
            connection_types = [connection_types]
        y_size_max = 0.
        for connection_type in connection_types:
            cg = getattr(self, '_'.join([connection_type, 'connections']))
            for connection in cg.itervalues():
                connection.relative_y = self.padding_top
            for connection in cg.itervalues():
                connection.calc_geom()
                y_size = connection.relative_y + connection.height
                if y_size > y_size_max:
                    y_size_max = y_size
        if y_size_max > self.height + self.padding_bottom:
            self.height = y_size_max + self.padding_bottom
    def on_connections_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        c = kwargs.get('obj')
        cg = kwargs.get('ChildGroup')
        self.update_connection_geom(type=cg.name.split('_')[0])
        if mode == 'add':
            c.bind(connector_added=self.on_connector_added)
        elif mode == 'remove':
            c.unbind(self.on_connector_added)
    def on_connector_added(self, **kwargs):
        self.emit('connector_added', **kwargs)
    def on_padding_changed(self, **kwargs):
        self.update_connection_geom()
    def on_own_position_changed(self, **kwargs):
        pos_type = kwargs.get('type')
        if pos_type in ['invert', 'size']:
            self.update_connection_geom()
        
class NodeConnector(BaseObject):
    _Properties = dict(
        source={'ignore_type':True}, 
        dest={'ignore_type':True}, 
    )
    _saved_class_name = 'NodeConnector'
    _saved_attributes = ['id', 'source_id', 'dest_id']
    signals_to_register = ['pre_delete', 'position_changed']
    def __init__(self, **kwargs):
        self.node_tree = kwargs.get('node_tree')
        super(NodeConnector, self).__init__(**kwargs)
        self.bind(source=self.on_connection_changed, 
                  dest=self.on_connection_changed)
        if 'deserialize' not in kwargs:
            self.id = setID(kwargs.get('id'))
            self.source = kwargs.get('source')
            self.dest = kwargs.get('dest')
        else:
            self.find_connections()
            if not self.connections_found:
                self.node_tree.bind(node_update=self.on_node_tree_node_update)
    @property
    def connections_found(self):
        return self.source is not None and self.dest is not None
    def unlink(self):
        self.node_tree.unbind(self)
        self.emit('pre_delete', obj=self)
        self.source = None
        self.dest = None
        super(NodeConnector, self).unlink()
    def find_connections(self, **kwargs):
        node = kwargs.get('node')
        tree = self.node_tree
        if self.source is None and self.source_id is not None:
            src = tree.find_connection(id=self.source_id, node=node)
            if src is not None:
                self.source = src
        if self.dest is None and self.dest_id is not None:
            dest = tree.find_connection(id=self.dest_id, node=node)
            if dest is not None:
                self.dest = dest
    def bind_connection(self, **kwargs):
        c = kwargs.get('connection')
        c.bind(pre_delete=self.on_connection_pre_delete, 
               position_changed=self.on_connection_position_changed)
        c.connectors[self.id] = self
    def unbind_connection(self, **kwargs):
        c = kwargs.get('connection')
        c.unbind(self)
        if self.id in c.connectors:
            del c.connectors[self.id]
    def on_connection_changed(self, **kwargs):
        value = kwargs.get('value')
        old = kwargs.get('old')
        prop = kwargs.get('Property')
        id_attr = '_'.join([prop.name, 'id'])
        if old is not None:
            self.unbind_connection(connection=old, type=prop.name)
        if value is None:
            setattr(self, id_attr, None)
            return
        self.bind_connection(connection=value, type=prop.name)
        if self.node_tree is None:
            self.node_tree = value.node_tree
        if getattr(self, id_attr, None) == value.id:
            return
        setattr(self, id_attr, value.id)
    def on_connection_pre_delete(self, **kwargs):
        self.unlink()
    def on_connection_position_changed(self, **kwargs):
        kwargs['connector'] = self
        self.emit('position_changed', **kwargs)
    def on_dest_changed(self, **kwargs):
        dest = kwargs.get('value')
        if dest is None:
            self.dest_id = None
            return
        if getattr(self, 'dest_id', None) == dest.id:
            return
        self.dest_id = dest.id
    def on_node_tree_node_update(self, **kwargs):
        if kwargs.get('mode') != 'add':
            return
        node = kwargs.get('obj')
        self.find_connections(node=node)
        if self.connections_found:
            self.node_tree.unbind(self.on_node_tree_node_update)
    def __repr__(self):
        return str(self)
    def __str__(self):
        return 'Connection: source=%s, dest=%s' % (self.source, self.dest)
        
class FreeNodeTree(NodeTree):
    _Properties = dict(
        x_invert={'default':False}, 
        y_invert={'default':True}, 
    )
    _saved_class_name = 'FreeNodeTree'
    _saved_attributes = ['x_invert', 'y_invert']
    _saved_child_objects = ['connectors']
    signals_to_register = ['connector_added']
    def __init__(self, **kwargs):
        kwargs.setdefault('node_class_name', 'FreeNode')
        super(FreeNodeTree, self).__init__(**kwargs)
        if 'deserialize' not in kwargs:
            self.connectors = {}
    def add_node(self, node=None, **kwargs):
        node = super(FreeNodeTree, self).add_node(node, **kwargs)
        self.bind_node(node)
        return node
    def remove_node(self, node):
        self.unbind_node(node)
        super(FreeNodeTree, self).remove_node(node)
    def find_connection(self, **kwargs):
        connection_id = kwargs.get('id')
        node = kwargs.get('node')
        if node is not None:
            return node.find_connection(id=connection_id)
        for node in self.nodes.itervalues():
            c = node.find_connection(id=connection_id)
            if c is not None:
                return c
        return None
    def _deserialize_child(self, d, **kwargs):
        if kwargs.get('saved_child_obj') == 'connectors':
            c = NodeConnector(node_tree=self, deserialize=d)
            self.bind_connector(c)
            return c
        node = super(FreeNodeTree, self)._deserialize_child(d, **kwargs)
        self.bind_node(node)
        return node
    def bind_node(self, node):
        node.bind(connector_added=self.on_connector_added, 
                  pre_delete=self.on_node_pre_delete)
    def unbind_node(self, node):
        node.unbind(self.on_connector_added, self.on_node_pre_delete)
    def bind_connector(self, connector):
        connector.bind(pre_delete=self.on_connector_pre_delete)
    def unbind_connector(self, connector):
        connector.unbind(self.on_connector_pre_delete)
    def on_connector_added(self, **kwargs):
        c = kwargs.get('connector')
        if c.id not in self.connectors:
            self.connectors[c.id] = c
        self.bind_connector(c)
        self.emit('connector_added', **kwargs)
    def on_node_pre_delete(self, **kwargs):
        pass
    def on_connector_pre_delete(self, **kwargs):
        c = kwargs.get('obj')
        self.unbind_connector(c)
        if c.id in self.connectors:
            del self.connectors[c.id]
        
FreeNode.node_tree_class = FreeNodeTree
REGISTRY.add_node_class(FreeNode)

def test():
    tree = FreeNodeTree()
    last_node = None
    for x in range(4):
        x += 1
        node = tree.add_node(name=str(x), x=x*200., y=0., height=100.)
        for i in range(4):
            i += 1
            in_c = node.add_connection(type='input', label='in %s' % (i))
            node.add_connection(type='output', label='out %s' % (i))
            if last_node is not None and x == 2 and i <= 2:
                last_c = last_node.find_connection(type='output', label='out %s' % (i))
                last_c.connect_to(in_c)
        if last_node is None:
            last_node = node
            continue
    return tree
