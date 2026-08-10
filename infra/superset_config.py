"""Minimal local Superset configuration for the Expedia BI stack."""

import os


SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://superset:superset@db:5432/superset"
)

FEATURE_FLAGS = {"ENABLE_TEMPLATE_PROCESSING": True}
WTF_CSRF_ENABLED = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
