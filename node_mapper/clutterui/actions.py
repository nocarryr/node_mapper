from nomadic_recording_lib.ui.gtk.bases.ui_modules import glib
from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

class Actionable(object):
    def init_actions(self, **kwargs):
        self.set_reactive(True)
    def trigger_action(self, **kwargs):
        pass
        
class Clickable(Actionable):
    def init_actions(self, **kwargs):
        self.connect('button-press-event', self._on_click_button_press)
        self.connect('button-release-event', self._on_click_button_release)
        super(Clickable, self).init_actions(**kwargs)
    @property
    def click_action_double_click_waiting(self):
        return getattr(self, '_click_action_double_click_waiting', False)
    @click_action_double_click_waiting.setter
    def click_action_double_click_waiting(self, value):
        if value == getattr(self, '_click_action_double_click_waiting', False):
            return
        self._click_action_double_click_waiting = value
        if value:
            settings = Clutter.Settings.get_default()
            wait_time = settings.get_property('double-click-time')
            e_id = glib.timeout_add(wait_time, self._click_on_double_click_wait_timer)
            self._click_action_double_click_wait_event_id = e_id
        else:
            e_id = self._click_action_double_click_wait_event_id
            if e_id is not None:
                glib.source_remove(e_id)
                self._click_action_double_click_wait_event_id = None
            self._click_action_double_click_event = None
    @property
    def click_action_long_press_waiting(self):
        return getattr(self, '_click_action_long_press_waiting', False)
    @click_action_long_press_waiting.setter
    def click_action_long_press_waiting(self, value):
        if value == getattr(self, '_click_action_long_press_waiting', False):
            return
        self._click_action_long_press_waiting = value
        if value:
            self._click_action_long_press_triggered = False
            settings = Clutter.Settings.get_default()
            wait_time = settings.get_property('long-press-duration')
            e_id = glib.timeout_add(wait_time, self._click_on_long_press_wait_timer)
            self._click_action_long_press_wait_event_id = e_id
        else:
            e_id = getattr(self, '_click_action_long_press_wait_event_id', None)
            if e_id is not None:
                glib.source_remove(e_id)
                self._click_action_long_press_wait_event_id = None
    def _click_on_double_click_wait_timer(self, *args):
        self._click_action_double_click_wait_event_id = None
        e = self._click_action_double_click_event
        if e.button == 1:
            btn = 'left'
        else:
            btn = 'right'
        self.click_action_double_click_waiting = False
        self.trigger_action(action='click', 
                            type='click', 
                            btn=btn, 
                            event=e, 
                            actor=self)
        return False
    def _click_on_long_press_wait_timer(self, *args):
        self._click_action_long_press_wait_event_id = None
        self._click_action_long_press_triggered = True
        self.click_action_long_press_waiting = False
        btn = self._click_action_long_press_button
        self.trigger_action(action='click', 
                            type='long_press', 
                            btn=btn, 
                            state='activate', 
                            actor=self) 
        return False
    def _on_click_button_press(self, actor, e):
        if e.button == 1:
            btn = 'left'
        else:
            btn = 'right'
        r = self.trigger_action(action='click', 
                                type='long_press', 
                                btn=btn, 
                                state='query', 
                                actor=self)
        if r:
            self._click_action_long_press_button = btn
        self.click_action_long_press_waiting = r
        if e.click_count == 1:
            self.click_action_double_click_waiting = False
            self._click_action_double_click_event = e
            self.click_action_double_click_waiting = True
        return False
    def _on_click_button_release(self, actor, e):
        self.click_action_long_press_waiting = False
        if e.button == 1:
            btn = 'left'
        else:
            btn = 'right'
        if getattr(self, '_click_action_long_press_triggered', False):
            self._click_action_long_press_triggered = False
            self.click_action_double_click_waiting = False
            return True
        if e.click_count == 2:
            self.click_action_double_click_waiting = False
            self.trigger_action(action='click', type='double_click', btn=btn, actor=self)
            return True
        
        
