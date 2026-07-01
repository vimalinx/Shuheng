"""Tests for pure input cursor/display geometry helpers."""
from __future__ import annotations

from types import SimpleNamespace

from ga_tui import app as app_module
from ga_tui import input_controller


class TestAppCompatibilityAliases:
    def test_input_helpers_reexported_from_app(self) -> None:
        assert app_module.raw_cursor_to_display is input_controller.raw_cursor_to_display
        assert app_module.display_cursor_to_raw is input_controller.display_cursor_to_raw
        assert app_module.input_segments is input_controller.input_segments
        assert app_module.display_index_for_cell is input_controller.display_index_for_cell
        assert app_module.input_cursor_info is input_controller.input_cursor_info
        assert app_module.input_layout is input_controller.input_layout
        assert app_module.input_vertical_cursor_target is input_controller.input_vertical_cursor_target
        assert app_module.normalize_pasted_text is input_controller.normalize_pasted_text
        assert app_module.InputHistoryBrowseResult is input_controller.InputHistoryBrowseResult
        assert app_module.input_history_browse_result is input_controller.input_history_browse_result
        assert app_module.MOUSE_BUTTON_STATES is input_controller.MOUSE_BUTTON_STATES
        assert app_module.mouse_button_mask_from_constants is input_controller.mouse_button_mask_from_constants
        assert app_module.mouse_modifier_mask_from_constants is input_controller.mouse_modifier_mask_from_constants
        assert app_module.mouse_known_bstate_mask_from_constants is input_controller.mouse_known_bstate_mask_from_constants
        assert (
            app_module.mouse_auxiliary_or_unknown_event_from_constants
            is input_controller.mouse_auxiliary_or_unknown_event_from_constants
        )
        assert app_module.clean_button1_action_from_constants is input_controller.clean_button1_action_from_constants

    def test_mouse_helpers_keep_app_curses_wrapper_parity(self) -> None:
        constants = app_module._mouse_curses_constants()
        assert app_module.mouse_button_mask(1) == input_controller.mouse_button_mask_from_constants(1, constants)
        assert app_module.mouse_modifier_mask() == input_controller.mouse_modifier_mask_from_constants(constants)
        assert app_module.mouse_known_bstate_mask() == input_controller.mouse_known_bstate_mask_from_constants(constants)
        sample_bstate = app_module.mouse_button_mask(1) | app_module.mouse_modifier_mask()
        allowed = int(getattr(app_module.curses, "BUTTON1_CLICKED", 0) or 0)
        assert app_module.mouse_auxiliary_or_unknown_event(
            sample_bstate
        ) == input_controller.mouse_auxiliary_or_unknown_event_from_constants(sample_bstate, constants)
        assert app_module.clean_button1_action(
            sample_bstate,
            allowed,
        ) == input_controller.clean_button1_action_from_constants(sample_bstate, allowed, constants)


class TestCursorMapping:
    def test_raw_newline_displays_as_two_cells(self) -> None:
        text = "a\nb"

        assert input_controller.raw_cursor_to_display(text, -1) == 0
        assert input_controller.raw_cursor_to_display(text, 0) == 0
        assert input_controller.raw_cursor_to_display(text, 1) == 1
        assert input_controller.raw_cursor_to_display(text, 2) == 3
        assert input_controller.raw_cursor_to_display(text, 3) == 4
        assert input_controller.raw_cursor_to_display(text, 99) == 4

    def test_display_cursor_maps_back_through_newline_escape(self) -> None:
        text = "a\nb"

        assert input_controller.display_cursor_to_raw(text, -1) == 0
        assert input_controller.display_cursor_to_raw(text, 0) == 0
        assert input_controller.display_cursor_to_raw(text, 1) == 1
        assert input_controller.display_cursor_to_raw(text, 2) == 2
        assert input_controller.display_cursor_to_raw(text, 3) == 2
        assert input_controller.display_cursor_to_raw(text, 4) == 3
        assert input_controller.display_cursor_to_raw(text, 99) == 3

    def test_raw_display_round_trip_clamps_source_cursor(self) -> None:
        text = "a\nb枢"

        for raw_cursor in range(-2, len(text) + 3):
            clamped = max(0, min(raw_cursor, len(text)))
            display_cursor = input_controller.raw_cursor_to_display(text, raw_cursor)
            assert input_controller.display_cursor_to_raw(text, display_cursor) == clamped


