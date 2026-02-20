# Domino UX Design Rules Reference

## UX Principles

1. **Pave a Smooth Path** — Guide users to goals with opinionated, helpful experiences. Explain concepts in-page (tooltips, descriptions). Give guidance on next steps.
2. **Increase User Confidence** — Detailed error messages with resolution steps. Consistent patterns and vocabulary. Feedback for every action.
3. **Reduce Effort to Value** — Automate low-value steps. Smart defaults. Progressive disclosure for advanced options. Present info when applicable, not all at once.
4. **Adapt to Repeat Users** — Design for intermediate users, not perpetual beginners. Allow "Don't show again" for repeated warnings. Support keyboard shortcuts.

## UX Writing

### Style
- Sentence case everywhere (exception: Domino branded terms like Workspace, Model API, Artifacts)
- No exclamation points
- Use contractions for natural tone
- Active voice ("Save changes" not "Changes can be saved")
- Numerals and symbols ("3%" not "three percent")
- Dates: "Month Day, Year" format; relative dates ("2 days ago") only within 7 days

### Word Catalog
| Word | Usage |
|------|-------|
| **Add** | Entity exists, being added to new context. No "new" prefix. |
| **Create** | Entity does not yet exist. No "new" prefix. |
| **Performance** | Deployment integrity metrics (model quality, data drift) |
| **System health** | System-level metrics (CPU, memory, latency, error rate) |
| **Usage** | Consumer usage metrics (app views) |

### Error Messages
- Be direct, concise, speak to the user
- Provide resolution actions
- No unnecessary apologies or anxiety
- Distinguish system errors (human-readable) from user code output (show raw)

**Examples:**
| Bad | Good |
|-----|------|
| "Error" | "Unable to save changes" |
| "Invalid input" | "Email address must include @" |
| "Unauthorized" | "You don't have permission. Contact your admin for access." |

### Error Placement
| Type | Placement |
|------|-----------|
| Inline validation | Next to the field (preferred) |
| Inline banner | Top of form/section |
| Toast notification | Corner of screen, auto-dismiss 5-8s, include action buttons |
| Modal dialog | Critical errors requiring attention |
| Full page | 404, 500, permission denied |

## Empty States

Every empty state must answer:
1. **What is this?** — Brief explanation
2. **Why is it empty?** — Context
3. **What can I do?** — Clear CTA

| Context | Bad | Good |
|---------|-----|------|
| No tags | "No tags" | "No tags yet — Tags help filter and organize jobs. [+ Add tag]" |
| Empty table | (blank) | "No jobs found. [Run a job] or adjust your filters." |
| Empty search | "No results" | "No jobs match your search. Try different keywords or [clear filters]." |

Use helpful tone ("No tags yet" not "You have no tags"). CTAs should be specific ("Add tag" not "Get started").

## Layout & Visual Hierarchy

### Reading Patterns
- **F-Pattern** for dashboards/data pages: key info along top and left
- **Z-Pattern** for landing pages: logo top-left, CTA bottom-right

### Hierarchy Tools
Size > Color/Contrast > Position > Whitespace > Typography weight

### Content Positioning
| Position | Best For |
|----------|----------|
| Top-left | Logo, nav, page title |
| Top-right | User menu, notifications, global actions |
| Above the fold | Key messages, primary CTA |
| Bottom of forms | Submit/Cancel |

### Spacing (Law of Proximity)
- **Within a group**: ~half the space **between** groups (1:2 ratio)
- Apply differential spacing to content panels with mixed elements
- Do NOT apply to data tables — uniform row spacing is correct for tabular data
- Spacing scale: 4px, 8px, 16px, 24px, 32px

## Typography

| Level | Size | Use |
|-------|------|-----|
| H1 | 32px | Page titles (one per page) |
| H2 | 26px | Section headers |
| H3 | 20px | Subsection headers |
| H4 | 16px | Card titles, labels |
| Body | 14-16px | Primary content |
| Caption | 12px | Helper text, metadata |

- Don't skip heading levels (H1 → H2 → H3)
- Min body text: 14px for UI
- Line length: 50-75 characters
- Left-align body text, never center
- Headings: 1.1-1.3 line height; Body: 1.4-1.6

