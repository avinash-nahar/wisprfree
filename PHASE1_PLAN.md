# WisprFree Phase 1: core hardening

Target: Apple Silicon macOS first; downloadable DMG through GitHub Releases. This branch adds testable foundations and packaging scaffolding. The existing app is not yet wired to these modules, so this is not a completed security fix or release build.

## Acceptance criteria
- [ ] No API key embedded in source, app bundle, logs, or release assets.
- [ ] Packaged app uses macOS Keychain; environment variables are development-only.
- [ ] Recording/transcription has explicit states, rejects overlap, and cleans up audio resources on every exit path.
- [ ] Empty transcripts are never pasted.
- [ ] Exam Mode is separate and opt-in; each session requires explicit consent, visible active indicator, and stop control. Every capture call site enforces the consent gate.
- [ ] Exact Gemini model ID is verified against the current API before release.
- [ ] HUD assets and JavaScript dependencies are bundled locally, not fetched from a CDN at launch.
- [ ] Tests pass and the arm64 app launches on a clean Apple Silicon Mac.
- [ ] Signed/notarized DMG is published with checksums and release notes.

## Files introduced
- wisprfree_core/pipeline.py: state machine primitive.
- wisprfree_core/exam_mode.py: session consent gate; must be wired into all capture paths.
- wisprfree_core/secrets.py: Keychain adapter; keyring must be a packaged dependency.
- tests/: unit tests for independent primitives.
- packaging/wisprfree.spec: PyInstaller bundle recipe; hidden imports/resources need validation on macOS.
- scripts/build_dmg.sh: local arm64 DMG build.
- .github/workflows/release-macos.yml: test/build artifact workflow. Signing and notarization are not configured.
- SECURITY.md: reporting and data-handling guidance.

## Integration sequence
1. Wire the pipeline to existing recording callbacks and guarantee stream cleanup with try/finally.
2. Replace production .env API-key loading with Keychain-backed Settings/onboarding; never package .env.
3. Route every screen capture through ExamModeConsent.require_consent(). Add explicit activation confirmation, persistent active UI, and stop control.
4. Verify model IDs via a real API smoke test and choose a supported model. Add timeouts, bounded retries, and user-readable errors.
5. Vendor the Lottie runtime and resolve assets from bundle resources.
6. Test microphone denial, disconnected device, empty transcript, invalid key, network timeout, cancel/quit during recording, and paste failures on macOS.
7. Add Developer ID signing, hardened runtime, notarization, stapling, and release publishing only after certificates/secrets are configured.

## Local validation
Run python -m pip install -r requirements-dev.txt, pytest -q, ruff check wisprfree_core tests, and python -m compileall wisprfree_core tests. Build on an Apple Silicon Mac. CI is not a substitute for testing macOS privacy prompts and paste behavior on a real desktop.
