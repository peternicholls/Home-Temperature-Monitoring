---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

0. **Pre-Execution Validation** (Project-specific requirements):
   - Check if `.specify/scripts/bash/pre-agent-check.sh` exists
   - If exists:
     - Run: `bash .specify/scripts/bash/pre-agent-check.sh`
     - Capture exit code and output
     - Exit 0: Proceed to Step 1
     - Exit 1: STOP - Display stderr, error message, do not continue
     - Exit 2: Display stdout/stderr as warning, proceed to Step 1
   - If not exists: Skip to Step 1
   - **Why This Helps**: Projects can inject custom requirements (constitution reminders, environment checks, auto-fixes) without modifying SpecKit agent files

1. Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `Makefile`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

6. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together  
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

8. Progress tracking and error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [X] in the tasks file.


9. Completion validation:
   - Verify all required tasks are completed
   - Check that implemented features match the original specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the implementation follows the technical plan
   - Report final status with summary of completed work 

10. **Post-Implementation Documentation** (REQUIRED):
    - **Implementation Report**: Follow the instructions exactly in `.specify/templates/commands/report-writing-process.md` to create a comprehensive implementation report.
    - **Steps**:
      - **Create report file directly** (do NOT use interactive script):
        - Determine phase number from work completed (or use 900-series for general work: 901, 902, etc.)
        - Generate filename: `YYYY-MM-DD-spec-NNN-phase-N-description-implementation-report.md` in `docs/reports/`
        - Copy template from `.specify/templates/report-template.md`
        - Replace placeholders: `[NNN]` with sprint number, `[N]` with phase, `[USN]` with user story or "N/A", `[YYYY-MM-DD]` with current date, `[NNN-sprint-name]` with sprint identifier, `[Feature Name]` with descriptive title
      - If there is no direct phase or story number mapping, use "N/A" or "Not Applicable" for phase and story number starting with 9, so "901" or "902" etc. 900 series is reserved for general implementation report content not tied to specific phases or stories.
      - YOU as agent are to fill all required sections (Executive Summary, Key Achievements, etc.)
      - Include 2-7 detailed "Lessons Learned" with specific, actionable content (quality over quantity)
      - Validate: `bash .specify/scripts/bash/validate-report.sh <report-path>`
      - **CRITICAL**: Once validation passes (exit code 0), IMMEDIATELY proceed to lessons learned extraction (do NOT stop or wait for user input)
    
    - **Lessons Learned Extraction** (AUTOMATIC - DO NOT ASK USER):
      - **IMMEDIATELY** after validation passes, run: `bash .specify/scripts/bash/extract-lessons-learned.sh`
      - Review the extraction script output to identify new vs duplicate lessons
      - **If new lessons exist** (script shows "New lesson: ..." lines):
        - Read the current `.specify/memory/lessons-learned.md` file
        - Follow the categorization instructions at the top of that file
        - For each new lesson from the report:
          - Determine appropriate category (Testing & Quality, Technical Architecture, Development Process, Performance & Optimization, Error Handling & Resilience, Tools & Frameworks, Security & Compliance, or create new category if needed)
          - Add under that category section in `.specify/memory/lessons-learned.md`
          - Include source attribution: `**Source**: Sprint NNN, Phase N, Date: YYYY-MM-DD`
          - Ensure lesson content is clear, concise, specific, and actionable
          - Remove any duplicate content
        - Update metadata in frontmatter: increment lesson count, update "Last updated" timestamp
      - **If all lessons are duplicates** (script shows "LESSONS ALREADY INTEGRATED"):
        - Report completion: "All lessons from this report already exist in knowledge base. No extraction needed."
      - **Why This Matters**: Lessons learned feed into future implementations, preventing repeated mistakes and capturing best practices for the team and AI agents.
      - **DO NOT** ask user whether to proceed - this step is mandatory and automatic after validation passes

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list if needed.
