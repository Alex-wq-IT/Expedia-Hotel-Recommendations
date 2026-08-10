# Expedia.com Presentation Brandbook v1

**Purpose:** a practical design document for an analytics / hackathon presentation inspired by the current consumer experience of **Expedia.com**.

**Status:** reverse-engineered presentation system, not an official Expedia brand book. It combines current Expedia.com product patterns, Expedia/Expedia Group public brand materials, and presentation-specific adaptations.

**Use case:** analytical deck → generated visual blocks → Figma assembly → hackathon defense.

---

## 0. The one-minute design contract

If another agent reads only this section, it should still produce something recognizably Expedia-like.

1. **White canvas dominates.** Target 70–85% white / near-white area per slide.
2. **Primary ink is midnight navy:** `#191E3B`.
3. **Primary interaction / analytical emphasis is cobalt:** `#1668E3`.
4. **Brand yellow is scarce voltage:** `#FDDB32`. Use it for highlights, small accents, badges, key moments — not as the default chart or button color.
5. **Surfaces are cool and restrained:** `#EFF3F7`, borders `#DFE0E4`.
6. **Typography is utilitarian and humanist.** Use Centra No.2 if licensed; otherwise **Inter** is the recommended presentation substitute.
7. **Cards are bordered before they are shadowed.** Radius 8–12 px; subtle or no shadow.
8. **UI geometry is compact, transactional, clean.** Avoid giant 24–32 px radii, glassmorphism, neumorphism, heavy gradients.
9. **Charts use blue/navy first.** Green/red/amber only when their semantics are useful. Yellow is a highlight, not a categorical workhorse.
10. **Travel photography adds emotion, not structure.** The analytics content remains dominant.
11. **Icons are simple outline icons**, dark navy or cobalt, generally 20–24 px.
12. **Every slide should have one visual hierarchy:** headline → main finding → evidence → supporting annotation.

### Core visual formula

> White marketplace canvas + midnight navy structure + cobalt interaction + rare yellow brand spark + thin cool-gray borders + highly legible sans typography + travel imagery used selectively.

---

# 1. Brand DNA

## 1.1 What Expedia currently feels like

The current consumer product is closer to a **high-trust marketplace / booking engine** than to a cinematic travel magazine. The search experience is the hero. The interface is information-dense but calm: white canvas, compact cards, clear controls, direct labels, blue interaction states and restrained brand accents.

For an analytics presentation this is useful: we should make the deck feel like **Expedia itself is explaining its marketplace data**.

### Keywords

- clear
- useful
- travel-native
- confident
- practical
- trustworthy
- data-rich
- spacious but not empty
- modern marketplace
- optimistic without being childish

### Avoid

- luxury editorial aesthetics
- dark cyber dashboards
- neon gradients
- excessive yellow
- glossy 3D icons
- glass cards
- overly playful illustrations
- huge rounded SaaS cards
- generic consulting-deck blue gradients

---

# 2. Important distinction: Expedia vs Expedia Group

There are two related but visually different systems.

### Expedia consumer product — PRIMARY reference for this deck

Use this for almost everything:

- midnight navy / blue-black ink
- cobalt interaction blue
- yellow brand accent
- white marketplace canvas
- compact booking-style components

### Expedia Group corporate system — SECONDARY reference

Public Expedia Group materials use stronger corporate electric blues such as `#000099` and dark navy `#020247`, with a broader corporate palette and larger editorial typography.

**Rule:** do not accidentally turn the presentation into an Expedia Group careers/corporate deck. Our hackathon deck should look primarily like **Expedia.com the product**.

---

# 3. Color system

## 3.1 Core presentation tokens

