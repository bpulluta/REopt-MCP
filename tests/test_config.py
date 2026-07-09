from reopt_mcp import config


def test_nlr_api_key_is_string() -> None:
    assert isinstance(config.NLR_API_KEY, str)


def test_reopt_api_base_url_points_to_nlr() -> None:
    assert "developer.nlr.gov" in config.REOPT_API_BASE_URL


def test_reopt_api_base_url_uses_stable_endpoint() -> None:
    assert config.REOPT_API_BASE_URL.endswith("/api/reopt/stable")
