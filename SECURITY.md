# Security Policy

## Reporting
Do not include API keys, audio, screenshots, transcripts, or other private data in public issues. Use GitHub private vulnerability reporting where enabled.

## Secret and data handling
- Never commit .env files, API keys, signing certificates, notarization credentials, recordings, screenshots, or transcript logs.
- Packaged builds should use macOS Keychain for user-provided API keys.
- CI signing/notarization secrets must be protected GitHub Actions secrets and never echoed to logs.
- Logs should not contain audio, screenshots, transcripts, or credentials by default.

## Optional Exam Mode
Screen capture must be disabled by default. Exam Mode requires explicit user activation and consent explaining screen capture and cloud processing. Show a persistent visible indicator, provide an obvious stop control, and revoke session consent when deactivated or the app exits. Every screen-capture call site must enforce the consent gate; no hidden background hotkey may bypass it.
