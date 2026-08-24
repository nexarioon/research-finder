# Research Prospect Finder — Agent Prompts Per Phase

## Global Agent Rules

You are implementing **Research Prospect Finder**, a Python CLI-first personal tool for discovering established local businesses that may become research/skripsi objects.

Rules:
- Follow the existing project architecture and preserve separation between CLI, application services, domain logic, providers, database, and infrastructure services.
- Do not put business logic directly inside CLI screens.
- Prefer deterministic rules over AI.
- AI must be optional and never required for core discovery/filtering.
- Never treat AI guesses about a business as verified facts. Phrase them as hypotheses to validate.
- Use public business information and normal provider access only. Do not bypass authentication or access private/non-public data.
- Add caching, rate limiting, retries, and clear provider failure handling where external services are involved.
- Do not send outreach automatically without explicit user approval in the MVP.
- Keep the code ready for a future FastAPI/web interface by keeping core/application services independent from CLI.
- Use small, focused changes and avoid unnecessary dependencies.
- Run existing validation after each phase: tests, lint/type checks if configured, and a build/import smoke test.
- Do not push changes to a remote repository unless explicitly asked.
- At the end of each phase, report: files changed, features completed, validation performed, remaining issues, and suggested next phase.

---

## Phase 1 — Foundation

### Prompt

Implement Phase 1 of Research Prospect Finder.

Goal:
Create the foundational Python CLI application with a clean architecture that can later support a web interface.

Requirements:
- Initialize a modern Python project using pyproject.toml.
- Create the package structure for cli, application, domain, providers, database, services, and config.
- Implement an interactive CLI entry point.
- Add a polished terminal UI using Rich and an interactive prompt library where appropriate.
- Create the main navigation:
  1. Discover Businesses
  2. Saved Businesses
  3. Analyze Prospects
  4. Research Opportunities
  5. Research Topics
  6. Outreach
  7. Dashboard
  8. Settings
  9. Exit
- Implement SQLite connection and basic SQLAlchemy setup.
- Add configuration loading and .env.example.
- Add structured logging.
- Add a health/smoke command or equivalent startup validation.
- Keep all business logic outside CLI presentation code.

Do not implement external business search or AI yet.

Acceptance criteria:
- `research-finder` launches successfully.
- Interactive navigation works.
- SQLite initializes correctly.
- Project imports cleanly.
- Architecture is ready for the next phase.

---

## Phase 2 — Business Discovery

### Prompt

Implement Phase 2: Business Discovery.

Requirements:
- Add a provider abstraction for business/location search.
- Implement location selection: current location if available, address, or coordinates.
- Implement radius selection.
- Implement category multi-select.
- Implement configurable filters:
  - minimum rating
  - minimum review count
  - local-business preference
  - franchise preference
  - online-presence preference
- Implement provider response normalization into the domain Business model.
- Implement deduplication.
- Persist discovered businesses to SQLite.
- Add interactive result table with selection/details/save actions.
- Add progress indicators and graceful provider errors.
- Add caching where practical to avoid repeating identical discovery requests.
- Do not use AI in this phase.

Acceptance criteria:
- User can discover businesses and save them.
- Duplicate businesses are not repeatedly inserted.
- Provider errors do not corrupt the database.
- Discovery remains usable with AI disabled.

---

## Phase 3 — Ranking & Candidate Scoring

### Prompt

Implement Phase 3: deterministic candidate scoring and ranking.

Requirements:
- Create a configurable scoring service.
- Default factors:
  - business size signal: 25%
  - online presence: 15%
  - customer/review signal: 15%
  - operational complexity: 20%
  - research accessibility: 15%
  - contact availability: 10%
- Normalize scores to 0–100.
- Store score breakdowns in the database.
- Add candidate ranking.
- Add filters for score thresholds.
- Add an interactive candidate table showing score and major signals.
- Allow selecting a limited number of top candidates for later AI analysis.
- Make clear that review count is only a proxy/signal, not proof of company size.

Do not use AI.

Acceptance criteria:
- Every qualified candidate can receive a deterministic score.
- Score components are inspectable.
- User can select top candidates.
- Scores are reproducible.

---

## Phase 4 — Website & Online Presence Analysis

### Prompt

Implement Phase 4: public website and online-presence analysis.

Requirements:
- Add a website provider/service using normal HTTP requests.
- Extract, when publicly available:
  - page title
  - meta description
  - visible service/product signals
  - contact details
  - forms
  - booking/order signals
  - customer portal signals
  - e-commerce signals
  - social links
  - basic technology indicators
- Add timeouts, retries, rate limiting, and caching.
- Store normalized website analysis data.
- If a website cannot be accessed, preserve the business record and mark the website analysis as unavailable.
- Do not bypass robots/authentication/access controls.
- Do not use AI yet.
- Add a human-readable CLI audit screen.

Acceptance criteria:
- Website audits work for normal public websites.
- Failed websites do not break discovery.
- Results are cached.
- No AI calls occur.

---

## Phase 5 — Minimal AI Analysis

### Prompt

Implement Phase 5: optional, token-efficient AI analysis.

