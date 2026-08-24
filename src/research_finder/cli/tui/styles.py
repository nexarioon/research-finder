"""Modern TUI styles for Research Finder."""

RESEARCH_FINDER_CSS = """
Screen {
    background: $surface;
}

#sidebar {
    width: 28;
    background: $panel;
    border-right: solid $primary;
    padding: 1;
}

#sidebar-title {
    text-align: center;
    padding: 1 0;
    text-style: bold;
    color: $primary;
    width: 100%;
}

#sidebar-subtitle {
    text-align: center;
    padding: 0 0 1 0;
    color: $text-muted;
    width: 100%;
}

#sidebar ListView {
    height: auto;
    max-height: 20;
}

#sidebar ListItem {
    padding: 0 1;
}

#sidebar ListItem.-active {
    background: $primary;
    color: $text;
}

#sidebar ListItem Label {
    width: 100%;
}

.screen-title {
    text-style: bold;
    padding: 1 0 0 0;
    width: 100%;
}

.screen-subtitle {
    padding: 0 0 1 0;
    width: 100%;
}

.content-table {
    height: 1fr;
    width: 100%;
}

.button-row {
    height: 3;
    padding: 1 0;
}

.button-row Button {
    margin: 0 1;
}

#main-content {
    width: 1fr;
    padding: 1 2;
}

#status-bar {
    dock: bottom;
    height: 1;
    background: $panel;
    padding: 0 2;
}

DataTable {
    border: solid $primary;
}

Button {
    min-width: 16;
}

.stat-card {
    width: 1fr;
    height: 5;
    margin: 0 1;
    padding: 1;
    background: $panel;
    border: solid $primary;
}

.stat-value {
    text-style: bold;
    color: $primary;
    width: 100%;
}

.stat-label {
    color: $text-muted;
    width: 100%;
}
"""
