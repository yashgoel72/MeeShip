---
description: "Halt current workflow to perform comprehensive Memory Bank synchronization across all modes and activities"
---

Halt the current workflow and perform a comprehensive Memory Bank synchronization. This command reviews all work completed during the current session across all modes, updates all Memory Bank files with precise and relevant changes, and ensures complete context preservation for future sessions.

## Process Overview

1. **Halt Current Workflow**
   - Stop all active tasks immediately
   - Acknowledge command with: `[MEMORY BANK: UPDATING]`
   - Prepare for comprehensive session review

2. **Cross-Mode Session Analysis**
   - Review complete chat history from session start
   - Extract information from all mode transitions (Code, Architect, Debug, etc.)
   - Identify codebase-relevant changes and context
   - Track activity relationships and dependencies
   - Map mode interactions and workflow transitions

3. **Identify Memory Bank Updates**
   - Parse session for significant changes requiring documentation
   - Filter for codebase changes (exclude orchestration workflow details)
   - Categorize updates by Memory Bank file type
   - Determine which files need updates and what content to add

5. **Get git status and diff to include relevant changes**
    - Identify modified, added, or deleted files in codebase
    - Correlate file changes with session activities
    - Extract relevant code snippets and change descriptions
    - Prepare detailed change log for Memory Bank entries

4. **Execute Precise Updates** (file-by-file strategy)
   
   **For productContext.md:**
   - Add major features implemented in session
   - Document architectural changes made
   - Record technology decisions with rationale
   - Note significant integrations or dependencies added
   
   **For activeContext.md:**
   - Update Current Focus if work scope changed
   - Document Recent Changes from session
   - Add Open Questions/Issues that emerged
   - Remove items that were resolved in session
   
   **For progress.md:**
   - Log task progress and completions
   - Record milestone achievements
   - Document blockers encountered
   - Note next steps identified
   
   **For decisionLog.md:**
   - Document architectural decisions made
   - Record technical choices with justification
   - Note design pattern adoptions
   - Exclude orchestration/workflow decisions (focus on code decisions)
   
   **For systemPatterns.md:**
   - Add new codebase patterns introduced
   - Update existing pattern descriptions if modified
   - Document pattern relationships discovered
   - Exclude orchestration patterns (focus on code patterns)

5. **Add Synchronization Metadata**
   - Prepend update timestamp to each modified file
   - Include mode attribution in entries (e.g., `[Code Mode]`, `[Architect Mode]`)
   - Add session identifier for traceability
   - Note cross-mode context preservation

6. **Verify Synchronization Results**
   - Confirm all session changes captured
   - Validate timestamp formatting consistency
   - Ensure no critical context lost
   - Check cross-mode information preservation

7. **Report Completion Status**
   - Display files updated with change counts
   - Confirm Memory Bank fully synchronized
   - Note all mode contexts preserved
   - State that session can be safely closed
   - Indicate next assistant will have complete context

## Update Rules

**What Gets Updated:**
- Codebase changes (new features, bug fixes, refactors)
- Architectural decisions and their rationale
- Technical patterns introduced or modified
- Dependencies added or changed
- Configuration changes
- Test implementations
- Documentation updates
- Questions answered during session
- Clarifications provided by user
- Context discovered through investigation

**What Does NOT Get Updated:**
- Orchestration workflow details
- Mode transition mechanics
- Command usage patterns
- Conversational exchanges
- Temporary debugging steps
- Failed attempts or experiments (unless lesson learned)

**Timestamp Format:**
- All entries MUST include: `[YYYY-MM-DD HH:MM:SS]`
- Use UTC time for consistency
- Place timestamp at start of each new entry

**Mode Attribution:**
- Tag entries with source mode when relevant
- Format: `[YYYY-MM-DD HH:MM:SS] [Code Mode] - Description`
- Helps track cross-mode activities
- Preserves context of how information was discovered

## File-Specific Guidelines

### productContext.md

**Update When:**
- Major features added to the product
- Core architecture modified significantly
- New technology stack components integrated
- Product goals or scope changed
- External service integrations added

**Format:**
```markdown
[YYYY-MM-DD HH:MM:SS] - Added {feature name} providing {capability}
[YYYY-MM-DD HH:MM:SS] - Migrated to {technology} for {reason}
```

**Avoid:**
- Minor implementation details
- Temporary changes
- Experimental features not committed

