"""Unit tests for src/utils/helpers.py — normalize_project_name and error logging helpers."""


from src.utils.helpers import get_file_name, get_function_name, normalize_project_name


class TestNormalizeProjectName:
    """Tests for the normalize_project_name utility function."""

    def test_removes_zeb_prefix(self):
        """Should remove 'zeb-' prefix from the beginning."""
        assert normalize_project_name("zeb-touchpoint-pj") == "touchpoint pj"

    def test_case_insensitive_zeb_prefix(self):
        """Should handle uppercase ZEB- prefix (lowercased first)."""
        assert normalize_project_name("ZEB-My-Project") == "my project"

    def test_replaces_hyphens_with_spaces(self):
        """Should replace all hyphens with spaces."""
        assert normalize_project_name("my-cool-project") == "my cool project"

    def test_lowercases_input(self):
        """Should lowercase the entire string."""
        assert normalize_project_name("Touchpoint PJ") == "touchpoint pj"

    def test_strips_whitespace(self):
        """Should strip leading and trailing whitespace."""
        assert normalize_project_name("  some-name  ") == "some name"

    def test_collapses_multiple_spaces(self):
        """Should collapse multiple spaces into one."""
        assert normalize_project_name("zeb-  double   space") == "double space"

    def test_matching_example_from_requirements(self):
        """The canonical example: 'zeb-touchpoint-pj' matches 'Touchpoint PJ'."""
        assert normalize_project_name("zeb-touchpoint-pj") == normalize_project_name("Touchpoint PJ")

    def test_empty_string_returns_empty(self):
        """Empty string returns empty string."""
        assert normalize_project_name("") == ""

    def test_none_returns_empty(self):
        """None input returns empty string."""
        assert normalize_project_name(None) == ""

    def test_only_zeb_prefix(self):
        """String that is just 'zeb-' returns empty after normalization."""
        assert normalize_project_name("zeb-") == ""

    def test_no_zeb_prefix_unchanged(self):
        """String without 'zeb-' prefix is just lowercased and hyphen-replaced."""
        assert normalize_project_name("Payment Gateway") == "payment gateway"

    def test_zeb_in_middle_not_removed(self):
        """'zeb-' only removed from the start, not the middle."""
        assert normalize_project_name("my-zeb-project") == "my zeb project"

    def test_complex_name(self):
        """Complex name with multiple transformations."""
        assert normalize_project_name("ZEB-Multi-Word-Project-Name") == "multi word project name"


class TestGetFunctionName:
    """Tests for the get_function_name helper."""

    def test_returns_function_name_from_traceback(self):
        """Should extract the function name from the exception traceback."""
        try:
            raise ValueError("test error")
        except ValueError as exc:
            result = get_function_name(exc)
            assert result == "test_returns_function_name_from_traceback"

    def test_returns_unknown_when_no_traceback(self):
        """Should return 'unknown' when exception has no traceback."""
        exc = ValueError("no traceback")
        result = get_function_name(exc)
        assert result == "unknown"


class TestGetFileName:
    """Tests for the get_file_name helper."""

    def test_returns_file_name_from_traceback(self):
        """Should extract the file name from the exception traceback."""
        try:
            raise ValueError("test error")
        except ValueError as exc:
            result = get_file_name(exc)
            assert "test_helpers" in result

    def test_returns_unknown_when_no_traceback(self):
        """Should return 'unknown' when exception has no traceback."""
        exc = ValueError("no traceback")
        result = get_file_name(exc)
        assert result == "unknown"
