import pytest

from telliot_feeds.utils.input_timeout import input_timeout, TimeoutOccurred


def test_input_timeout() -> None:
    """Test input_timeout() function."""
    # with pytest.raises(TimeoutOccurred):
    #     input_timeout(timeout=0.1)
