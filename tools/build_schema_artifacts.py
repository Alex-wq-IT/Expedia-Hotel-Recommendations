"""Render a current RAW → STAGING → CORE → MARTS catalog as Markdown and HTML.

The catalog is inspected read-only. The renderer intentionally documents only
objects currently registered in analytics.duckdb plus the materialized Parquet
paths already present in the repository.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "analytics.duckdb"
ARTIFACTS = ROOT / "artifacts"
LAYERS = ("raw", "staging", "core", "marts")

LAYER_META = {
    "raw": {
        "title": "RAW",
        "purpose": "Immutable source-aligned views over Expedia train, test and destinations data.",
        "processing": "No business cleaning, deduplication, imputation or aggregation. Source semantics are preserved.",
        "path": "data/parquet/ and source CSV files; catalog views in analytics.duckdb",
    },
    "staging": {
        "title": "STAGING",
        "purpose": "Source-grain technical normalization and data-quality metadata.",
        "processing": "Type/date normalization, source metadata, duplicate metadata, missing-distance and quality flags; no destructive filtering or business aggregation.",
        "path": "data/derived/staging/*.parquet",
    },
    "core": {
        "title": "CORE",
        "purpose": "Business entities, facts, deterministic derived features and validated distance enrichment.",
        "processing": "Controlled exact deduplication, dimensions, event/booking facts, date and search features, validity flags, and median distance imputation with provenance.",
        "path": "data/derived/core/*.parquet",
    },
    "marts": {
        "title": "MARTS",
        "purpose": "Business-ready analytical aggregates for product, session, travel, channel, destination and retention analysis.",
        "processing": "Train-only behavioral aggregation where applicable; row-based and cnt-weighted measures are kept explicitly named.",
        "path": "data/derived/marts/*.parquet",
    },
}

TABLE_META = {
    "raw.train": ("Source train interaction log", "one source train log row; train-only booking fields are present"),
    "raw.test": ("Source test interaction log", "one source test log row; no booking outcome fields"),
    "raw.destinations": ("Source latent destination features", "one destination ID with latent d1…d149 features"),
    "staging.interaction": ("Normalized interaction stream", "one source interaction row, preserving source grain"),
    "staging.destinations": ("Normalized destinations reference", "one source destination row"),
    "core.dim_date": ("Calendar dimension", "one row per valid calendar day"),
    "core.dim_hour": ("Hour-of-day dimension", "one row per hour of day"),
    "core.dim_user": ("User dimension", "one row per observed user"),
    "core.dim_user_location": ("Observed user location dimension", "one row per observed country/region/city combination"),
    "core.dim_platform": ("Point-of-sale platform dimension", "one row per site_name × posa_continent combination"),
    "core.dim_destination": ("Destination dimension", "one row per destination ID, with latent features when available"),
    "core.dim_destination_type": ("Destination type dimension", "one row per destination type ID"),
    "core.dim_hotel_market": ("Hotel market dimension", "one row per observed market × country × continent combination"),
    "core.dim_hotel_cluster": ("Hotel cluster dimension", "one row per hotel cluster ID"),
    "core.dim_search_params": ("Search parameters dimension", "one row per adults × children × rooms × stay/party feature combination"),
    "core.fct_event": ("Deduplicated event fact", "one unique aggregated source log row after controlled exact deduplication"),
    "core.fct_booking": ("Booking fact", "one train booking log event, filtered to is_booking = 1"),
    "core.ref_distance_stats": ("Distance estimator reference", "one median estimator per imputation hierarchy group"),
    "core.event_session_map": ("Event-to-session bridge", "one eligible train event assigned to one session-rule version"),
    "core.fct_session": ("Reconstructed session fact", "one reconstructed user session under gap_30m_v1"),
    "marts.mart_product_daily": ("Daily product KPI mart", "one event date"),
    "marts.mart_session_daily": ("Daily session KPI mart", "one session start date"),
    "marts.mart_travel_calendar_daily": ("Travel calendar mart", "one calendar date, combining event and stay-date roles"),
    "marts.mart_channel_platform": ("Channel/platform performance mart", "one month × channel × platform × mobile flag"),
    "marts.mart_destination_performance": ("Destination performance mart", "one month × destination × hotel market"),
    "marts.mart_user_360": ("User 360 mart", "one user"),
    "marts.mart_origin_destination": ("Origin-destination mart", "one month × user country × hotel country"),
    "marts.mart_trip_profile": ("Trip profile mart", "one month × lead bucket × stay bucket × party segment"),
    "marts.mart_retention_cohort": ("Booking retention mart", "one first-booking month × months since first booking"),
    "marts.mart_booking_frequency": ("Booking frequency mart", "one booking-count bucket"),
    "marts.mart_data_quality_daily": ("Daily data-quality mart", "one event date"),
    "marts.mart_distance_quality": ("Distance quality mart", "one imputation level × support threshold"),
}

TABLE_META["core.session_events"] = ("Sessionization fragments", "one eligible event per deterministic user-hash fragment")
TABLE_META["core.session_summaries"] = ("Sessionization summary fragments", "one reconstructed session per deterministic user-hash fragment")

EDGES = [
    ("raw.train", "staging.interaction", "type/date normalization + quality flags"),
    ("raw.test", "staging.interaction", "same source-grain interaction contract"),
    ("raw.destinations", "staging.destinations", "source metadata + column rename"),
    ("staging.interaction", "core.fct_event", "deduplicate + keys + derived features"),
    ("staging.destinations", "core.dim_destination", "destination dimension + d1…d149"),
    ("core.fct_event", "core.fct_booking", "filter train bookings"),
    ("core.fct_event", "core.dim_user", "distinct user IDs"),
    ("core.fct_event", "core.dim_user_location", "observed location combinations"),
    ("core.fct_event", "core.dim_platform", "site_name × posa_continent"),
    ("core.fct_event", "core.dim_destination_type", "distinct type IDs"),
    ("core.fct_event", "core.dim_hotel_market", "market attribute combinations"),
    ("core.fct_event", "core.dim_hotel_cluster", "distinct cluster IDs"),
    ("core.fct_event", "core.dim_search_params", "distinct search feature combinations"),
    ("core.fct_event", "core.dim_date", "event/check-in/check-out date roles"),
    ("core.fct_event", "core.dim_hour", "event hour role"),
    ("core.fct_event", "core.ref_distance_stats", "validated median estimators"),
    ("core.fct_event", "core.event_session_map", "gap_30m_v1 session assignment"),
    ("core.event_session_map", "core.fct_session", "session aggregation"),
]
for mart in (
    "mart_product_daily", "mart_session_daily", "mart_travel_calendar_daily",
    "mart_channel_platform", "mart_destination_performance", "mart_user_360",
    "mart_origin_destination", "mart_trip_profile", "mart_retention_cohort",
    "mart_booking_frequency", "mart_data_quality_daily", "mart_distance_quality",
):
    source = "core.fct_session" if mart in {"mart_session_daily", "mart_retention_cohort", "mart_booking_frequency"} else "core.fct_event"
    EDGES.append((source, f"marts.{mart}", "business aggregation"))

SPECIAL_FIELDS = {
    "date_time": "Source event timestamp; distinct from requested check-in and check-out dates.",
    "event_ts": "Normalized event timestamp derived from date_time.",
    "srch_ci": "Source requested check-in date; source-aligned value may be text.",
    "srch_co": "Source requested check-out date; source-aligned value may be text/date.",
    "checkin_date": "Normalized requested check-in date.",
    "checkout_date": "Normalized requested check-out date.",
    "cnt": "Multiplicity of similar events represented by the source log row; not a session ID.",
    "is_booking": "Train outcome flag: 1 means booking, 0 means click/non-booking interaction.",
    "booking_value_proxy": "Relative package/value proxy: 0 non-booking, 1 hotel-only booking, 2 package booking; not revenue.",
    "posa_continent": "Encoded point-of-sale continent associated with site_name, not necessarily user geography.",
    "orig_destination_distance": "Source physical distance from user origin to destination when available.",
    "distance_raw": "Immutable source distance before any enrichment.",
    "distance_filled": "Distance used for analysis: source distance or validated CORE estimate.",
    "distance_imputation_level": "Hierarchy level used to fill a missing distance, if any.",
    "source_row_id": "Deterministic source row identifier used for lineage and duplicate selection.",
    "source_dataset": "Source population label, such as train, test or destinations.",
    "quality_issue_count": "Count of quality flags raised for the row.",
}


def field_description(table: str, name: str, dtype: str) -> str:
    if name in SPECIAL_FIELDS:
        return SPECIAL_FIELDS[name]
    if re.fullmatch(r"d\d+", name):
        return "Latent destination/search-region feature; encoded numeric signal, not human-readable geography."
    if name.startswith("q_") or name in {"distance_was_missing", "distance_is_imputed", "valid_for_lead_time", "valid_for_stay_length", "valid_for_party_metrics"}:
        return "Boolean data-quality or metric-validity flag produced by the pipeline."
    if name.endswith("_date_key") or name == "date_key":
        return "Integer YYYYMMDD key for a calendar-date role."
    if name.endswith("_hour_key") or name == "hour_key":
        return "Integer key for the hour-of-day dimension."
    if name.endswith("_id"):
        if table.startswith("raw.") or table.startswith("staging."):
            return "Encoded source identifier; no real-world name is inferred from this value."
        return "Surrogate or encoded identifier used to join this entity in the analytical model."
    if name in {"hotel_continent", "hotel_country", "hotel_market", "user_country", "user_region", "user_city", "site_name", "channel", "destination_type_id"}:
        return "Encoded categorical identifier; treat as an ID rather than a real-world label."
    if name in {"loaded_at", "first_seen_date", "last_seen_date", "first_booking_date", "last_booking_date", "observation_end_date", "full_date", "cohort_month"}:
        return "Date or timestamp used for lineage, cohorting or calendar analysis."
    if name.endswith("_share") or name.endswith("_rate") or name.endswith("_pct"):
        return "Ratio metric; numerator and denominator are defined by the mart build logic."
    if name.startswith("avg_") or name.startswith("median_"):
        return "Aggregated average or median measure at the table grain."
    if name.endswith("_count") or name in {"rows", "events", "bookings", "bookers", "users", "sessions", "active_users", "weighted_events", "row_events"}:
        return "Aggregated count at the table grain; weighted measures use SUM(cnt) where explicitly named."
    if name in {"year", "quarter", "month", "iso_week", "day_of_month", "day_of_year", "day_of_week", "hour"}:
        return "Calendar or clock attribute."
    if name in {"is_mobile", "is_package", "has_children", "is_weekend", "meets_min_volume_flag", "meets_booking_min_volume_flag"}:
        return "Boolean or encoded indicator retained for segmentation."
    if name.startswith("lead_") or name.startswith("stay_") or name in {"party_size", "adults_cnt", "children_cnt", "room_cnt"}:
        return "Derived or requested trip/search characteristic."
    return f"Field in the {table} object; physical type {dtype}."


def catalog() -> dict[str, list[dict]]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows = con.execute(
            """SELECT table_schema, table_name FROM information_schema.tables
               WHERE table_schema IN ('raw', 'staging', 'core', 'marts')
               ORDER BY table_schema, table_name"""
        ).fetchall()
        result = {layer: [] for layer in LAYERS}
        for layer, name in rows:
            fq = f"{layer}.{name}"
            cols = con.execute(
                """SELECT column_name, data_type, is_nullable
                   FROM information_schema.columns
                   WHERE table_schema = ? AND table_name = ?
                   ORDER BY ordinal_position""", [layer, name]
            ).fetchall()
            description, grain = TABLE_META.get(fq, ("Registered analytical object", "Grain documented by the current contract."))
            parquet = None
            if layer in {"staging", "core", "marts"}:
                candidate = ROOT / "data" / "derived" / layer / f"{name}.parquet"
                parquet = str(candidate.relative_to(ROOT)) if candidate.exists() else None
            result[layer].append({
                "name": fq,
                "short_name": name,
                "description": description,
                "grain": grain,
                "parquet": parquet,
                "columns": [
                    {"name": c, "type": t, "nullable": n == "YES", "description": field_description(fq, c, t)}
                    for c, t, n in cols
                ],
            })
        return result
    finally:
        con.close()


def render_markdown(data: dict[str, list[dict]]) -> str:
    lines = [
        "# Текущая схема данных Expedia Analytics",
        "",
        "> Сгенерировано `tools/build_schema_artifacts.py` из read-only каталога `data/analytics.duckdb`; состояние на момент генерации отражает зарегистрированные объекты и существующие Parquet-слои.",
        "",
        "## Поток",
        "",
        "`RAW → STAGING → CORE → MARTS → BI / product analytics`",
        "",
        "### Правила интерпретации",
        "",
        "- `raw` неизменяем: исходные значения, включая NULL и encoded IDs, сохраняются.",
        "- STAGING сохраняет grain источника и добавляет технические типы, даты, lineage и quality flags.",
        "- CORE делает controlled exact deduplication, dimensions, facts, derived features и validated distance enrichment.",
        "- MARTS агрегируют преимущественно train-популяцию; row-based объёмы используют `COUNT(*)`, weighted-объёмы — `SUM(cnt)`.",
        "- `date_time` — event time; `srch_ci`/`srch_co` — даты запрошенного проживания, их нельзя смешивать.",
        "- `posa_continent`, location, hotel и destination IDs — encoded IDs; реальные географические названия из них не выводятся.",
        "",
        "## Обработки по слоям",
        "",
    ]
    for layer in LAYERS:
        meta = LAYER_META[layer]
        lines += [f"### {meta['title']}", "", f"**Назначение:** {meta['purpose']}", "", f"**Обработка:** {meta['processing']}", "", f"**Материализация:** `{meta['path']}`", ""]
    lines += ["## Lineage", "", "| Откуда | Куда | Обработка |", "|---|---|---|"]
    lines += [f"| `{a}` | `{b}` | {label} |" for a, b, label in EDGES]
    lines += ["", "## Таблицы и поля", ""]
    for layer in LAYERS:
        lines += [f"### {layer.upper()}", ""]
        for table in data[layer]:
            lines += [f"#### `{table['name']}`", "", table["description"] + ".", "", f"**Зерно:** {table['grain']}."]
            if table["parquet"]:
                lines.append(f"**Parquet:** `{table['parquet']}`")
            lines += ["", "| Поле | Тип | Nullable | Описание |", "|---|---|:---:|---|"]
            for col in table["columns"]:
                desc = col["description"].replace("|", "\\|")
                lines.append(f"| `{col['name']}` | `{col['type']}` | {'да' if col['nullable'] else 'нет'} | {desc} |")
            lines.append("")
    lines += ["## HTML-диаграмма", "", "Интерактивная версия: [`data_flow.html`](data_flow.html). Нажмите на таблицу, чтобы раскрыть поля; наведите курсор на поле, чтобы увидеть описание.", ""]
    return "\n".join(lines)


def render_html(data: dict[str, list[dict]]) -> str:
    payload = json.dumps({"layers": data, "edges": EDGES}, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HotelsBooking · Data Flow</title>
<style>
:root {{ --ink:#17212b; --muted:#657482; --line:#dbe4ea; --bg:#f5f8fa; --accent:#0b5cab; --raw:#eef5ff; --stg:#eef9f3; --core:#fff7e6; --mart:#f6efff; }}
* {{ box-sizing:border-box }} body {{ margin:0; color:var(--ink); font:14px/1.45 Inter, ui-sans-serif, system-ui, sans-serif; background:var(--bg) }}
header {{ padding:28px 34px 22px; background:#fff; border-bottom:1px solid var(--line) }} h1 {{ margin:0 0 6px; font-size:26px }} h2 {{ margin:0 0 6px; font-size:18px }} p {{ margin:5px 0; color:var(--muted) }}
.toolbar {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:18px }} input {{ min-width:280px; flex:1; padding:10px 12px; border:1px solid var(--line); border-radius:8px; font:inherit }} button {{ border:1px solid var(--line); background:#fff; padding:9px 12px; border-radius:8px; cursor:pointer }} button:hover {{ border-color:var(--accent); color:var(--accent) }}
main {{ padding:24px 28px 48px; overflow:auto }} .flow {{ display:grid; grid-template-columns:repeat(4,minmax(270px,1fr)); gap:18px; min-width:1160px; align-items:start }}
.layer {{ position:relative; min-height:140px }} .layer-head {{ border-radius:12px; padding:15px; margin-bottom:12px; border:1px solid var(--line) }} .layer-head small {{ display:block; color:var(--muted); margin-top:6px }}
.layer.raw .layer-head {{ background:var(--raw) }} .layer.staging .layer-head {{ background:var(--stg) }} .layer.core .layer-head {{ background:var(--core) }} .layer.marts .layer-head {{ background:var(--mart) }}
.table {{ background:#fff; border:1px solid var(--line); border-radius:10px; margin:10px 0; overflow:visible; box-shadow:0 2px 7px #162b3d0b; cursor:pointer }} .table:hover {{ border-color:#8fb5d3; box-shadow:0 5px 14px #162b3d18 }}
.table-title {{ padding:11px 13px; font-weight:700; position:relative }} .table-title code {{ font-size:13px }} .badge {{ float:right; color:var(--muted); font-size:11px; font-weight:500 }} .table-desc {{ padding:0 13px 10px; color:var(--muted); font-size:12px }}
.fields {{ display:none; border-top:1px solid var(--line); padding:4px 0 7px }} .table.open .fields {{ display:block }} .field {{ position:relative; display:grid; grid-template-columns:1fr auto; gap:8px; padding:5px 13px; font-size:12px }} .field:hover {{ background:#f0f6fb }} .field code {{ color:#174d77 }} .type {{ color:var(--muted); font-size:11px }}
.tooltip {{ display:none; position:absolute; z-index:20; left:13px; right:13px; top:100%; margin-top:4px; padding:9px 10px; background:#17212b; color:#fff; border-radius:7px; box-shadow:0 5px 20px #0003; font-size:12px; font-weight:400 }} .field:hover .tooltip {{ display:block }}
.legend {{ display:flex; gap:16px; flex-wrap:wrap; margin:18px 0 12px; color:var(--muted); font-size:12px }} .legend span::before {{ content:''; display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:5px; background:var(--c) }}
.edges {{ margin-top:24px; background:#fff; border:1px solid var(--line); border-radius:12px; padding:16px; min-width:900px }} .edges table {{ width:100%; border-collapse:collapse }} .edges td,.edges th {{ text-align:left; padding:7px 9px; border-bottom:1px solid var(--line) }} .edges th {{ font-size:12px; color:var(--muted) }} .empty {{ color:var(--muted); font-style:italic }}
@media(max-width:900px) {{ header {{ padding:22px 18px }} main {{ padding:18px 12px }} }}
</style></head>
<body><header><h1>HotelsBooking · Data Flow</h1><p>Текущий поток данных: RAW → STAGING → CORE → MARTS. Схема построена из каталога DuckDB и файлов derived-слоёв.</p><div class="toolbar"><input id="search" placeholder="Фильтр по таблице или полю…"><button id="expand">Раскрыть всё</button><button id="collapse">Свернуть всё</button></div></header>
<main><div class="legend"><span style="--c:var(--raw)">RAW</span><span style="--c:var(--stg)">STAGING</span><span style="--c:var(--core)">CORE</span><span style="--c:var(--mart)">MARTS</span><span>Клик по карточке — поля</span><span>Наведение на поле — описание</span></div><section id="flow" class="flow"></section><section class="edges"><h2>Потоки и обработки</h2><table><thead><tr><th>Откуда</th><th>Куда</th><th>Обработка</th></tr></thead><tbody id="edges"></tbody></table></section></main>
<script>
const model = {payload};
const flow = document.querySelector('#flow');
const esc = s => String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
function draw() {{
  flow.innerHTML = '';
  for (const layer of ['raw','staging','core','marts']) {{
    const meta = {json.dumps(LAYER_META, ensure_ascii=False)}[layer];
    const section = document.createElement('section'); section.className = `layer ${{layer}}`;
    section.innerHTML = `<div class="layer-head"><h2>${{meta.title}}</h2><p>${{esc(meta.purpose)}}</p><small>${{esc(meta.processing)}}</small></div>`;
    for (const t of model.layers[layer]) {{
      const card = document.createElement('article'); card.className='table'; card.dataset.search = `${{t.name}} ${{t.description}} ${{t.columns.map(c=>c.name+' '+c.description).join(' ')}}`.toLowerCase();
      card.innerHTML = `<div class="table-title"><code>${{esc(t.name)}}</code><span class="badge">${{t.columns.length}} полей</span></div><div class="table-desc">${{esc(t.description)}}<br><em>${{esc(t.grain)}}</em></div><div class="fields">${{t.columns.map(c=>`<div class="field"><span><code>${{esc(c.name)}}</code></span><span class="type">${{esc(c.type)}}${{c.nullable?' · NULL':''}}</span><span class="tooltip">${{esc(c.description)}}</span></div>`).join('')}}</div>`;
      card.addEventListener('click', () => card.classList.toggle('open'));
      section.appendChild(card);
    }}
    flow.appendChild(section);
  }}
  renderEdges();
}}
function renderEdges() {{ document.querySelector('#edges').innerHTML = model.edges.map(e=>`<tr><td><code>${{esc(e[0])}}</code></td><td><code>${{esc(e[1])}}</code></td><td>${{esc(e[2])}}</td></tr>`).join(''); }}
document.querySelector('#search').addEventListener('input', e => {{ const q=e.target.value.toLowerCase().trim(); document.querySelectorAll('.table').forEach(t=>t.style.display=(!q||t.dataset.search.includes(q))?'block':'none'); }});
document.querySelector('#expand').addEventListener('click', () => document.querySelectorAll('.table').forEach(t=>t.classList.add('open')));
document.querySelector('#collapse').addEventListener('click', () => document.querySelectorAll('.table').forEach(t=>t.classList.remove('open')));
draw();
</script></body></html>'''


def main() -> None:
    data = catalog()
    (ARTIFACTS / "schema.md").write_text(render_markdown(data), encoding="utf-8")
    (ARTIFACTS / "data_flow.html").write_text(render_html(data), encoding="utf-8")
    counts = {layer: len(tables) for layer, tables in data.items()}
    print(json.dumps({"artifacts": ["artifacts/schema.md", "artifacts/data_flow.html"], "objects": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
