---
inclusion: auto
description: Project-specific patterns, preferences, and lessons learned over time (user-editable)
---

# Lessons Learned

This file captures project-specific patterns, coding preferences, common pitfalls, and architectural decisions that emerge during development. It serves as a workaround for continuous learning by allowing you to document patterns manually.

**How to use this file:**
1. The `extract-patterns` hook will suggest patterns after agent sessions
2. Review suggestions and add genuinely useful patterns below
3. Edit this file directly to capture team conventions
4. Keep it focused on project-specific insights, not general best practices

---

## Project-Specific Patterns

*Document patterns unique to this project that the team should follow.*

### Example: API Error Handling
```typescript
// Always use our custom ApiError class for consistent error responses
throw new ApiError(404, 'Resource not found', { resourceId });
```

---

## Code Style Preferences

*Document team preferences that go beyond standard linting rules.*

### Example: Import Organization
```typescript
// Group imports: external, internal, types
import { useState } from 'react';
import { Button } from '@/components/ui';
import type { User } from '@/types';
```

---

## Kiro Global Config (Windows)

### `fsWrite` cannot write to `~/.kiro` � use shell commands instead
On Windows, Kiro's `fsWrite` tool resolves `~` to a sandboxed path, not `%USERPROFILE%`. To write files into the global `~/.kiro/` directory (steering, agents, hooks), use `executePwsh` with `$env:USERPROFILE` or `Copy-Item`. Only use `fsWrite` for workspace-relative paths.

### Use Windows junctions (not symlinks) to link skill libraries globally
`cmd /c mklink /J "$env:USERPROFILE\.kiro\skills\<name>" "<source-path>"` creates a directory junction that Kiro resolves correctly. Regular `New-Item -ItemType SymbolicLink` requires elevated privileges on Windows. Junctions work without elevation and are the right tool for linking external skill repos into `~/.kiro/skills/`.

### Third-party skill/agent repos belong in `~/.kiro/<repo-name>`, linked into the right dirs
Clone external repos (superpowers, everything-claude-code, etc.) into `~/.kiro/<repo-name>/`, then junction their `skills/` into `~/.kiro/skills/<name>` and copy their `agents/*.md` into `~/.kiro/agents/`. This keeps the source updatable via `git pull` while making assets globally available to Kiro.

---
## Kiro Hooks

### `install.sh` is additive-only — it won't update existing installations
The installer skips any file that already exists in the target (`if [ ! -f ... ]`). Running it against a folder that already has `.kiro/` will not overwrite or update hooks, agents, or steering files. To push updates to an existing project, manually copy the changed files or remove the target files first before re-running the installer.

### README.md mirrors hook configurations — keep them in sync
The hooks table and Example 5 in README.md document the action type (`runCommand` vs `askAgent`) and behavior of each hook. When changing a hook's `then.type` or behavior, update both the hook file and the corresponding README entries to avoid misleading documentation.

### Prefer `askAgent` over `runCommand` for file-event hooks
`runCommand` hooks on `fileEdited` or `fileCreated` events spawn a new terminal session every time they fire, creating friction. Use `askAgent` instead so the agent handles the task inline. Reserve `runCommand` for `userTriggered` hooks where a manual, isolated terminal run is intentional (e.g., `quality-gate`).

---

## Common Pitfalls

*Document mistakes that have been made and how to avoid them.*

### Example: Database Transactions
- Always wrap multiple database operations in a transaction
- Remember to handle rollback on errors
- Don't forget to close connections in finally blocks

---

## Architecture Decisions

*Document key architectural decisions and their rationale.*

### Example: State Management
- **Decision**: Use Zustand for global state, React Context for component trees
- **Rationale**: Zustand provides better performance and simpler API than Redux
- **Trade-offs**: Less ecosystem tooling than Redux, but sufficient for our needs

---

## Property-Based Testing with Hypothesis

### Use timezone-aware datetimes in Hypothesis strategies to avoid serialization issues
When generating datetime objects for property tests, always use `timezone.utc` or another explicit timezone. Naive datetimes can cause comparison failures after ISO serialization round-trips because `datetime.fromisoformat()` preserves timezone info. Pattern:
```python
@st.composite
def datetime_strategy(draw):
    # Generate with explicit timezone
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
```

### Limit string sizes in Hypothesis strategies to keep test execution fast
Unbounded text generation can create multi-MB strings that slow property tests dramatically. Use `max_size` constraints appropriate to real-world data:
```python
title = draw(st.text(min_size=1, max_size=200))  # Not st.text() unbounded
text_content = draw(st.text(min_size=0, max_size=5000))  # Reasonable article length
```

