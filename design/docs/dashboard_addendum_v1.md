# Expedia-inspired Dashboard Addendum v1

This addendum adapts `expedia_presentation_brandbook_v1.md` from slide design to a dense analytical dashboard.

## 1. What changes from presentation → dashboard

### Keep unchanged
- Primary ink: `#191E3B`
- Primary blue: `#1668E3`
- Brand yellow: `#FDDB32`
- White canvas and cool-gray surfaces
- Thin borders, restrained shadows
- Inter as practical Centra substitute
- Data-first hierarchy

### Change for dashboard use

1. **Increase information density.** Slides can breathe; dashboards should scan quickly. Use 12-column desktop grid, 16–24 px gaps, 16–20 px card padding.
2. **Reduce radii.** Prefer 8–12 px for cards and 6–8 px for controls. Avoid presentation-sized rounded containers.
3. **Reduce typography scale.** Typical desktop dashboard: 12 px metadata, 14 px body/control labels, 16–18 px section titles, 24–32 px KPI values.
4. **Use borders instead of shadows.** Default card: white fill + `#DFE0E4` border. Shadow only for popovers, menus, floating controls.
5. **Make filters persistent.** Date, POS, destination, device, traveler segment and other common cuts belong in a compact top filter bar or left rail.
6. **Use yellow very sparingly.** Best uses: selected brand marker, one standout insight, warning/highlight badge. Do not use yellow as a default data series.
7. **Use semantic colors only semantically.** Positive `#227950`, negative `#A7183C`, warning `#8B6400`.
8. **Minimize travel photography.** Good for onboarding/empty states, not for the main analytical workspace.
9. **Favor tables and small multiples.** Dashboard exploration benefits from ranked tables, sparklines, small multiples and compact distributions more than giant presentation charts.
10. **Design interaction states explicitly.** Hover, selected, focus, disabled, loading and no-data states should be part of the system.

## 2. Recommended desktop shell

- Canvas: `#F8F9FA` or `#FFFFFF`
- Top app bar: 56–64 px
- Optional left navigation: 64 px collapsed / 220–240 px expanded
- Main content max width: fluid; 24–32 px outer padding
- Section gap: 24 px
- Card gap: 16 px
- Card border: 1 px `#DFE0E4`
- Card radius: 10 px
- Card padding: 16 px compact / 20 px normal

### Header hierarchy

Left: Expedia mark/logo on a light surface.
Center/left: dashboard title + compact scope text.
Right: date range, export, info/help, user/project controls.

For a hackathon prototype, add a small descriptor such as `Hackathon analytics prototype` so the interface is not presented as an official Expedia product.

## 3. KPI cards

Recommended anatomy:
- 12 px muted label
- 26–32 px KPI value, semibold
- 12 px change vs baseline
- optional 48–72 px sparkline
- no decorative icon unless it adds meaning

Keep all KPI cards on one row aligned to the same baseline. Use green/red only for direction when direction is truly good/bad.

## 4. Charts

### Primary series
`#1668E3`

### Comparison series
`#191E3B`, `#676A7D`, `#C8DFF9`

### Gridlines
`#DFE0E4`, low emphasis

### Tooltips
White card, 8 px radius, subtle shadow, primary value in navy, secondary text muted.

### Selection
Selected item: cobalt. Unselected: 20–40% opacity or cool gray.

### Avoid
- rainbow categorical palettes
- 3D charts
- gradients inside bars
- unnecessary legends
- yellow bars everywhere

## 5. Tables

- 36–44 px row height
- 12–14 px text
- sticky header when scrollable
- header background `#EFF3F7`
- subtle horizontal dividers
- right-align numeric values
- use tabular numbers
- hover row fill: very pale blue/gray
- selected row: pale blue tint + cobalt indicator

## 6. Controls

- Input/select height: 36–40 px
- Primary action: Expedia blue fill, white label
- Secondary action: white fill, cool-gray border, navy text
- Icon button: 32–36 px hit area, 16–18 px icon
- Segmented controls: compact; selected item gets blue-tinted fill or blue border
- Search/filter controls should look functional, not decorative

## 7. Icon rules

The archive's UI icons are practical open-source assets rather than a copied Expedia proprietary icon set.

- Default size: 16–18 px in controls, 20 px in navigation
- Default color: `#191E3B`
- Active color: `#1668E3`
- Disabled: `#818494`
- Use one icon style consistently per surface
- Avoid large illustrative icons in analytical cards

## 8. Suggested dashboard information architecture for the hackathon

1. **Overview** — searches, users/sessions, bookings, conversion, revenue/value proxies
2. **Demand & seasonality** — search datetime, check-in/check-out seasonality, weekday/hour patterns
3. **Funnel** — search → click/interaction → booking where available
4. **Destinations & geography** — POS/destination matrices, maps, top routes
5. **Hotels** — property performance, ranking, price/quality proxies
6. **Users / segments** — RFM-style segmentation and travel behavior
7. **Recommendations / insights** — prioritized findings and possible product actions

## 9. Dashboard-specific anti-patterns

- giant hero cards copied from landing pages
- photos behind charts
- yellow backgrounds for whole sections
- more than 3–4 strong colors on one screen
- shadows around every card
- 16+ px card radii everywhere
- presentation-scale titles consuming the first screen
- logo repeated on every card
- decorative icons preceding every metric

## 10. Brand/legal note

The Expedia logo files in this package are isolated from Expedia Group's official public trademark artwork for convenience. Expedia states that its logos/trademarks are proprietary and provides usage guidelines. Use the logo only to identify the analyzed brand/company, preserve its appearance, keep clear space, and avoid presenting the hackathon dashboard as an official Expedia product.

Official public sources used:
- Expedia Group trademarks page: https://legal.expediagroup.com/intellectual-property/trademarks
- Expedia Group Connectivity Partners Brand Guidelines: https://go2.expediagroup.com/rs/443-YYQ-410/images/ConnectivityGuidelines_2022-FINAL.pdf
- Expedia Newsroom media assets terms: https://www.expedia.co.uk/newsroom/media-assets/
- Expedia Group Careers design-system reference: https://careers.expediagroup.com/job/senior-android-engineer-design-system/austin-tx/R-99604/
