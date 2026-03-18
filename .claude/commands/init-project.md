---
description: Analyze the codebase and auto-generate all claude-flow configuration files
argument-hint: [project description]
---

# /init-project

Automatically analyze the current codebase and generate all claude-flow configuration files. The user should NOT need to fill any placeholders manually.

## Phase 0: Detect Project State

First, determine whether this is an **existing project** or a **new (empty) project**:

- Use Glob to check for source code files (`**/*.{ts,js,py,go,rs,cs,java,jsx,tsx}`)
- Check for manifest files (package.json, go.mod, Cargo.toml, *.csproj, pyproject.toml, etc.)

**If source files found** → go to Phase 1A (Existing Project)
**If no source files found** → go to Phase 1B (New Project)

## Phase 1A: Existing Project — Codebase Analysis (NO file writing)

Scan the project to understand its structure. Use Glob, Grep, Read tools:

1. **Detect project type and tech stack**
   - Check for: package.json, go.mod, Cargo.toml, *.csproj, pyproject.toml, pom.xml, build.gradle, etc.
   - Identify primary language(s), frameworks, and build tools
   - Check for existing test frameworks and linting tools

2. **Map the architecture**
   - Identify top-level directory structure and purpose of each directory
   - Find entry points (main files, route definitions, etc.)
   - Detect patterns: layered architecture, module boundaries, communication patterns
   - Identify shared/common code vs domain-specific code

3. **Identify constraints AI would violate**
   - Check for custom wrappers (logging, HTTP client, error handling) — AI would use stdlib instead
   - Check for architectural patterns (DI, event bus, actor model) — AI would use direct imports
   - Check for performance-sensitive paths — AI would write allocating code
   - Check for enforced tech choices (specific ORM, async library, etc.)

4. **Check existing configuration**
   - Look for existing CLAUDE.md, .claude/ directory, .claudeignore
   - Look for existing linting config, test config, CI/CD setup
   - If configs already exist, ask user whether to overwrite or merge

5. **Present findings and confirm**

   Output a summary via AskUserQuestion:
   ```
   Detected:
   - Language: {detected}
   - Framework: {detected}
   - Architecture: {detected pattern}
   - Test framework: {detected}
   - Linter: {detected}

   Proposed constitution articles:
   §1: {proposed constraint}
   §2: {proposed constraint}
   ...

   Proceed with generation? (Or tell me what to adjust)
   ```

   **Must wait for user confirmation before Phase 2.**

## Phase 1B: New Project — Guided Setup (NO file writing)

Ask the user to describe the project via AskUserQuestion. Gather in 1-2 rounds:

**Round 1 (required):**
```
This looks like a new project. Tell me about it:

1. Language & framework? (e.g., TypeScript + Next.js, Python + FastAPI, Go + Gin, C# + Unity)
2. What does it do? (one sentence)
3. Any specific architecture? (e.g., monorepo, microservices, layered, ECS)
```

**Round 2 (if needed, based on Round 1 answers):**
```
A few more details:
- Test framework preference? (e.g., Jest, pytest, go test)
- Linter preference? (e.g., ESLint, Ruff, golangci-lint)
- Any hard constraints? (e.g., "must use SQLAlchemy not raw SQL", "no class components")
```

Then present a summary for confirmation, same format as Phase 1A step 5 but based on user's answers instead of code scanning.

**Must wait for user confirmation before Phase 2.**

## Phase 2: Generate Configuration Files

Generate all files based on Phase 1 analysis. Every file must contain **concrete, project-specific content** — no placeholders left.

### 2.0 New project only: Initialize project scaffold

If this is a new project (came from Phase 1B), first set up the basic project structure:

1. **Create manifest file** — `package.json` / `go.mod` / `pyproject.toml` / `*.csproj` etc., based on the user's chosen stack
2. **Create directory skeleton** — `src/`, `tests/`, etc., appropriate for the stack and architecture
3. **Create entry point** — A minimal main file so the project can run
4. **Initialize git** — `git init` if not already a git repo
5. **Install linter** — Add linter as dev dependency if the user specified one

