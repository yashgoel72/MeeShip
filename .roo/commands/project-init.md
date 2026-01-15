---
description: "Analyze codebase and create conscise and technically accurate projectBrief.md through guided discovery and architectural analysis"
---

Analyze the current project workspace to create a **conscise**, technically accurate `projectBrief.md` file. This command orchestrates a two-phase approach: first gathering context through targeted questions (ASK mode), then synthesizing findings into conscise and accurate documentation (ARCHITECT mode). **Do not make it too verbose, with unnecessary and repetitive information.**

## Process Overview

### Phase 1: Discovery & Analysis (ASK Mode)

1. **Workspace Analysis**
   - Scan project directory structure recursively
   - Identify primary programming languages and frameworks
   - Locate configuration files (package.json, requirements.txt, pom.xml, etc.)
   - Find build scripts and CI/CD configurations
   - Detect testing frameworks and test directories
   - Identify documentation files (README, CONTRIBUTING, etc.)
   - Analyze dependency manifests

2. **Codebase Pattern Recognition**
   - Detect architectural patterns (MVC, microservices, monolith, etc.)
   - Identify common design patterns in use
   - Analyze file organization and module structure
   - Find API definitions (OpenAPI, GraphQL schemas, etc.)
   - Locate database schemas and migration files
   - Identify authentication/authorization mechanisms
   - Detect third-party integrations

3. **Gap Identification**
   - Determine what information is **missing** from code analysis alone:
     * Business purpose and problem statement
     * Target audience and user personas
     * Non-functional requirements (performance, scalability, security)
     * Deployment architecture and infrastructure
     * Development workflow and branching strategy
     * Release process and versioning approach
     * Known limitations or technical debt
     * Future roadmap or planned features

4. **Generate Targeted Questions**
   - Create 5-10 specific questions addressing identified gaps
   - Prioritize questions by importance:
     * Critical: Project purpose, target users, core functionality
     * Important: Architecture decisions, technology choices
     * Helpful: Development practices, deployment strategy
   - Format questions for clarity and specificity
   - Provide context for each question based on code findings

5. **Present Findings & Questions**
   - Summarize what was discovered from code analysis
   - Present knowledge gaps requiring user input
   - Ask questions in priority order
   - Wait for user responses before proceeding

### Phase 2: Documentation Synthesis (ARCHITECT Mode)

6. **Compile Information Sources**
   - Code analysis findings from Phase 1
   - User responses to discovery questions
   - Existing documentation (README, docs/, etc.)
   - Configuration files and build scripts
   - Dependency manifests and version constraints
   - Test files indicating feature coverage

7. **Structure projectBrief.md**
   - Create comprehensive sections (defined below)
   - Use consistent Markdown formatting
   - Include Mermaid diagrams for architecture
   - Add code snippets from actual codebase
   - Reference specific files and line numbers
   - Organize information hierarchically

8. **Technical Accuracy Validation**
   - Verify all technical claims against actual code
   - Cross-reference architecture descriptions with file structure
   - Validate dependency versions from manifest files
   - Confirm API contracts match code implementations
   - Ensure build/deployment steps match actual scripts
   - Check that design patterns cited are actually used

9. **Write projectBrief.md**
   - Generate complete file content
   - Apply professional technical writing standards
   - Maintain objectivity and precision
   - Include attribution for external sources
   - Add last-updated timestamp

10. **Verification & Handoff**
    - Verify projectBrief.md is valid Markdown
    - Confirm all sections are complete
    - Check internal links and references
    - Validate Mermaid diagram syntax
    - Present summary of what was documented
    - Offer to initialize Memory Bank if not present

## projectBrief.md Structure

The generated `projectBrief.md` MUST include the following sections:

### 1. Project Overview
```markdown
# [Project Name]

**Last Updated:** YYYY-MM-DD

## Executive Summary
[2-3 paragraphs summarizing the project]

## Problem Statement
[What problem does this solve? Why does it exist?]

## Solution Approach
[High-level description of how the project solves the problem]
```

### 2. Project Metadata
```markdown
## Project Information

- **Name:** [Project Name]
- **Version:** [Current Version from package manifest]
- **License:** [License Type]
- **Repository:** [Git repository URL if available]
- **Primary Language(s):** [Languages with percentages]
- **Status:** [Development/Production/Maintenance]
```

### 3. Target Audience & Use Cases
```markdown
## Target Audience

### Primary Users
- [User persona 1]
- [User persona 2]

### Use Cases
1. **[Use Case Name]**
   - Actor: [Who]
   - Goal: [What they want to accomplish]
   - Flow: [Brief description]

[Repeat for each major use case]
```

