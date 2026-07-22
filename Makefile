# Ω∞v OceanicOS — full-stack build targets
IMAGE ?= oceanicos
PORT ?= 5000

.PHONY: help install test run build docker-build docker-run stack verify-ledger boot clean

help:
	@echo "OceanicOS full-stack targets:"
	@echo "  make install       install runtime + test deps"
	@echo "  make test          run the full test suite"
	@echo "  make run           run the app under gunicorn (PORT=$(PORT))"
	@echo "  make docker-build  build the container image ($(IMAGE))"
	@echo "  make docker-run    run the container image"
	@echo "  make stack         test -> docker-build -> docker-run (the full stack)"
	@echo "  make verify-ledger verify an exported ledger offline (BUNDLE=path [KEY=secret])"
	@echo "  make boot          instantiate the stack from boot/init.v1 (the invocation)"
	@echo "  make doctor        check readiness, verify the ledger, print stats (offline)"
	@echo "  make clean         remove local db, workspace, and caches"

install:
	pip install -r requirements.txt

test:
	OCEANICOS_DB=$${OCEANICOS_DB:-/tmp/oceanicos-test.db} \
	OCEANICOS_WORKSPACE=$${OCEANICOS_WORKSPACE:-/tmp/oceanicos-test-ws} \
	python -m pytest -q

run:
	gunicorn --bind 0.0.0.0:$(PORT) --workers 2 wsgi:app

build: docker-build

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p $(PORT):$(PORT) -e PORT=$(PORT) $(IMAGE)

# The full stack: verify, containerize, launch.
stack: test docker-build
	@echo "Stack built. Launch with: make docker-run"

# Verify an exported attestation ledger offline — the ground truth without the system.
# Usage: make verify-ledger BUNDLE=bundle.json [KEY=your-signing-key]
verify-ledger:
	python verify_ledger.py $(if $(KEY),--key $(KEY),) "$(BUNDLE)"

# Operator CLI: check the ledger and dependencies offline, no server needed.
doctor:
	python oceanic_os.py ready && python oceanic_os.py verify && python oceanic_os.py stats

# The invocation: boot the stack from the ratified manifest.
boot:
	python oceanic_os.py --boot boot/init.v1 --state stateless --exit 0

clean:
	rm -f oceanicos.db *.sqlite3
	rm -rf workspace __pycache__ tests/__pycache__ .pytest_cache
