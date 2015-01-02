from nomadic_recording_lib.ui.gtk.bases.ui_modules import gtk
from nomadic_recording_lib.Bases import BaseObject
from nomadic_recording_lib.Bases.misc import setID, iterbases
    
class MenuItem(BaseObject):
    path_delimiter = '>>'
    _Properties = dict(
        label={'default':''}, 
        enabled={'default':True}, 
        is_separator={'default':False}, 
        parent={'ignore_type':True}, 
    )
    _ChildGroups = dict(
        child_items={'child_class':'__self__'}, 
    )
    signals_to_register = ['activate']
    def __init__(self, **kwargs):
        super(MenuItem, self).__init__(**kwargs)
        self.label = kwargs.get('label')
        self.id = kwargs.get('id', self.label)
        self.enabled = kwargs.get('enabled', True)
        self.parent = kwargs.get('parent')
        if self.parent is not None:
            delim = self.parent.path_delimiter
            if delim != self.path_delimiter:
                self.path_delimiter = delim
        self.is_separator = kwargs.get('is_separator', False)
        self.widget = self.build_widget()
        self.child_items.bind(child_update=self.on_child_items_ChildGroup_update)
        for child in kwargs.get('child_items', []):
            if isinstance(child, basestring):
                if child == 'SEPARATOR':
                    child = {'is_separator':True}
                else:
                    child = {'label':child}
            self.add_child_item(**child)
        self.bind(label=self.on_label_set, 
                  enabled=self.on_enabled_set)
    @property
    def menu_path(self):
        parent = self.parent
        if parent is None:
            return self.id
        p = parent.menu_path
        return self.path_delimiter.join([p, self.id])
    @property
    def application(self):
        return self.GLOBAL_CONFIG['GUIApplication']
    def get_by_path(self, p):
        if self.parent is None:
            return self._get_by_path(p)
        if isinstance(p, basestring):
            p = p.split(self.path_delimiter)
        return self.parent.get_by_path(p)
    def _get_by_path(self, p):
        c_id = p[0]
        p = p[1:]
        child = self.child_items.get(c_id)
        if not len(p):
            return child
        return child._get_by_path(p)
    def build_widget(self):
        if self.is_separator:
            return gtk.SeparatorMenuItem()
        w = gtk.MenuItem(label=self.label)
        w.connect('activate', self.on_menuitem_activate)
        return w
    def get_submenu(self):
        w = self.widget
        if self.is_separator:
            return None
        return w.get_submenu()
    def add_child_item(self, **kwargs):
        if self.is_separator:
            return
        kwargs['parent'] = self
        self.child_items.add_child(**kwargs)
    def on_child_items_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        child = kwargs.get('obj')
        if mode == 'add':
            child.bind(activate=self.on_child_item_activate)
            submenu = self.get_submenu()
            if submenu is None and not self.is_separator:
                submenu = gtk.Menu()
                self.widget.set_submenu(submenu)
            submenu.append(child.widget)
        elif mode == 'remove':
            submenu = self.get_submenu()
            if submenu is not None:
                submenu.remove(child.widget)
            child.unbind(self)
    def on_label_set(self, **kwargs):
        value = kwargs.get('value')
        w = self.widget
        if self.is_separator:
            return
        w.set_label(value)
    def on_enabled_set(self, **kwargs):
        pass
    def on_child_item_activate(self, **kwargs):
        self.emit('activate', **kwargs)
    def on_menuitem_activate(self, *args):
        self.emit('activate', 
                  obj=self, 
                  menu_path=self.menu_path, 
                  path_delimiter=self.path_delimiter)
    
class ActionKeyError(Exception):
    def __init__(self, obj, key):
        self.obj = obj
        self.key = key
    def __str__(self):
        return 'cannot add action %r. key (%r) already exists' % (self.obj, self.key)
        
ALL_ACTIONS = {}
def add_action_instance(obj):
    global ALL_ACTIONS
    if obj.id in ALL_ACTIONS:
        raise ActionKeyError(obj, obj.id)
    ALL_ACTIONS[obj.id] = obj
    