### 4. Technical Architecture
```markdown
## Architecture Overview

### System Architecture

[Mermaid diagram showing high-level components]

### Component Breakdown

#### [Component Name]
- **Purpose:** [What it does]
- **Technology:** [Implementation tech]
- **Location:** [File paths]
- **Dependencies:** [What it depends on]
- **Interfaces:** [How it's accessed]

[Repeat for each major component]

### Data Flow

[Mermaid sequence diagram showing key data flows]
```

### 5. Technology Stack
```markdown
## Technology Stack

### Core Technologies
- **Runtime:** [e.g., Node.js 18.x, Python 3.11]
- **Framework:** [e.g., Express 4.x, Django 4.2]
- **Database:** [e.g., PostgreSQL 15, MongoDB 6.0]
- **Cache:** [e.g., Redis 7.x]

### Key Dependencies

| Package | Version | Purpose | Critical? |
|---------|---------|---------|-----------|
| [name]  | [ver]   | [why]   | Yes/No    |

### Development Tools
- **Build System:** [e.g., Webpack, Gradle]
- **Testing:** [e.g., Jest, PyTest]
- **Linting:** [e.g., ESLint, Pylint]
- **CI/CD:** [e.g., GitHub Actions, Jenkins]

### Technology Decisions

#### Why [Technology X]?
- **Decision:** Chose [X] over [Y]
- **Rationale:** [Reasoning]
- **Trade-offs:** [What was sacrificed]
- **Source:** [File/config that shows this choice]
```

### 6. System Design & Patterns
```markdown
## Design Patterns & Principles

### Architectural Patterns
- **Primary Pattern:** [e.g., MVC, Microservices]
- **File Evidence:** [Where pattern is visible]
- **Implementation:** [How it's applied]

### Design Patterns in Use
1. **[Pattern Name]** (e.g., Singleton, Factory)
   - Location: `[file:line]`
   - Purpose: [Why used here]

### Code Organization
- **Module Structure:** [How code is organized]
- **Naming Conventions:** [Patterns observed]
- **Layering:** [Presentation, Business, Data layers]
```

### 7. Data Models
```markdown
## Data Models & Schemas

### Database Schema

[Mermaid ER diagram if applicable]

### Core Entities

#### [Entity Name]
```language
[Actual schema definition from code]
```
- **Purpose:** [What this entity represents]
- **Relationships:** [Connections to other entities]
- **Location:** `[schema file path]`

### Data Storage Strategy
- **Primary Database:** [Type and reasoning]
- **Caching Strategy:** [If applicable]
- **File Storage:** [If applicable]
```

### 8. API & Integration Points
```markdown
## APIs & Integrations

### Internal APIs

#### [API Name/Endpoint]
- **Type:** REST/GraphQL/gRPC
- **Authentication:** [Method]
- **Endpoints:**
  ```
  GET    /api/resource       - [Description]
  POST   /api/resource       - [Description]
  ```
- **Documentation:** [Link to OpenAPI spec if exists]

### External Integrations
- **[Service Name]:** [Purpose, how integrated]
- **[API/SDK]:** [Version, authentication method]

### Message Formats
```language
[Example request/response from code]
```
```

### 9. Development Environment
```markdown
## Development Setup

### Prerequisites
- [Tool 1] version [X]
- [Tool 2] version [Y]

### Installation Steps
```bash
# Based on actual project scripts
[Step-by-step commands from README or scripts]
```

### Environment Variables
| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| [NAME]   | [What]  | Yes/No   | [Value] |

### Configuration Files
- `[config file]` - [Purpose and key settings]

### Local Development
```bash
# Start development server
[Actual command from package.json or Makefile]

# Run tests
[Actual test command]
```
```

### 10. Build, Test & Deployment
```markdown
## Build & Deployment

### Build Process
```bash
# Based on actual build scripts
[Commands from CI/CD or build files]
```

### Testing Strategy
- **Unit Tests:** [Framework, coverage target]
  - Location: `[test directory]`
  - Run: `[command]`
- **Integration Tests:** [If present]
- **E2E Tests:** [If present]

### CI/CD Pipeline
[Mermaid diagram of pipeline stages]

### Deployment Architecture
- **Environment:** [Cloud provider, hosting]
- **Infrastructure:** [Servers, containers, serverless]
- **Deployment Method:** [How code gets deployed]
- **Monitoring:** [Tools and metrics]

### Release Process
1. [Step 1 from actual workflow]
2. [Step 2]
[...]
```

