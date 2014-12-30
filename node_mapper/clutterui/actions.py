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
        a.connect('clicked', self._on_click_action)
        super(Clickable, self).init_actions(**kwargs)
    def _on_click_action(self, action, actor):
        btn = action.get_button()
        if btn == 1:
            click_type = 'left'
        else:
            click_type = 'right'
        self.trigger_action(action='click', type=click_type, actor=self)
        
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
    def _on_drop_can_drop(self, action, actor, x, y):
        return True
    def _on_drop_drop(self, action, actor, x, y):
        self.trigger_action(action='drop', 
                            type='drop', 
                            drop_actor=actor, 
                            abs_pos=(x, y), 
                            actor=self)
    def _on_drop_cancel(self, action, actor, x, y):
        self.trigger_action(action='drop', 
                            type='cancel', 
                            drop_actor=actor, 
                            abs_pos=(x, y), 
                            actor=self)
    def _on_drop_over_in(self, action, actor):
        self.trigger_action(action='drop', 
                            type='over_in', 
                            drop_actor=actor, 
                            actor=self)
    def _on_drop_over_out(self, action, actor):
        self.trigger_action(action='drop', 
                            type='over_out', 
                            drop_actor=actor, 
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
        self.trigger_action(action='drag', 
                            type='begin', 
                            abs_pos=(x, y), 
                            actor=self)
    def _on_drag_motion(self, action, actor, delta_x, delta_y):
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
