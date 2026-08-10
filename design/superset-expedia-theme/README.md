# Expedia Hotel Analytics theme

This is the reusable Superset 6.x visual layer for the Expedia Hotel Analytics hackathon prototype. It uses the supplied, unmodified Expedia consumer logo and the local design package as its source of truth.

## What changes

- Native Ant Design/Superset tokens establish the light marketplace canvas, Inter typography, cobalt interaction states, navy hierarchy, compact controls, and restrained borders.
- The instance-wide `Expedia Analytics` default scheme sets the ECharts palette; chart authors can use the named sequential and semantic schemes where those encodings are appropriate.
- Superset exposes the `Expedia Analytics`, `Expedia Blue Sequential`, and `Expedia Semantic` schemes to chart authors.
- Docker mounts the supplied logo into Superset's static directory; the application shell is named **Expedia Hotel Analytics** and explicitly labelled a **Hackathon prototype**.
- `expedia-dashboard.css` is an optional dashboard CSS template for chart cards, tabs, native filters, tables, and empty states that theme tokens alone cannot scope to a dashboard.

## Token source and customization

`expedia-theme.json` is the canonical theme. Change colors, typography, or component radii there. The durable local runtime configuration at `superset/docker/pythonpath_dev/superset_config.py` loads that JSON.

The branding asset is `design/brand/expedia_logo_fullcolor_light_bg.svg`. It is mounted read-only into the container and is never recolored or copied into application source.

## Applying the theme

The compose instance loads the theme as `THEME_DEFAULT`, so it applies to the entire instance after a restart. Theme administration remains enabled; an administrator can inspect, export, or replace a system theme in **Settings → Themes**.

For the strongest dashboard canvas treatment, paste or select the contents of `expedia-dashboard.css` in **Edit dashboard → Properties → CSS**. This is intentionally optional: themes and color schemes still apply to every dashboard without it.

## Run

From `superset/`:

```bash
docker compose up -d --build
docker compose restart superset superset-worker superset-worker-beat
```

No frontend rebuild is required for token/configuration changes in the mounted Docker development setup. Rebuild the frontend only when changing files under `superset-frontend/`.

## Core source changes

None. The implementation uses Superset 6.x configuration and theme APIs plus Docker read-only asset mounts.
