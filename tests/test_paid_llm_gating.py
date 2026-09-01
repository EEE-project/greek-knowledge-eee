"""Tests the paid_llm_api gating mechanism itself (marker + CLI flag +
fixture-level double-gate), entirely through synthetic, throwaway test code
generated inside isolated pytester sandboxes. This file makes ZERO real
network calls or real LLM client constructions anywhere, and must NOT
itself be marked integration or paid_llm_api -- it runs cleanly under
`uv run pytest -m "not integration"`.

Every sandbox re-registers the real tests.conftest module as a plugin
(`pytest_plugins = ['tests.conftest']`) rather than hand-copying the hooks,
so these tests exercise the actual implementation and cannot silently
drift out of sync with it.
"""

import pytest


def test_marker_skipped_by_default(pytester):
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.paid_llm_api
        def test_dummy():
            assert True
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(skipped=1)


def test_runs_when_flag_and_both_env_gates_satisfied(pytester, monkeypatch):
    monkeypatch.setenv("FAKE_PAID_API_KEY", "real-looking-key")
    monkeypatch.setenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", "1")
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import MagicMock
        from tests.conftest import require_paid_llm_gate

        construct_llm_backend = MagicMock()

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")
            construct_llm_backend()
            return object()

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            pass

        def test_construction_point_reached():
            construct_llm_backend.assert_called_once()
        """
    )
    result = pytester.runpytest("--run-paid-llm-tests")
    result.assert_outcomes(passed=2)


def test_direct_marker_selection_without_flag_still_skips(pytester):
    """Proves the collection-hook gate, not just an abstract description of
    intent, is what actually blocks execution regardless of how the test
    got selected -- `-m paid_llm_api` selects this test, but the hook still
    applies its skip marker since --run-paid-llm-tests was never passed."""
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.paid_llm_api
        def test_dummy():
            assert True
        """
    )
    result = pytester.runpytest("-m", "paid_llm_api")
    result.assert_outcomes(skipped=1)


def test_skips_cleanly_when_key_env_var_unset(pytester, monkeypatch):
    monkeypatch.delenv("FAKE_PAID_API_KEY", raising=False)
    monkeypatch.setenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", "1")
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from tests.conftest import require_paid_llm_gate

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            pass
        """
    )
    result = pytester.runpytest("--run-paid-llm-tests", "-rs")
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(["*FAKE_PAID_API_KEY*to be set*"])


def test_skips_when_key_present_but_whitespace_only(pytester, monkeypatch):
    monkeypatch.setenv("FAKE_PAID_API_KEY", "   ")
    monkeypatch.setenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", "1")
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from tests.conftest import require_paid_llm_gate

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            pass
        """
    )
    result = pytester.runpytest("--run-paid-llm-tests", "-rs")
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(["*FAKE_PAID_API_KEY*to be set*"])


def test_skips_with_distinguishable_message_when_confirm_var_unset(pytester, monkeypatch):
    monkeypatch.setenv("FAKE_PAID_API_KEY", "real-looking-key")
    monkeypatch.delenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", raising=False)
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from tests.conftest import require_paid_llm_gate

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            pass
        """
    )
    result = pytester.runpytest("--run-paid-llm-tests", "-rs")
    result.assert_outcomes(skipped=1)
    result.stdout.fnmatch_lines(["*GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS=1*"])
    result.stdout.no_fnmatch_line("*FAKE_PAID_API_KEY*to be set*")


@pytest.mark.parametrize("confirm_value", ["0", "false", "true", "yes", "TRUE", " 1", "1 "])
def test_skips_unless_confirm_var_is_exactly_one(pytester, monkeypatch, confirm_value):
    """Exact-match, not truthy-string, semantics -- includes whitespace-
    padded "1" to prove the comparison is against the RAW, unstripped
    value (unlike the key check, which strips before testing).
    Parametrized (not a bare loop) so a failing value is individually
    named in the test result, not just "somewhere in this test"."""
    monkeypatch.setenv("FAKE_PAID_API_KEY", "real-looking-key")
    monkeypatch.setenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", confirm_value)
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from tests.conftest import require_paid_llm_gate

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            pass
        """
    )
    result = pytester.runpytest("--run-paid-llm-tests")
    result.assert_outcomes(skipped=1)


def test_no_real_construction_when_key_missing(pytester, monkeypatch):
    """Distinct from the outcome-only skip checks above: asserts on the
    construction mock's OWN call state directly, not merely that the
    test's outcome was "skipped" -- a second, unmarked test function in
    the same sandboxed module shares the mock object and runs
    unconditionally, proving the construction point was truly never
    reached (pytest.skip() inside the fixture prevents anything after it
    in that fixture body from ever executing)."""
    monkeypatch.delenv("FAKE_PAID_API_KEY", raising=False)
    monkeypatch.setenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", "1")
    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import MagicMock
        from tests.conftest import require_paid_llm_gate

        construct_llm_backend = MagicMock()

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")
            construct_llm_backend()
            return object()

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            pass

        def test_construction_point_never_reached():
            construct_llm_backend.assert_not_called()
        """
    )
    result = pytester.runpytest("--run-paid-llm-tests")
    result.assert_outcomes(skipped=1, passed=1)


@pytest.mark.parametrize(
    "invocation_args,key_set,confirm_set,expect_construction",
    [
        ((), True, True, False),
        ((), True, False, False),
        ((), False, True, False),
        ((), False, False, False),
        (("-m", "paid_llm_api"), True, True, False),
        (("-m", "paid_llm_api"), True, False, False),
        (("-m", "paid_llm_api"), False, True, False),
        (("-m", "paid_llm_api"), False, False, False),
        (("--run-paid-llm-tests", "-m", "paid_llm_api"), True, True, True),
        (("--run-paid-llm-tests", "-m", "paid_llm_api"), True, False, False),
        (("--run-paid-llm-tests", "-m", "paid_llm_api"), False, True, False),
        (("--run-paid-llm-tests", "-m", "paid_llm_api"), False, False, False),
    ],
)
def test_invocation_matrix_only_full_gate_reaches_construction(
    pytester, monkeypatch, invocation_args, key_set, confirm_set, expect_construction
):
    """Crosses {no flag, -m selection alone, flag+-m} x {key set/unset} x
    {confirm set/unset}: the real-construction point is reached in exactly
    one of these twelve combinations -- flag present AND key present AND
    confirm=="1" -- proving the actual invocation matrix, not just the
    single intended happy path."""
    if key_set:
        monkeypatch.setenv("FAKE_PAID_API_KEY", "real-looking-key")
    else:
        monkeypatch.delenv("FAKE_PAID_API_KEY", raising=False)
    if confirm_set:
        monkeypatch.setenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", "1")
    else:
        monkeypatch.delenv("GREEK_KNOWLEDGE_RUN_PAID_LLM_TESTS", raising=False)

    pytester.makeconftest("pytest_plugins = ['tests.conftest']")
    pytester.makepyfile(
        """
        import pytest
        from unittest.mock import MagicMock
        from tests.conftest import require_paid_llm_gate

        construct_llm_backend = MagicMock()

        @pytest.fixture
        def real_config():
            require_paid_llm_gate("FAKE_PAID_API_KEY")
            construct_llm_backend()
            return object()

        @pytest.mark.paid_llm_api
        def test_uses_real_config(real_config):
            assert construct_llm_backend.called
        """
    )
    result = pytester.runpytest(*invocation_args)

    if expect_construction:
        result.assert_outcomes(passed=1)
    else:
        result.assert_outcomes(skipped=1)