class TestInputSegments:
    def test_wraps_escaped_newline_by_display_cells(self) -> None:
        assert input_controller.input_segments("a\nb", 4) == (
            "a\\nb",
            [("a\\", 0, 2), ("nb", 2, 4)],
        )

    def test_wraps_east_asian_wide_characters(self) -> None:
        assert input_controller.input_segments("ab枢衡", 4) == (
            "ab枢衡",
            [("ab", 0, 2), ("枢", 2, 3), ("衡", 3, 4)],
        )

    def test_combining_marks_do_not_consume_cells(self) -> None:
        assert input_controller.input_segments("e\u0301f", 4) == (
            "e\u0301f",
            [("e\u0301f", 0, 3)],
        )

    def test_empty_input_keeps_one_empty_segment(self) -> None:
        assert input_controller.input_segments("", 0) == ("", [("", 0, 0)])


class TestDisplayIndexForCell:
    def test_ascii_cell_lookup(self) -> None:
        display = "abcd"

        assert input_controller.display_index_for_cell(display, 1, 4, -1) == 1
        assert input_controller.display_index_for_cell(display, 1, 4, 0) == 1
        assert input_controller.display_index_for_cell(display, 1, 4, 1) == 2
        assert input_controller.display_index_for_cell(display, 1, 4, 3) == 4
        assert input_controller.display_index_for_cell(display, 1, 4, 9) == 4

    def test_wide_character_cell_lookup(self) -> None:
        display = "a枢b"

        assert input_controller.display_index_for_cell(display, 0, len(display), 0) == 0
        assert input_controller.display_index_for_cell(display, 0, len(display), 1) == 1
        assert input_controller.display_index_for_cell(display, 0, len(display), 2) == 1
        assert input_controller.display_index_for_cell(display, 0, len(display), 3) == 2
        assert input_controller.display_index_for_cell(display, 0, len(display), 4) == 3


class TestInputCursorInfo:
    def test_cursor_info_for_wrapped_newline_display(self) -> None:
        assert input_controller.input_cursor_info("a\nb", 4, 3) == (
            "a\\nb",
            [("a\\", 0, 2), ("nb", 2, 4)],
            4,
            1,
            2,
        )

    def test_cursor_info_for_wide_and_combining_text(self) -> None:
        assert input_controller.input_cursor_info("e\u0301枢", 4, 3) == (
            "e\u0301枢",
            [("e\u0301", 0, 2), ("枢", 2, 3)],
            3,
            1,
            2,
        )

    def test_cursor_info_clamps_raw_cursor(self) -> None:
        assert input_controller.input_cursor_info("abc", 10, 99) == (
            "abc",
            [("abc", 0, 3)],
            3,
            0,
            3,
        )


class TestInputLayout:
    def test_simple_unwrapped_layout(self) -> None:
        assert input_controller.input_layout("abc", 10, 3, 2) == (["> abc"], 0, 4)

    def test_wrapped_layout_uses_prompt_width_for_continuations(self) -> None:
        assert input_controller.input_layout("abcd", 4, 3, 3) == (["> ab", "  cd"], 1, 3)

    def test_scrolled_layout_keeps_cursor_line_visible(self) -> None:
        assert input_controller.input_layout("abcdef", 4, 2, 5) == (["… cd", "  ef"], 1, 3)

    def test_hidden_first_visible_line_uses_ellipsis_prefix(self) -> None:
        assert input_controller.input_layout("abcdef", 4, 2, 3) == (["… cd", "  ef"], 0, 3)

    def test_custom_prompt_controls_initial_cursor_x(self) -> None:
        assert input_controller.input_layout("abc", 10, 2, 1, "secret> ") == (["secret> abc"], 0, 9)

    def test_newline_layout_uses_escaped_display_text(self) -> None:
        assert input_controller.input_layout("a\nb", 4, 3, 3) == (["> a\\", "  nb"], 1, 4)

    def test_wide_and_combining_text_cursor_x_uses_cell_width(self) -> None:
        assert input_controller.input_layout("e\u0301枢", 4, 2, 3) == (["> e\u0301", "  枢"], 1, 4)

    def test_max_lines_is_at_least_one(self) -> None:
        assert input_controller.input_layout("abcd", 4, 0, 3) == (["… cd"], 0, 3)


