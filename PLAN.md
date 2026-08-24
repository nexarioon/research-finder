# Coding Plan: Modern Interactive CLI

## 1. Requirements

Transform the existing Research Prospect Finder CLI from a basic `input()`-menu loop into a modern, keyboard-driven, interactive terminal application. The CLI should feel like a polished developer tool (GitHub CLI, Vercel CLI, Linear CLI quality).

Key requirements:
- Interactive dashboard with live stats on launch
- Keyboard-driven navigation (arrow keys, enter, escape)
- Command mode for scripting/automation (`research-finder scan`, `research-finder results`, etc.)
- Reusable UI components (panels, tables, selects, progress, confirmations)
- Consistent visual language (accent color, muted text, status indicators)
- Proper error handling with actionable messages
- Empty states for every screen
- Progress indicators for long-running operations
- Non-interactive/JSON output mode (`--json` flags)
- Contextual help (`?` key, `--help` flags)
- First-time setup wizard

## 2. Existing Architecture

### Current CLI Flow
- `CLI` class in `cli/main.py` runs async main loop
- 8 screens loaded lazily: Discover, Saved, Analyze, Opportunities, Topics, Outreach, Dashboard, Settings
- Each screen uses `input()` for user interaction
- Rich used for panels, tables, spinners (but not interactive)

### Existing Business Logic (DO NOT REWRITE)
- `application/` - DiscoveryService, RankingService, AIAnalysisService
- `providers/` - NominatimProvider, WebsiteAnalyzer, email, location
- `services/` - scoring engine, email templates
- `database/` - SQLAlchemy async repos (6+ repository classes)
- `domain/models.py` - dataclasses and enums
- `config/settings.py` - Pydantic Settings

### Existing Dependencies (already in pyproject.toml)
- `rich>=13.0` - Terminal rendering
- `questionary>=2.0` - Interactive prompts (currently unused, key dependency)
- `textual>=0.82` - TUI framework (unused, keep for future)

### What to Reuse
- ALL business logic services and repositories
- Database models and connection layer
- Domain models and enums
- Configuration system
- Email templates
- Scoring engine

## 3. Scope

### In Scope
- New CLI shell with interactive navigation
- Reusable UI component library
- Dashboard with live stats
- Command-line argument parsing (interactive + command modes)
- Refactored screens using new UI components
- Keyboard-driven selection menus
- Progress indicators for all async operations
- Error handling UX
- Empty states
- Non-interactive output modes (--json, --csv)
- Contextual help
- Version display

### Out of Scope
- TUI mode (textual-based) - future work
- Web API - future work
- Business logic changes
- Database schema changes
- New features beyond CLI UX
- Comprehensive test suite (no tests exist currently)

## 4. Files

### Files to Create
```
src/research_finder/cli/
├── __init__.py                    # (modify) expose main entry
├── main.py                        # (rewrite) argument parsing + mode routing
├── shell.py                       # (create) interactive shell with navigation
├── components/
│   ├── __init__.py                # (create) component exports
│   ├── header.py                  # (create) app header/banner
│   ├── panel.py                   # (create) styled panels
│   ├── table.py                   # (create) responsive tables
│   ├── select.py                  # (create) keyboard-driven select
│   ├── multiselect.py             # (create) multi-select with checkboxes
│   ├── confirm.py                 # (create) confirmation prompts
│   ├── progress.py                # (create) progress bars/spinners
│   ├── empty_state.py             # (create) empty state displays
│   ├── error_state.py             # (create) error displays
│   ├── status.py                  # (create) status indicators
│   └── shortcuts.py               # (create) keyboard shortcut bar
├── screens/
│   ├── __init__.py                # (modify) add new exports
│   ├── dashboard.py               # (rewrite) interactive dashboard
│   ├── discover.py                # (rewrite) interactive discovery
│   ├── saved.py                   # (rewrite) browsable saved list
│   ├── analyze.py                 # (rewrite) interactive analysis
│   ├── opportunities.py           # (rewrite) browsable opportunities
│   ├── topics.py                  # (rewrite) browsable topics
│   ├── outreach.py                # (rewrite) interactive outreach
│   ├── export.py                  # (rewrite) interactive export
│   ├── settings.py                # (rewrite) settings view
│   └── website_audit.py           # (rewrite) interactive audit
└── utils.py                       # (create) shared CLI utilities
```

### Files NOT Modified (Business Logic)
- `application/*` - all services
- `providers/*` - all providers
- `services/*` - scoring, email templates
- `database/*` - all models and repos
- `domain/*` - domain models
- `config/*` - settings, logging

## 5. Components

### Core UI Components
1. **Header** - App banner with version, tagline
2. **Panel** - Styled bordered panels (consistent borders, padding)
3. **Table** - Responsive tables with truncation, alignment
4. **Select** - Arrow-key driven single selection
5. **MultiSelect** - Checkbox multi-selection
6. **Confirm** - Yes/no confirmation prompts
7. **Progress** - Spinners, progress bars, step indicators
8. **EmptyState** - Meaningful empty state messages with actions
9. **ErrorState** - User-friendly error displays
10. **Status** - Status indicators (success, warning, error, info)
11. **Shortcuts** - Bottom keyboard shortcut bar