class MenuAction(BaseObject):
    signals_to_register = ['activate']
    def __init__(self, **kwargs):
        super(MenuAction, self).__init__(**kwargs)
        if not hasattr(self, 'id'):
            action_id = kwargs.get('id')
            if not action_id:
                if self.__class__ is not MenuAction:
                    action_id = self.__class__.__name__
                else:
                    action_id = setID(None)
            self.id = action_id
        add_action_instance(self)
        self.search_paths = set()
        search_paths = set()
        for cls in iterbases(MenuAction):
            if hasattr(cls, 'search_paths'):
                _search_paths = cls.search_paths
                if not isinstance(_search_paths, set):
                    _search_paths = set(_search_paths)
                search_paths |= _search_paths
        search_paths |= set(kwargs.get('search_paths', []))
        menu_items = kwargs.get('menu_items', [])
        for search_path in search_paths:
            self.add_search(search_path)
        if type(menu_items) not in [list, tuple, set]:
            menu_items = [menu_items]
        self.bind_menuitem(*menu_items)
        
    @property
    def application(self):
        return self.GLOBAL_CONFIG['GUIApplication']
    def add_search(self, p):
        if type(p) in [list, tuple]:
            p = MenuItem.path_delimiter.join(p)
        self.search_paths.add(p)
    def match_path(self, p, delim):
        p_split = p.split(delim)
        def match(search_path):
            search_path = search_path.split(MenuItem.path_delimiter)
            #print '----\n%s\n%s\n----' % (p_split, search_path)
            if '*' not in search_path:
                if len(search_path) != len(p_split):
                    return False
                for sitem, pitem in zip(search_path, p_split):
                    if sitem != pitem:
                        return False
                return True
            _p_split = p_split[:]
            last_sitem = None
            while True:
                if last_sitem is None or last_sitem != '*':
                    sitem = search_path.pop(0)
                    if last_sitem is None:
                        last_sitem = sitem
                pitem = _p_split.pop(0)
                print sitem, pitem, last_sitem
                if last_sitem == '*':
                    if sitem == pitem:
                        if not len(search_path):
                            return True
                        else:
                            last_sitem = sitem
                elif sitem != pitem:
                    return False
                if not len(_p_split) or not len(search_path):
                    return sitem == '*'
                
        for search_path in self.search_paths:
            if match(search_path):
                return True
    def bind_menuitem(self, *args):
        for arg in args:
            arg.bind(activate=self.on_menuitem_activate)
    def unbind_menuitem(self, *args):
        for arg in args:
            arg.unbind(self)
    def on_menuitem_activate(self, **kwargs):
        menu_path = kwargs.get('menu_path')
        delim = kwargs.get('path_delimiter')
        if self.match_path(menu_path, delim):
            self.handle_item(**kwargs)
            self.emit('activate', **kwargs)
    def handle_item(self, **kwargs):
        pass

class MenuShell(BaseObject):
    _ChildGroups = dict(
        menus={'child_class':MenuItem}, 
        actions={'ignore_index':True}, 
    )
    signals_to_register = ['activate', 'menu_activate', 'action_activate']
    def __init__(self, **kwargs):
        super(MenuShell, self).__init__(**kwargs)
        self.menus.bind(child_update=self.on_menus_ChildGroup_update)
        self.actions.bind(child_update=self.on_actions_ChildGroup_update)
        for menu in kwargs.get('menus', []):
            self.add_menu(**menu)
        actions = kwargs.get('actions', {})
        if isinstance(actions, dict):
            for key, action in actions.iteritems():
                action.setdefault('id', key)
                self.add_action(**action)
        else:
            for action in actions:
                if isinstance(action, MenuAction) or issubclass(action, MenuAction):
                    self.add_action(action)
                else:
                    self.add_action(**action)
    @property
    def application(self):
        return self.GLOBAL_CONFIG['GUIApplication']
    def add_menu(self, **kwargs):
        return self.menus.add_child(**kwargs)
    def add_action(self, *args, **kwargs):
        cls = MenuAction
        if len(args) == 1:
            if isinstance(args[0], MenuAction):
                kwargs['existing_object'] = args[0]
            elif issubclass(args[0], MenuAction):
                cls = args[0]
        try:
            action = self.actions.add_child(cls, **kwargs)
        except ActionKeyError as e:
            action = ALL_ACTIONS[e.key]
            self.actions.add_child(existing_object=action)
        return action
    def on_menus_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        menu = kwargs.get('obj')
        if mode == 'add':
            menu.bind(activate=self.on_menuitem_activate)
            for action in self.actions.itervalues():
                action.bind_menuitem(menu)
        elif mode == 'remove':
            menu.unbind(self)
            for action in self.actions.itervalues():
                action.unbind_menuitem(menu)
    def on_actions_ChildGroup_update(self, **kwargs):
        mode = kwargs.get('mode')
        action = kwargs.get('obj')
        if mode == 'add':
            action.bind(activate=self.on_action_activate)
            action.bind_menuitem(*self.menus.values())
        elif mode == 'remove':
            action.unbind(self)
            action.unbind_menuitem(*self.menus.values())
    def on_menuitem_activate(self, **kwargs):
        self.emit('menu_activate', **kwargs)
        kwargs['activate_type'] = 'menu'
        self.emit('activate', **kwargs)
    def on_action_activate(self, **kwargs):
        self.emit('action_activate', **kwargs)
        kwargs['activate_type'] = 'action'
        self.emit('activate', **kwargs)
        
