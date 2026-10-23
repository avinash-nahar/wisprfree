"""Thread-safe recording/transcription state machine, independent of macOS APIs."""
from enum import Enum
from threading import RLock

class PipelineState(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class InvalidTransition(RuntimeError):
    """Raised when an operation conflicts with the current pipeline state."""

class Pipeline:
    _allowed = {
        PipelineState.IDLE: {PipelineState.RECORDING},
        PipelineState.RECORDING: {PipelineState.TRANSCRIBING, PipelineState.FAILED, PipelineState.CANCELLED},
        PipelineState.TRANSCRIBING: {PipelineState.COMPLETE, PipelineState.FAILED, PipelineState.CANCELLED},
        PipelineState.COMPLETE: {PipelineState.RECORDING, PipelineState.IDLE},
        PipelineState.FAILED: {PipelineState.RECORDING, PipelineState.IDLE},
        PipelineState.CANCELLED: {PipelineState.RECORDING, PipelineState.IDLE},
    }
    def __init__(self):
        self._state = PipelineState.IDLE
        self._lock = RLock()
    @property
    def state(self):
        with self._lock:
            return self._state
    def transition(self, target):
        target = PipelineState(target)
        with self._lock:
            if target not in self._allowed[self._state]:
                raise InvalidTransition(f"Cannot transition from {self._state.value} to {target.value}")
            self._state = target
            return target
    def start(self):
        with self._lock:
            if self._state in {PipelineState.COMPLETE, PipelineState.FAILED, PipelineState.CANCELLED}:
                self._state = PipelineState.IDLE
            if self._state is not PipelineState.IDLE:
                raise InvalidTransition("Recording or transcription is already in progress")
            self._state = PipelineState.RECORDING
            return self._state
    def finish_recording(self):
        return self.transition(PipelineState.TRANSCRIBING)
    def complete(self, transcript):
        if not isinstance(transcript, str) or not transcript.strip():
            self.transition(PipelineState.FAILED)
            return False
        self.transition(PipelineState.COMPLETE)
        return True
    def fail(self):
        with self._lock:
            if self._state in {PipelineState.RECORDING, PipelineState.TRANSCRIBING}:
                self._state = PipelineState.FAILED
            return self._state
    def cancel(self):
        with self._lock:
            if self._state in {PipelineState.RECORDING, PipelineState.TRANSCRIBING}:
                self._state = PipelineState.CANCELLED
            return self._state
