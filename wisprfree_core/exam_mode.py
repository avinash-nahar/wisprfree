"""Session consent gate for optional screen capture. This module does not capture screens."""
class ExamModeConsent:
    def __init__(self):
        self._enabled = False
        self._consent_granted = False
    @property
    def enabled(self):
        return self._enabled and self._consent_granted
    def activate(self, *, user_confirmed):
        if user_confirmed is not True:
            self.deactivate()
            return False
        self._consent_granted = True
        self._enabled = True
        return True
    def require_consent(self):
        if not self.enabled:
            raise PermissionError("Exam Mode requires explicit user consent and activation")
    def deactivate(self):
        self._enabled = False
        self._consent_granted = False
