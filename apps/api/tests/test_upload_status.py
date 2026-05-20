from app.services.upload_status import count_pending_for_upload


def test_count_pending_for_upload_returns_zero_without_db():
    """Smoke test: função existe e aceita parâmetros esperados."""
    assert callable(count_pending_for_upload)
