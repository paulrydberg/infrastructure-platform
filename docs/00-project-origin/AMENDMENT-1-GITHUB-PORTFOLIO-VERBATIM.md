# HERMES CTO — FOLLOW-UP SPECIFICATION (AMENDMENT 1)

> **CANONICAL VERBATIM RECORD — AMENDMENT 1**
> Received via Telegram 2026-09-24. This is an amendment to the master
> specification (`MASTER-SPEC-FULL.md`) and is additive to it — it does not
> replace, simplify, or discard the master spec.
> Telegram introduced a few mid-word line-wrap artifacts; these were rejoined
> (meaningful↔architectural, architect↔ure, enginee↔ring, unit↔s, wai↔nt).
> Section 44's diagram contains formatting damage from transport; it is
> preserved as received. No other edits were made.
> Prompt log: `../PROMPTS.md` · Roadmap status: `../ROADMAP-STATUS.md`

---

# Hermes CTO — Follow-Up Specification

GitHub Repository Architecture, Engineering Portfolio & Employment-Focused Project Structure

You have already received and are operating from the previously provided master specification for the Reproducible Cloud-Native Infrastructure & Autonomous Operations Platform.

This document is a follow-up architectural amendment to that specification.

Do not replace, simplify, or discard the existing master specification.

Instead, incorporate the requirements below into the existing project architecture, roadmap, documentation, Git strategy, repository strategy, GitHub Projects, implementation plan, testing strategy, reproducibility model, and final portfolio presentation.

The purpose of this amendment is to make the project serve two purposes simultaneously:

1. It must be a genuinely useful, technically sound infrastructure/platform engineering system.
2. It must deliberately produce a professional GitHub portfolio that demonstrates practical engineering capability to prospective employers.

The second objective must never be allowed to compromise the first.

The project must not become a portfolio façade.

The GitHub repositories, commits, issues, pull requests, projects, documentation, architecture decisions, incident reports, testing history, failure experiments, and reconstruction evidence should emerge from the actual engineering work being performed.

---

## 1. PRIMARY ADDITIONAL OBJECTIVE

Add the following objective to the project's formal goals:

«Build a professional, publicly demonstrable GitHub engineering portfolio that provides concrete evidence of infrastructure, cloud, Kubernetes, platform engineering, DevOps, SRE, security, observability, automation, incident response, disaster recovery, reproducibility, and AI-operations capabilities.»

The project should allow an employer or technical interviewer to inspect the work and understand:

- what was built
- why it was built
- how it was designed
- how it was implemented
- how it was tested
- how it failed
- how failures were diagnosed
- how failures were recovered
- how changes were reviewed
- how infrastructure was reproduced
- how security was enforced
- how deployments were controlled
- how automation was designed
- where AI is useful
- where AI is intentionally not used
- what tradeoffs were made
- what remains incomplete
- what the operator learned from the system

The resulting GitHub presence should demonstrate engineering process, not merely source code.

---

## 2. GITHUB IS PART OF THE SYSTEM'S ENGINEERING SURFACE

Treat GitHub as a first-class engineering system.

The architecture should explicitly account for:

- repositories
- branches
- commits
- pull requests
- issues
- discussions where useful
- GitHub Projects
- GitHub Actions
- releases
- tags
- changelogs
- CODEOWNERS
- branch protection
- security scanning
- dependency management
- documentation
- architecture decision records
- incident records
- experiments
- roadmap
- release history

GitHub must not merely contain the source code.

It should provide the externally visible engineering history of the platform.

The project should therefore maintain a clear relationship between:

Engineering Work
        ↓
Git
        ↓
GitHub Repository
        ↓
Issue / Project / ADR
        ↓
Pull Request
        ↓
CI
        ↓
Security / Policy Validation
        ↓
Artifact
        ↓
GitOps
        ↓
Deployment
        ↓
Observability
        ↓
Incident / Result
        ↓
Documentation
        ↓
Future Engineering Work

---

## 3. REPOSITORY ARCHITECTURE

The previous master specification contains logical project boundaries.

Now make the GitHub repository strategy explicit.

Do NOT automatically create a separate repository for every technology.

Repository boundaries must be based on legitimate engineering concerns such as:

- independent lifecycle
- independent deployment
- independent release cadence
- independent ownership
- security boundary
- access-control boundary
- reusable component
- infrastructure state boundary
- independently versioned artifact
- meaningful architectural boundary
- materially different operational responsibilities

Do NOT create repositories merely because:

- Kubernetes is separate from Helm
- Prometheus is separate from Grafana
- Terraform is a different technology
- Docker exists
- a component has a different programming language

Avoid "one repository per tool" architecture.

The CTO must evaluate the repository architecture as an engineering design decision.

---

## 4. INITIAL RECOMMENDED GITHUB REPOSITORY MODEL

Evaluate and, where justified, establish a repository structure approximately like this:

