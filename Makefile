.PHONY: bootstrap dev demo verify loc

bootstrap:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	cd apps/dashboard && npm ci

dev:
	./scripts/dev.sh

demo:
	./scripts/demo.sh

verify:
	./scripts/verify.sh

loc:
	python scripts/loc.py