### Test both property invariants AND edge cases in separate test classes
Property tests validate universal invariants (round-trip preservation, idempotency), while edge case tests validate specific scenarios (empty fields, special characters). Separate them into distinct test classes for clarity:
```python
class TestSerializationProperties:  # Universal properties with @given
    @given(content_item_strategy())
    def test_round_trip_preserves_fields(self, item): ...

class TestSerializationEdgeCases:  # Specific examples without @given
    def test_empty_content_item(self): ...
    def test_special_characters(self): ...
```

---

## Notes

- Keep entries concise and actionable
- Remove patterns that are no longer relevant
- Update patterns as the project evolves
- Focus on what's unique to this project

### Use context7 MCP for live package version lookups before any install
Before installing or recommending any package version, use context7 MCP:
resolve-library-id to find the package, then get-library-docs to get current
version, peer requirements, and compatibility info. This eliminates version
guessing and prevents peer dependency conflicts entirely. The dependency-resolver
agent and dependency-management skill both enforce this workflow.

### Kiro preToolUse hooks fire on ALL shell commands - scope them carefully
The ECC git-push-review hook used toolTypes: [shell] with no command filter,
causing it to intercept every single shell command. This creates constant friction.
Either scope hooks narrowly, or write the askAgent prompt to self-dismiss on
non-matching commands (e.g. 'if not git push, respond PROCEED'). Always test
hooks after installing from third-party repos.

### Write global Kiro files via temp file + Copy-Item, not fsWrite to ~/.kiro paths
fsWrite resolves ~ to a sandboxed workspace path on Windows, not USERPROFILE.
Reliable pattern: write to a workspace temp file with fsWrite, then Copy-Item it
to the real destination via executePwsh, then Remove-Item the temp file.
This avoids ENOENT errors on all global config writes.

### Never point filesystem MCP at home root - scope to a specific folder
Configuring @modelcontextprotocol/server-filesystem with C:\Users\<name> exposes
the entire home directory including .ssh, .aws, credentials, and other sensitive
files. Always scope to a specific projects folder (e.g. C:\Users\karan\projects).
Keep disabled:true by default and only enable per-project when needed.

### Use DESIGN.md as a steering file to keep AI-generated code on-brand
Google Stitch can export your design system as DESIGN.md - an agent-friendly
markdown file containing colors, typography, spacing, and component rules.
Drop it in .kiro/steering/ and Kiro will automatically apply your design system
when generating UI code, eliminating pixel-drift between designs and implementation.
Free workflow: Stitch (free) -> export DESIGN.md -> .kiro/steering/DESIGN.md -> Kiro reads it.

### Antigravity uses project-level .agent/ not a global config dir
Unlike Kiro (~/.kiro/) and Claude Code (~/.claude/), Antigravity config lives in
.agent/ at the project root - not in a global home directory. ECC maps:
rules/ -> .agent/rules/ (flattened), commands/ -> .agent/workflows/, agents/ -> .agent/skills/
Run the ECC installer per-project: .\install.ps1 --target antigravity typescript
Do not try to create a global ~/.agent/ - it won't be picked up.

### Antigravity MCPs go in settings.json, global skills go in ~/.agent/
Antigravity reads MCP servers from %APPDATA%\Antigravity\User\settings.json
under the key mcp.servers (same JSON shape as VS Code). Global rules/skills/workflows
can be placed in ~/.agent/rules/, ~/.agent/skills/, ~/.agent/workflows/ and will
apply across all projects without per-project install.

### Antigravity real config locations (not .agent/ or settings.json)
Antigravity uses ~/.gemini/ as its config root:
- ~/.gemini/GEMINI.md: global rules loaded every session (visible in Rules tab)
- ~/.gemini/antigravity/mcp_config.json: MCP servers as {mcpServers:{...}}
- Workflows: UI only, added via + Global button in the Workflows panel
Previous assumptions about .agent/ and mcp.servers in settings.json were wrong.

### Antigravity definitive config locations (from official docs)
- ~/.gemini/GEMINI.md: global rules, max 12000 chars, all workspaces
- ~/.gemini/antigravity/skills/<name>/SKILL.md: global skills, auto-discovered
- ~/.gemini/antigravity/mcp_config.json: MCPs as {mcpServers:{...}}
- Workspace rules: .agents/rules/ (not .agent/rules/ - that is deprecated)
- Workspace skills: .agents/skills/ (not .agent/skills/ - that is deprecated)
- Workflows: UI only via + Global, no file path for global workflows
- Skills use progressive disclosure: agent sees description first, reads full SKILL.md only if relevant