GitHub
│
├── infrastructure-platform
│
├── infrastructure-as-code
│
├── platform-engineering
│
├── operations-automation
│
├── observability-platform
│
├── security-platform
│
└── ai-operations

These are architectural candidates, not unconditional requirements.

The CTO must determine which repositories should actually exist based on project maturity and legitimate boundaries.

The flagship repository should remain:

infrastructure-platform

unless the CTO documents a stronger architectural reason to use another name.

The flagship repository should serve as the primary architectural reference point for the entire platform.

---

## 5. FLAGSHIP REPOSITORY

The flagship repository should contain or coordinate the core platform architecture.

Candidate structure:

infrastructure-platform/
├── bootstrap/
├── platform/
├── applications/
├── automation/
├── policies/
├── tests/
├── scripts/
├── docs/
├── diagrams/
├── .github/
└── README.md

The exact structure may evolve.

The repository should clearly explain how it relates to every other repository.

It should contain the top-level architecture and platform integration model.

---

## 6. INFRASTRUCTURE-AS-CODE REPOSITORY

Where justified, establish:

infrastructure-as-code

for infrastructure provisioning.

Potential responsibilities:

infrastructure-as-code/
├── terraform/
├── modules/
├── environments/
│   ├── local/
│   ├── development/
│   ├── staging/
│   └── production/
├── aws/
├── networking/
├── iam/
├── ecr/
├── eks/
├── storage/
├── documentation/
└── README.md

Use Terraform and/or OpenTofu according to the existing architectural decision.

This repository must clearly distinguish:

- infrastructure code
- infrastructure state
- secrets
- generated artifacts
- environment configuration

Never commit sensitive Terraform state or credentials.

The repository should demonstrate:

- modular IaC
- environment separation
- variable management
- provider pinning
- state strategy
- plan/apply workflow
- drift detection
- validation
- security
- cost awareness
- destruction/recreation procedures

---

## 7. PLATFORM ENGINEERING REPOSITORY

Evaluate whether Kubernetes/Helm/Argo CD/platform-specific components warrant an independently managed:

platform-engineering

repository.

Potential responsibilities:

platform-engineering/
├── helm/
├── argocd/
├── kubernetes/
├── operators/
├── networking/
├── storage/
├── policies/
├── environments/
├── tests/
└── docs/

The repository should demonstrate practical platform-engineering concepts rather than merely contain YAML.

Document:

- cluster bootstrap
- platform services
- Helm packaging
- Argo CD applications
- GitOps structure
- environment promotion
- secrets handling
- policy enforcement
- upgrades
- rollback
- failure recovery

---

## 8. OPERATIONS AUTOMATION REPOSITORY

Evaluate whether operational automation should become:

operations-automation

Potential areas:

operations-automation/
├── maintenance/
├── incident-response/
├── disaster-recovery/
├── reproducibility/
├── diagnostics/
├── backup/
├── restore/
├── health-checks/
├── validation/
└── docs/

This repository should demonstrate that infrastructure engineering includes the operational lifecycle after deployment.

Examples:

- maintenance automation
- update detection
- cleanup
- health checks
- incident collection
- diagnostic scripts
- backup verification
- restore testing
- disaster recovery
- reconstruction testing
- environment validation

Automation must remain deterministic wherever deterministic automation is appropriate.

---

## 9. OBSERVABILITY PLATFORM

Evaluate whether observability should eventually become:

observability-platform

Potential responsibilities:

- Prometheus
- Grafana
- Loki
- OpenTelemetry
- exporters
- dashboards
- alert rules
- recording rules
- log pipelines
- tracing
- SLO/SLA/SLI definitions
- observability tests
- alert validation

The repository should demonstrate that observability is engineered rather than simply installed.

Include evidence of:

- metrics
- logs
- traces
- dashboards
- alerting
- failure detection
- capacity monitoring
- resource monitoring
- AI task monitoring
- deployment monitoring
- reconstruction monitoring

---

## 10. SECURITY PLATFORM

Evaluate whether security deserves:

security-platform

Potential responsibilities:

- Trivy
- SBOM generation
- image scanning
- dependency scanning
- Kyverno
- admission policies
- image policy
- provenance
- signing
- Cosign
- secret-management strategy
- supply-chain security
- vulnerability workflows

Security enforcement must remain deterministic.

AI may assist with:

- analysis
- explanation
- prioritization
- remediation proposals
- migration work

AI must not become the final security authority.

Policy engines and deterministic validation must remain authoritative.

---

## 11. AI OPERATIONS REPOSITORY

Evaluate whether the AI subsystem should eventually become:

ai-operations

Potential structure:

ai-operations/
├── providers/
├── models/
├── queue/
├── resource-management/
├── workflows/
├── policies/
├── prompts/
├── validation/
├── observability/
└── docs/

The repository should demonstrate the project's distinctive AI architecture:

event
 ↓
classification
 ↓
deterministic handling
 ↓
reasoning required?
 ↓
AI queue
 ↓
