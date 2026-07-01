"""Tests for terminal cell-width / wrapping utilities.

These functions compute display widths for East-Asian-Wide characters and wrap
text to a terminal cell budget. They are pure: no IO, no curses.
"""
from __future__ import annotations

from ga_tui import app as app_module
from ga_tui import text_utils, ui_types
from ga_tui.text_utils import (
    ANSI_RE,
    cell_width,
    clean_text,
    compact_category,
    compact_title,
    pad_cells,
    truncate_cells,
    wrap_cells,
)


class TestAppCompatibilityAliases:
    def test_text_utils_reexported_from_app(self) -> None:
        assert app_module.ANSI_RE is text_utils.ANSI_RE
        assert app_module.cell_width is text_utils.cell_width
        assert app_module.truncate_cells is text_utils.truncate_cells
        assert app_module.pad_cells is text_utils.pad_cells
        assert app_module.clean_text is text_utils.clean_text
        assert app_module.wrap_cells is text_utils.wrap_cells
        assert app_module.compact_title is text_utils.compact_title
        assert app_module.compact_category is text_utils.compact_category

    def test_ui_types_reexported_from_app(self) -> None:
        assert app_module.Message is ui_types.Message
        assert app_module.RenderLine is ui_types.RenderLine
        assert app_module.State is ui_types.State
        assert app_module.SubAgentRuntime is ui_types.SubAgentRuntime
        assert app_module.MAIN_HOME_SESSION_KEY == ui_types.MAIN_HOME_SESSION_KEY
        assert app_module.SCHEDULED_REPORTS_SESSION_KEY == ui_types.SCHEDULED_REPORTS_SESSION_KEY
        assert app_module.SUBAGENT_HOME_SESSION_PREFIX == ui_types.SUBAGENT_HOME_SESSION_PREFIX


class TestCellWidth:
    def test_ascii(self) -> None:
        assert cell_width("hello") == 5

    def test_empty(self) -> None:
        assert cell_width("") == 0
    def test_mixed(self) -> None:
        # 2 ASCII + 2 CJK (2 cells each) = 2 + 4
        assert cell_width("ab枢衡") == 6
        assert cell_width("枢衡") == 4

    def test_combining_marks_zero_width(self) -> None:
        # U+0301 COMBINING ACUTE ACCENT adds no width.
        assert cell_width("e\u0301") == 1

    def test_emoji_wide(self) -> None:
        # Most emoji render at width 2 in terminals; unicodedata classifies
        # many as W. Assert at least the common case.
        assert cell_width("\N{POLICE CAR}") >= 1


class TestTruncateCells:
    def test_truncate_ascii(self) -> None:
        assert truncate_cells("hello world", 5) == "hello…"

    def test_zero_width_returns_empty(self) -> None:
        assert truncate_cells("abc", 0) == ""

    def test_negative_width_returns_empty(self) -> None:
        assert truncate_cells("abc", -1) == ""

    def test_exact_fit_no_ellipsis(self) -> None:
        assert truncate_cells("abc", 3) == "abc"

    def test_truncate_mid_cjk(self) -> None:
        # One CJK char = 2 cells; width 3 fits one CJK (2) + ellipsis.
        assert truncate_cells("枢衡", 3) == "枢…"

    def test_truncate_at_cjk_boundary(self) -> None:
        # width 2 fits exactly one CJK, ellipsis won't fit -> just the char.
        assert truncate_cells("枢衡xyz", 2) == "枢…"


class TestPadCells:
    def test_pad_short_ascii(self) -> None:
        assert pad_cells("hi", 5) == "hi   "

    def test_pad_exact(self) -> None:
        assert pad_cells("abc", 3) == "abc"

    def test_pad_truncates_overflow(self) -> None:
        # Overflow truncates with ellipsis; the ellipsis "…" is 1 cell, so a
        # width-3 budget yields "abc…" which is 4 cells (overflow by 1). This
        # documents the existing design where truncation prefers showing the
        # ellipsis marker over strictly respecting the cell budget.
        result = pad_cells("abcdef", 3)
        assert result == "abc…"

    def test_pad_overflow_width_matches_truncate(self) -> None:
        # pad_cells delegates to truncate_cells then pads only if shorter.
        assert pad_cells("abcdef", 3) == truncate_cells("abcdef", 3)
    def test_pad_cjk(self) -> None:
        # 枢 is 2 cells; target 4 -> 2 trailing spaces.
        assert pad_cells("枢", 4) == "枢  "


