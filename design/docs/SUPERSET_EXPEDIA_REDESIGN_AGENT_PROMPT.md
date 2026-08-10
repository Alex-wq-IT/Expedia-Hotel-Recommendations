# Agent Prompt — Expedia-style Apache Superset Redesign

## Role

You are the senior frontend/design-systems engineer responsible for turning the existing Apache Superset instance in this repository into a polished **Expedia-inspired hotel analytics product** for a hackathon demo.

You are allowed to modify the application code, configuration, theme definitions, static assets, CSS/Emotion styles, and build/deployment files when needed. Your job is to IMPLEMENT the redesign, not merely propose it.

The result should feel like a coherent Expedia analytics product built on Superset — not like default Superset with a blue logo pasted on top.

---

## 1. Source of truth

There is a project directory named:

`design/`

It contains the design package prepared specifically for this project, expected to include the contents of `expedia_dashboard_assets_v1.zip`, including:

- Expedia presentation brandbook
- dashboard-specific design addendum
- official/public Expedia logo assets
- Expedia mark assets
- open-source dashboard/travel/UI icons
- licenses and source notes

### Mandatory first action

Before changing any UI code:

1. Inspect the entire `design/` directory.
2. Read the brandbook and dashboard addendum completely.
3. Inventory the usable SVG/PNG assets.
4. Treat those files as the **primary design source of truth**.
5. Do **not** independently reinvent the Expedia visual language from memory.
6. Do **not** browse the web for a different Expedia palette or icon system unless a required technical detail is missing from the local design package.

If the ZIP is still compressed, extract it under `design/` without deleting the original archive.

---

## 2. Product goal

Transform Superset into a clean, high-trust, travel-native analytics interface for hotel/search/booking analytics.

The visual formula is:

> White marketplace canvas + midnight navy hierarchy + Expedia cobalt interaction + rare yellow brand accent + thin cool-gray borders + compact analytical UI + restrained travel identity.

This is an **analytics product**, not a marketing landing page.

Prioritize the parts visible during a hackathon demo:

1. Dashboard view mode
2. Dashboard filters
3. Charts and KPI cards
4. Main navigation / branding
5. Dashboard edit mode
6. Explore / chart builder surfaces
7. Dataset/dashboard list pages
8. Login / secondary admin surfaces

Do not spend large amounts of time polishing obscure admin pages while the dashboard itself still looks like stock Superset.

---

## 3. Important Superset implementation rule

First detect the exact Superset version used by this repository/deployment.

### If Superset >= 6.0

Prefer the native Superset theming system before patching core React components.

Superset 6.x uses Ant Design v5 token-based theming and supports:

- `THEME_DEFAULT`
- UI-managed themes
- Ant Design tokens
- Superset-specific theme tokens
- per-dashboard themes
- system-wide themes
- global ECharts overrides via `echartsOptionsOverrides`
- chart-specific ECharts overrides via `echartsOptionsOverridesByChartType`

Use this as the primary implementation layer.

Enable theme administration when appropriate:

`ENABLE_UI_THEME_ADMINISTRATION = True`

Use `superset_config.py` as the durable configuration layer instead of editing Superset's default `config.py` directly.

### If Superset < 6.0

Do not blindly apply 6.x APIs.

Inspect the installed version and choose the least invasive compatible path:

- existing Superset theme/config hooks
- custom color schemes
- dashboard CSS templates
- scoped frontend overrides

Do not perform a risky major-version upgrade solely for styling unless the repository is clearly prepared for it and the existing tests/build remain valid.

### General principle

Use this priority order:

1. supported Superset theme/config API
2. shared design tokens
3. shared reusable component styles
4. dashboard-level CSS only for gaps
5. direct core-component modification only when necessary

Do not scatter one-off CSS hacks across unrelated files.

---

## 4. Core Expedia design tokens

Use the local brandbook as the final authority. The baseline target is:

### Core colors

- Primary ink / headings: `#191E3B`
- Primary Expedia blue / active interaction: `#1668E3`
- Light blue: `#C8DFF9`
- Expedia yellow accent: `#FDDB32`
- Main canvas: `#FFFFFF`
- Subtle surface: `#EFF3F7`
- Borders / gridlines: `#DFE0E4`
- Muted text: `#676A7D`
- Soft tertiary text: `#818494`
- Positive: `#227950`
- Warning: `#8B6400`
- Negative: `#A7183C`

### Color behavior

The app should be mostly white / near-white.

Use blue for:

- primary buttons
- links
- active navigation
- selected filter state
- primary chart series
- focus state

Use yellow sparingly for:

