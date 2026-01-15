---
description: "Consolidate and clean up Memory Bank by removing stale entries and organizing active context"
---

Consolidate the Memory Bank to remove stale information, merge redundant entries, and preserve essential context. This command helps manage memory bank growth and maintains efficient context retrieval.

## Usage

```
/compact-memory [optional user query]
```

**Without query:** Consolidates entire memory bank
**With query:** Consolidates only memory sections relevant to the specified query

**Examples:**
- `/compact-memory` - Full memory bank consolidation
- `/compact-memory cloud deployment` - Consolidate only cloud deployment-related entries
- `/compact-memory validator patterns` - Consolidate only validator-related content

## Process Overview

1. **Analyze Memory Bank Files**
   - Read all 5 memory bank files (productContext.md, activeContext.md, progress.md, decisionLog.md, systemPatterns.md)
   - **If user query provided:**
     - Parse query to identify relevant topics/keywords
     - Filter entries by relevance to query (using semantic matching on entry content)
     - Mark entries as "in-scope" or "out-of-scope" for consolidation
     - Only consolidate in-scope entries; preserve out-of-scope entries unchanged
   - **If no query provided:**
     - Process entire memory bank (current behavior)
   - Parse timestamps and update logs
   - Identify stale, redundant, and duplicate entries
   - Calculate consolidation opportunities and space savings

2. **Present Consolidation Strategy**
   - **If user query provided:**
     - Show query interpretation and identified relevant topics
     - List entries marked as in-scope vs out-of-scope
     - Explain relevance criteria used for filtering
   - Show detailed plan of what will be:
     - Archived (moved to timestamped backup)
     - Removed (stale/superseded information)
     - Merged (related entries consolidated)
     - Preserved (current/active information or out-of-scope if query-targeted)
   - Display before/after line counts for each file
   - Estimate token/context savings

3. **Request User Approval** (unless --auto-approve flag used)
   - Wait for user confirmation: "Proceed with consolidation? (yes/no)"
   - If user declines, exit without changes
   - If --dry-run flag, show plan and exit without changes

4. **Execute Consolidation** (file-by-file)
   
   **Query-Aware Processing:**
   - **If query provided:** Only process entries marked as in-scope
   - **If no query:** Process all entries (full consolidation)
   - Preserve out-of-scope entries exactly as-is with no modifications
   
   **For productContext.md:**
   - Keep: Project Goal, Key Features, Overall Architecture (latest versions or if out-of-scope)
   - Condense: Multiple update logs → Single "Evolution History" section (in-scope only)
   - Remove: Duplicate information, interim versions (in-scope only)
   - Add: Consolidation metadata header with query scope if applicable
   
   **For activeContext.md:**
   - Keep: Current Focus, Open Questions/Issues (active items or out-of-scope)
   - Move: Completed "Recent Changes" → progress.md if significant (in-scope only)
   - Remove: Stale items, resolved questions, old "current" items (in-scope only)
   - Merge: Multiple "Update Log" sections → Single consolidated log (in-scope only)
   
   **For progress.md:**
   - Keep: Current Tasks, Next Steps (or out-of-scope)
   - Archive: Completed tasks older than 30 days (in-scope only)
   - Condense: Detailed task logs → Milestone summaries (in-scope only)
   - Add: Link to archive for historical tasks
   
   **For decisionLog.md:**
   - Merge: Related decisions into single entry with evolution notes (in-scope only)
   - Mark: Superseded decisions with "Superseded by [Decision]" notation (in-scope only)
   - Keep: Active architectural decisions (or out-of-scope)
   - Condense: Verbose implementation details → Summaries (in-scope only)
   
   **For systemPatterns.md:**
   - Keep: Actively used patterns (or out-of-scope)
   - Remove: Obsolete patterns (in-scope only, e.g., deprecated naming conventions)
   - Update: Pattern descriptions to reflect current state (in-scope only)
   - Archive: Historical patterns for reference (in-scope only)

5. **Add Consolidation Metadata**
   - Add header to each consolidated file with:
     - Last consolidated timestamp
     - **Query scope (if query-targeted consolidation)**
     - Link to backup archive
     - Summary of changes (lines reduced, entries archived, etc.)
     - Note if partial/targeted consolidation was performed

6. **Verify Results**
   - Compare before/after line counts
   - Ensure no critical information lost
   - Validate file structure and formatting
   - Confirm all files are valid markdown

7. **Report Results**
   - Display consolidation summary:
     - **Query scope used (if applicable)**
     - Lines reduced per file
     - Total entries archived (in-scope vs total)
     - Context/token savings achieved
     - Archive location for rollback
     - Note: Out-of-scope entries preserved unchanged (if query-targeted)
   - Confirm Memory Bank is ready for use

## Consolidation Rules

**Query Relevance Criteria (when query provided):**
- Entry content contains query keywords or semantically related terms
- Entry topic/category matches query intent
- Entry references entities mentioned in query
- Use fuzzy matching for partial keyword matches
- When in doubt, mark as in-scope to avoid losing potentially relevant info

**Stale Information Criteria (applied to in-scope entries only):**
- Entries older than 30 days in activeContext.md "Current Focus"
- Completed tasks older than 7 days in progress.md
- Superseded decisions in decisionLog.md
- Obsolete patterns in systemPatterns.md
- Duplicate "Update Log" sections

**Preservation Criteria:**
- All current/active information
- Critical architectural decisions (even if old)
- Key milestones and achievements
- Open questions and issues
- Active system patterns
- **All out-of-scope entries (when query provided)**


## Safety Features

- Full backup before any changes
- User approval required (unless --auto-approve)
- Reversible via archive
- Verification after consolidation
- Detailed change reporting

## Expected Outcomes

**Full Consolidation (no query):**
- Reduced memory bank file sizes (typically 40-60% reduction)
- Faster Memory Query mode retrieval
- Clearer, more relevant context
- Better token efficiency
- Preserved historical data in archives
- Improved semantic accuracy ("Current" actually means current)

**Targeted Consolidation (with query):**
- Focused reduction in query-relevant sections (10-30% reduction)
- Faster retrieval for specific topics
- Preserved unrelated context unchanged
- Surgical cleanup without affecting other areas
- Lower risk of unintended information loss

## Post-Consolidation

- Memory Bank is immediately usable
- All modes can access consolidated context
- Archive available at `memory-bank/archive/YYYY-MM-DD-HH-MM/`
- Original files preserved for rollback if needed
- Consider running consolidation monthly or when files exceed 200 lines