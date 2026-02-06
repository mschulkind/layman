"""Tests for Phase 10 polish features."""

import json

import pytest

from layman.focus_history import FocusHistory
from layman.factory import LayoutManagerFactory
from layman.presets import LayoutPreset, PresetManager
from layman.rules import WindowRule, WindowRuleEngine

from tests.mocks.i3ipc_mocks import MockCon, MockConnection


# =============================================================================
# FocusHistory Tests (Task 32)
# =============================================================================


class TestFocusHistory:
    def test_empty(self):
        h = FocusHistory()
        assert len(h) == 0
        assert h.current() is None
        assert h.previous() is None

    def test_push(self):
        h = FocusHistory()
        h.push(100)
        assert len(h) == 1
        assert h.current() == 100

    def test_push_deduplicates(self):
        h = FocusHistory()
        h.push(100)
        h.push(100)
        assert len(h) == 1

    def test_previous(self):
        h = FocusHistory()
        h.push(100)
        h.push(200)
        assert h.current() == 200
        assert h.previous() == 100

    def test_previous_atEnd(self):
        h = FocusHistory()
        h.push(100)
        assert h.previous() is None

    def test_remove(self):
        h = FocusHistory()
        h.push(100)
        h.push(200)
        h.remove(100)
        assert len(h) == 1
        assert 100 not in h

    def test_contains(self):
        h = FocusHistory()
        h.push(100)
        assert 100 in h
        assert 200 not in h

    def test_entries(self):
        h = FocusHistory()
        h.push(100)
        h.push(200)
        h.push(300)
        assert h.entries == [300, 200, 100]

    def test_maxSize(self):
        h = FocusHistory(max_size=3)
        for i in range(5):
            h.push(i)
        assert len(h) == 3

    def test_resetNavigation(self):
        h = FocusHistory()
        h.push(100)
        h.push(200)
        h.previous()  # Move back
        h.reset_navigation()
        assert h.current() == 200

    def test_clear(self):
        h = FocusHistory()
        h.push(100)
        h.clear()
        assert len(h) == 0

    def test_push_movesToFront(self):
        h = FocusHistory()
        h.push(100)
        h.push(200)
        h.push(100)  # Move 100 back to front
        assert h.entries == [100, 200]


# =============================================================================
# LayoutManagerFactory Tests (Task 33)
# =============================================================================


class TestLayoutManagerFactory:
    def test_register(self):
        from layman.managers.workspace import WorkspaceLayoutManager

        factory = LayoutManagerFactory()
        factory.register(WorkspaceLayoutManager)
        assert factory.is_registered("none")

    def test_available_layouts(self):
        from layman.managers.workspace import WorkspaceLayoutManager

        factory = LayoutManagerFactory()
        factory.register(WorkspaceLayoutManager)
        assert "none" in factory.available_layouts()

    def test_create_unknown(self):
        factory = LayoutManagerFactory()
        assert factory.create("unknown", MockConnection(), None, "1", None) is None

    def test_get_class(self):
        from layman.managers.workspace import WorkspaceLayoutManager

        factory = LayoutManagerFactory()
        factory.register(WorkspaceLayoutManager)
        assert factory.get_class("none") is WorkspaceLayoutManager

    def test_get_class_unknown(self):
        factory = LayoutManagerFactory()
        assert factory.get_class("unknown") is None

    def test_register_many(self):
        from layman.managers.workspace import WorkspaceLayoutManager

        factory = LayoutManagerFactory()
        factory.register_many([WorkspaceLayoutManager])
        assert factory.is_registered("none")


# =============================================================================
# PresetManager Tests (Task 37)
# =============================================================================


class TestPresetManager:
    @pytest.fixture
    def presets_dir(self, tmp_path):
        return str(tmp_path / "presets")

    @pytest.fixture
    def mgr(self, presets_dir):
        return PresetManager(presets_dir)

    def test_save_and_load(self, mgr):
        mgr.save("coding", "MasterStack", {"masterWidth": 60})
        preset = mgr.load("coding")
        assert preset is not None
        assert preset.layout_name == "MasterStack"
        assert preset.options["masterWidth"] == 60

    def test_list_presets(self, mgr):
        mgr.save("a", "MasterStack")
        mgr.save("b", "Grid")
        presets = mgr.list_presets()
        assert "a" in presets
        assert "b" in presets

    def test_delete(self, mgr):
        mgr.save("temp", "MasterStack")
        assert mgr.delete("temp") is True
        assert "temp" not in mgr.list_presets()

    def test_delete_nonexistent(self, mgr):
        assert mgr.delete("nonexistent") is False

    def test_load_nonexistent(self, mgr):
        assert mgr.load("nonexistent") is None


# =============================================================================
# WindowRuleEngine Tests (Task 38)
# =============================================================================


class TestWindowRuleEngine:
    def test_emptyRules(self):
        engine = WindowRuleEngine()
        window = MockCon(id=1, app_id="firefox")
        assert engine.evaluate(window) == {}

    def test_matchAppId(self):
        rule = WindowRule(match_app_id="firefox", exclude=True)
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, app_id="firefox")
        actions = engine.evaluate(window)
        assert actions.get("exclude") is True

    def test_noMatch(self):
        rule = WindowRule(match_app_id="firefox", exclude=True)
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, app_id="chromium")
        assert engine.evaluate(window) == {}

    def test_matchWindowClass(self):
        rule = WindowRule(match_window_class="Firefox", floating=True)
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, window_class="Firefox")
        actions = engine.evaluate(window)
        assert actions.get("floating") is True

    def test_regexMatch(self):
        rule = WindowRule(match_app_id="fire.*", exclude=True)
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, app_id="firefox")
        assert engine.evaluate(window).get("exclude") is True

    def test_caseInsensitive(self):
        rule = WindowRule(match_app_id="Firefox", exclude=True)
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, app_id="firefox")
        assert engine.evaluate(window).get("exclude") is True

    def test_workspaceAction(self):
        rule = WindowRule(match_app_id="slack", workspace="3")
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, app_id="slack")
        assert engine.evaluate(window).get("workspace") == "3"

    def test_multipleRules(self):
        rules = [
            WindowRule(match_app_id="firefox", floating=True),
            WindowRule(match_app_id="firefox", position="master"),
        ]
        engine = WindowRuleEngine(rules)
        window = MockCon(id=1, app_id="firefox")
        actions = engine.evaluate(window)
        assert actions.get("floating") is True
        assert actions.get("position") == "master"

    def test_fromConfig(self):
        config = [
            {"match_app_id": "pavucontrol", "floating": True},
            {"match_app_id": "waybar", "exclude": True},
        ]
        engine = WindowRuleEngine.from_config(config)
        assert len(engine.rules) == 2

    def test_noMatchField(self):
        """Rules without match fields should not match anything."""
        rule = WindowRule(exclude=True)
        engine = WindowRuleEngine([rule])
        window = MockCon(id=1, app_id="anything")
        assert engine.evaluate(window) == {}

    def test_addRule(self):
        engine = WindowRuleEngine()
        engine.add_rule(WindowRule(match_app_id="test", exclude=True))
        assert len(engine.rules) == 1

    def test_clearRules(self):
        engine = WindowRuleEngine([WindowRule(match_app_id="test")])
        engine.clear()
        assert len(engine.rules) == 0