resource evaluation
 ↓
provider/model selection
 ↓
inference
 ↓
proposal
 ↓
validation
 ↓
Git branch
 ↓
pull request
 ↓
CI
 ↓
policy
 ↓
staging
 ↓
authorization
 ↓
GitOps
 ↓
deployment
 ↓
observation

The AI repository must preserve the central architectural principle:

«AI is an optional reasoning subsystem, not a prerequisite for infrastructure operation.»

---

## 12. APPLICATION REPOSITORIES

Do not force every future application into the platform repository.

If the platform eventually hosts real applications, evaluate whether those applications should live in independent repositories.

For example:

application-a
application-b
application-c

The platform should demonstrate the ability to consume independently developed workloads through:

- CI/CD
- container images
- registries
- Helm
- GitOps
- environment promotion
- observability
- security policy

This provides evidence that the platform is actually a platform rather than merely a collection of infrastructure configuration.

---

## 13. REPOSITORY SOURCE-OF-TRUTH MATRIX

Create and maintain a document defining exactly which repository owns which system.

For example:

Domain| Repository| Source of Truth
Platform architecture| infrastructure-platform| Git
Cloud infrastructure| infrastructure-as-code| Git + IaC state
Kubernetes platform| platform-engineering| Git
Operations automation| operations-automation| Git
Observability| observability-platform| Git
Security policy| security-platform| Git
AI operations| ai-operations| Git
Applications| application repositories| Git

Do not blindly adopt this table.

The CTO must produce the actual architecture.

Document:

- owner
- source of truth
- deployment mechanism
- lifecycle
- dependencies
- release mechanism
- state
- secrets
- external dependencies
- reconstruction procedure

---

## 14. CROSS-REPOSITORY DEPENDENCIES

If multiple repositories are created, explicitly model their relationships.

Avoid circular dependencies.

Document:

Repository A
    ↓
Repository B
    ↓
Repository C

where appropriate.

Establish versioning rules for:

- Helm charts
- container images
- Terraform modules
- reusable scripts
- automation packages
- APIs
- platform contracts
- GitHub Actions
- shared libraries

Use immutable references where practical.

Prefer:

image@sha256:...

over:

image:latest

Prefer pinned versions
over floating versions.

---

## 15. PLATFORM RECONSTRUCTION ACROSS MULTIPLE REPOSITORIES

Extend the existing reproducibility architecture.

The platform must remain reconstructable even if its source is distributed across multiple GitHub repositories.

Create a:

Platform Reconstruction Manifest

that identifies:

- repository
- URL
- required branch/tag/commit
- version
- dependency
- purpose
- reconstruction order
- deployment mechanism
- required secrets
- required external services
- validation method

Conceptually:

Platform Reconstruction Manifest
│
├── infrastructure-platform
├── infrastructure-as-code
├── platform-engineering
├── operations-automation
├── observability-platform
├── security-platform
└── ai-operations

The exact repositories must reflect the actual final architecture.

A fresh machine should be able to determine what source repositories are required without relying on human memory.

---

## 16. GITHUB PROJECTS

GitHub Projects must become an explicit component of the engineering workflow.

Create meaningful projects as the architecture matures.

Potential project structure:

Infrastructure Platform
Infrastructure as Code
Platform Engineering
Observability
Security & Supply Chain
Operations & Reliability
Reproducibility & Disaster Recovery
AI Operations

Do not create empty portfolio projects simply to make the GitHub profile appear impressive.

Each project should represent actual engineering work.

Use:

- issues
- milestones
- epics
- tasks
- bugs
- incidents
- experiments
- technical debt
- architecture work
- security work
- operational improvements
- reconstruction work

where appropriate.

---

## 17. GITHUB PROJECT WORKFLOW

Where appropriate, demonstrate a professional workflow:

Idea
 ↓
Issue
 ↓
Project
 ↓
Design / ADR
 ↓
Implementation
 ↓
Branch
 ↓
Pull Request
 ↓
CI
 ↓
Review
 ↓
Merge
 ↓
Release
 ↓
Deployment
 ↓
Validation
 ↓
Documentation

For incidents:

Alert
 ↓
Incident
 ↓
Investigation
 ↓
Evidence
 ↓
Root Cause
 ↓
Remediation
 ↓
PR
 ↓
Validation
 ↓
Deployment
 ↓
Postmortem
 ↓
Follow-up Work

For AI-assisted changes:

Event
 ↓
AI Task
 ↓
Analysis
 ↓
Proposal
 ↓
Branch
 ↓
PR
 ↓
CI
 ↓
Security
 ↓
Policy
 ↓
Human/automated authorization
 ↓
Deployment

The GitHub history should naturally reflect these workflows.

---

## 18. GITHUB ACTIONS

Use GitHub Actions to demonstrate actual CI/CD engineering.

Where appropriate, pipelines should include:

checkout
 ↓
lint
 ↓
unit tests
 ↓
integration tests
 ↓
