import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AnneDroid"))

from message import Message


class TestMessage:
    def test_construct(self):
        msg = Message("Alice", "hello world", "general", "2024_01_15-10:30:00")
        assert msg.author == "Alice"
        assert msg.message == "hello world"
        assert msg.channel == "general"
        assert msg.date == "2024_01_15-10:30:00"

    def test_format_constant(self):
        assert Message.FORMAT == "%Y_%m_%d-%H:%M:%S"

    def test_multiple_messages_have_separate_state(self):
        a = Message("A", "msg1", "ch1", "t1")
        b = Message("B", "msg2", "ch2", "t2")
        assert a.author != b.author
        assert a.message != b.message
        assert a.channel != b.channel
        assert a.date != b.date
