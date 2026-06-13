---
name: codegraph
description: >
  Semantic knowledge graph for AI coding agents. Pre-indexes codebases into a
  local SQLite graph (symbols, callers, callees, dependencies) so AI agents
  can answer structural questions instantly without expensive file scans.
  Trigger: When the user needs to explore code structure, find symbol
  relationships, analyze impact of changes, or understand codebase architecture.
  Also when the user says "codegraph", "knowledge graph", "semantic index",
  "code index", or "explore codebase".
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- **Explore symbol relationships**: Find where a symbol is defined, called, or referenced.
- **Impact analysis**: Before modifying a function/class, find all callers to assess breakage.
- **Codebase onboarding**: Quickly understand structure without reading every file.
- **Cross-language navigation**: Bridge language gaps (Python ↔ TypeScript, React Native ↔ native code).
- **Framework awareness**: Understand web-framework routing (Django, FastAPI, Express, Rails).
- **Find test files**: Discover which tests are affected by a change.
- **Search codebase**: Full-text search with semantic ranking.

## Critical Patterns

1. **Always init first**: Run `codegraph init -i` in the project root before querying.
2. **Index is local**: The `.codegraph/` directory is auto-created in the project root. It's local-only, no data leaves your machine.
3. **Auto-syncs**: CodeGraph uses a native file watcher. The index is usually up to date. If in doubt, run `codegraph sync`.
4. **Use for context gathering**: Before editing a file, use `codegraph explore <symbol>` to understand all relationships.
5. **Use for impact analysis**: Before refactoring, run `codegraph impact <symbol>` to see all affected code.
6. **The index is fast**: 60 files index in ~1 second. Use it liberally.

## Commands

### Initialization

```bash
# Initialize and index the project
codegraph init -i

# Re-index all files
codegraph index

# Sync changes since last index
codegraph sync

# Remove codegraph from project
codegraph uninit
```

### Querying

```bash
# Search for symbols (full-text with semantic ranking)
codegraph query <search-term>

# Explore a symbol: definition, callers, callees, source
codegraph explore <symbol-name>

# View a symbol's source and its caller/callee trail
codegraph node <symbol-name>

# Find direct callers of a symbol
codegraph callers <symbol-name>

# Find direct callees (functions called by a symbol)
codegraph callees <symbol-name>

# Impact analysis - trace all affected code
codegraph impact <symbol-name>

# Show indexed project file structure
codegraph files

# Find relevant test files for given source files
codegraph affected <file-paths>
```

### Status & Maintenance

```bash
# Show index statistics and sync status
codegraph status

# Serve as MCP server for AI agent integration
codegraph serve

# Integrate with AI agents (Claude Code, Cursor, etc.)
codegraph install

# Remove integration
codegraph uninstall

# Upgrade codegraph
codegraph upgrade

# Telemetry settings
codegraph telemetry
```

## Code Examples

### Before editing a file

```bash
# 1. Understand the symbol
codegraph explore UserService

# 2. Check who calls it
codegraph callers UserService.create_user

# 3. Find related tests
codegraph affected src/services/user_service.py
```

### Before a refactor

```bash
# Check impact radius
codegraph impact Case.save

# Find all usages
codegraph query Case

# Check test coverage
codegraph affected src/models/case.py
```

### Framework routing exploration

```bash
# Find all FastAPI routes (understands framework patterns)
codegraph explore router
codegraph query @router
```

## Resources

- **GitHub Repository**: https://github.com/colbymchenry/codegraph
- **Local project index**: The `.codegraph/` directory in the project root
- **Installation**: `npm i -g @colbymchenry/codegraph`