class TestVerticalCursorTarget:
    def test_empty_or_single_line_input_does_not_consume(self) -> None:
        assert input_controller.input_vertical_cursor_target("", 4, 0, 1) == (False, None)
        assert input_controller.input_vertical_cursor_target("abc", 10, 1, 1) == (False, None)

    def test_out_of_range_line_consumes_without_target(self) -> None:
        assert input_controller.input_vertical_cursor_target("abcdef", 4, 5, 1) == (True, None)
        assert input_controller.input_vertical_cursor_target("abcdef", 4, 1, -1) == (True, None)

    def test_moves_between_wrapped_lines_preserving_display_cell(self) -> None:
        assert input_controller.input_vertical_cursor_target("abcdef", 4, 5, -1) == (True, 3)
        assert input_controller.input_vertical_cursor_target("abcdef", 4, 1, 1) == (True, 3)

    def test_wide_and_combining_text_preserves_existing_geometry(self) -> None:
        text = "e\u0301枢ab"

        assert input_controller.input_vertical_cursor_target(text, 4, len(text), -1) == (True, 3)
        assert input_controller.input_vertical_cursor_target(text, 4, 1, 1) == (True, 2)

    def test_app_wrapper_mutates_only_when_target_exists(self) -> None:
        state = SimpleNamespace(input_text="abcdef", input_cursor=5, dirty=False)

        assert app_module.move_input_cursor_vertical(state, 4, -1)
        assert state.input_cursor == 3
        assert state.dirty

    def test_app_wrapper_keeps_out_of_range_consumption_without_dirtying(self) -> None:
        state = SimpleNamespace(input_text="abcdef", input_cursor=5, dirty=False)

        assert app_module.move_input_cursor_vertical(state, 4, 1)
        assert state.input_cursor == 5
        assert not state.dirty

    def test_app_wrapper_marks_dirty_for_in_range_same_target(self) -> None:
        state = SimpleNamespace(input_text="abcdef", input_cursor=5, dirty=False)

        assert app_module.move_input_cursor_vertical(state, 4, 0)
        assert state.input_cursor == 5
        assert state.dirty


class TestPasteNormalization:
    def test_collapses_newline_runs_and_surrounding_spaces(self) -> None:
        assert input_controller.normalize_pasted_text(" alpha \n\t beta\r\n gamma ") == " alpha beta gamma "

    def test_replaces_remaining_tabs_with_four_spaces(self) -> None:
        assert input_controller.normalize_pasted_text("a\tb\nc\t\td") == "a    b c        d"

    def test_app_alias_matches_input_controller_helper(self) -> None:
        text = "one\n two\tthree"
        assert app_module.normalize_pasted_text(text) == input_controller.normalize_pasted_text(text)


class TestInputHistoryBrowse:
    def test_empty_history_or_down_before_browsing_does_not_consume(self) -> None:
        assert not input_controller.input_history_browse_result([], "draft", 2, None, "", 0, -1).consumed
        assert not input_controller.input_history_browse_result(["old"], "draft", 2, None, "", 0, 1).consumed

    def test_first_up_saves_draft_and_selects_latest_entry(self) -> None:
        result = input_controller.input_history_browse_result(["old", "new"], "draft", 3, None, "", 0, -1)

        assert result == input_controller.InputHistoryBrowseResult(True, "new", 3, 1, "draft", 3)

    def test_up_clamps_at_oldest_entry(self) -> None:
        result = input_controller.input_history_browse_result(["old", "new"], "new", 3, 1, "draft", 3, -9)

        assert result == input_controller.InputHistoryBrowseResult(True, "old", 3, 0, "draft", 3)

    def test_down_restores_draft_after_newest_entry(self) -> None:
        result = input_controller.input_history_browse_result(["old"], "old", 3, 0, "draft", 2, 1)

        assert result == input_controller.InputHistoryBrowseResult(True, "draft", 2, None, "", 0)

    def test_app_wrapper_applies_history_result_and_marks_dirty(self) -> None:
        state = SimpleNamespace(
            input_history=["old", "new"],
            input_text="draft",
            input_cursor=2,
            input_history_index=None,
            input_history_draft="",
            input_history_draft_cursor=0,
            command_index=3,
            dirty=False,
        )

        assert app_module.browse_input_history(state, -1)
        assert state.input_text == "new"
        assert state.input_cursor == 3
        assert state.input_history_index == 1
        assert state.input_history_draft == "draft"
        assert state.input_history_draft_cursor == 2
        assert state.command_index == 0
        assert state.dirty

    def test_app_wrapper_restores_saved_draft_after_newest_entry(self) -> None:
        state = SimpleNamespace(
            input_history=["old"],
            input_text="old",
            input_cursor=3,
            input_history_index=0,
            input_history_draft="draft",
            input_history_draft_cursor=2,
            command_index=4,
            dirty=False,
        )

        assert app_module.browse_input_history(state, 1)
        assert state.input_text == "draft"
        assert state.input_cursor == 2
        assert state.input_history_index is None
        assert state.input_history_draft == ""
        assert state.input_history_draft_cursor == 0
        assert state.command_index == 0
        assert state.dirty


