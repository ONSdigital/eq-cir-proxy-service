"""Sample test to prevent checks failing - to be deleted when further tests are implemented."""

from eq_cir_proxy_service.main import add_numbers


def test_add_numbers():
    """Tests that two numbers are added together correctly."""
    expected_result = 5
    assert add_numbers(2, 3) == expected_result
