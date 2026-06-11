import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AnneDroid"))

from statistics import Statistics
from message import Message


class MockStorage:
    def __init__(self, messages=None):
        self.messages = messages or []

    def select_messages_by_channel(self, channel):
        return [m for m in self.messages if m.channel == channel]


@pytest.fixture
def stats():
    return Statistics(MockStorage())


@pytest.fixture
def populated_stats():
    messages = [
        Message("Alice", "hello world", "general", "t1"),
        Message("Bob", "hi", "general", "t2"),
        Message("Alice", "another message here", "general", "t3"),
    ]
    return Statistics(MockStorage(messages))


class TestStatistics:
    def test_message_length_stats_empty(self, stats):
        result = stats.message_length_stats("empty_channel")
        assert isinstance(result, str)
        # Should have just a newline
        assert result == "\n"

    def test_message_length_stats_with_messages(self, populated_stats):
        result = populated_stats.message_length_stats("general")
        # Alice has 2 messages: "hello world" (11) + "another message here" (19) = 30 chars
        # Bob has 1 message: "hi" (2) chars
        assert "Alice" in result
        assert "Bob" in result

    def test_random_quote_returns_expected_format(self, populated_stats):
        result = populated_stats.random_quote("general")
        assert result.startswith("```")
        assert result.endswith("```")
        # Should contain author and message separated by ": "
        assert ": " in result

    def test_random_quote_different_channels(self):
        msgs = [
            Message("Alice", "general msg", "general", "t1"),
            Message("Bob", "random msg", "random", "t2"),
        ]
        s = Statistics(MockStorage(msgs))
        result = s.random_quote("random")
        assert "random msg" in result
        assert "Bob" in result

    def test_message_length_stats_sorted_by_length(self, populated_stats):
        result = populated_stats.message_length_stats("general")
        lines = [l for l in result.split("\n") if l.strip()]

        # Alice should appear before Bob since she has more total chars
        alice_pos = next(i for i, l in enumerate(lines) if "Alice" in l)
        bob_pos = next(i for i, l in enumerate(lines) if "Bob" in l)
        assert alice_pos < bob_pos