### Shell
- Interactive navigation loop
- Screen state management
- Back/forward navigation
- Global keyboard shortcuts (q, ?, Esc)

## 6. APIs

### CLI Entry Points
```bash
# Interactive mode
research-finder                    # Launch interactive dashboard

# Command mode
research-finder scan               # Discover businesses
research-finder results            # Browse saved businesses
research-finder analyze            # Score and rank candidates
research-finder opportunities      # Browse research opportunities
research-finder topics             # Manage research topics
research-finder outreach           # Manage outreach
research-finder export             # Export data
research-finder config             # View settings

# Output modes
research-finder results --json     # JSON output
research-finder results --csv      # CSV output
research-finder export --format json

# Help
research-finder --help
research-finder scan --help
```

## 7. State Management

### Shell State
```python
class ShellState:
    current_screen: str        # Current screen name
    screen_stack: list[str]    # Navigation history for back
    is_interactive: bool       # Interactive vs command mode
    json_output: bool          # --json flag
```

### Screen State
Each screen manages its own local state:
- Selected items
- Filter state
- Pagination position
- Search query

## 8. Risks

1. **Questionary compatibility** - questionary prompts may not compose well with Rich Live display. Mitigation: use questionary for simple prompts, custom Rich-based selects for complex ones.

2. **Terminal width responsiveness** - Tables may break on narrow terminals. Mitigation: truncate intelligently, adapt column count.

3. **Async/sync mixing** - questionary is sync, Rich is sync, business logic is async. Mitigation: use asyncio.run_in_executor for questionary, keep async for business logic.

4. **Breaking existing commands** - Command mode must preserve backward compatibility. Mitigation: test all command variants.

## 9. Phase Breakdown

### Phase 1: CLI Shell & Argument Parsing
**Objective:** Create the new entry point with argument parsing and mode routing.
- Create `cli/main.py` with argparse
- Create `cli/shell.py` with interactive loop
- Support `research-finder` (interactive) and `research-finder <command>` (command mode)
- Add `--help`, `--version`, `--json` flags

**Test:** `research-finder --help` works, `research-finder` launches shell, `research-finder results` routes correctly.

### Phase 2: UI Component Library
**Objective:** Build reusable CLI components.
- Create `cli/components/` with all components
- Header, Panel, Table, Select, Confirm, Progress, EmptyState, ErrorState, Status, Shortcuts
- Each component uses Rich for rendering
- Select/Confirm use questionary for keyboard input

**Test:** Each component renders correctly in isolation.

### Phase 3: Dashboard
**Objective:** Create the interactive home screen.
- Rewrite `dashboard.py` with live stats
- Show pipeline overview (discovered, qualified, analyzed, etc.)
- Show recent activity
- Keyboard-driven quick actions
- Status bar with version and shortcuts

**Test:** Dashboard shows correct stats, navigation works.

### Phase 4: Core Screens Refactor
**Objective:** Refactor all screens to use new components.
- Refactor Discover, Saved, Analyze screens
- Use Select for menu choices
- Use Table for data display
- Use Progress for long operations
- Add empty states

**Test:** Each screen works with keyboard navigation.

### Phase 5: Secondary Screens Refactor
**Objective:** Refactor remaining screens.
- Refactor Opportunities, Topics, Outreach, Export, Settings, WebsiteAudit
- Consistent patterns across all screens

**Test:** All screens functional with new UI.

### Phase 6: Command Mode & Non-Interactive
**Objective:** Ensure command mode works without interaction.
- `research-finder results --json` outputs JSON
- `research-finder export --format csv` works
- All commands have `--help`

**Test:** Command mode produces correct output, no interactive prompts in command mode.

### Phase 7: Polish & Error Handling
**Objective:** Final UX polish.
- Error messages with actionable suggestions
- Loading states
- Responsive terminal width
- Keyboard shortcut consistency
- Visual consistency review

**Test:** Error states display correctly, narrow terminals don't break.

## 10. Testing Strategy

### Manual Testing Checklist
- [ ] `research-finder` launches interactive mode
- [ ] `research-finder --help` shows help
- [ ] `research-finder --version` shows version
- [ ] Arrow keys navigate menus
- [ ] Enter selects items
- [ ] Esc goes back
- [ ] q quits
- [ ] Dashboard shows correct stats
- [ ] Discover flow works end-to-end
- [ ] Saved businesses list displays
- [ ] Analyze scores and shows table
- [ ] Opportunities browse works
- [ ] Topics management works
- [ ] Outreach draft/send works
- [ ] Export produces correct files
- [ ] Settings display correctly
- [ ] `research-finder scan` works in command mode
- [ ] `research-finder results --json` outputs JSON
- [ ] Empty states show when no data
- [ ] Error messages are helpful
- [ ] Narrow terminal (80 cols) doesn't break