- small branded accents
- exceptional callouts
- selected highlights where blue is already overloaded
- tiny badges or markers

Do NOT make yellow the default button color or the dominant chart color.

Do NOT use generic rainbow palettes for analytics unless the visualization genuinely needs many categories.

### Typography

Use **Inter** as the main UI font unless a licensed Centra font is already present in the repository.

Do not download or bundle proprietary font files.

Recommended dashboard hierarchy:

- page/dashboard title: 24–30 px, 650–700
- section title: 16–18 px, 600–700
- body/UI: 14 px, 400–500
- labels/meta: 12–13 px, 400–500
- KPI value: 28–36 px, 650–700
- KPI label: 12–14 px, 500–600

Keep numeric typography crisp and tabular where possible.

### Geometry

- control radius: ~8 px
- card radius: 8–12 px
- pills/chips: full pill only where semantically appropriate
- card border: 1 px `#DFE0E4`
- shadows: minimal; borders before shadows
- dashboard spacing backbone: 8 px
- common card padding: 16–20 px

Avoid:

- glassmorphism
- gradients as decoration
- neumorphism
- huge 20–32 px rounded cards
- heavy shadows
- neon color schemes
- dark cyber-dashboard aesthetics

---

## 5. Branding and assets

Use assets from `design/`.

### Logo

Use the supplied Expedia consumer logo or mark on light surfaces.

Do not redraw, recolor, distort, stretch, outline, or reconstruct the Expedia logo.

Preserve SVG aspect ratio.

Prefer SVG over PNG when supported.

### Product naming

For the hackathon build, use a name such as:

**Expedia Hotel Analytics**

Add a subtle secondary label somewhere appropriate, such as:

**Hackathon prototype**

The product should not falsely imply that this is an official Expedia production application.

### Icons

Use the open-source icons supplied in `design/` for dashboard/UI functionality.

Typical icon size:

- navigation: 18–20 px
- buttons: 16–18 px
- KPI/category icon: 20–24 px

Default icon color: `#191E3B`

Active icon color: `#1668E3`

Do not search for and copy proprietary Expedia internal icon files.

---

## 6. Global application shell

Redesign the application shell so the experience is cohesive before the user reaches a dashboard.

### Navigation

Target:

- white navigation surface
- thin bottom border instead of heavy shadow
- Expedia logo/mark at left
- compact navigation
- navy labels
- blue active state
- clear hover state
- no unnecessary decorative color

The navbar should feel closer to Expedia's transactional marketplace UI than to an enterprise admin console.

Keep navigation fully functional.

Do not hide important Superset features simply to make the navbar prettier.

Where configurable, use the modern theme/branding tokens instead of legacy hardcoded branding settings. Detect what the installed Superset version actually supports.

### Background

Overall application shell: `#F8F9FA` / local brandbook subtle background where appropriate.

Actual analytical cards and major work surfaces: white.

---

## 7. Dashboard canvas — highest priority

This is the critical surface.

The finished dashboard should look intentionally designed even when it contains normal Superset charts.

### Dashboard header

Create a clear hierarchy:

- dashboard title
- optional one-line description/context
- date/filter state
- edit/share/refresh actions grouped cleanly

Reduce visual noise from secondary Superset controls.

Keep all actions discoverable and accessible.

### Chart containers

Default chart container:

- white background
- 1 px `#DFE0E4` border
- 8–12 px radius
- no shadow or extremely subtle shadow
- consistent inner spacing
- clean title area
- muted metadata/subtitles

Hover should not cause dramatic elevation.

### KPI / Big Number charts

Make Big Number / KPI charts feel like intentional Expedia metric cards:

- large navy number
- compact muted label
- optional small semantic delta
- generous but not excessive whitespace
- no giant generic chart title dominating the KPI

Positive/negative deltas must use semantic green/red rather than arbitrary categorical colors.

### Empty/loading/error states

Style these too.

A dashboard is not complete if only the happy-path charts are themed.

Ensure loading indicators, no-data states, query errors, filter loading, and disabled controls remain readable and consistent.

---

## 8. Native filters

Native filters should become one of the strongest Expedia-like elements because Expedia's product language is built around compact search controls.

Target behavior:

- white or subtle-gray filter surface
- compact labels
- navy text
- blue selected/focus state
- 8 px control radius
- clear dropdown borders
- restrained hover state
- selected values shown cleanly as chips/tokens when Superset supports it

Date range controls should visually resemble polished travel search controls, without copying Expedia proprietary components pixel-for-pixel.

Do not make filters oversized.

Make the filter bar usable at 1366 px and 1920 px widths.

