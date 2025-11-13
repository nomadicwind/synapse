# OpenSpec Cheatsheet

## Purpose
OpenSpec is a spec-driven development system that documents what the system SHOULD do (changes) and what it DOES do (specs). It provides a structured workflow for proposing, implementing, and archiving changes to ensure alignment between specifications and implementation.

## Directory Structure
```
openspec/
├── project.md              # Project conventions and context
├── AGENTS.md               # Instructions for AI assistants using OpenSpec
├── CHEATSHEET.md           # This file (quick reference guide)
├── specs/                  # Current truth - what IS built
│   └── [capability]/       # Single focused capability
│       └── spec.md         # Requirements and scenarios
├── changes/                # Proposals - what SHOULD change
│   ├── [change-name]/      # Active change proposals
│   │   ├── proposal.md     # Why, what, impact
│   │   ├── tasks.md        # Implementation checklist
│   │   ├── design.md       # Technical decisions (optional)
│   │   └── specs/          # Delta changes to existing specs
│   └── archive/            # Completed changes (archived)
```

## Three-Stage Workflow

### Stage 1: Creating Changes
1. **Check existing work**: Use `openspec list` and `openspec list --specs` to avoid duplication
2. **Choose change ID**: Use kebab-case, verb-led format (e.g., `add-two-factor-auth`)
3. **Scaffold files**: Create `proposal.md`, `tasks.md`, optional `design.md`, and spec deltas
4. **Write deltas**: Use `## ADDED|MODIFIED|REMOVED Requirements` with at least one `#### Scenario:` per requirement
5. **Validate**: Run `openspec validate [change-id] --strict` before sharing

### Stage 2: Implementing Changes
1. Read `proposal.md` to understand what's being built
2. Read `design.md` (if exists) to review technical decisions
3. Read `tasks.md` to get implementation checklist
4. Implement tasks sequentially
5. Confirm completion of all tasks before updating statuses
6. Update checklist: Set every task to `- [x]` when finished
7. Do not start implementation until proposal is approved

### Stage 3: Archiving Changes
After deployment:
1. Move `changes/[name]/` → `changes/archive/YYYY-MM-DD-[name]/`
2. Update `specs/` if capabilities changed
3. Use `openspec archive <change-id> --skip-specs --yes` for tooling-only changes
4. Run `openspec validate --strict` to confirm archived change passes checks

## Essential CLI Commands

```bash
# List active changes and specifications
openspec list                  # List active changes
openspec list --specs          # List specifications

# Display details
openspec show [item]           # Display change or spec
openspec show [spec] --json -r 1  # Show specific requirement

# Validation
openspec validate [item]       # Validate changes or specs
openspec validate [change] --strict  # Comprehensive validation

# Archive completed changes
openspec archive <change-id> [--yes|-y]  # Archive after deployment

# Search (use ripgrep for full-text)
rg -n "Requirement:|Scenario:" openspec/specs  # Search specs
```

## Spec File Format

### Requirements
- Use `### Requirement: [Name]` for requirement headers
- Use SHALL/MUST for normative requirements
- Every requirement MUST have at least one scenario

### Scenarios (Critical Format)
```markdown
#### Scenario: [Description]
- **WHEN** [condition]
- **THEN** [expected result]
```

### Delta Operations
- `## ADDED Requirements` - New capabilities
- `## MODIFIED Requirements` - Changed behavior (include full updated requirement)
- `## REMOVED Requirements` - Deprecated features
- `## RENAMED Requirements` - Name changes

## Best Practices

### Change ID Naming
- Use kebab-case: `add-two-factor-auth`
- Prefer verb-led prefixes: `add-`, `update-`, `remove-`, `refactor-`
- Ensure uniqueness

### Capability Naming
- Use verb-noun: `user-auth`, `payment-capture`
- Single purpose per capability
- Split if description needs "AND"

### When to Create a Proposal
Create proposal for:
- New features or functionality
- Breaking changes (API, schema)
- Architecture or pattern changes
- Performance optimizations that change behavior
- Security pattern updates

Skip proposal for:
- Bug fixes (restore intended behavior)
- Typos, formatting, comments
- Dependency updates (non-breaking)
- Configuration changes
- Tests for existing behavior

## Common Pitfalls & Troubleshooting

### Common Errors
- **"Change must have at least one delta"**: Check `changes/[name]/specs/` exists with .md files
- **"Requirement must have at least one scenario"**: Check scenarios use `#### Scenario:` format (4 hashtags)
- **Silent scenario parsing failures**: Use exact format `#### Scenario: Name`

### Validation Tips
```bash
# Always use strict mode
openspec validate [change] --strict

# Debug delta parsing
openspec show [change] --json | jq '.deltas'
```

## Quick Reference

### File Purposes
- `project.md` - Project context and conventions
- `AGENTS.md` - Instructions for AI assistants
- `proposal.md` - Why and what (business justification)
- `tasks.md` - Implementation steps (technical checklist)
- `design.md` - Technical decisions (when needed)
- `spec.md` - Requirements and behavior (specification)

### Stage Indicators
- `changes/` - Proposed, not yet built
- `specs/` - Built and deployed
- `archive/` - Completed changes

Remember: Specs are truth. Changes are proposals. Keep them in sync.
