---
inclusion: always
---

# Superpowers Skills

You have access to a library of skills located at `~/.kiro/skills/superpowers/`. Each skill is a directory containing a `SKILL.md` file with detailed instructions. When a skill applies, read its `SKILL.md` and follow it exactly.

## How to Use Skills

Before responding to any request, check whether a skill applies. If there is even a 1% chance a skill is relevant, read it and follow it. Skills override default behavior but user instructions always take precedence.

To use a skill: read the file at `~/.kiro/skills/superpowers/<skill-name>/SKILL.md` and follow its instructions.

## Available Skills

| Skill | When to use |
|-------|-------------|
| `brainstorming` | You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. |
| `writing-plans` | Use when you have a spec or requirements for a multi-step task, before touching code. |
| `executing-plans` | Use when you have a written implementation plan to execute in a separate session with review checkpoints. |
| `subagent-driven-development` | Use when executing implementation plans with independent tasks in the current session. |
| `test-driven-development` | Use when implementing any feature or bugfix, before writing implementation code. |
| `systematic-debugging` | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. |
| `verification-before-completion` | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs. |
| `requesting-code-review` | Use when completing tasks, implementing major features, or before merging to verify work meets requirements. |
| `receiving-code-review` | Use when receiving code review feedback, before implementing suggestions. |
| `brainstorming` | Use before any creative work - features, components, new functionality. |
| `using-git-worktrees` | Use when starting feature work that needs isolation from current workspace. |
| `finishing-a-development-branch` | Use when implementation is complete and you need to decide how to integrate the work. |
| `dispatching-parallel-agents` | Use when facing 2+ independent tasks that can be worked on without shared state. |
| `writing-skills` | Use when creating or editing skills. |

## Skill Priority

1. Process skills first: `brainstorming`, `systematic-debugging` — these determine HOW to approach the task
2. Implementation skills second — these guide execution

## Key Rules

- "Let's build X" → invoke `brainstorming` first, always
- "Fix this bug" → invoke `systematic-debugging` first
- About to say "done" or "fixed" → invoke `verification-before-completion` first
- Implementing anything → invoke `test-driven-development` first

Skills are mandatory workflows, not suggestions. If a skill applies, you must use it.