MENU_DATA_MAIN = [
    {
        'label':'File', 
        'child_items':[
            'New', 
            'Open', 
            'Save', 
            'SEPARATOR', 
            'Exit', 
        ], 
    }, {
        'label':'Edit', 
        'child_items':[
            'Undo', 
            'Redo', 
        ], 
    }, 
]
CONTEXT_MENU_DATA = {
    'node':{
        'label':'Node Edit', 
        'child_items':[
            'Rename', 
            'Delete', 
        ], 
    }, 
    'connection':{
        'label':'Connection Edit', 
        'child_items':[
            'Rename', 
            'Delete', 
        ]
    }, 
    'connector':{
        'label':'Connector Edit', 
        'child_items':[
            'Delete', 
            'Color', 
        ], 
    }, 
    'window':{
        'label':'Window Edit', 
        'child_items':[
            'Add Node', 
        ], 
    }, 
}
class FileAction(MenuAction):
    pass
class FileOpen(FileAction):
    search_paths = 'File>>Open'
class FileSave(FileAction):
    search_paths = 'File>>Save'
class FileNew(FileAction):
    search_paths = 'File>>New'
class ExitAction(MenuAction):
    search_paths = 'File>>Exit'
    
MAIN_ACTION_CLASSES = [FileOpen, FileSave, FileNew, ExitAction]

class MenuBar(MenuShell):
    def __init__(self, **kwargs):
        super(MenuBar, self).__init__(**kwargs)
        self.widget = gtk.MenuBar()
        for menu in MENU_DATA_MAIN:
            self.add_menu(**menu)
        for cls in MAIN_ACTION_CLASSES:
            self.add_action(cls)
    def on_menus_ChildGroup_update(self, **kwargs):
        super(MenuBar, self).on_menus_ChildGroup_update(**kwargs)
        menu = kwargs.get('obj')
        self.widget.append(menu.widget)
    
class ContextAction(MenuAction):
    @property
    def context_obj(self):
        return getattr(self.application, 'menu_context_obj', None)
    @context_obj.setter
    def context_obj(self, value):
        app = self.application
        if getattr(app, 'menu_context_obj', None) == value:
            return
        app.menu_context_obj = value
    def finish_handle_item(self, value):
        pass
    def cancel_handle_item(self):
        self.context_obj = None
        
class RenameAction(ContextAction):
    context_obj_attr = None
    def handle_item(self, **kwargs):
        pass
    def finish_handle_item(self, value):
        setattr(self.context_obj, self.context_obj_attr, value)
        self.context_obj = None
class NodeRenameAction(RenameAction):
    context_obj_attr = 'name'
    search_paths = 'node>>Rename'
class ConnectionRenameAction(RenameAction):
    context_obj_attr = 'label'
    search_paths = 'connection>>Rename'
class AddNodeAction(MenuAction):
    search_paths = 'window>>Add Node'
    def handle_item(self, **kwargs):
        pass

CONTEXT_ACTION_CLASSES = [NodeRenameAction, ConnectionRenameAction, AddNodeAction]
    
class ContextMenus(MenuShell):
    def __init__(self, **kwargs):
        self._widget = None
        self._active_menu = None
        super(ContextMenus, self).__init__(**kwargs)
        for key, menu in CONTEXT_MENU_DATA.iteritems():
            mkwargs = menu.copy()
            mkwargs['id'] = key
            self.add_menu(**mkwargs)
        for cls in CONTEXT_ACTION_CLASSES:
            self.add_action(cls)
    @property
    def active_menu(self):
        return self._active_menu
    @active_menu.setter
    def active_menu(self, value):
        if self._active_menu == value:
            return
        if self._active_menu is not None:
            self._widget.remove(self._active_menu.widget)
            self._widget.popdown()
            self._widget = None
        self._active_menu = value
        if value is not None:
            self._widget = gtk.Menu()
            self._widget.append(value.widget)
    def trigger_menu(self, **kwargs):
        menu_id = kwargs.get('id')
        btn = kwargs.get('btn')
        data = kwargs.get('data', {})
        timestamp = kwargs.get('timestamp')
        if timestamp is None:
            timestamp = gtk.get_current_event_time()
        self.active_menu = self.menus[menu_id]
        self._widget.popup(None, None, None, data, btn, timestamp)
        