class TestMouseMaskHelpers:
    CONSTANTS = {
        "BUTTON1_PRESSED": 1 << 0,
        "BUTTON1_RELEASED": 1 << 1,
        "BUTTON1_CLICKED": 1 << 2,
        "BUTTON1_DOUBLE_CLICKED": 1 << 3,
        "BUTTON1_TRIPLE_CLICKED": 1 << 4,
        "BUTTON2_CLICKED": 1 << 5,
        "BUTTON3_CLICKED": 1 << 6,
        "REPORT_MOUSE_POSITION": 1 << 7,
        "BUTTON_SHIFT": 1 << 8,
        "BUTTON_CTRL": 1 << 9,
        "BUTTON_ALT": 1 << 10,
    }

    def test_button_modifier_and_known_masks_use_explicit_constants(self) -> None:
        button1 = sum(1 << bit for bit in range(5))
        assert input_controller.mouse_button_mask_from_constants(1, self.CONSTANTS) == button1
        assert input_controller.mouse_button_mask_from_constants(2, self.CONSTANTS) == 1 << 5
        assert input_controller.mouse_modifier_mask_from_constants(self.CONSTANTS) == (1 << 8) | (1 << 9) | (1 << 10)
        assert input_controller.mouse_known_bstate_mask_from_constants(self.CONSTANTS, button_count=3) == (
            button1 | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 8) | (1 << 9) | (1 << 10)
        )

    def test_auxiliary_or_unknown_event_detects_non_primary_and_unknown_bits(self) -> None:
        primary_with_modifier = self.CONSTANTS["BUTTON1_CLICKED"] | self.CONSTANTS["BUTTON_SHIFT"]
        assert not input_controller.mouse_auxiliary_or_unknown_event_from_constants(primary_with_modifier, self.CONSTANTS)
        assert input_controller.mouse_auxiliary_or_unknown_event_from_constants(
            self.CONSTANTS["BUTTON2_CLICKED"],
            self.CONSTANTS,
        )
        assert input_controller.mouse_auxiliary_or_unknown_event_from_constants(1 << 30, self.CONSTANTS)

    def test_clean_button1_action_allows_only_requested_primary_action_and_modifiers(self) -> None:
        clicked = self.CONSTANTS["BUTTON1_CLICKED"]
        shifted_clicked = clicked | self.CONSTANTS["BUTTON_SHIFT"]
        assert input_controller.clean_button1_action_from_constants(clicked, clicked, self.CONSTANTS)
        assert input_controller.clean_button1_action_from_constants(shifted_clicked, clicked, self.CONSTANTS)
        assert not input_controller.clean_button1_action_from_constants(
            self.CONSTANTS["BUTTON1_PRESSED"],
            clicked,
            self.CONSTANTS,
        )
        assert not input_controller.clean_button1_action_from_constants(
            clicked | self.CONSTANTS["BUTTON2_CLICKED"],
            clicked,
            self.CONSTANTS,
        )
        assert not input_controller.clean_button1_action_from_constants(clicked | (1 << 30), clicked, self.CONSTANTS)
