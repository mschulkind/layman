"""
Integration test placeholders for layman.

These tests require a running Sway/i3 instance and are marked
with @pytest.mark.integration. They are skipped by default.

Run with: just test-integration
"""

import pytest


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestLaymanIntegration:
    """Integration tests for full layman functionality."""

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_layman_starts_without_crash(self):
        """Layman daemon should start without errors."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_masterstack_layout_applies(self):
        """MasterStack layout should correctly arrange windows."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_autotiling_layout_applies(self):
        """Autotiling layout should correctly alternate splits."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_command_handling(self):
        """Commands via named pipe should be processed."""
        pass

    @pytest.mark.skip(reason="Requires running Sway/i3")
    def test_config_reload(self):
        """Config reload should apply new settings."""
        pass