build
 ↓
container build
 ↓
SBOM
 ↓
Trivy
 ↓
policy validation
 ↓
artifact validation
 ↓
publish
 ↓
GitOps update

Do not add steps merely for resume keywords.

Each step must have a documented engineering purpose.

---

## 19. BRANCHING AND PULL REQUEST STRATEGY

Establish a documented Git strategy.

At minimum consider:

- protected main branch
- feature branches
- pull requests
- required CI
- required status checks
- meaningful commit messages
- CODEOWNERS where justified
- release tags
- changelog generation
- rollback strategy

AI-generated changes must not bypass the normal engineering workflow.

---

## 20. COMMIT HISTORY AS ENGINEERING EVIDENCE

Do not manufacture fake commit history.

Do not create meaningless commits solely to make the repository appear active.

Instead, preserve meaningful engineering evolution.

Examples:

feat: bootstrap local k3s environment
feat: add Helm platform chart
feat: introduce Argo CD GitOps deployment
feat: add Prometheus monitoring
fix: correct node resource alert threshold
feat: add Kyverno image policy
test: add reconstruction validation
fix: restore failed GitOps deployment
feat: add AI maintenance queue

Commit messages should describe actual work.

---

## 21. ARCHITECTURE DECISION RECORDS AS PORTFOLIO EVIDENCE

ADRs should explicitly document important engineering decisions.

Examples:

ADR-0001 — Project Foundation
ADR-0002 — Local Kubernetes Distribution
ADR-0003 — Helm Packaging Strategy
ADR-0004 — GitOps with Argo CD
ADR-0005 — Terraform/OpenTofu Strategy
ADR-0006 — Local-to-AWS Architecture
ADR-0007 — Observability Architecture
ADR-0008 — Security Policy Architecture
ADR-0009 — Deterministic-First AI Architecture
ADR-0010 — AI Resource Governance
ADR-0011 — Repository Architecture
ADR-0012 — Reproducibility Architecture
ADR-0013 — Disaster Recovery Strategy

Only create ADRs for real decisions.

Do not create documentation merely to increase document count.

---

## 22. EMPLOYMENT-ORIENTED ENGINEERING EVIDENCE

The project should intentionally produce evidence relevant to infrastructure and platform engineering positions.

Demonstrate practical capability in:

Linux

- system administration
- processes
- networking
- storage
- permissions
- resource management
- diagnostics

Containers

- Docker
- image construction
- image optimization
- registries
- image security
- lifecycle management

Kubernetes

- cluster management
- deployments
- services
- ingress
- configuration
- secrets
- resource limits
- health checks
- storage
- networking
- troubleshooting

Helm

- chart design
- values
- environments
- templating
- upgrades
- rollback

GitOps

- Argo CD
- desired state
- reconciliation
- drift
- promotion
- rollback

CI/CD

- GitHub Actions
- testing
- artifacts
- containers
- security
- deployment

Cloud

- AWS
- VPC
- IAM
- ECR
- EKS
- storage
- networking
- cost awareness

Infrastructure as Code

- Terraform/OpenTofu
- modules
- environments
- state
- drift
- reconstruction

Observability

- Prometheus
- Grafana
- Loki
- OpenTelemetry
- metrics
- logs
- traces
- alerting

Security

- Trivy
- Kyverno
- SBOM
- image signing
- provenance
- least privilege
- secrets
- admission control

Reliability

- failure testing
- rollback
- recovery
- backups
- disaster recovery
- incident response
- postmortems

Platform Engineering

- platform abstractions
- developer workflows
- standardized deployment
- self-service concepts
- environment consistency
- operational automation

AI Operations

- event-driven AI
- task queues
- model selection
- resource governance
- AI observability
- AI safety
- validation
- controlled autonomy

---

## 23. DO NOT OVERSTATE EXPERIENCE

This project is evidence of demonstrated capability.

It must never falsely imply:

- professional production experience that does not exist
- enterprise scale that has not been demonstrated
- AWS production experience if only a personal environment was used
- Kubernetes expertise beyond demonstrated capability
- SRE experience beyond actual operational exercises
- security certifications that were not earned
- operational maturity that was not tested

Documentation should distinguish:

Implemented
Tested
Experimented With
Designed
Planned
Not Yet Implemented

This distinction is critical.

---

## 24. ENGINEERING MATURITY LABELS

Each major subsystem should have an honest maturity indicator.

For example:

Design
Prototype
Experimental
Functional
Tested
Production-like
Operational
Continuously Validated

Do not use "production-ready" unless the project has actually demonstrated the criteria required to justify that claim.

---

## 25. RECRUITER / ENGINEER ENTRY POINT

The flagship GitHub repository README must serve two audiences:

Technical audience

An engineer should be able to understand:

- architecture
- code
- deployment
- infrastructure
- tests
- security
- observability
- failure recovery

Hiring audience

A recruiter or hiring manager should quickly understand:

