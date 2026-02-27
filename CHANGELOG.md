# Changelog

All notable changes to this project will be documented in this file.

## [2.3.3] - 2026-02-27

### Fixed
- Thread context: all three orchestration strategies now inject conversation history into prompts
- Session FK constraint: ConversationMessage now saved correctly
- Fact extractor: fixed thread_id → session_id kwarg
