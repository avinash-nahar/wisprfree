import pytest
from wisprfree_core.pipeline import InvalidTransition, Pipeline, PipelineState

def test_happy_path_and_reuse():
    p = Pipeline()
    assert p.start() is PipelineState.RECORDING
    assert p.finish_recording() is PipelineState.TRANSCRIBING
    assert p.complete(" hello ") is True
    assert p.state is PipelineState.COMPLETE
    assert p.start() is PipelineState.RECORDING

def test_rejects_overlapping_recording():
    p = Pipeline()
    p.start()
    with pytest.raises(InvalidTransition):
        p.start()

def test_empty_transcript_fails():
    p = Pipeline()
    p.start()
    p.finish_recording()
    assert p.complete("  ") is False
    assert p.state is PipelineState.FAILED

def test_failure_and_cancel_are_recoverable():
    p = Pipeline()
    p.start()
    p.fail()
    assert p.start() is PipelineState.RECORDING
    p.cancel()
    assert p.state is PipelineState.CANCELLED
