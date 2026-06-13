# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| Explore codebase, find symbol relationships, impact analysis, code index | codegraph | skills/codegraph/SKILL.md |
| When creating PRs, writing PR descriptions, using `gh` CLI | github-pr | skills/github-pr/SKILL.md |
| When creating Jira epics with multiple sub-tasks | jira-epic | skills/jira-epic/SKILL.md |
| When creating Jira tasks, tickets, issues | jira-task | skills/jira-task/SKILL.md |
| When writing Python tests, using pytest, fixtures, mocking | pytest | skills/pytest/SKILL.md |
| When working with React components, hooks, JSX | react-19 | skills/react-19/SKILL.md |
| When creating new AI agent skills, documenting patterns for AI | skill-creator | skills/skill-creator/SKILL.md |
| When writing CSS, styling components with Tailwind | tailwind-4 | skills/tailwind-4/SKILL.md |
| When writing TypeScript, defining types, interfaces | typescript | skills/typescript/SKILL.md |
| When managing state with Zustand stores | zustand-5 | skills/zustand-5/SKILL.md |

## Compact Rules

### codegraph
- Before editing any file, run `codegraph explore <symbol>` to understand all relationships, callers, and callees
- Before refactoring, run `codegraph impact <symbol>` to assess breakage radius across all callers
- Use `codegraph query <term>` for full-text search with semantic ranking across the entire codebase
- Use `codegraph affected <file>` to find which test files are relevant to a change
- Index auto-syncs via file watcher — if in doubt, run `codegraph sync`

### github-pr
- PR title must follow Conventional Commit format: `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- PR description must include: Summary (1-3 bullets), Changes list, Testing checklist, Closes #issue

### jira-epic
- Epic must contain: Goal, Scope, Out of Scope, Technical Design links, Child Jira Tasks
- Use checklists for technical design decisions before implementation
- Each child task gets its own sub-task with clear scope

### jira-task
- For work spanning multiple components (API, UI, SDK), create separate tasks per component
- Bug structure: use sibling tasks per component with dependency relationships
- Feature structure: parent-child hierarchy (parent for stakeholders, children for technical details)

### pytest
- Use fixtures with `conftest.py` for shared state
- Use `@pytest.mark.parametrize` for testing multiple input/output scenarios
- Use `unittest.mock` (patch, MagicMock) for mocking external dependencies
- Use `@pytest.mark.asyncio` for async test support
- Use custom markers in `pyproject.toml` for test categorization (`slow`, `integration`)

### react-19
- No manual `useMemo`/`useCallback` — React Compiler handles memoization automatically
- Named imports required: `import { useState } from "react"`, NOT `import React from "react"`
- Server Components by default, add `"use client"` only for hooks/event handlers/browser APIs
- Use `use()` hook for reading promises and conditional context access
- `ref` is a regular prop — no `forwardRef` needed
- Actions: use `useActionState` for form mutations

### skill-creator
- Create when patterns are repeated and AI needs guidance
- Structure: `skills/{name}/SKILL.md` with YAML frontmatter
- Frontmatter: name, description (with Trigger), license Apache-2.0, metadata (author, version)
- Include: When to Use, Critical Patterns, Code Examples, Anti-Patterns, Commands
- Register in AGENTS.md after creation

### tailwind-4
- Static styling → Tailwind classes
- Dynamic values → `style` prop (e.g., `style={{ width: \`${x}%\` }}`)
- Conditional styles → `cn()` utility (e.g., `cn("base", condition && "variant")`)
- No `var()` or hex colors in `className` — use semantic Tailwind classes

### typescript
- Define objects with `as const`, infer union types from them (single source of truth)
- Interfaces must be flat (1 level depth) — nested objects get their own interface
- `any` is forbidden — use `unknown` for unknown types, generics for flexibility
- Use `import type` for type-only imports
- Use type guards: `function isUser(value: unknown): value is User`

### zustand-5
- Use `useShallow` for selector comparison to prevent unnecessary re-renders
- Use `persist` middleware for localStorage persistence
- Use `immer` middleware for direct state mutation in actions
- Organize complex stores with the Slices pattern
- Access state outside React via `getState()` and `subscribe()`

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| Plan de implementación | plan.txt | Plan maestro con fases, stack y arquitectura |
| Estado de implementación | STATUS.md | Tablero de progreso con lo implementado vs pendiente |
| Configuración de entorno | backend/.env.example | Variables de entorno documentadas |