- what the project demonstrates
- what technologies are used
- what engineering problems it solves
- what was actually implemented
- where the architecture is documented
- where they can inspect CI/CD
- where they can inspect infrastructure
- where they can inspect incident response
- where they can inspect reproducibility
- where they can inspect AI operations

Do not dumb the project down for recruiters.

Instead, provide a concise high-level entry point with links into the deeper technical material.

---

## 26. PORTFOLIO LANDING PAGE

Evaluate whether the GitHub profile should contain a concise portfolio-oriented landing README.

It should explain the engineering focus of the project without making unsupported claims.

Potential structure:

Infrastructure /
Cloud / Platform Engineering

Flagship Platform
Infrastructure as Code
Kubernetes / GitOps
Observability
Security
Operations Automation
AI Operations

Architecture
Reproducibility
Disaster Recovery
Engineering Documentation

Link to actual repositories and technical documentation.

Avoid marketing language that cannot be substantiated.

---

## 27. DEMONSTRATION SCENARIOS

The project should include reproducible demonstrations that an interviewer could understand.

Examples:

Scenario 1 — Deploy

Git commit
→ CI
→ container
→ registry
→ GitOps
→ Kubernetes
→ observability

Scenario 2 — Dependency Update

dependency update
→ detection
→ analysis
→ tests
→ security scan
→ PR
→ merge
→ deployment

Scenario 3 — Kubernetes Failure

failure
→ alert
→ diagnosis
→ remediation
→ validation
→ recovery

Scenario 4 — AI-Assisted Maintenance

event
→ deterministic analysis
→ AI escalation
→ queued inference
→ proposed change
→ PR
→ CI
→ policy
→ deployment

Scenario 5 — Complete Reconstruction

empty machine
→ bootstrap
→ infrastructure
→ Kubernetes
→ GitOps
→ platform
→ workloads
→ observability
→ security
→ validation

These demonstrations should be documented and reproducible.

---

## 28. PORTFOLIO DEMONSTRATION DOCUMENTATION

Create a dedicated documentation area for concise demonstrations.

For example:

docs/portfolio/
├── overview.md
├── architecture-walkthrough.md
├── ci-cd-demonstration.md
├── kubernetes-demonstration.md
├── gitops-demonstration.md
├── observability-demonstration.md
├── security-demonstration.md
├── incident-response-demonstration.md
├── disaster-recovery-demonstration.md
├── reproducibility-demonstration.md
├── ai-operations-demonstration.md
└── cloud-demonstration.md

These documents should link to deeper technical documentation.

---

## 29. GITHUB ISSUE TAXONOMY

Establish useful labels.

Potential categories:

area:infrastructure
area:kubernetes
area:helm
area:gitops
area:ci
area:observability
area:security
area:cloud
area:automation
area:ai
area:reproducibility
area:disaster-recovery

type:feature
type:bug
type:incident
type:experiment
type:documentation
type:technical-debt
type:security
type:maintenance

priority:low
priority:medium
priority:high
priority:critical

status:blocked
status:ready
status:in-progress
status:validation

Do not create excessive labels.

Use a small, coherent taxonomy.

---

## 30. GITHUB RELEASES

Where meaningful, use GitHub releases to mark major architectural milestones.

Examples:

v0.1.0 — Local Container Foundation
v0.2.0 — Kubernetes Platform
v0.3.0 — GitOps
v0.4.0 — Observability
v0.5.0 — Security
v0.6.0 — AWS Integration
v0.7.0 — Operations Automation
v0.8.0 — AI Operations
v0.9.0 — Reproducibility
v1.0.0 — Reproducible Platform Baseline

These are examples only.

Do not release versions simply because the roadmap says so.

Use versions when the implementation has reached a meaningful state.

---

## 31. GITHUB REPOSITORY SPLIT CRITERIA

The CTO must explicitly document when a subsystem should be extracted into its own repository.

Create a decision checklist:

Does it have an independent lifecycle?
Does it have an independent release cadence?
Does it have independent CI?
Does it have independent deployment?
Does it have independent access control?
Does it have reusable value?
Does it have a meaningful security boundary?
Does repository separation improve maintainability?
Does repository separation improve portfolio clarity?
Does repository separation improve reproducibility?
Does repository separation create unnecessary complexity?

Only split when the net engineering value is positive.

---

## 32. MONOREPO VS MULTI-REPO DECISION

Document the decision explicitly.

Evaluate:

Monorepo advantages

- easier global changes
- simpler dependency management
- easier reconstruction
- centralized documentation
- atomic changes
- simpler early development

Multi-repo advantages

- clearer boundaries
- independent lifecycle
- independent CI/CD
- independent permissions
- clearer portfolio presentation
- reusable components
- realistic organizational modeling

The CTO must choose an architecture based on actual project needs.

The goal is not "maximum number of repositories."

The goal is:

«A repository architecture that is technically coherent and professionally demonstrable.»

---

