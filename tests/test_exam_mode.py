import pytest
from wisprfree_core.exam_mode import ExamModeConsent

def test_disabled_by_default():
    gate = ExamModeConsent()
    assert not gate.enabled
    with pytest.raises(PermissionError):
        gate.require_consent()

def test_requires_explicit_confirmation():
    gate = ExamModeConsent()
    assert not gate.activate(user_confirmed=False)
    assert not gate.enabled
    assert gate.activate(user_confirmed=True)
    gate.require_consent()

def test_deactivation_revokes_consent():
    gate = ExamModeConsent()
    gate.activate(user_confirmed=True)
    gate.deactivate()
    with pytest.raises(PermissionError):
        gate.require_consent()