---

### activeContext.md

**Update When:**
- Current work focus shifts to different area
- Recent changes completed in session
- New questions or issues identified
- Blockers encountered that need tracking
- Old items resolved and can be removed

**Sections to Update:**
- **Current Focus**: What's actively being worked on
- **Recent Changes**: Completed work in this session
- **Open Questions/Issues**: Unresolved items for future work

**Format:**
```markdown
## Current Focus
[YYYY-MM-DD HH:MM:SS] - Implementing {feature} to address {need}

## Recent Changes
[YYYY-MM-DD HH:MM:SS] [Code Mode] - Completed {change} in {files}

## Open Questions/Issues
[YYYY-MM-DD HH:MM:SS] - Need to determine {question}
```

**Avoid:**
- Stale "current" items from previous sessions
- Completed changes (move to progress.md if significant)
- Resolved questions

---

### progress.md

**Update When:**
- Tasks started or completed
- Milestones reached
- Blockers encountered
- Next steps identified
- Work estimates changed

**Format:**
```markdown
[YYYY-MM-DD HH:MM:SS] - ✅ Completed: {task description}
[YYYY-MM-DD HH:MM:SS] - 🚧 In Progress: {task description}
[YYYY-MM-DD HH:MM:SS] - ⚠️ Blocked: {task} - {blocker reason}
[YYYY-MM-DD HH:MM:SS] - 📋 Next: {planned task}
```

**Avoid:**
- Granular step-by-step details
- Temporary status changes
- Speculative future work

---

### decisionLog.md

**Update When:**
- Architectural decisions made (code-level only)
- Technology choices finalized
- Design patterns adopted
- API contracts defined
- Data models chosen

**Format:**
```markdown
## Decision: {Decision Title}
**Date:** [YYYY-MM-DD HH:MM:SS]
**Context:** {What problem this solves}
**Decision:** {What was decided}
**Rationale:** {Why this approach}
**Implications:** {Impact on codebase}
**Alternatives Considered:** {Other options and why rejected}
```

**Avoid:**
- Orchestration/workflow decisions
- Mode usage patterns
- Temporary implementation choices
- Routine code changes

---

### systemPatterns.md

**Update When:**
- New architectural patterns introduced
- Code organization patterns established
- Naming conventions defined
- Error handling patterns implemented
- Testing patterns created

**Format:**
```markdown
## Pattern: {Pattern Name}
**Introduced:** [YYYY-MM-DD HH:MM:SS]
**Context:** {When to use this pattern}
**Implementation:** {How it's implemented}
**Example:** {Code location or example}
**Related Patterns:** {Links to related patterns}
```

**Avoid:**
- Orchestration patterns
- One-off code solutions
- Language-standard patterns (unless custom variation)
- Temporary workarounds

## Override Settings

This command operates with elevated permissions to ensure complete Memory Bank synchronization:

```
override_file_restrictions: true
override_mode_restrictions: true
```

These overrides allow UMB to:
- Update Memory Bank files regardless of current mode restrictions
- Access and modify all 5 Memory Bank files atomically
- Preserve cross-mode context seamlessly

## Expected Outcomes

After UMB execution, you should observe:

- **Complete Session Capture**: All relevant work from current session documented
- **Cross-Mode Consistency**: Information from all modes preserved coherently
- **Future Session Ready**: Next assistant has full context to continue work
- **Clean Continuation Points**: Clear documentation of where work left off
- **Preserved Activity Threads**: Related work across modes properly linked
- **Updated Timestamps**: All entries have current, accurate timestamps
- **Mode Attribution**: Clear indication of which mode contributed each piece of context

## Post-UMB Status

After UMB completion:

- Memory Bank is **fully synchronized** with session activities
- All mode contexts are **preserved and linked**
- Session can be **safely closed** without context loss
- Next assistant will have **complete context** to continue work
- No manual Memory Bank updates needed for current session
- All 5 files updated with **precise, relevant changes** only

## Usage Recommendations

**When to Use UMB:**
- Before ending a work session
- After completing major features or changes
- When switching between significantly different tasks
- Before requesting help from another team member
- When Memory Bank files haven't been updated in current session

**Command Invocation:**
Simply type: `Update Memory Bank` or `UMB`

**Frequency:**
- End of each significant work session
- After major architectural changes
- When context preservation is critical
- Before long breaks from the project