### 11. Security & Authentication
```markdown
## Security Considerations

### Authentication
- **Method:** [JWT, OAuth, Session, etc.]
- **Implementation:** `[file path where implemented]`
- **Token Storage:** [How/where tokens stored]

### Authorization
- **Access Control:** [RBAC, ABAC, etc.]
- **Permission Model:** [How permissions managed]

### Security Measures
- **Data Encryption:** [At rest, in transit]
- **Input Validation:** [How implemented]
- **Rate Limiting:** [If present]
- **CORS Configuration:** [Settings]
- **Secrets Management:** [How API keys/secrets handled]

### Known Security Considerations
- [Any documented security concerns]
- [Dependencies with known vulnerabilities]
```

### 12. Performance & Scalability
```markdown
## Performance Requirements

### Performance Targets
- **Response Time:** [Target latency]
- **Throughput:** [Requests/transactions per second]
- **Concurrent Users:** [Expected load]

### Scalability Approach
- **Horizontal Scaling:** [How/if supported]
- **Caching Strategy:** [What's cached, TTL]
- **Database Optimization:** [Indexes, query optimization]

### Performance Monitoring
- **Metrics Tracked:** [What's measured]
- **Tools Used:** [Monitoring solutions]
```

### 13. Dependencies & Services
```markdown
## Dependencies

### Production Dependencies
[Auto-generated from package manifest with versions]

### Development Dependencies
[Auto-generated from package manifest]

### Third-Party Services
- **[Service Name]:** [Purpose, criticality]
- **[Service Name]:** [Purpose, criticality]

### Dependency Management
- **Update Strategy:** [How dependencies updated]
- **Security Scanning:** [Tools/process]
```

### 14. Repository Structure
```markdown
## Repository Organization

### Directory Structure
```
[Actual directory tree with explanations]
/src
  /components  - [Purpose]
  /services    - [Purpose]
/tests         - [Purpose]
/docs          - [Purpose]
```

### Key Files
- `[file]` - [Purpose and importance]
- `[file]` - [Purpose and importance]

### Module Organization
[Explanation of how code is modularized]
```

### 15. Development Guidelines
```markdown
## Contributing & Standards

### Coding Standards
- **Style Guide:** [Link or description]
- **Linting Rules:** [Config file reference]
- **Formatting:** [Tool and config]

### Git Workflow
- **Branching Strategy:** [Git Flow, trunk-based, etc.]
- **Commit Conventions:** [Conventional commits, etc.]
- **PR Process:** [Review requirements]

### Code Review Guidelines
- [Requirements for approval]
- [Testing expectations]

### Documentation Standards
- [How to document code]
- [Documentation tools used]
```

### 16. Additional Context
```markdown
## Known Limitations & Technical Debt
- [Documented limitations]
- [Technical debt items]

## Future Roadmap
- [Planned features if known]
- [Planned improvements]

## References
- [Links to related documentation]
- [External resources]
- [Design documents]
```

## Quality Standards

### Technical Accuracy Requirements
- ✅ All architecture diagrams reflect actual code structure
- ✅ Dependency versions match manifest files exactly
- ✅ Code snippets are actual code from the project
- ✅ File paths and line numbers are accurate
- ✅ API contracts match implementation
- ✅ Build commands are tested and working
- ✅ Environment variables are documented from actual usage

### Documentation Standards
- ✅ Clear, professional technical writing
- ✅ Consistent Markdown formatting
- ✅ No broken internal links
- ✅ Valid Mermaid diagram syntax
- ✅ Code blocks specify language for syntax highlighting
- ✅ Tables are properly formatted
- ✅ Sections are logically organized

### Completeness Criteria
- ✅ All required sections present
- ✅ No placeholder text like "TODO" or "[Fill in]"
- ✅ Sufficient detail for new developer onboarding
- ✅ Technical decisions are explained with rationale
- ✅ Integration points are documented
- ✅ Security considerations addressed

## Mode Transition Guidelines

### Entering ASK Mode
**Trigger:** Command `/project-init` invoked

**Actions:**
1. Acknowledge command: "Analyzing project workspace..."
2. Perform workspace scan and code analysis
3. Identify knowledge gaps
4. Generate targeted questions
5. Present findings and questions to user
6. Wait for user responses
7. When questions answered: "Analysis complete. Switching to ARCHITECT mode to generate projectBrief.md..."

### Entering ARCHITECT Mode
**Trigger:** User has answered discovery questions from ASK mode

