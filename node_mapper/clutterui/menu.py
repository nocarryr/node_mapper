from nomadic_recording_lib.ui.gtk.bases.ui_modules import gtk
from nomadic_recording_lib.Bases import BaseObject
    
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
    
class MenuAction(BaseObject):
    signals_to_register = ['activate']
    def __init__(self, **kwargs):
        super(MenuAction, self).__init__(**kwargs)
        self.search_paths = set()
        search_paths = kwargs.get('search_path', [])
        menu_items = kwargs.get('menu_items', [])
        if isinstance(search_paths, basestring):
            search_paths = [search_paths]
        for search_path in search_paths:
            self.add_search(search_path)
        if type(menu_items) not in [list, tuple, set]:
            menu_items = [menu_items]
        self.bind_menuitem(*menu_items)
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
