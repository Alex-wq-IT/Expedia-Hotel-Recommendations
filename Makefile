.PHONY: bi-up bi-down bi-build bi-publish bi-export bi-all bi-test

bi-up:
	docker compose -f infra/docker-compose.yml up -d

bi-down:
	docker compose -f infra/docker-compose.yml down

bi-build:
	python tools/build_analytics.py

bi-publish:
	python tools/publish_bi.py publish

bi-export:
	python tools/publish_bi.py export

bi-all:
	python tools/build_analytics.py
	python tools/publish_bi.py all

bi-test:
	python -m unittest discover -s tests -v
