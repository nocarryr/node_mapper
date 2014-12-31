from nomadic_recording_lib.ui.gtk.bases import clutter_bases
Clutter = clutter_bases.clutter

class Actionable(object):
    def init_actions(self, **kwargs):
        self.set_reactive(True)
    def trigger_action(self, **kwargs):
        pass
        
class Clickable(Actionable):
    def init_actions(self, **kwargs):
        a = Clutter.ClickAction.new()
        self.add_action_with_name('click', a)
        a.connect('clicked', self._on_click_click)
        a.connect('long-press', self._on_click_long_press)
        super(Clickable, self).init_actions(**kwargs)
    def _on_click_click(self, action, actor):
        if action.get_button() == 1:
            btn = 'left'
        else:
            btn = 'right'
        self.trigger_action(action='click', type='click', btn=btn, actor=self)
    def _on_click_long_press(self, action, actor, press_state):
        if action.get_button() == 1:
            btn = 'left'
        else:
            btn = 'right'
        enum = Clutter.LongPressState
        if press_state == enum.QUERY:
            state = 'query'
        elif press_state == enum.CANCEL:
            state = 'cancel'
        else:
            state = 'activate'
        r = self.trigger_action(action='click', 
                                type='long_press', 
                                btn=btn, 
                                state=state, 
                                actor=self)
        if not isinstance(r, bool):
            return True
        return r
        
        
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
        a = Clutter.DragAction.new()
        self.add_action_with_name('drag', a)
        a.connect('drag-begin', self._on_drag_begin)
        a.connect('drag-progress', self._on_drag_motion)
        a.connect('drag-end', self._on_drag_end)
        super(Dragable, self).init_actions(**kwargs)
    def _on_drag_begin(self, action, actor, x, y, modifiers):
        r = self.trigger_action(action='drag', 
                                type='begin', 
                                abs_pos=(x, y), 
                                actor=self)
        if r:
            self.current_drag_actor = self
    def _on_drag_motion(self, action, actor, delta_x, delta_y):
        if self.current_drag_actor is not self:
            return False
        x, y = action.get_motion_coords()
        self.trigger_action(action='drag', 
                            type='motion', 
                            abs_pos=(x, y), 
                            delta_pos=(delta_x, delta_y), 
                            actor=self)
        return False
    def _on_drag_end(self, action, actor, x, y, modifiers):
        self.trigger_action(action='drag', 
                            type='end', 
                            abs_pos=(x, y), 
                            actor=self)
        if self.current_drag_actor is self:
            if self.current_drop_actor is None:
                self.current_drag_actor = None
