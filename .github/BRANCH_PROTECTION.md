# DuCO-Agent: Branch Protection Rules
# =====================================
# This file documents the branch protection policy for this repository.
# Branch protection MUST be configured via GitHub Settings > Branches after repo creation.

## Main Branch Protection Rules

branch: main
protection:
  - No direct pushes allowed to main
  - All changes must go through Pull Requests
  - Require at least 1 approving review before merge
  - Require status checks to pass (if CI is configured)
  - Dismiss stale PR reviews when new commits are pushed
  - Require conversation resolution before merging

## Development Workflow

All development happens on feature branches:

feature/intake-agent      → Intake & multi-modal parsing (Step 1–2)
feature/cob-logic         → COB determination & financial calculations (Steps 4–5)
feature/multi-modal-outputs → Letter gen, visual output, audio brief (Steps 6–8)

## Commit Convention (Semantic Commits)

Format: <type>(<scope>): <description>

Types:
  feat     → New feature
  fix      → Bug fix
  docs     → Documentation only
  chore    → Maintenance (deps, config)
  test     → Test additions/changes
  refactor → Code restructuring

Examples:
  feat(intake): add Gemini vision parsing for PT invoice images
  feat(cob): implement subscriber rule COB determination logic
  feat(financial): add dual-coverage savings calculation in INR
  feat(letters): generate PDF pre-auth letters for Plan A and B
  docs(readme): add setup instructions and API key configuration
  chore(deps): pin langgraph version in requirements.txt
  fix(image-parser): handle fallback when Gemini vision fails

## GitHub Setup Commands

# After creating the private repo on GitHub:
git remote add origin https://github.com/YOUR_USERNAME/duco-agent-ai-assessment.git

# Protect main branch via GitHub web UI:
# Settings → Branches → Add branch protection rule → main
# Check: "Require a pull request before merging"
# Check: "Require approvals" (1 required)
# Check: "Block direct pushes"

# Invite collaborators:
# Settings → Collaborators → Add people
# Add: @ShreyasHegde, @VinayKumar
