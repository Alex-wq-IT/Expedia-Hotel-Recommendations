FROM apache/superset:latest

USER root
RUN uv pip install --python /app/.venv/bin/python \
    "clickhouse-connect>=0.5.14,<1.0" \
    "psycopg2-binary"