| Token | Hex | Primary use |
|---|---:|---|
| `expedia.ink` | `#191E3B` | Headlines, primary text, icons, strong borders |
| `expedia.blue` | `#1668E3` | Primary analytical series, links, selected state, CTA |
| `expedia.blue.light` | `#C8DFF9` | Selection tint, secondary blue fill, range bands |
| `expedia.yellow` | `#FDDB32` | Brand accent, key highlight, tiny section marker |
| `surface.canvas` | `#FFFFFF` | Main slide/card background |
| `surface.subtle` | `#EFF3F7` | Secondary panels, table headers, chart plot backgrounds |
| `border.default` | `#DFE0E4` | Card borders, dividers, chart gridlines |
| `text.muted` | `#676A7D` | Secondary labels, annotations |
| `text.soft` | `#818494` | Captions, tertiary metadata |
| `semantic.positive` | `#227950` | Positive KPI / success only |
| `semantic.positiveLight` | `#BEECC6` | Positive badge background |
| `semantic.warning` | `#8B6400` | Warning / attention only |
| `semantic.error` | `#A7183C` | Negative / failure only |
| `overlay.scrim` | `#0C0E1C` | Dark overlay on photographs |

## 3.2 Color proportions per slide

A useful target:

- **70–85%** white / very light neutral
- **10–20%** navy + cobalt
- **0–5%** yellow
- **0–5%** semantic colors / photography-dependent color

Yellow should feel special. If it appears everywhere, the deck stops looking like Expedia.

## 3.3 Recommended data-viz behavior

### One metric / one series

Use `#1668E3`.

### Baseline vs target

- actual: `#1668E3`
- baseline / previous period: `#676A7D` or `#C8DFF9`
- target / benchmark: navy dashed line `#191E3B`

### Positive / negative

- positive: `#227950`
- negative: `#A7183C`
- neutral: `#676A7D`

### Highlight one category

- all categories: pale blue / cool gray
- selected category: cobalt `#1668E3`
- exceptional callout: yellow `#FDDB32` with navy text

### Multi-category charts

Prefer a small number of meaningful categories. Suggested presentation extension:

1. `#1668E3` — primary blue
2. `#191E3B` — navy
3. `#6FA6EC` — blue tint
4. `#227950` — green when semantically acceptable
5. `#676A7D` — slate

Do not use red/green merely to make categories colorful; preserve them for meaning where possible.

---

# 4. Typography

## 4.1 Typeface

### Preferred

**Centra No.2 / CentraNo2** — historically adopted across Expedia web/native UI and visible in Expedia Group public design-system materials.

### Practical Figma substitute

**Inter**.

Why Inter works for the deck:

- similar utilitarian digital feel
- strong numeric readability
- excellent tabular figures
- easy availability across Figma / export environments

Do not imitate the Expedia logotype using a substitute font. Use an official logo asset if the logo is needed.

## 4.2 Slide typography scale — adapted for 16:9 presentations

The website uses smaller UI sizes; a presentation requires scaling up while preserving the same hierarchy.

| Style | Size | Weight | Line height | Use |
|---|---:|---:|---:|---|
| `Display` | 48–56 | 700 | 1.05–1.1 | Cover / section statement |
| `H1` | 36–44 | 700 | 1.1 | Slide title |
| `H2` | 26–32 | 600–700 | 1.15 | Card / major block heading |
| `H3` | 20–24 | 600 | 1.2 | Subheading |
| `Body L` | 20–22 | 400–500 | 1.4 | Main explanatory text |
| `Body` | 17–19 | 400 | 1.4 | Standard slide text |
| `Caption` | 13–15 | 400–500 | 1.35 | Sources / metadata |
| `KPI` | 38–52 | 700 | 1.0 | Main numbers |
| `Eyebrow` | 12–14 | 600–700 | 1.1 | Uppercase category label |

### Numeric typography

Use tabular figures for:

- prices
- conversion
- booking counts
- percentages
- ranks
- time-series labels

KPI values should be visually stronger than their labels, never the reverse.

---

# 5. Geometry, spacing and layout

## 5.1 Master slide

- format: **16:9**
- design reference: 1920×1080 px
- safe side margins: **80 px**
- top/bottom safe margins: **64–72 px**
- grid: **12 columns**
- gutter: **24 px**

