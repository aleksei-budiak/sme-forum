import api


def test_get_health():
    result = api.get_health()
    assert result == {"status": "pass"}
