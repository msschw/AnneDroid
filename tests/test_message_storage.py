import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AnneDroid"))

from message import Message
from message_storage import MessageStorage
from errors import StorageError


@pytest.fixture
def db():
    storage = MessageStorage(":memory:")
    yield storage
    storage.connection.close()


class TestMessageStorage:
    def test_create_db_in_memory(self):
        storage = MessageStorage(":memory:")
        assert storage.connection is not None
        storage.connection.close()

    def test_insert_message(self, db):
        msg = Message("Alice", "hello", "general", "2024_01_15-10:30:00")
        msg_id = db.insert_message(msg)
        assert msg_id is not None
        assert isinstance(msg_id, int)

    def test_insert_and_retrieve(self, db):
        msg = Message("Bob", "test message", "random", "2024_01_15-10:31:00")
        db.insert_message(msg)

        results = list(db.select_messages_by_channel("random"))
        assert len(results) == 1
        assert results[0].author == "Bob"
        assert results[0].message == "test message"
        assert results[0].channel == "random"

    def test_select_messages_by_author(self, db):
        db.insert_message(Message("Alice", "msg1", "ch1", "t1"))
        db.insert_message(Message("Alice", "msg2", "ch2", "t2"))
        db.insert_message(Message("Bob", "msg3", "ch1", "t3"))

        alice_msgs = list(db.select_messages_by_author("Alice"))
        assert len(alice_msgs) == 2
        assert all(m.author == "Alice" for m in alice_msgs)

    def test_select_messages_by_channel(self, db):
        db.insert_message(Message("A", "m1", "general", "t1"))
        db.insert_message(Message("B", "m2", "general", "t2"))
        db.insert_message(Message("C", "m3", "other", "t3"))

        general_msgs = list(db.select_messages_by_channel("general"))
        assert len(general_msgs) == 2

    def test_select_messages_returns_all(self, db):
        db.insert_message(Message("A", "m1", "ch", "t1"))
        db.insert_message(Message("B", "m2", "ch", "t2"))

        all_msgs = list(db.select_messages())
        assert len(all_msgs) == 2

    def test_insert_non_message_raises(self, db):
        with pytest.raises(StorageError):
            db.insert_message("not a message")

    def test_multiple_inserts_and_retrieval(self, db):
        messages = [
            Message("Alice", "hello", "general", "t1"),
            Message("Bob", "world", "general", "t2"),
            Message("Alice", "another", "random", "t3"),
        ]
        for m in messages:
            db.insert_message(m)

        assert len(list(db.select_messages())) == 3
        assert len(list(db.select_messages_by_channel("general"))) == 2
        assert len(list(db.select_messages_by_channel("random"))) == 1
        assert len(list(db.select_messages_by_author("Alice"))) == 2
