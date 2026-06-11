import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "AnneDroid"))

from errors import CommandError, StorageError


class TestCommandError:
    def test_is_exception(self):
        assert issubclass(CommandError, Exception)

    def test_can_be_raised_with_message(self):
        with pytest.raises(CommandError, match="invalid command"):
            raise CommandError("invalid command")

    def test_can_be_raised_without_message(self):
        with pytest.raises(CommandError):
            raise CommandError()


class TestStorageError:
    def test_is_exception(self):
        assert issubclass(StorageError, Exception)

    def test_can_be_raised_with_message(self):
        with pytest.raises(StorageError, match="storage failed"):
            raise StorageError("storage failed")

    def test_can_be_raised_without_message(self):
        with pytest.raises(StorageError):
            raise StorageError()