## 33. REPRODUCIBILITY MUST SURVIVE REPOSITORY SEPARATION

If multiple repositories exist, the platform must still be reconstructable.

A fresh environment must be able to determine:

which repositories are required
which versions are required
which commit/tag is authoritative
what order they are reconstructed in
what dependencies exist
what secrets are required
what external services are required
how success is validated

Do not allow multi-repository architecture to create undocumented manual dependency chains.

---

## 34. GITHUB AS A RECONSTRUCTION SOURCE

GitHub repositories must be considered external source dependencies in the reproducibility model.

The reconstruction documentation must define:

- repository URLs
- required references
- authentication requirements
- release/tag strategy
- expected artifacts
- dependency relationships
- failure behavior if GitHub is unavailable

Where appropriate, support cached or mirrored artifacts so that temporary GitHub outages do not make the running infrastructure unusable.

---

## 35. PORTFOLIO QUALITY GATE

Before declaring the project portfolio-ready, validate:

Repository quality

- professional names
- coherent README files
- architecture documentation
- reproducible setup
- meaningful CI
- security scanning
- tests
- issue history
- PR history
- release history

Engineering quality

- deterministic operation
- reproducibility
- observability
- security
- rollback
- failure handling
- disaster recovery

Documentation quality

- ADRs
- runbooks
- incidents
- experiments
- architecture diagrams
- reconstruction documentation
- troubleshooting

Portfolio quality

An external engineer should be able to inspect the project and identify evidence of:

- Linux
- Docker
- Kubernetes
- Helm
- GitOps
- GitHub Actions
- Terraform/OpenTofu
- AWS
- observability
- security
- automation
- incident response
- disaster recovery
- platform engineering
- AI operations

---

## 36. INTERVIEW-READY ENGINEERING STORIES

The project should naturally produce several interview-quality engineering stories.

Examples:

"Tell me about something you built."

Answer should be supported by the flagship platform.

"Tell me about a production-like failure."

Use a documented failure experiment or incident.

"How did you handle infrastructure drift?"

Use GitOps/IaC drift detection.

"How do you deploy safely?"

Use CI → security → policy → GitOps → observability.

"How do you recover from a destroyed environment?"

Use reproducibility and disaster recovery.

"Where does AI fit into your architecture?"

Explain deterministic-first, event-driven, resource-aware AI.

"What happens if the AI system fails?"

Demonstrate zero-inference operation.

"How do you know your infrastructure is reproducible?"

Demonstrate reconstruction testing.

"How do you secure the supply chain?"

Demonstrate scanning, SBOM, policy, signing/provenance where implemented.

The CTO should create documentation and demonstrations that make these answers truthful and technically defensible.

---

## 37. DO NOT BUILD FOR RESUME KEYWORDS

This requirement is critical.

Do not add:

- Kubernetes
- AWS
- Terraform
- Prometheus
- AI
- Argo CD
- Kyverno
- OpenTelemetry
- GitHub Actions

simply because they look good on a resume.

Each technology must have an architectural purpose.

For every major technology, document:

Why does it exist?
What problem does it solve?
What alternatives were considered?
What does it cost?
What operational burden does it introduce?
How is it tested?
How is it recovered?
How does it contribute to the platform?

This turns the project from a keyword collection into an engineering system.

---

## 38. PORTFOLIO OPTIMIZATION WITHOUT ARCHITECTURAL COMPROMISE

The project should intentionally maximize the amount of real engineering evidence produced by the work.

Prefer tasks that simultaneously improve the platform and demonstrate engineering capability.

For example:

Implement backup verification

demonstrates:

- automation
- reliability
- storage
- testing
- DR
- operational engineering

Rather than creating artificial projects such as:

Create a random Terraform example

Prefer integrated engineering work.

---

## 39. REALISTIC SCALE

Do not pretend the Mac Mini is an enterprise datacenter.

Instead, demonstrate engineering principles at a scale that can be honestly operated.

Document:

- hardware constraints
- CPU
- RAM
- storage
- network
- workload capacity
- limitations
- resource pressure
- scaling boundaries

Then demonstrate how the architecture could translate to AWS.

This is more credible than pretending a home system has enterprise-scale capacity.

---

## 40. LOCAL → CLOUD PORTFOLIO STORY

The final architecture should provide a clear engineering progression:

Mac Mini
   ↓
Docker
   ↓
k3s
   ↓
Helm
   ↓
Argo CD
   ↓
Observability
   ↓
Security
   ↓
Automation
   ↓
Reproducibility
   ↓
AWS
   ↓
VPC
   ↓
ECR
   ↓
EKS
   ↓
Cloud deployment

The implementation should demonstrate which pieces are portable and which are environment-specific.

Document the differences between:

Local Environment

and:

AWS Environment

without pretending they are identical.

---

## 41. EMPLOYMENT TARGETS

The project should be designed to provide evidence relevant to roles such as:

