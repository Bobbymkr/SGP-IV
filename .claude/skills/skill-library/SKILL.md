# Skill Library Router

This router provides searchable access to LIBRARY skills — useful references that don't need to load every session.

## DAILY vs LIBRARY

**DAILY** (in `.claude/skills/DAILY/`) — Loaded every session:
- `python-patterns`, `python-testing`, `mle-workflow`, `deployment-patterns`, `docker-patterns`, `benchmark-optimization-loop`, `tdd-workflow`, `coding-standards`, `error-handling`, `security-review`, `cost-aware-llm-pipeline`, `autonomous-loops`, `continuous-learning-v2`, `parallel-execution-optimizer`, `search-first`, `backend-patterns`, `api-design`, `database-migrations`, `production-audit`, `verification-loop`

**LIBRARY** (in `.claude/skills/LIBRARY/`) — Access via this router:
- Framework-specific: `django-patterns`, `fastapi-patterns`, `react-patterns`, `angular-developer`, `springboot-patterns`, `dotnet-patterns`, `rust-patterns`, `swiftui-patterns`, `android-clean-architecture`, `kotlin-patterns`, `laravel-patterns`, `perl-patterns`, `cpp-coding-standards`
- Operations: `github-ops`, `jira-integration`
- Security: `security-bounty-hunter`, `hipaa-compliance`, `healthcare-phi-compliance`
- Business: `lead-intelligence`, `market-research`, `investor-materials`, `investor-outreach`
- Content: `article-writing`, `brand-voice`, `content-engine`, `crosspost`

## Usage

To access a LIBRARY skill, use the `skill` tool:

```
skill name: "django-patterns"
```

Or search for relevant skills:

```
skill name: "skill-scout"
```

## Trigger Keywords

| Keywords | Likely LIBRARY Skill |
|----------|---------------------|
| "Django", "DRF", "ORM" | django-patterns |
| "FastAPI", "async API" | fastapi-patterns |
| "React", "Next.js", "hooks" | react-patterns |
| "Angular", "signals", "SSR" | angular-developer |
| "Spring Boot", "Java" | springboot-patterns |
| "C#", ".NET", "ASP.NET" | dotnet-patterns |
| "Rust", "Cargo" | rust-patterns |
| "Swift", "SwiftUI", "iOS" | swiftui-patterns |
| "Android", "Kotlin Multiplatform" | android-clean-architecture |
| "Kotlin", "coroutines" | kotlin-patterns |
| "Laravel", "PHP", "Eloquent" | laravel-patterns |
| "C++", "CMake" | cpp-coding-standards |
| "GitHub Actions", "issues", "PRs" | github-ops |
| "Jira", "tickets", "sprints" | jira-integration |
| "bug bounty", "CVE", "exploit" | security-bounty-hunter |
| "HIPAA", "PHI", "BAA" | hipaa-compliance |
| "healthcare", "patient data" | healthcare-phi-compliance |
| "lead gen", "outreach", "Apollo" | lead-intelligence |
| "market size", "competitors" | market-research |
| "pitch deck", "fundraising" | investor-materials |
| "cold email", "VC outreach" | investor-outreach |
| "blog post", "technical article" | article-writing |
| "brand voice", "style guide" | brand-voice |
| "social media", "LinkedIn", "X" | content-engine, crosspost |

## Project Context

This is the **Adaptive-Traffic-Signal-Timer** project:
- Python 3.13 + PyTorch + YOLOv8 + OpenCV
- Streamlit dashboard + Pygame simulation
- Edge deployment to Jetson Orin
- ML workflow: training → ONNX export → TensorRT → edge inference
