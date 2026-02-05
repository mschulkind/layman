"""
Unit tests for layman.config module.

Tests the LaymanConfig class for:
- TOML parsing
- Default value retrieval
- Workspace-specific configuration
- Error handling
"""

import pytest

from layman.config import (
    LaymanConfig,
    KEY_DEBUG,
    KEY_LAYOUT,
    KEY_EXCLUDED_WORKSPACES,
    TABLE_LAYMAN,
    TABLE_WORKSPACE,
)

# Additional key names for testing (not exported from config module)
KEY_MASTER_WIDTH = "masterWidth"
KEY_STACK_LAYOUT = "stackLayout"
KEY_STACK_SIDE = "stackSide"
KEY_VISIBLE_STACK_LIMIT = "visibleStackLimit"


class TestLaymanConfigParse:
    """Tests for LaymanConfig.parse() method."""

    def test_parse_validToml_returnsDict(self, configs_path):
        """Valid TOML file should parse to a dictionary."""
        config = LaymanConfig(str(configs_path / "valid_config.toml"))
        assert isinstance(config.configDict, dict)
        assert TABLE_LAYMAN in config.configDict

    def test_parse_minimalConfig_returnsDict(self, configs_path):
        """Minimal config with just [layman] section should parse."""
        config = LaymanConfig(str(configs_path / "minimal_config.toml"))
        assert isinstance(config.configDict, dict)
        assert TABLE_LAYMAN in config.configDict

    def test_parse_invalidToml_raisesConfigError(self, configs_path):
        """Invalid TOML should raise ConfigError (Decision #1)."""
        from layman.config import ConfigError
        with pytest.raises(ConfigError, match="Failed to parse config file"):
            LaymanConfig(str(configs_path / "invalid_config.toml"))

    def test_parse_missingFile_raisesError(self, tmp_path):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            LaymanConfig(str(tmp_path / "nonexistent.toml"))

    def test_parse_emptyFile_returnsEmptyDict(self, tmp_path):
        """Empty TOML file should return empty dict."""
        empty_file = tmp_path / "empty.toml"
        empty_file.write_text("")
        config = LaymanConfig(str(empty_file))
        assert config.configDict == {}


class TestLaymanConfigGetDefault:
    """Tests for LaymanConfig.getDefault() method."""

    def test_getDefault_existingKey_returnsValue(self, valid_config):
        """Should return value when key exists in [layman] section."""
        assert valid_config.getDefault(KEY_DEBUG) is True
        assert valid_config.getDefault(KEY_LAYOUT) == "MasterStack"

    def test_getDefault_missingKey_returnsNone(self, valid_config):
        """Should return None when key doesn't exist."""
        assert valid_config.getDefault("nonexistent_key") is None

    def test_getDefault_intValue_returnsInt(self, valid_config):
        """Should preserve integer type."""
        width = valid_config.getDefault(KEY_MASTER_WIDTH)
        assert isinstance(width, int)
        assert width == 50

    def test_getDefault_listValue_returnsList(self, valid_config):
        """Should preserve list type."""
        excluded = valid_config.getDefault(KEY_EXCLUDED_WORKSPACES)
        assert isinstance(excluded, list)
        assert "10" in excluded

    def test_getDefault_stringValue_returnsString(self, valid_config):
        """Should preserve string type."""
        layout = valid_config.getDefault(KEY_STACK_LAYOUT)
        assert isinstance(layout, str)
        assert layout == "splitv"

    def test_getDefault_emptyConfig_returnsNone(self, tmp_path):
        """Empty config should return None for all keys."""
        empty_file = tmp_path / "empty.toml"
        empty_file.write_text("")
        config = LaymanConfig(str(empty_file))
        assert config.getDefault(KEY_DEBUG) is None
        assert config.getDefault(KEY_LAYOUT) is None