class Dropable(Clickable):
    def init_actions(self, **kwargs):
        a = Clutter.DropAction.new()
        self.add_action_with_name('drop', a)
        a.connect('can-drop', self._on_drop_can_drop)
        a.connect('drop', self._on_drop_drop)
        a.connect('drop-cancel', self._on_drop_cancel)
        a.connect('over-in', self._on_drop_over_in)
        a.connect('over-out', self._on_drop_over_out)
        super(Dropable, self).init_actions(**kwargs)
    @property
    def current_drop_actor(self):
        stage = self.get_stage()
        if stage is None:
            return None
        if not hasattr(stage, '_current_drop_actor'):
            stage._current_drop_actor = None
        return stage._current_drag_actor
    @current_drop_actor.setter
    def current_drop_actor(self, value):
        stage = self.get_stage()
        if stage is None:
            return
        if getattr(stage, '_current_drop_actor', None) == value:
            return
        stage._current_drop_actor = value
    @property
    def current_drag_actor(self):
        stage = self.get_stage()
        if stage is None:
            return None
        if not hasattr(stage, '_current_drag_actor'):
            stage._current_drag_actor = None
        return stage._current_drag_actor
    @current_drag_actor.setter
    def current_drag_actor(self, value):
        stage = self.get_stage()
        if stage is None:
            return
        if getattr(stage, '_current_drag_actor', None) == value:
            return
        stage._current_drag_actor = value
    def _on_drop_can_drop(self, action, actor, x, y):
        r = self.trigger_action(action='drop', 
                                type='can_drop', 
                                drop_actor=actor, 
                                drag_actor=self.current_drag_actor, 
                                actor=self)
        if not isinstance(r, bool):
            r = True
        if r:
            self.current_drop_actor = self
        return r
    def _on_drop_drop(self, action, actor, x, y):
        self.trigger_action(action='drop', 
                            type='drop', 
                            drop_actor=actor, 
                            drag_actor=self.current_drag_actor, 
                            abs_pos=(x, y), 
                            actor=self)
        if self.current_drop_actor is self:
            self.current_drop_actor = None
            self.current_drag_actor = None
    def _on_drop_cancel(self, action, actor, x, y):
        self.trigger_action(action='drop', 
                            type='cancel', 
                            drop_actor=actor, 
                            drag_actor=self.current_drag_actor, 
                            abs_pos=(x, y), 
                            actor=self)
        if self.current_drop_actor is self:
            self.current_drop_actor = None
            self.current_drag_actor = None
    def _on_drop_over_in(self, action, actor):
        self.trigger_action(action='drop', 
                            type='over_in', 
                            drop_actor=actor, 
                            drag_actor=self.current_drag_actor, 
                            actor=self)
    def _on_drop_over_out(self, action, actor):
        self.trigger_action(action='drop', 
                            type='over_out', 
                            drop_actor=actor, 
                            drag_actor=self.current_drag_actor, 
                            actor=self)
class Dragable(Dropable):
    def init_actions(self, **kwargs):
        super(Dragable, self).init_actions(**kwargs)
        a = Clutter.DragAction.new()
        a.set_property('x-drag-threshold', 4)
        a.set_property('y-drag-threshold', 4)
        self.add_action_with_name('drag', a)
        a.connect('drag-begin', self._on_drag_begin)
        a.connect('drag-progress', self._on_drag_motion)
        a.connect('drag-end', self._on_drag_end)
        
    def _on_drag_begin(self, action, actor, x, y, modifiers):
        r = self.trigger_action(action='drag', 
                                type='begin', 
                                abs_pos=(x, y), 
                                actor=self)
        if r:
            self.current_drag_actor = self
            self.click_action_double_click_waiting = False
            self.click_action_long_press_waiting = False
    def _on_drag_motion(self, action, actor, delta_x, delta_y):
        if self.current_drag_actor is not self:
            return False
        x, y = action.get_motion_coords()
        r = self.trigger_action(action='drag', 
                                type='motion', 
                                abs_pos=(x, y), 
                                delta_pos=(delta_x, delta_y), 
                                actor=self)
        if not isinstance(r, bool):
            r = False
        return r
    def _on_drag_end(self, action, actor, x, y, modifiers):
        self.trigger_action(action='drag', 
                            type='end', 
                            abs_pos=(x, y), 
                            actor=self)
        if self.current_drag_actor is self:
            if self.current_drop_actor is None:
                self.current_drag_actor = None