## 5.2 Spacing scale

Use an 8 px backbone:

`4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 80`

Common combinations:

- icon → label: 8–12
- heading → body: 12–16
- card padding: 20–24
- major block gap: 24–32
- section gap: 48–64

## 5.3 Radius

| Token | Radius | Use |
|---|---:|---|
| `radius.xs` | 4 px | tags, tiny controls |
| `radius.control` | 8 px | buttons, inputs, chart tooltips |
| `radius.card` | 12 px | presentation cards |
| `radius.pill` | 999 px | tabs, chips, filters |

Avoid 20–32 px card radii. They make the system look like generic modern SaaS rather than Expedia.

## 5.4 Borders and shadows

Default card:

- fill `#FFFFFF`
- border 1 px `#DFE0E4`
- radius 12 px
- no shadow

Elevated card when truly needed:

- border 1 px `#DFE0E4`
- shadow approximately `0 2 8 rgba(25,30,59,0.08)`

Use elevation sparingly.

---

# 6. Logo use

Use the **official Expedia logo asset** rather than recreating it.

Presentation recommendations:

- light slide → full-color Expedia logo
- dark/photo slide → official white logo where available
- preserve generous clear space
- never recolor the logo to match a chart
- never stretch or distort
- do not lock your hackathon/team logo into Expedia’s logo as if it were an official co-brand

Public Expedia Group partner guidance specifies generous clear space around brand logos and emphasizes use of approved high-resolution/vector assets.

### Hackathon labeling

Add a small qualifier on title/final slide when appropriate:

> Independent hackathon analysis of Expedia public / competition data

This avoids implying that the deck is an official Expedia publication.

---

# 7. Iconography

## Style

- outline first
- 1.5–2 px stroke
- 20–24 px standard size
- rounded but not bubbly geometry
- navy by default
- cobalt for selected / interactive state

## Useful icon concepts

- hotel / bed
- location pin
- calendar
- travelers / users
- plane
- search
- filter
- map
- trend
- price tag
- clock
- star / rating

Avoid mixed icon families on the same slide.

---

# 8. Photography and image direction

Expedia is a travel product, so photography is valuable — but the current product experience is not built around full-bleed photography on every screen.

## Use photography for

- cover slide
- section dividers
- destination examples
- hotel recommendation examples
- final / vision slide

## Do not use it behind dense charts or tables

## Photo direction

Prefer:

- real destinations
- real accommodation environments
- people in travel context when helpful
- bright natural light
- clear focal subject
- authentic, premium but accessible feel

Avoid:

- oversaturated “Instagram travel” look
- extreme HDR
- fantasy AI landscapes
- generic corporate people pointing at laptops

## Overlay

For text over a photo, apply dark navy/black scrim based on `#0C0E1C`, around 30–55% depending on image contrast.

---

# 9. Presentation component library

These are the blocks another agent should be able to generate individually for Figma.

## 9.1 KPI Card

**Use:** key business metrics.

Structure:

- white card
- 1 px cool-gray border
- 12 px radius
- 24 px padding
- tiny label at top
- large navy KPI
- optional delta chip
- optional tiny sparkline at bottom

Example:

**Booking Conversion**  
`7.8%`  
`+0.9 pp vs baseline`

Delta:

- positive = green text / pale green chip
- negative = burgundy text / pale neutral-red tint

---

## 9.2 Insight Callout

**Use:** the single conclusion judges must remember.

Structure:

- pale blue `#EFF3F7` or white
- 4 px cobalt left rail OR small yellow accent square
- 20–28 px semibold statement
- one line of evidence below in muted text

Avoid full yellow background for large callouts.

---

## 9.3 Chart Card

Structure:

- title + optional subtitle
- chart body
- legend aligned at top/right
- one insight annotation
- source in 13–14 px muted text

Style:

- white background
- minimal horizontal gridlines `#EFF3F7` / `#DFE0E4`
- no chart border box inside the card
- no 3D
- no gradients
- direct labels preferred when possible