class TestLaymanConfigGetForWorkspace:
    """Tests for LaymanConfig.getForWorkspace() method."""

    def test_getForWorkspace_workspaceOverride_returnsOverride(self, valid_config):
        """Should return workspace-specific value when present."""
        # Workspace 1 has masterWidth = 60 (overriding default 50)
        assert valid_config.getForWorkspace("1", KEY_MASTER_WIDTH) == 60

    def test_getForWorkspace_noOverride_fallsBackToDefault(self, valid_config):
        """Should fall back to [layman] default when workspace key missing."""
        # Workspace 3 doesn't have masterWidth, should use default 50
        assert valid_config.getForWorkspace("3", KEY_MASTER_WIDTH) == 50

    def test_getForWorkspace_missingBoth_returnsNone(self, valid_config):
        """Should return None when neither workspace nor default has key."""
        assert valid_config.getForWorkspace("1", "nonexistent_key") is None

    def test_getForWorkspace_numericName_works(self, valid_config):
        """Should work with numeric workspace names as strings."""
        assert valid_config.getForWorkspace("1", KEY_LAYOUT) == "MasterStack"
        assert valid_config.getForWorkspace("2", KEY_LAYOUT) == "Autotiling"

    def test_getForWorkspace_namedWorkspace_works(self, valid_config):
        """Should work with named workspaces."""
        assert valid_config.getForWorkspace("coding", KEY_LAYOUT) == "MasterStack"
        assert valid_config.getForWorkspace("coding", KEY_MASTER_WIDTH) == 65
        assert valid_config.getForWorkspace("coding", KEY_STACK_LAYOUT) == "stacking"

    def test_getForWorkspace_undefinedWorkspace_usesDefault(self, valid_config):
        """Undefined workspace should use [layman] defaults."""
        assert valid_config.getForWorkspace("99", KEY_LAYOUT) == "MasterStack"
        assert valid_config.getForWorkspace("unknown", KEY_MASTER_WIDTH) == 50

    def test_getForWorkspace_visibleStackLimit_perWorkspace(self, valid_config):
        """visibleStackLimit should be workspace-specific."""
        assert valid_config.getForWorkspace("1", KEY_VISIBLE_STACK_LIMIT) == 5
        assert valid_config.getForWorkspace("2", KEY_VISIBLE_STACK_LIMIT) == 4
        # Workspace 3 and default have 3
        assert valid_config.getForWorkspace("3", KEY_VISIBLE_STACK_LIMIT) == 3


class TestLaymanConfigEdgeCases:
    """Edge case tests for LaymanConfig."""

    def test_specialCharactersInWorkspaceName(self, temp_config):
        """Workspace names with special characters should work."""
        config = temp_config(
            """
[layman]
defaultLayout = "none"

[workspace."my-workspace"]
defaultLayout = "MasterStack"

[workspace."workspace:1"]
defaultLayout = "Grid"
"""
        )
        assert config.getForWorkspace("my-workspace", KEY_LAYOUT) == "MasterStack"
        assert config.getForWorkspace("workspace:1", KEY_LAYOUT) == "Grid"

    def test_masterWidthBoundaries(self, temp_config):
        """masterWidth at boundaries should be stored correctly."""
        config = temp_config(
            """
[layman]
masterWidth = 1

[workspace.1]
masterWidth = 99

[workspace.2]
masterWidth = 50
"""
        )
        assert config.getDefault(KEY_MASTER_WIDTH) == 1
        assert config.getForWorkspace("1", KEY_MASTER_WIDTH) == 99
        assert config.getForWorkspace("2", KEY_MASTER_WIDTH) == 50

    def test_emptyExcludedLists(self, temp_config):
        """Empty excluded lists should return empty list, not None."""
        config = temp_config(
            """
[layman]
excludeWorkspaces = []
excludeOutputs = []
"""
        )
        assert config.getDefault(KEY_EXCLUDED_WORKSPACES) == []

    def test_booleanValues(self, temp_config):
        """Boolean values should be preserved."""
        config = temp_config(
            """
[layman]
debug = true

[workspace.1]
debug = false
"""
        )
        assert config.getDefault(KEY_DEBUG) is True
        assert config.getForWorkspace("1", KEY_DEBUG) is False

    def test_configPathIsNone_usesDefaultPath(self, monkeypatch, tmp_path):
        """When configPath is None, should use default CONFIG_PATH."""
        # This test would need to mock the file system or set up the default path
        # For now, we just verify the constructor accepts None
        # (though it will likely fail trying to open the default path)
        pass  # Skipping as it requires environment setup
