from student_agent.config import Settings


def test_settings_do_not_require_secrets_for_construction():
    settings = Settings()
    assert not settings.canvas_configured
    assert not settings.llm_configured