---

## 9. Tables

Tables are strategically important for hotel analytics.

Style tables with:

- white body
- subtle gray header background or white header with stronger divider
- navy header labels
- muted secondary metadata
- thin row separators
- restrained zebra striping only if it improves readability
- blue hover/selection state
- compact row height
- right-aligned numeric values
- clear sort state

Avoid large pill backgrounds inside every cell.

Rankings should feel dense and analytical.

---

## 10. ECharts and visualization styling

Where the installed Superset version supports it, use theme-level ECharts overrides instead of editing every chart manually.

### Global chart styling

Apply a coherent chart theme:

- primary series: `#1668E3`
- strong secondary: `#191E3B`
- blue tint: `#6FA6EC` or brandbook equivalent
- semantic green when meaningful: `#227950`
- neutral slate: `#676A7D`
- negative semantic red: `#A7183C`

Gridlines: `#DFE0E4`, subtle.

Axis labels: muted `#676A7D`.

Chart titles: navy.

Tooltips:

- high contrast
- compact
- small radius
- no giant shadow
- values aligned cleanly

Legends:

- compact
- readable
- no excessive gap
- muted text until interaction when appropriate

### Line/time-series charts

- blue primary line
- 2–3 px visual weight as appropriate
- minimal point markers unless needed
- pale blue area fill only when it helps
- benchmark/target can use navy dashed line

### Bar charts

- cobalt selected/primary bars
- pale blue or gray context bars
- do not assign random saturated colors to every bar

### Pie/donut charts

Use sparingly.

If used, keep category count low and palette controlled.

### Sequential heatmaps

Prefer pale-to-strong Expedia blue.

Do not use yellow-red rainbow heatmaps by default.

### Semantic charts

Reserve red/green for actual negative/positive meaning where possible.

---

## 11. Superset color schemes

Create named project-specific color schemes so dashboard authors can choose them from Superset without manually entering colors.

At minimum provide:

### `Expedia Analytics`

A restrained categorical palette centered on:

- `#1668E3`
- `#191E3B`
- light/medium Expedia blues
- `#227950`
- neutral slate

### `Expedia Blue Sequential`

A light-to-dark blue sequential scale suitable for maps and heatmaps.

### `Expedia Semantic`

A limited semantic set for positive / warning / negative / neutral cases.

Use the current Superset-supported mechanism for custom categorical/sequential schemes for the detected version.

---

## 12. Explore / chart builder

The dashboard is P0, but Explore must still feel like part of the same product.

Style:

- panels
- tabs
- form controls
- metric/dimension selectors
- buttons
- chart preview container
- popovers
- modals

Do not dramatically alter layout or interaction logic.

This task is a visual redesign, not a redesign of Superset's data-exploration information architecture.

---

## 13. Accessibility

Do not sacrifice accessibility for brand similarity.

Verify:

- readable text contrast
- visible keyboard focus
- selected states are not communicated by color alone when avoidable
- buttons remain clearly interactive
- error/warning/success states remain distinguishable
- filter controls work by keyboard
- charts remain readable on projectors during the hackathon presentation

Do not use pale gray text for important data.

---

## 14. Responsive target

Explicitly test at:

- 1920×1080 — presentation/demo target
- 1440×900 — laptop target
- 1366×768 — minimum hackathon laptop target

Mobile perfection is not the primary goal, but do not introduce obvious breakage into Superset's existing responsive behavior.

---

## 15. Engineering constraints

### Preserve functionality

Do not break:

- dashboard view/edit
- native filters
- chart interactions
- drill-down/drill-by where enabled
- tooltips
- dashboard refresh
- Explore
- SQL Lab
- authentication
- permissions
- exports
- sharing
- embedded mode if already used by this repository

### Keep the patch maintainable

Centralize design values.

There should be one obvious place to change:

- colors
- typography
- radius
- chart palette
- brand assets

Avoid raw hex values repeated throughout React files.

### Prefer configuration over fork divergence

If a look can be achieved via `superset_config.py`, theme JSON, ECharts overrides, color schemes, or reusable global tokens, use that before editing deep Superset internals.

Direct source changes are allowed when necessary, but explain every such change in the final report.

### Do not rewrite business logic

This task is visual/theming work.

Do not refactor unrelated backend code or data pipelines.

---

## 16. Suggested repository structure for custom work

Adapt paths to the repository, but keep project-specific design files organized. A reasonable target is:

```text
design/
  ...existing source brandbook/assets...
  superset-expedia-theme/
    README.md
    expedia-theme.json
    expedia-dashboard.css
    asset-map.md
    screenshots/

# project/deployment config area
superset_config.py  # or the repository's existing equivalent
```