- Cloud Support Engineer
- Cloud Operations Engineer
- Infrastructure Support Engineer
- Linux Systems Administrator
- Systems Administrator
- Technical Operations Engineer
- Junior Cloud Engineer
- Cloud Engineer
- Junior DevOps Engineer
- DevOps Engineer
- Infrastructure Engineer
- Infrastructure Automation Engineer
- Platform Engineer
- Cloud Infrastructure Engineer
- Kubernetes / Container Engineer
- Junior SRE
- DevSecOps Engineer
- Release / Build Engineer

Do not claim that the project qualifies the user for any particular role.

Instead, ensure the project produces demonstrable evidence relevant to these categories.

---

## 42. JOB-SEARCH FEEDBACK LOOP

The platform architecture should be periodically evaluated against real job descriptions.

This should not cause arbitrary technology accumulation.

Instead:

Job-market observation
        ↓
Identify recurring engineering requirements
        ↓
Compare against demonstrated capability
        ↓
Identify meaningful gap
        ↓
Evaluate whether gap belongs in project
        ↓
ADR if significant
        ↓
Implement if justified
        ↓
Document evidence

Do not add technology solely because one job posting mentions it.

Look for recurring requirements across relevant infrastructure/platform/cloud roles.

---

## 43. PORTFOLIO GAP ANALYSIS

Create a periodic portfolio gap report.

Evaluate:

Capability
Evidence
Implementation Status
Test Status
Documentation Status
Portfolio Visibility
Remaining Gap

Example:

Capability| Evidence| Tested| Documented| Portfolio Visible
Kubernetes| k3s platform| Yes/No| Yes/No| Yes/No
GitOps| Argo CD| Yes/No| Yes/No| Yes/No
IaC| Terraform| Yes/No| Yes/No| Yes/No
AWS| EKS/VPC/ECR| Yes/No| Yes/No| Yes/No
Observability| Prometheus/Grafana/Loki| Yes/No| Yes/No| Yes/No
Security| Trivy/Kyverno| Yes/No| Yes/No| Yes/No
DR| Reconstruction| Yes/No| Yes/No| Yes/No
AI Operations| AI queue/workflows| Yes/No| Yes/No| Yes/No

The actual report must reflect reality.

---

## 44. FINAL PORTFOLIO ARCHITECTURE

The intended end state should resemble:

                         GitHub
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     Repositories      Projects          Actions
          │                │                │
          └────────────────┼────────────────┘
                           │
                    Platform Source
                       of Truth
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
       IaC              GitOps             Apps
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                      Kubernetes
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Observability       Security          Automation
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    AI Operations
                           │
                    Resource-Aware
                     Event-Driven
                         AI
                           │
                 ┌─────────┴─────────┐
                 │                   │
            Local Mac Mini          AWS
                 │                   │
                 └─────────┬─────────┘
                           │
                    Reproducibility
                           │
                    Reconstruction
                           │
                     Validation

The exact implementation may differ.

The architectural principles must remain.

---

## 45. REQUIRED DOCUMENTATION ADDITIONS

Extend the existing documentation tree with:

docs/
├── portfolio/
│   ├── overview.md
│   ├── architecture-walkthrough.md
│   ├── ci-cd-demonstration.md
│   ├── kubernetes-demonstration.md
│   ├── gitops-demonstration.md
│   ├── observability-demonstration.md
│   ├── security-demonstration.md
│   ├── incident-response-demonstration.md
│   ├── disaster-recovery-demonstration.md
│   ├── reproducibility-demonstration.md
│   ├── ai-operations-demonstration.md
│   └── cloud-demonstration.md
│
├── architecture/
│   ├── github-repository-architecture.md
│   ├── repository-source-of-truth.md
│   ├── cross-repository-dependencies.md
│   └── github-project-strategy.md
│
└── career-evidence/
    ├── capability-matrix.md
    ├── portfolio-gap-analysis.md
    └── engineering-evidence.md

Only create documents that have meaningful content.

---

## 46. REQUIRED ADR

Create:

docs/decisions/ADR-0011-repository-architecture.md

or the next available ADR number if the existing ADR sequence has advanced.

The ADR must evaluate:

- monorepo
- multi-repo
- hybrid architecture
- repository boundaries
- GitHub Projects
- cross-repository dependencies
- reproducibility
- security boundaries
- portfolio considerations
- operational complexity

The final decision must be based on engineering reasoning.

---

## 47. REQUIRED CTO ACTIONS

After reading this amendment, do not merely acknowledge it.

Perform an architectural assessment of the existing project.

Determine:

1. Which repository architecture currently exists.
2. Which repository architecture the master specification implies.
3. Which additional repositories are actually justified.
4. Which systems should remain in the flagship repository.
5. Which systems should eventually be extracted.
6. What GitHub Projects should exist.
7. What GitHub Actions belong in each repository.
8. What the cross-repository dependency graph should be.
9. How reproducibility works across repositories.
10. How the repository architecture supports the employment/portfolio objective without compromising engineering quality.

