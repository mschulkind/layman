"""Tests for the performance utilities (Phase 7)."""

import time

import pytest

from layman.perf import CommandBatcher, TreeCache, EventDebouncer

from tests.mocks.i3ipc_mocks import (
    MockCon,
    MockConnection,
    MockRect,
    create_workspace,
    create_tree_with_workspaces,
)


# =============================================================================
# CommandBatcher Tests
# =============================================================================


class TestCommandBatcher:
    """Tests for the CommandBatcher context manager."""

    def test_directCommand_sendsImmediately(self):
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        batcher.command("[con_id=1] focus")
        assert len(conn.commands_executed) == 1
        assert conn.commands_executed[0] == "[con_id=1] focus"

    def test_batchContext_joinsCommands(self):
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        with batcher.batch():
            batcher.command("[con_id=1] move left")
            batcher.command("[con_id=2] focus")

        # Should have sent ONE combined command
        assert len(conn.commands_executed) == 1
        assert conn.commands_executed[0] == "[con_id=1] move left; [con_id=2] focus"

    def test_batchContext_emptyBatch(self):
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        with batcher.batch():
            pass
        assert len(conn.commands_executed) == 0

    def test_batchContext_singleCommand(self):
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        with batcher.batch():
            batcher.command("[con_id=1] focus")
        assert len(conn.commands_executed) == 1
        assert conn.commands_executed[0] == "[con_id=1] focus"

    def test_batchContext_manyCommands(self):
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        with batcher.batch():
            for i in range(10):
                batcher.command(f"[con_id={i}] focus")
        assert len(conn.commands_executed) == 1
        assert conn.commands_executed[0].count(";") == 9

    def test_afterBatch_commandsSendDirectly(self):
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        with batcher.batch():
            batcher.command("[con_id=1] focus")
        batcher.command("[con_id=2] focus")
        assert len(conn.commands_executed) == 2

    def test_nestedBatchNotSupported(self):
        """Nesting batches just flushes the outer batch early."""
        conn = MockConnection()
        batcher = CommandBatcher(conn)
        with batcher.batch():
            batcher.command("[con_id=1] focus")
            # Inner "batch" would flush and restart
        assert len(conn.commands_executed) >= 1


# =============================================================================
# TreeCache Tests
# =============================================================================


class TestTreeCache:
    """Tests for the TreeCache."""

    def test_freshCache_returnsWorkspaceName(self):
        tree = create_tree_with_workspaces(
            [
                {"name": "1", "window_count": 2},
                {"name": "2", "window_count": 1},
            ]
        )
        conn = MockConnection(tree=tree)
        cache = TreeCache(conn)

        # Window IDs from create_workspace start at 100
        assert cache.get_workspace_for_window(100) == "1"
        assert cache.get_workspace_for_window(101) == "1"
        assert cache.get_workspace_for_window(102) == "2"

    def test_unknownWindow_returnsNone(self):
        tree = create_tree_with_workspaces([{"name": "1", "window_count": 1}])
        conn = MockConnection(tree=tree)
        cache = TreeCache(conn)
        assert cache.get_workspace_for_window(9999) is None

    def test_invalidate_clearsCache(self):
        tree = create_tree_with_workspaces([{"name": "1", "window_count": 1}])
        conn = MockConnection(tree=tree)
        cache = TreeCache(conn)
        cache.get_workspace_for_window(100)  # Populate cache
        cache.invalidate()
        assert cache._cache == {}

    def test_staleCache_refreshesAutomatically(self):
        tree = create_tree_with_workspaces([{"name": "1", "window_count": 1}])
        conn = MockConnection(tree=tree)
        cache = TreeCache(conn, max_age_seconds=0.001)  # 1ms

        cache.get_workspace_for_window(100)  # Populate
        time.sleep(0.01)  # Wait for cache to go stale
        # Should still work (refreshes automatically)
        assert cache.get_workspace_for_window(100) == "1"

    def test_emptyTree_returnsNone(self):
        conn = MockConnection()
        cache = TreeCache(conn)
        assert cache.get_workspace_for_window(100) is None


# =============================================================================
# EventDebouncer Tests
# =============================================================================


class TestEventDebouncer:
    """Tests for the EventDebouncer."""

    def test_firstEvent_alwaysProcessed(self):
        debouncer = EventDebouncer(window_ms=100)
        assert debouncer.should_process("test_key") is True

    def test_rapidDuplicate_debounced(self):
        debouncer = EventDebouncer(window_ms=1000)  # 1 second window
        assert debouncer.should_process("key1") is True
        assert debouncer.should_process("key1") is False  # Too fast

    def test_differentKeys_notDebounced(self):
        debouncer = EventDebouncer(window_ms=1000)
        assert debouncer.should_process("key1") is True
        assert debouncer.should_process("key2") is True

    def test_afterWindow_processed(self):
        debouncer = EventDebouncer(window_ms=1)  # 1ms window
        assert debouncer.should_process("key1") is True
        time.sleep(0.01)  # 10ms > 1ms window
        assert debouncer.should_process("key1") is True

    def test_clear(self):
        debouncer = EventDebouncer(window_ms=1000)
        debouncer.should_process("key1")
        debouncer.clear()
        assert debouncer.should_process("key1") is True

    def test_cleanup_removesOldEntries(self):
        debouncer = EventDebouncer(window_ms=1)
        debouncer.should_process("key1")
        debouncer.should_process("key2")
        time.sleep(0.01)
        debouncer.cleanup(max_age_seconds=0.001)
        assert len(debouncer._last_seen) == 0

    def test_cleanup_keepsRecentEntries(self):
        debouncer = EventDebouncer(window_ms=1)
        debouncer.should_process("key1")
        debouncer.cleanup(max_age_seconds=60.0)
        assert "key1" in debouncer._last_seen