### Data Typography
- Tabular/monospace figures for number alignment
- Thousand separators (1,234,567)
- Units in smaller/lighter weight
- Trends: use color + icon, not just +/- symbols
- Empty/null values: use "—" or "N/A", not "0" or blank

## Buttons & CTAs

### Labeling
- Start with a verb: "Save", "Delete", "Export", "Create"
- Be specific: "Delete project" not "Delete"
- Match the trigger: "Edit profile" → "Save profile"
- Never use "OK", "Submit", "Click here"

### Disable vs. Hide
| Approach | When |
|----------|------|
| Disable (grayed out) | Action exists but unavailable yet — tooltip explaining why |
| Hide | User will never need this action |

### Button Hierarchy
Use Primary/Secondary/Tertiary buttons per Ant Design. One clear primary CTA per screen.

## Tables

- Truncated cells **must** have tooltips
- Primary identifiers must be readable without clicking
- Numbers right-aligned, text left-aligned
- Protect table width — side panels should not crush tables
- Consider column visibility toggles for wide tables

## Side Panels

| Pattern | Best For |
|---------|----------|
| **Overlay drawer** (preferred) | Detail views from table rows — main content stays full width |
| Push panel | Persistent context needed alongside main view — set min widths |
| Modal | Focused tasks, confirmations |
| Full-page nav | Complex detail/editing workflows |

Overlay drawers: backdrop that closes on click, close (X) button, Escape to close, slide from right.

## Icon-Only Buttons
- **Always** include tooltips
- Use recognizable icons (trash=delete, pencil=edit)
- Min click target: 24×24px desktop, 44×44px touch
- For critical/destructive actions, prefer icon + label

## Forms

- One column layout preferred
- Labels above fields (not placeholder-as-label)
- Keep labels short ("Email" not "Please enter your email address")
- Mark required fields with * or "(required)"
- Validate on blur, show success states
- Preserve input on errors, scroll to first error
- Smart defaults: pre-fill known info, remember recent choices

### Checkboxes & Toggles
- **Checked = ON/Enabled/Active** (never checked = OFF/disabled)
- Toggle labels: put label before toggle, toggle shows state
- Checkbox: multiple selections, settings on form submit
- Toggle: binary on/off with immediate effect

## Charts & Data Visualization

- Choose right chart type: line=trends, bar=categories, pie=parts of whole (max 6 slices)
- Label clearly: title, axis labels, units, legends
- Y-axis starts at zero for bar charts
- Scale time axis to selected range
- Empty chart states: explain why no data, suggest actions
- Colorblind-safe palettes, max 5-7 colors
- Hover tooltips with exact values

## Interaction Feedback

- Hover states on interactive elements
- Button press animation/color change
- Loading states: disable interactive elements, show progress, provide cancel for long ops
- Success confirmation after completed actions

## UX Review Checklist

### Layout
- [ ] Side panels overlay (not push/crush)?
- [ ] Tables readable width?
- [ ] Differential spacing in content panels (tight within groups, loose between)?

### Tables & Data
- [ ] Tooltips on truncated text?
- [ ] Primary identifiers readable?
- [ ] Numbers right-aligned?

### Interactive Elements
- [ ] Icon-only buttons have tooltips?
- [ ] Button labels action-oriented and specific?
- [ ] Disabled elements explain why?
- [ ] Click targets adequate size (min 24×24px)?

### Empty & Error States
- [ ] Empty states actionable (what/why/what to do)?
- [ ] System errors human-readable with guidance?
- [ ] User code output shown raw (as expected)?

### Copy
- [ ] Sentence case (except Domino terms)?
- [ ] No exclamation points?
- [ ] Grammar, spelling, punctuation correct?

### Severity Scale
| Severity | Definition |
|----------|------------|
| **High** | Blocks goals or causes confusion (missing error guidance, unreadable table) |
| **Medium** | Slows users down (missing tooltips, poor grouping, non-actionable empty states) |
| **Low** | Minor polish (suboptimal spacing, copy tweaks) |

### Do NOT Flag
- User code output shown raw (stack traces in stderr)
- Uniform table row spacing (correct pattern)
- Dense info displays for technical users (job logs)
