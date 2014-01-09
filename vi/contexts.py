import sublime

from Vintageous.vi.constants import MODE_NORMAL, MODE_NORMAL_INSERT, MODE_INSERT, ACTIONS_EXITING_TO_INSERT_MODE, MODE_VISUAL_LINE, MODE_VISUAL, MODE_SELECT
from Vintageous.vi.constants import MODE_VISUAL_BLOCK
from Vintageous.vi import constants
from Vintageous.vi import utils
from Vintageous.vi.constants import action_to_namespace


class KeyContext(object):
    def __get__(self, instance, owner):
        self.state = instance
        return self

    def vi_must_change_mode(self, key, operator, operand, match_all):
        is_normal_mode = self.state.settings.view['command_mode']
        is_exit_mode_insert = (self.state.action in ACTIONS_EXITING_TO_INSERT_MODE)
        if (is_normal_mode and is_exit_mode_insert):
            return self._check(True, operator, operand, match_all)

        # Close the ':' panel.
        if self.vi_is_cmdline(key, operator, operand, match_all):
            # We return False so that vi_esc will be skipped and the default Sublime Text command
            # will be triggered instead. When the input panel finally closes, the initialization
            # code in state.py will take care of clearing the state so we are left in a consistent
            # state.
            return False

        # If we have primed counts, we have to clear the state.
        if self.state.user_provided_count or self.state.motion or self.state.action:
            return True

        # TODO: Simplify comparisons.
        if self.state.mode == MODE_NORMAL_INSERT:
            return True

        if self.state.mode == MODE_INSERT:
            return True

        # check if we are NOT in normal mode -- if NOT, we need to change modes
        # This covers, for example, SELECT_MODE.
        if self.state.mode != MODE_NORMAL:
            return True

        # Clear non-empty selections if there any.
        # For example, this will be the case when we've used select mode (gh).
        if not all(r.empty() for r in self.state.view.sel()):
            return True

        # XXX Actually, if we already are in normal mode, we still need to perform certain
        # cleanup tasks, so let the command run anyway.
        if self.state.view.get_regions('vi_search'):
            return True


    def vi_is_buffer(self, key, operator, operand, match_all):
        # !! The following check is based on an implementation detail of Sublime Text. !!
        is_console = False if (getattr(self.state.view, 'settings') is not None) else True
        is_widget = self.state.view.settings().get('is_widget')
        value = (is_console or is_widget)
        return self._check(value, operand, operand, match_all)

    def vi_must_exit_to_insert_mode(self, key, operator, operand, match_all):
        # XXX: This conext most likely not needed any more.
        is_normal_mode = self.state.settings.view['command_mode']
        is_exit_mode_insert = (self.state.action in ACTIONS_EXITING_TO_INSERT_MODE)
        value = (is_normal_mode and is_exit_mode_insert)
        return self._check(value, operator, operand, match_all)

    def vi_use_ctrl_keys(self, key, operator, operand, match_all):
        value = self.state.settings.view['vintageous_use_ctrl_keys']
        return self._check(value, operator, operand, match_all)

    def vi_is_cmdline(self, key, operator, operand, match_all):
        value = (self.state.view.score_selector(0, 'text.excmdline') != 0)
        return self._check(value, operator, operand, match_all)

    def vi_enable_cmdline_mode(self, key, operator, operand, match_all):
        value = self.state.settings.view['vintageous_enable_cmdline_mode']
        return self._check(value, operator, operand, match_all)

    def vi_has_incomplete_action(self, key, operator, operand, match_all):
        value = any(x for x in (self.state.action, self.state.motion) if
                          x in constants.INCOMPLETE_ACTIONS)
        return self._check(value, operator, operand, match_all)

    def vi_has_action(self, key, operator, operand, match_all):
        value = self.state.action
        value = value and (value not in constants.INCOMPLETE_ACTIONS)
        return self._check(value, operator, operand, match_all)

    def vi_has_motion_count(self, key, operator, operand, match_all):
        value = self.state.motion_digits
        return self._check(value, operator, operand, match_all)

    def vi_mode_normal_insert(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_NORMAL_INSERT
        return self._check(value, operator, operand, match_all)

    def vi_mode_visual_block(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_VISUAL_BLOCK
        return self._check(value, operator, operand, match_all)

    def vi_mode_cannot_push_zero(self, key, operator, operand, match_all):
        value = False
        if operator == sublime.OP_EQUAL:
            value = not (self.state.motion_digits or
                             self.state.action_digits)

        return self._check(value, operator, operand, match_all)

    def vi_mode_visual_any(self, key, operator, operand, match_all):
        value = self.state.mode in (MODE_VISUAL_LINE, MODE_VISUAL, MODE_VISUAL_BLOCK)
        return self._check(value, operator, operand, match_all)

    def vi_mode_select(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_SELECT
        return self._check(value, operator, operand, match_all)

    def vi_mode_visual_line(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_VISUAL_LINE
        return self._check(value, operator, operand, match_all)

    def vi_mode_insert(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_INSERT
        return self._check(value, operator, operand, match_all)

    def vi_mode_visual(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_VISUAL
        return self._check(value, operator, operand, match_all)

    def vi_mode_normal(self, key, operator, operand, match_all):
        value = self.state.mode == MODE_NORMAL
        return self._check(value, operator, operand, match_all)

    def vi_mode_normal_or_visual(self, key, operator, operand, match_all):
        # XXX: This context is used to disable some keys for VISUALLINE.
        # However, this is hiding some problems in visual transformers that might not be dealing
        # correctly with VISUALLINE.
        normal = self.vi_mode_normal(key, operator, operand, match_all)
        visual = self.vi_mode_visual(key, operator, operand, match_all)
        visual = visual or self.vi_mode_visual_block(key, operator, operand, match_all)
        return self._check((normal or visual), operator, operand, match_all)

    def vi_mode_normal_or_any_visual(self, key, operator, operand, match_all):
        normal_or_visual = self.vi_mode_normal_or_visual(key, operator, operand, match_all)
        visual_line = self.vi_mode_visual_line(key, operator, operand, match_all)
        return self._check((normal_or_visual or visual_line), operator, operand, match_all)

    def vi_state_next_character_is_user_input(self, key, operator, operand, match_all):
        value = (self.state.expecting_user_input or
                 self.state.expecting_register)
        return self._check(value, operator, operand, match_all)

    def vi_state_expecting_user_input(self, key, operator, operand, match_all):
        value = self.state.expecting_user_input
        return self._check(value, operator, operand, match_all)

    def vi_state_expecting_register(self, key, operator, operand, match_all):
        value = self.state.expecting_register
        return self._check(value, operator, operand, match_all)

    def vi_mode_can_push_digit(self, key, operator, operand, match_all):
        motion_digits = not self.state.motion
        action_digits = self.state.motion
        value = motion_digits or action_digits
        return self._check(value, operator, operand, match_all)

    def vi_is_recording_macro(self, key, operator, operand, match_all):
        value = self.state.is_recording
        return self._check(value, operator, operand, match_all)

    def vi_in_key_namespace(self, key, operator, operand, match_all):
        has_incomplete_action = self.vi_has_incomplete_action('vi_has_incomplete_action', sublime.OP_EQUAL, True, False)
        if not has_incomplete_action:
            return False

        value = action_to_namespace(self.state.action) or action_to_namespace(self.state.motion)
        if not value:
            return False
        value = value == operand
        return value
        # return self._check(value, operator, True, match_all)

    def vi_can_enter_any_visual_mode(self, key, operator, operand, match_all):
        sels = self.state.view.sel()
        rv = True
        for sel in sels:
            # We're assuming we are in normal mode.
            if sel.b == self.state.view.size() and self.state.view.line(sel.b).empty():
                rv = False
                break

        if not rv:
            print("Vintageous: Can't enter visual mode at EOF if last line is empty.")
            utils.blink()

        return self._check(rv, operator, operand, match_all)

    def check(self, key, operator, operand, match_all):
        func = getattr(self, key, None)
        if func:
            return func(key, operator, operand, match_all)
        else:
            return None

    def _check(self, value, operator, operand, match_all):
        if operator == sublime.OP_EQUAL:
            if operand == True:
                return value
            elif operand == False:
                return not value
        elif operator == sublime.OP_NOT_EQUAL:
            if operand == True:
                return not value
            elif operand == False:
                return value