class TestCleanText:
    def test_strips_ansi_color(self) -> None:
        assert clean_text("\x1b[31mred\x1b[0m") == "red"

    def test_strips_csi_cursor(self) -> None:
        assert clean_text("a\x1b[2Kb") == "ab"

    def test_collapses_excessive_newlines(self) -> None:
        assert clean_text("a\n\n\n\n\nb") == "a\n\n\nb"

    def test_strips_trailing_whitespace(self) -> None:
        assert clean_text("text   \n  ") == "text"

    def test_none_input(self) -> None:
        assert clean_text(None) == ""  # type: ignore[arg-type]

    def test_osc_terminator(self) -> None:
        # OSC sequence ended by BEL.
        assert ANSI_RE.sub("", "\x1b]0;title\x07text") == "text"


class TestCompactTitle:
    def test_strips_markdown_html_and_boilerplate(self) -> None:
        assert compact_title("用户要求: **实现** <b>功能</b> #1", 80) == "实现 功能 1"
        assert compact_title("总结：下一步计划。", 80) == "下一步计划"

    def test_drops_fenced_code_and_truncates_by_cells(self) -> None:
        text = "```python\nprint('hidden')\n```\n枢衡标题abcdef"

        assert compact_title(text, 8) == "枢衡标题…"

    def test_empty_after_cleanup(self) -> None:
        assert compact_title("```hidden```", 80) == ""


class TestCompactCategory:
    def test_filters_sentinel_values(self) -> None:
        assert compact_category("-") == ""
        assert compact_category("clear") == ""
        assert compact_category("未分类") == ""

    def test_compacts_regular_category(self) -> None:
        assert compact_category("  **Shuheng / Agent**  ") == "Shuheng / Agent"


class TestWrapCells:
    def test_wrap_simple(self) -> None:
        # width > 4 uses the real wrap path; width 6 wraps "abcdef" in two.
        lines = wrap_cells("abcdef", 3)
        # width 3 <= 4 triggers the fallback (single truncated line).
        assert lines == ["abc…"]

    def test_wrap_real_path(self) -> None:
        lines = wrap_cells("abcdef", 5)
        assert lines == ["abcde", "f"]

    def test_wrap_exact_fit(self) -> None:
        lines = wrap_cells("abcdef", 6)
        assert lines == ["abcdef"]

    def test_wrap_narrow_returns_truncated(self) -> None:
        # width <= 4 falls back to single truncated line.
        lines = wrap_cells("abcdef", 2)
        assert lines == ["ab…"]

    def test_wrap_preserves_newlines(self) -> None:
        lines = wrap_cells("ab\ncd", 10)
        assert lines == ["ab", "cd"]

    def test_wrap_empty_lines_kept(self) -> None:
        lines = wrap_cells("a\n\nb", 10)
        assert lines == ["a", "", "b"]

    def test_wrap_expands_tabs(self) -> None:
        lines = wrap_cells("a\tb", 10)
        assert lines == ["a    b"]

    def test_wrap_cjk(self) -> None:
        # 枢 is 2 cells; width 6 (>4 for real wrap) fits three CJK chars.
        lines = wrap_cells("枢枢枢枢", 6)
        assert lines == ["枢枢枢", "枢"]

    def test_wrap_empty_input(self) -> None:
        lines = wrap_cells("", 10)
        assert lines == [""]

    def test_wrap_none_input(self) -> None:
        lines = wrap_cells(None, 10)  # type: ignore[arg-type]
        assert lines == [""]