---

## 9.4 Search-Module Header

Borrow the Expedia booking-search metaphor for a section opener.

Use a horizontal row of 3–4 rounded fields:

- Location / Segment
- Check-in / Period start
- Check-out / Period end
- Travelers / Sample size

Then a cobalt search button.

For the analytics deck, fields can be repurposed as **filters** while keeping the recognizable travel-search visual language.

Do not make every slide a fake search page; use this as a motif only.

---

## 9.5 Filter Chips

- pill shape
- 1 px navy/gray border
- white default
- selected: pale blue fill + cobalt border/text
- 14–16 px text
- 8–12 px horizontal gap

Useful for:

- business vs leisure
- domestic vs international
- weekday vs weekend
- booked vs not booked
- mobile vs desktop

---

## 9.6 Hotel / Recommendation Card

Excellent for recommendation-system slides.

Structure:

- image left or top
- hotel name
- location
- review score badge
- 2–3 concise attributes
- price / predicted relevance / ranking metric aligned right
- optional “Recommended” / “Best match” tag

Keep the card analytical; do not recreate the live site pixel-for-pixel.

---

## 9.7 Comparison Table

- white canvas
- pale blue/gray header row
- 1 px horizontal dividers
- no vertical gridlines unless necessary
- first column navy semibold
- best value can receive pale blue fill
- one yellow marker can identify the final chosen model

---

## 9.8 Section Divider

Recommended structure:

- white or navy background
- tiny yellow eyebrow / marker
- very large 48–56 px statement
- optional travel image occupying 30–45% of slide

Use section dividers to introduce:

- Data
- User behavior
- Search funnel
- Recommendation model
- Business value

---

# 10. Data visualization language

## 10.1 Bar charts

- square/very slightly rounded bar ends
- one main cobalt series
- comparison in cool gray
- highlight specific bar in yellow only when necessary
- labels outside bars when readable

## 10.2 Line charts

- 2–3 px line
- primary cobalt
- secondary navy / muted blue
- dot markers only for highlighted observations
- forecast area: pale blue translucent band

## 10.3 Funnel

Do **not** use a giant decorative funnel shape.

Prefer stacked horizontal stages with:

- stage name
- count
- conversion to next stage
- thin connecting arrows

This feels more product/marketplace-like.

## 10.4 Heatmaps

Prefer a monochrome blue scale from very pale blue to cobalt/navy.

Use yellow only to mark a chosen cell, not as one endpoint of the heatmap.

## 10.5 Maps

- light neutral basemap
- cobalt markers
- selected / top destination = yellow marker with navy outline
- keep map labels minimal

## 10.6 Distribution plots

Use blue fill at 15–25% opacity + cobalt outline. Median/benchmark line in navy.

---

# 11. Recommended slide templates

## Template A — Cover

**Layout:** 55/45 split.

Left:

- small yellow brand marker
- 48–56 px title
- 20–22 px subtitle
- team / hackathon metadata

Right:

- travel image or collage with 12 px radius

Optional Expedia logo small in top-left or bottom-right.

---

## Template B — Executive Summary

Top: slide title.

Body: 3 KPI cards in one row.

Bottom: one large insight callout.

This should be one of the cleanest slides in the deck.

---

## Template C — One Big Finding

Left 35%:

- eyebrow
- 32–40 px insight statement
- 2 supporting bullets max

Right 65%:

- one dominant chart

Use yellow only on the one element the audience must notice.

---

## Template D — Data / DWH Architecture

White background.

Use rounded 8–12 px modules with dark navy labels.

Arrows cobalt.

Raw / staging layers pale gray.

Core / mart layer pale blue.

Gold/yellow marker only on the final analytics-ready mart.

Avoid glowing pipelines and dark-cloud architecture diagrams.

---

## Template E — Model Comparison

Left: comparison table or horizontal bars.

Right: selected model card with pale-blue fill and a tiny yellow “Chosen” tag.