**Actions:**
1. Acknowledge mode switch: "Generating conscise and technically accurate projectBrief.md..."
2. Compile all information sources
3. Generate projectBrief.md with all required sections
4. Validate technical accuracy
5. Write file to workspace root
6. Verify file integrity
7. Present completion summary
8. Offer Memory Bank initialization if not present

## Edge Cases & Handling

### Case: projectBrief.md Already Exists
**Action:**
- Inform user existing file found
- Ask: "projectBrief.md already exists. How should I proceed?"
  - Suggest: "Create backup and regenerate from scratch"
  - Suggest: "Update/enhance existing file with new analysis"
  - Suggest: "Cancel operation",
  - Suggest: "Update or create memory bank"
- Wait for user choice before proceeding

### Case: Minimal/Unclear Codebase
**Action:**
- Document what IS discoverable
- Clearly mark sections with insufficient information
- Ask more detailed questions in ASK mode
- Note gaps prominently in generated file
- Recommend project structure improvements

### Case: Multi-Language Project
**Action:**
- Document each language stack separately
- Show how components in different languages interact
- Create integration architecture diagram
- Document build process for each stack

### Case: Monorepo with Multiple Projects
**Action:**
- Ask user which project to document
- Suggest: List all detected sub-projects
- Allow user to choose specific project or document entire monorepo structure

## Expected Outcomes

### Deliverables
- ✅ `projectBrief.md` created in workspace root
- ✅ Conscise, technically accurate documentation
- ✅ Ready for Memory Bank initialization (if applicable)
- ✅ Serves as single source of truth for project context

### Benefits
- **Onboarding:** New developers understand project quickly
- **Context Preservation:** Critical knowledge documented
- **Architecture Clarity:** System design is explicit
- **Decision Record:** Technical choices are explained
- **Memory Bank Foundation:** Powers AI-assisted development

### Success Metrics
- New developer can set up project from projectBrief.md alone
- All technical claims verifiable from code
- No ambiguous or vague sections
- Diagrams accurately represent architecture
- Document serves as effective project overview

## Post-Generation Actions

1. **Verify File Creation**
   - Confirm projectBrief.md exists in workspace root
   - Validate Markdown formatting
   - Check file size (should be substantial for real projects)

2. **Offer Memory Bank Initialization**
   - If memory-bank/ doesn't exist:
     - "Would you like to initialize the Memory Bank using this projectBrief.md?"
     - If yes: Use projectBrief.md to populate productContext.md
     - If no: Note that Memory Bank can be initialized later

3. **Completion Summary**
   - Report sections documented
   - Highlight any gaps or assumptions made
   - Suggest next steps (e.g., "Review and refine technical details")

## Usage Examples

### Example 1: New Project Analysis
```
User: /project-init
Switch to Project Research Mode
Project Research Mode:
- Analyzes Node.js Express project
- Finds package.json, routes/, models/
- Detects PostgreSQL connection in config
- Identifies gaps: purpose, target users, deployment strategy
- Asks 5 questions about business context

User: [Answers questions]

Switch to ARCHITECT Mode:
- Generates projectBrief.md with:
  - Express REST API architecture
  - PostgreSQL data models
  - Docker deployment setup
  - JWT authentication details
  - Actual dependency versions
- File created: projectBrief.md (245 lines)
```

### Example 2: Complex Microservices Project
```
User: /project-init
Switch to Project Research Mode:
- Detects multiple service directories
- Finds docker-compose.yml
- Identifies Spring Boot, React, Python services
- Asks about service communication patterns
- Asks about deployment orchestration

User: [Provides Kubernetes deployment info]

Switch to ARCHITECT Mode:
- Generates multi-section architecture
- Creates Mermaid diagrams for:
  - Microservice interaction
  - Data flow between services
  - Deployment topology
- Documents each service stack separately
- File created: projectBrief.md (380 lines)
```

## Safety & Validation

- ✅ Never overwrite existing projectBrief.md without confirmation
- ✅ Validate all file paths before referencing in documentation
- ✅ Test Mermaid syntax before including in document
- ✅ Verify dependency versions from actual manifest files
- ✅ Confirm code snippets are real code, not invented examples
- ✅ Include timestamp to track documentation freshness
- ✅ Preserve attribution for external sources or documentation

## Notes for Implementation

- This is a **two-mode orchestrated command**
- Project Research mode should be used for discovery and gap analysis
- Switch to ARCHITECT mode should generate the actual documentation
- The transition between modes should be explicit and user-visible
- All generated content must be traceable to actual code or user input
- Prioritize accuracy over completeness—document what's known, mark what's uncertain