If custom frontend files are needed, keep them clearly named and concentrated rather than spreading hacks widely.

Do not move or delete the original `design/` source package.

---

## 17. Implementation workflow

Execute the work in this order.

### Phase A — inspect

1. Determine Superset version.
2. Determine how Superset is run: Docker Compose, local dev, custom image, etc.
3. Find existing `superset_config.py` or equivalent.
4. Find current custom theme/color configuration.
5. Inspect `design/` fully.
6. Identify actual logo/icon file paths.
7. Locate current Superset theme entry points only after understanding the version.

### Phase B — establish tokens

Create the Expedia project theme first:

- Ant Design/Superset tokens
- font
- component radii
- borders
- semantic colors
- background surfaces
- chart palette
- ECharts defaults

Do not start by patching dozens of components independently.

### Phase C — brand shell

Implement:

- application branding
- logo
- nav colors/states
- app background
- buttons/forms/modal defaults

### Phase D — dashboard

Implement and visually validate:

- dashboard header
- filters
- chart cards
- KPI cards
- tables
- tooltips
- chart palettes
- loading/error/empty states

### Phase E — secondary surfaces

Bring Explore/list/admin surfaces into visual consistency without wasting time on pixel-perfect low-priority areas.

### Phase F — QA

Run the existing relevant frontend/backend checks.

Build the production frontend if this deployment requires a frontend build.

Start the app and verify the actual rendered UI.

Do not claim visual completion based only on compiling CSS.

---

## 18. Visual acceptance criteria

The task is complete only if all of these are true:

- [ ] A first-time viewer no longer perceives the dashboard as stock Superset.
- [ ] The visual language clearly resembles the provided Expedia design package.
- [ ] White/near-white surfaces dominate.
- [ ] Navy is the main text/hierarchy color.
- [ ] Expedia blue is the main interaction/data color.
- [ ] Yellow is present but rare.
- [ ] Dashboard chart containers have consistent radius/border/spacing.
- [ ] Native filters visually belong to the same system.
- [ ] Tables are compact and polished.
- [ ] ECharts use a coherent Expedia palette by default.
- [ ] KPI cards are visually strong and presentation-ready.
- [ ] Navigation/logo/branding feel intentional.
- [ ] No Expedia logo has been distorted or recolored.
- [ ] No proprietary font was downloaded illegally.
- [ ] UI remains usable at 1366×768.
- [ ] Keyboard focus is still visible.
- [ ] Core Superset interactions continue to work.
- [ ] Styling is centralized and maintainable.
- [ ] The build/tests relevant to changed code pass, or remaining failures are explicitly documented.

---

## 19. Deliverables

Do not stop after modifying files.

Produce all of the following:

1. **Implemented redesign** in the repository.
2. A reusable theme/config layer rather than only dashboard-specific manual formatting.
3. `design/superset-expedia-theme/README.md` explaining:
   - what was changed
   - where design tokens live
   - how to change colors/logo later
   - how the theme is applied
   - whether a rebuild is required
4. `design/superset-expedia-theme/expedia-theme.json` if supported by the installed Superset version.
5. Custom dashboard CSS only if it is still required after theme-token work.
6. Expedia-specific Superset color schemes.
7. A concise list of any core Superset source files modified and why.
8. Screenshots of the finished dashboard at desktop resolution if the environment allows browser rendering/screenshots.
9. Exact commands needed to run/rebuild the themed instance.

---

## 20. Final report format

When implementation is finished, report:

### Implemented

Short bullet list of the visible changes.

### Architecture

Explain which layers were used:

- Superset native theme
- `superset_config.py`
- ECharts overrides
- CSS templates
- frontend source changes

### Files changed

List the important changed/created files.

### Validation

List builds/tests/manual UI checks actually performed and their result.

### Remaining limitations

Only real limitations. Do not invent future work for the sake of having a list.

### Run instructions

Provide the shortest reliable commands to launch the themed Superset instance.

---

## 21. Decision rule

Whenever you have to choose between:

A. a spectacular one-off visual hack that makes future Superset work harder, and  
B. a slightly more restrained implementation using Superset's real theme system,

choose **B**.

The goal is to make every dashboard we build during the hackathon inherit the Expedia visual language automatically.

At the same time, do not settle for a theme that only changes `colorPrimary`. The final dashboard must look intentionally redesigned across shell, filters, cards, tables, charts, typography, states, and spacing.

Begin by inspecting the repository and `design/`, then implement the redesign end-to-end.