Requirements:
- Create an AI provider abstraction.
- Support an OpenAI-compatible API configuration so providers such as 9Router can be used.
- Add model/base URL/API key configuration through environment variables.
- Add an explicit AI-disabled mode.
- Add a configurable maximum number of AI analyses per run/day.
- Only analyze businesses selected by the user or businesses that pass the deterministic candidate threshold.
- Combine all reasoning into ONE AI request per business.
- The request must produce:
  1. potential operational problems
  2. information-system opportunities
  3. research relevance
  4. 3–5 research topic candidates
  5. validation questions for the business owner
- Store the AI result in SQLite.
- Create an input/data hash and reuse cached analysis when the business data has not materially changed.
- Add `--reanalyze` or equivalent to force a new analysis.
- Ensure prompts explicitly instruct the model not to state unverified assumptions as facts.
- If AI fails, preserve all existing data and allow retry.

Acceptance criteria:
- Core discovery works with AI disabled.
- AI can analyze a selected candidate.
- One request returns all required analysis sections.
- Cached candidates do not consume another AI call.
- Daily/run limits are enforced.

---

## Phase 6 — Research Opportunities & Topics

### Prompt

Implement Phase 6: research opportunity and topic management.

Requirements:
- Create domain models for research opportunities and research topics.
- Present AI findings as hypotheses requiring validation.
- Add interactive screens for:
  - opportunities by business
  - opportunities by category
  - topic candidates
  - validation questions
- Allow user to save/favorite promising topics.
- Each topic should store:
  - title
  - problem statement
  - proposed system
  - target users
  - scope
  - validation questions
  - source business
  - AI analysis reference
- Allow exporting selected topics to Markdown.
- Do not regenerate AI output unnecessarily.

Acceptance criteria:
- User can move from a business → opportunity → topic.
- Topics remain linked to the source business and analysis.
- User can edit/save/delete local notes without AI calls.

---

## Phase 7 — Outreach

### Prompt

Implement Phase 7: respectful business outreach.

Requirements:
- Add public business contact handling.
- Add email draft model and outreach event history.
- Implement deterministic email templates first.
- AI personalization must be optional.
- Email must focus on requesting research participation/interview, not pretending that an unverified business problem is known.
- Add preview/edit/save/send workflow.
- Require explicit user approval before sending.
- Track:
  NOT_CONTACTED, DRAFT, READY, SENT, DELIVERED, REPLIED, INTERESTED, DECLINED, NO_RESPONSE, DO_NOT_CONTACT.
- Add a do-not-contact state that prevents further outreach.
- Add provider abstraction for SMTP/Gmail or another configured email provider.
- Add rate limiting and retry handling.
- Never expose credentials in logs.
- Do not implement mass automatic sending.

Acceptance criteria:
- User can create, review, edit, and explicitly send an email.
- Outreach history is persisted.
- Do-not-contact prevents sending.
- Provider errors do not lose drafts.

---

## Phase 8 — Dashboard, Export & Polish

### Prompt

Implement Phase 8: final MVP polish.

Requirements:
- Add CLI dashboard with:
  discovered businesses
  qualified businesses
  saved candidates
  AI analyzed
  research opportunities
  topics
  sent emails
  replies
  interested
  no response
- Add CSV, JSON, and Markdown exports.
- Add database backup command.
- Improve loading/progress states.
- Improve error messages and retry flows.
- Add structured logs.
- Review caching and rate limiting.
- Add configuration screens.
- Add an AI budget screen showing configured limit and remaining budget.
- Add comprehensive smoke tests for the main user journey.
- Ensure the application remains fully usable without AI.
- Review architecture for future FastAPI integration.

Acceptance criteria:
- Complete end-to-end flow works from discovery to outreach.
- Data can be exported and backed up.
- AI usage is visible and controlled.
- No core feature depends on AI.
- CLI code remains an adapter around application/domain services.

---

## Phase 9 — Future Web Preparation (Do Not Build Full Web Yet)

### Prompt

Review the completed CLI application specifically for future web migration.

Do not build the web frontend yet.

Requirements:
- Identify any business logic still coupled to CLI code.
- Move reusable logic into application/domain services where necessary.
- Ensure provider interfaces are clean.
- Ensure database repositories can be called independently from CLI.
- Define the future FastAPI service boundaries without implementing the API.
- Document which services can be reused by a future web application.
- Produce a short architecture report with:
  - current architecture
  - coupling problems
  - recommended service boundaries
  - future FastAPI endpoints
  - future authentication considerations
  - future background jobs
  - migration risks

Do not make unnecessary rewrites.

---

## End-to-End Validation Prompt

After all phases are complete, run a full validation of the application.

Test this journey:

1. Launch CLI.
2. Discover businesses.
3. Apply established-business filters.
4. Save candidates.
5. Rank candidates.
6. Analyze only a selected small subset.
7. Verify AI caching.
8. Generate research opportunities.
9. Generate/save topic candidates.
10. Draft an outreach email.
11. Review/edit it.
12. Send only after explicit confirmation.
13. Verify outreach history.
14. Export results.
15. Run the same flow with AI disabled.

Report:
- Passed steps
- Failed steps
- Bugs
- Architecture issues
- Token-saving opportunities
- Security/privacy concerns
- Recommended fixes

Do not push changes.