Document these findings.

---

## 48. DO NOT DESTROY EXISTING WORK

This amendment must be additive.

Do not:

- rewrite working infrastructure unnecessarily
- reorganize repositories purely for aesthetics
- migrate code merely to make the GitHub structure look impressive
- discard existing documentation
- rewrite project history
- create fake commits
- create fake incidents
- create fake issues
- claim tests that were not executed
- claim AWS deployments that were not performed
- claim production experience
- claim reproducibility that has not been demonstrated

Preserve history.

If restructuring becomes justified, perform it as a documented engineering migration.

---

## 49. REPOSITORY MIGRATION RULE

If the existing project is currently in one repository, do not immediately split it.

First:

1. inventory the current repository
2. map components
3. identify lifecycle boundaries
4. identify dependencies
5. identify state
6. identify security boundaries
7. identify deployment units
8. identify CI boundaries
9. identify reproducibility implications
10. evaluate portfolio implications
11. produce an ADR
12. decide whether to split
13. migrate only if justified
14. validate the resulting architecture
15. update reconstruction manifests
16. update documentation

The repository architecture must be earned by engineering requirements.

---

## 50. PORTFOLIO-FIRST DOES NOT MEAN PORTFOLIO-ONLY

The hierarchy of priorities is:

1. Correctness
2. Reliability
3. Security
4. Reproducibility
5. Maintainability
6. Operational usefulness
7. Architectural clarity
8. Documentation
9. Portfolio visibility

Portfolio value is important, but it must not override the engineering system.

A technically honest, well-tested project is more valuable than a visually impressive but artificial portfolio.

---

## 51. FINAL SUCCESS CRITERIA

The project should eventually satisfy the following:

Engineering

- infrastructure works
- platform works
- deployments work
- observability works
- security controls work
- automation works
- failures can be diagnosed
- failures can be recovered
- infrastructure can be reconstructed
- AI is optional

GitHub

- repositories have clear responsibilities
- repositories have professional READMEs
- Git history reflects real engineering
- issues represent actual work
- pull requests document meaningful changes
- GitHub Projects represent real engineering planning
- CI/CD is functional
- security checks are functional
- releases represent real milestones

Reproducibility

- source of truth is explicit
- dependencies are explicit
- versions are pinned where appropriate
- reconstruction order is explicit
- external dependencies are documented
- secrets requirements are documented
- reconstruction is tested
- deviations are reported

Portfolio

An external technical reviewer should be able to inspect the GitHub presence and reasonably conclude that the project provides concrete evidence of practical work involving:

- Linux
- containers
- Kubernetes
- Helm
- GitOps
- CI/CD
- Terraform/OpenTofu
- AWS
- observability
- security
- automation
- reliability
- disaster recovery
- platform engineering
- AI-assisted operations

without the documentation making unsupported claims.

---

## 52. FINAL ARCHITECTURAL PRINCIPLE

Add this principle to the project's architectural north star:

«The GitHub presence is not a marketing layer placed on top of the platform. It is the externally visible engineering record of the platform.»

The platform should therefore make its engineering quality observable through:

Code
+
Infrastructure
+
Configuration
+
Tests
+
CI/CD
+
GitOps
+
Security
+
Observability
+
Incidents
+
Recovery
+
Reconstruction
+
Architecture Decisions
+
Issues
+
Pull Requests
+
Releases
+
GitHub Projects
+
Documentation

The ultimate objective is to build a system that can be examined by a technically competent employer and understood as a serious engineering project.

The project should demonstrate not merely:

«I know these technologies.»

It should demonstrate:

«I can design, build, operate, troubleshoot, secure, recover, reproduce, document, and continuously improve a complex infrastructure platform.»

The project should remain honest about its scale, limitations, maturity, and lack of production history where applicable.

Do not optimize for the appearance of expertise.

Optimize for demonstrable engineering capability.

---

## 53. IMMEDIATE NEXT STEP

After incorporating this amendment:

1. Inspect the existing project state.
2. Inspect the current repository structure.
3. Inspect the current Git history.
4. Inspect existing documentation.
5. Inspect existing GitHub-related configuration.
6. Compare the current state against this amendment.
7. Produce a GitHub Portfolio & Repository Architecture Gap Analysis.
8. Produce the repository-boundary recommendation.
9. Produce the GitHub Projects recommendation.
10. Produce the cross-repository dependency model.
11. Produce the updated reconstruction/source-of-truth model.
12. Identify which changes should be made now.
13. Identify which changes should wait until later project phases.
14. Create or update the relevant ADRs.
15. Update the roadmap accordingly.
16. Do not perform large migrations merely for cosmetic reasons.
17. Do not claim anything has been implemented until it has actually been implemented and validated.

The result should integrate naturally with the previously established master specification rather than becoming a parallel architecture.

The final system should be both:

a real reproducible infrastructure/platform engineering system

and

a credible, technically inspectable GitHub engineering portfolio.