Include both ML quality and business interpretation.

---

## Template F — Recommendation Experience

Use a miniature Expedia-like product panel:

- search/filter row
- 2–3 hotel cards
- recommendation tags / score

Beside it, explain the ranking logic and business benefit.

This can be one of the strongest visual slides in the defense.

---

## Template G — Business Impact

Top-left: big KPI / expected uplift.

Bottom-left: concise mechanism.

Right: before/after chart.

Use green only for the positive impact number, not as the entire slide theme.

---

## Template H — Final Slide

Large concise statement:

> Better matching → less search friction → more confident bookings

Then 3 small proof points.

Use one optimistic travel image or a clean white background with a yellow accent.

---

# 12. Figma variables

Create these variables before assembling slides.

## Colors

```text
Color / Ink / Primary        #191E3B
Color / Ink / Muted          #676A7D
Color / Ink / Soft           #818494
Color / Action / Primary     #1668E3
Color / Action / Light       #C8DFF9
Color / Brand / Yellow       #FDDB32
Color / Surface / Canvas     #FFFFFF
Color / Surface / Subtle     #EFF3F7
Color / Border / Default     #DFE0E4
Color / Semantic / Positive  #227950
Color / Semantic / PosLight  #BEECC6
Color / Semantic / Warning   #8B6400
Color / Semantic / Error     #A7183C
Color / Overlay / Scrim      #0C0E1C
```

## Radius

```text
Radius / XS       4
Radius / Control  8
Radius / Card     12
Radius / Pill     999
```

## Spacing

```text
Space / 0.5   4
Space / 1     8
Space / 1.5  12
Space / 2    16
Space / 3    24
Space / 4    32
Space / 6    48
Space / 8    64
Space / 10   80
```

## Suggested components

- `Card / KPI`
- `Card / Chart`
- `Card / Insight`
- `Card / Hotel`
- `Chip / Default`
- `Chip / Selected`
- `Badge / Positive`
- `Badge / Highlight`
- `Button / Primary`
- `Table / Header`
- `SearchField / Presentation`
- `Section / Eyebrow`

---

# 13. Content style for the presentation

Visual design works best when copy also resembles a product analytics organization.

## Headline pattern

Prefer a conclusion, not a topic.

Weak:

> Booking conversion by weekday

Better:

> Weekend searches convert less despite higher intent signals

## Supporting copy

- short
- specific
- numeric
- no marketing fluff
- usually 1–2 sentences

## KPI formatting

Prefer:

> **+12.4%** booking conversion

rather than:

> Booking conversion demonstrated a statistically significant positive increase of 12.4 percent.

---

# 14. Anti-pattern checklist

Reject a generated block if any of these are true:

- yellow is used as the main slide background without a strong reason
- primary button is yellow by default
- more than 3 saturated colors compete on one slide
- cards have 24+ px radius
- shadows are heavy / floating
- background is dark on most slides
- charts have gradients or 3D effects
- every section uses travel photography
- typography looks geometric-futuristic instead of utilitarian
- Expedia Group corporate electric blue dominates instead of consumer cobalt/navy
- logo has been recreated with text
- hotel UI is copied so literally that it looks like a fake Expedia screenshot
- decorative icons outnumber actual insights

---

# 15. Prompt contract for a visual-generation agent

Copy the following block as the persistent design instruction for an agent generating individual slide visuals.

---

## EXPEDIA PRESENTATION VISUAL SYSTEM — AGENT INSTRUCTION

Design **16:9 analytical presentation visuals inspired by the current Expedia.com consumer product**, not a generic travel website and not primarily the Expedia Group corporate careers style.

### Visual DNA

Use a bright white marketplace canvas, strong midnight-navy information hierarchy, cobalt-blue interaction/data emphasis, and very sparse Expedia-yellow accents. The result must feel trustworthy, utilitarian, travel-native, commercial, modern and data-rich.

### Exact working palette

