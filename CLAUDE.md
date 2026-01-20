# CLAUDE.md - AI Assistant Guide for Clauding Repository

> **Repository Status:** This is a new repository. This document establishes conventions and guidelines for development.

## Table of Contents
1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Development Workflow](#development-workflow)
4. [Key Conventions](#key-conventions)
5. [AI Assistant Guidelines](#ai-assistant-guidelines)
6. [Git Workflow](#git-workflow)
7. [Common Tasks](#common-tasks)

---

## Repository Overview

**Repository Name:** Clauding
**Owner:** mattlichti
**Purpose:** [To be determined as project develops]

### Current State
- **Status:** Empty repository, ready for initial setup
- **Branch Strategy:** Claude session branches follow pattern: `claude/claude-md-[SESSION-ID]`
- **Remote:** Local proxy setup at `http://127.0.0.1:29213/git/mattlichti/Clauding`

---

## Codebase Structure

### Recommended Directory Structure

As this project develops, consider organizing code as follows:

```
Clauding/
├── .github/              # GitHub Actions, issue templates, PR templates
├── src/                  # Source code
│   ├── components/       # Reusable components
│   ├── services/         # Business logic and services
│   ├── utils/            # Utility functions
│   └── types/            # Type definitions (if TypeScript)
├── tests/                # Test files
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── docs/                 # Documentation
├── scripts/              # Build and utility scripts
├── config/               # Configuration files
├── public/               # Static assets (if web project)
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
├── CLAUDE.md            # This file - AI assistant guide
├── CONTRIBUTING.md      # Contribution guidelines
└── package.json         # Dependencies (if Node.js project)
```

### Key Files to Create

When initializing this project, consider creating:

- **README.md** - Project description, setup instructions, usage
- **.gitignore** - Ignore patterns for dependencies, build artifacts, secrets
- **LICENSE** - Project license
- **CONTRIBUTING.md** - Guidelines for contributors
- **package.json** or equivalent - Dependency management
- **Configuration files** - ESLint, Prettier, TypeScript, etc.

---

## Development Workflow

### Initial Setup

When starting development:

1. **Define the project type and purpose**
   - Web application? CLI tool? Library? API?
   - Technology stack (JavaScript/TypeScript, Python, Go, etc.)

2. **Initialize project structure**
   - Create directory structure
   - Set up package manager (npm, pip, cargo, etc.)
   - Configure build tools

3. **Set up development tools**
   - Linters (ESLint, Flake8, etc.)
   - Formatters (Prettier, Black, etc.)
   - Type checkers (TypeScript, mypy, etc.)
   - Testing frameworks (Jest, pytest, etc.)

4. **Configure CI/CD**
   - GitHub Actions workflows
   - Pre-commit hooks
   - Automated testing

### Development Cycle

```
1. Create/checkout feature branch
   ↓
2. Implement changes with tests
   ↓
3. Run linters and tests locally
   ↓
4. Commit with descriptive messages
   ↓
5. Push to remote branch
   ↓
6. Create pull request
   ↓
7. Code review and CI checks
   ↓
8. Merge to main branch
```

---

## Key Conventions

### Code Style

**General Principles:**
- **Consistency** - Follow existing patterns in the codebase
- **Clarity** - Write self-documenting code with clear names
- **Simplicity** - Avoid over-engineering; implement what's needed
- **Security** - Validate inputs, avoid XSS, SQL injection, command injection

**Naming Conventions:**
- Use descriptive, intention-revealing names
- Follow language-specific conventions (camelCase, snake_case, PascalCase)
- Avoid abbreviations unless widely understood
- Use verb-noun pairs for functions (e.g., `getUserData`, `validateInput`)

**Comments and Documentation:**
- Only add comments where logic isn't self-evident
- Document public APIs and complex algorithms
- Keep comments up-to-date with code changes
- Prefer self-documenting code over excessive comments

### Testing Standards

- **Coverage** - Aim for meaningful test coverage, not just high percentages
- **Test Types** - Unit tests for logic, integration tests for components, E2E for workflows
- **Test Naming** - Use descriptive names: `test_user_login_with_invalid_credentials`
- **Assertions** - One logical assertion per test when possible
- **Fixtures** - Share common setup with fixtures/factories

### Error Handling

- Validate at system boundaries (user input, external APIs)
- Trust internal code and framework guarantees
- Use appropriate error types for different scenarios
- Log errors with sufficient context for debugging
- Don't catch exceptions you can't handle meaningfully

---

## AI Assistant Guidelines

### When Working on This Repository

**1. Always Read Before Modifying**
- Never propose changes to code you haven't read
- Use `Read` tool to examine files before suggesting modifications
- Understand existing patterns before adding new code

**2. Use Task Management**
- Use `TodoWrite` tool for multi-step tasks (3+ steps)
- Mark tasks as `in_progress` before starting
- Mark tasks as `completed` immediately after finishing
- Keep exactly ONE task `in_progress` at a time

**3. Exploration and Search**
- Use `Task` tool with `subagent_type=Explore` for open-ended codebase exploration
- Use `Glob` for finding files by name patterns
- Use `Grep` for searching specific code patterns
- Use specialized tools (Read, Edit, Write) instead of bash commands for file operations

**4. Code Quality Standards**
- **No over-engineering** - Only implement what's requested
- **No premature abstraction** - Don't create utilities for one-time use
- **No unnecessary changes** - Don't refactor code that wasn't touched
- **No backwards-compatibility hacks** - Delete unused code completely
- **Security first** - Always consider OWASP top 10 vulnerabilities

**5. Commit Guidelines**
- Only commit when explicitly requested by user
- Write clear, concise commit messages focusing on "why"
- Follow repository's existing commit message style
- Use heredoc format for commit messages:
  ```bash
  git commit -m "$(cat <<'EOF'
  Commit message here
  EOF
  )"
  ```

**6. Tool Usage Best Practices**
- Call multiple independent tools in parallel (single message)
- Use specialized tools over bash commands for file operations
- Never use bash echo to communicate with user - output text directly
- Check for file existence before creating new files

**7. Question and Clarify**
- Use `AskUserQuestion` tool when assumptions need validation
- Clarify requirements before implementing complex features
- Present options without time estimates

---

## Git Workflow

### Branch Naming Convention

- **Feature branches:** `claude/claude-md-[SESSION-ID]` for Claude sessions
- **Main branch:** `main` or `master` (to be determined)
- **Other branches:** Follow conventional patterns:
  - `feature/description` - New features
  - `fix/description` - Bug fixes
  - `refactor/description` - Code refactoring
  - `docs/description` - Documentation updates

### Git Commands Best Practices

**Pushing changes:**
```bash
# Always use -u flag for new branches
git push -u origin <branch-name>

# Branch must start with 'claude/' and end with session ID
# If push fails due to network, retry up to 4 times with exponential backoff
```

**Fetching changes:**
```bash
# Prefer specific branch fetches
git fetch origin <branch-name>

# Use pull for fetching and merging
git pull origin <branch-name>
```

**Committing changes:**
```bash
# Stage relevant files
git add <files>

# Commit with descriptive message
git commit -m "$(cat <<'EOF'
Brief description of changes

More detailed explanation if needed
EOF
)"
```

### Git Safety Protocol

**NEVER:**
- Update git config without explicit permission
- Run destructive commands (force push, hard reset) without user request
- Skip hooks (--no-verify, --no-gpg-sign) without permission
- Force push to main/master branch
- Commit secrets or sensitive files (.env, credentials.json, etc.)
- Use `git commit --amend` unless all conditions are met:
  1. User explicitly requested OR pre-commit hook auto-modified files
  2. HEAD commit was created in this conversation
  3. Commit has NOT been pushed to remote

**ALWAYS:**
- Verify changes with `git status` and `git diff` before committing
- Check recent commits with `git log` to match commit message style
- Warn user if attempting to commit sensitive files
- Create new commits instead of amending when commit fails

---

## Common Tasks

### Starting a New Feature

1. Ensure working directory is clean: `git status`
2. Create or checkout feature branch
3. Plan implementation with TodoWrite tool
4. Implement changes incrementally
5. Write tests alongside code
6. Run linters and tests
7. Commit with clear messages
8. Push to remote branch

### Creating a Pull Request

1. Run `git status` to check staged/unstaged changes
2. Run `git diff` to review changes
3. Check branch is up to date with remote
4. Run `git log` and `git diff [base-branch]...HEAD` to see full commit history
5. Analyze ALL commits in the PR (not just latest)
6. Create PR with `gh pr create`:
   ```bash
   gh pr create --title "Brief title" --body "$(cat <<'EOF'
   ## Summary
   - Bullet point summary

   ## Test plan
   - Testing checklist
   EOF
   )"
   ```

### Running Tests

```bash
# Run all tests
[test command for project]

# Run specific test file
[test command] path/to/test

# Run with coverage
[test command with coverage]
```

### Building the Project

```bash
# Development build
[dev build command]

# Production build
[prod build command]

# Watch mode
[watch command]
```

---

## Best Practices Summary

### Do's ✓
- Read code before modifying
- Use task management for complex work
- Write tests for new features
- Validate user input at boundaries
- Keep solutions simple and focused
- Delete unused code completely
- Ask questions when unclear
- Use specialized tools appropriately
- Commit with clear messages

### Don'ts ✗
- Don't over-engineer solutions
- Don't add features beyond what's requested
- Don't refactor unrelated code
- Don't create premature abstractions
- Don't skip reading existing code
- Don't commit without user request
- Don't use bash for file operations when tools exist
- Don't ignore security vulnerabilities
- Don't make assumptions - verify

---

## Project-Specific Notes

**This section should be updated as the project develops with:**
- Project-specific architecture decisions
- Important design patterns used
- API conventions and standards
- Database schema and migrations
- Deployment procedures
- Environment setup instructions
- Third-party integrations
- Performance considerations
- Security requirements

---

## Updates and Maintenance

**Last Updated:** 2026-01-20
**Updated By:** Claude (Initial creation)

**Update History:**
- 2026-01-20: Initial CLAUDE.md creation for empty repository

**When to Update:**
- When project structure changes significantly
- When new conventions or standards are adopted
- When major dependencies or frameworks are added
- When development workflow changes
- When AI assistants encounter recurring issues

---

## Additional Resources

**Documentation to Create:**
- [ ] README.md - Project overview and setup
- [ ] CONTRIBUTING.md - Contribution guidelines
- [ ] CODE_OF_CONDUCT.md - Community guidelines
- [ ] SECURITY.md - Security policy and reporting
- [ ] LICENSE - Project license

**Tools to Configure:**
- [ ] Linter configuration
- [ ] Formatter configuration
- [ ] Test framework setup
- [ ] CI/CD pipelines
- [ ] Pre-commit hooks
- [ ] Issue templates
- [ ] PR templates

---

*This document is a living guide. Update it as the project evolves to keep AI assistants aligned with project conventions and best practices.*