Keep the scaffold minimal — just enough for the project to build/run. The user will add features later.

### 2.1 Generate `CLAUDE.md`

Root entry point. Content:
- Project name (from package.json/go.mod/etc. or directory name)
- Architecture overview (actual directory structure — from Phase 1A scan or Phase 1B scaffold)
- @import references to subsystem CLAUDE.md files (if multi-module)

Keep under 30 lines. No generic rules — only project-specific structure.

### 2.2 Generate `.claude/constitution.md`

- **Existing project**: 4-7 articles based on Phase 1A constraint analysis. Each article must have ✅/❌ paired code examples **using the project's actual code patterns**.
- **New project**: 2-4 articles based on user's stated constraints and the chosen stack's best practices. Use idiomatic code examples for the language/framework. Focus on constraints that AI would likely violate (e.g., "use X ORM not raw SQL", "all state through store, no local state").

Include the Governance section with enforcement protocol (copy from template).

### 2.3 Generate `.claude/rules/coding-style.md`

1-3 rules that supplement the constitution with concrete coding details.
Each rule references a constitution article (per Constitution §N).
End with a self-check checklist.

Only create rules that are NOT derivable from the constitution. If there's nothing to add, create a minimal file with just the self-check checklist.

### 2.4 Generate `.claudeignore`

Based on detected project type:
- Always include: build artifacts, dependencies, IDE files, logs
- Language-specific: node_modules/, vendor/, bin/, obj/, target/, etc.
- Project-specific: large assets, generated code, etc.

### 2.5 Configure `.claude/settings.json`

Set up Hooks based on detected linter:
- Node.js project with ESLint → configure lint-feedback.sh hook
- Python with Ruff/Flake8 → configure lint-feedback.sh hook
- Go with golangci-lint → configure lint-feedback.sh hook
- If no linter detected → configure basic hook, suggest installing one

### 2.6 Copy built-in Skills

Ensure `tdd/SKILL.md` and `verification/SKILL.md` are in place.
If the project has a specific test framework, uncomment the relevant section in tdd/SKILL.md.

### 2.7 Generate project-specific Skills (if applicable)

If Phase 1 found custom frameworks/wrappers that AI would misuse, create Skills for them:
- Custom logging wrapper → logging Skill
- Custom HTTP client → http-client Skill
- Custom state management → state Skill

Each Skill follows the `_template/SKILL.md` format with **actual code examples from the project**.

### 2.8 Copy commands and scripts

Ensure `/feature-plan-creator`, `/bug-fix` commands are in place.
Copy `scripts/lint-feedback.sh` if Hooks are configured.

## Phase 3: Verification

1. Read back each generated file and verify:
   - No `{placeholder}` text remains in any file
   - Constitution articles reference actual project patterns
   - Code examples are syntactically correct for the project's language
   - .claudeignore covers the project's build artifacts
   - settings.json hooks point to correct script paths

2. Output a summary:
   ```
   Generated:
   - CLAUDE.md (N lines)
   - .claude/constitution.md (N articles)
   - .claude/rules/coding-style.md (N rules)
   - .claudeignore
   - .claude/settings.json (hooks: lint-feedback)
   - .claude/skills/tdd/SKILL.md
   - .claude/skills/verification/SKILL.md
   - .claude/skills/{custom}/SKILL.md (if any)
   - .claude/commands/feature-plan-creator.md
   - .claude/commands/bug-fix.md

   Next steps:
   - Review the generated constitution — adjust if any article is wrong
   - Start using: just describe your task, Claude Code will follow the framework
   - For complex features: /feature-plan-creator <name>
   - For bugs: /bug-fix <description>
   ```

## Prohibited Actions

- Do not leave any `{placeholder}` in generated files
- Do not generate generic/boilerplate rules that AI already follows by default
- Do not create Skills for standard library usage (only for project-specific wrappers)
- Do not skip user confirmation in Phase 1
- Do not overwrite existing configuration without user permission