- primary ink: `#191E3B`
- primary blue: `#1668E3`
- light blue: `#C8DFF9`
- brand yellow: `#FDDB32`
- canvas: `#FFFFFF`
- subtle surface: `#EFF3F7`
- borders: `#DFE0E4`
- muted text: `#676A7D`
- soft text: `#818494`
- positive: `#227950`
- warning: `#8B6400`
- negative: `#A7183C`

### Typography

Use Inter, or Centra No.2 when available. Bold/semibold headings, highly legible body text, tabular figures for metrics. No futuristic display fonts.

### Geometry

- card radius: 12 px
- control radius: 8 px
- pill chips: fully rounded
- 1 px cool-gray borders
- minimal shadows
- generous internal padding
- 8 px spacing system

### Color discipline

- white/near-white should occupy roughly 70–85% of the composition
- cobalt blue is the main analytical and interactive color
- yellow must remain rare: use it to mark the single most important item, a small badge, tiny section marker or exceptional CTA
- do not make yellow the default primary button
- use green/red only semantically

### Data visualization

Make charts clean and flat. Use cobalt for primary data, navy or cool gray for comparison, pale blue for uncertainty/ranges. Thin light-gray gridlines. No gradients, no 3D, no glossy effects. Direct labels where possible.

### Components

Prefer Expedia-like product patterns: search fields, tabs, filter chips, hotel/result cards, bordered KPI cards, rating badges and clean list layouts. Translate these motifs into presentation components rather than reproducing a website screenshot.

### Photography

Use real-looking bright travel photography only when it improves the story: cover, destination example, section divider or recommendation mockup. Keep dense analytical slides mostly white.

### Icons

Simple 20–24 px outline travel/product icons with navy or cobalt stroke.

### Never do

No glassmorphism, neumorphism, neon gradients, giant pill cards, heavy shadows, dark-dashboard aesthetic, fake Expedia wordmark, oversaturated travel imagery, excessive decoration or dense walls of text.

### Presentation priority

Each visual must communicate one finding first. The reading order is: headline → key number/finding → evidence → supporting annotation.

---

# 16. Suggested generation jobs for the agent

Generate each as a separate editable-looking visual block rather than one complete deck image:

1. Cover hero block
2. Three-card KPI row
3. “One big insight” chart card
4. Search funnel visualization
5. User segment / RFM cards
6. Session-definition diagram
7. DWH architecture diagram
8. Seasonality heatmap card
9. Destination / origin map card
10. Hotel recommendation result card
11. Ranking-model comparison card
12. Conversion funnel card
13. Business-impact before/after card
14. Final conclusion block

This makes Figma assembly much easier than generating full slides as raster images.

---

# 17. Source / evidence notes

This guide was built from:

- the current Expedia.com homepage and current product copy/navigation observed in August 2026
- Expedia’s 2026 brand platform, **“The One Place You Go to Go Places”**
- public Expedia / Expedia Group media and logo materials
- Expedia Group public design-system references describing color, CentraNo2 typography, controls and layout
- Expedia Group Connectivity Partner brand guidance for logo handling
- public historical notes from Expedia design-system work on Centra typography
- current third-party reverse-engineering of Expedia.com consumer UI tokens, used only to help identify practical current product colors and then cross-checked against the live visual language

Where public Expedia Group corporate materials and the current Expedia consumer UI differ, this document intentionally prioritizes the **current Expedia.com consumer UI** because the target is an analytics presentation about the Expedia service.

---

# 18. Final recommendation for the hackathon deck

Do not try to make every slide look like a travel ad. The strongest interpretation is:

**“Expedia product UI turned into an internal analytics deck.”**

That means:

- mostly white
- serious navy typography
- blue data
- small yellow moments
- bordered cards
- clean product-like layouts
- occasional travel photography
- a few recognizable booking/recommendation UI motifs

This will look more authentic, more coherent with the dataset, and more convincing on a technical/business hackathon defense than a heavily branded advertising presentation.
