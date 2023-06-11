
setup: venv install pre-commit

venv:
	@echo "Creating venv..."
	poetry env use python3.10

install: pre-commit
	@echo "Installing dependencies..."
	poetry install --no-root --sync
	poetry run playwright install --with-deps --force

pre-commit:
	@echo "Setting up pre-commit..."
	poetry run pre-commit install
	poetry run pre-commit autoupdate

test:
	@echo "Running test coverage..."
	pytest -vv --cov-report term-missing --cov-report xml --cov=scrapy_kit --cov-fail-under=60 tests/


export_requirements:
	@echo "Exporting requirements..."
	poetry export --without-hashes -f requirements.txt --output requirements.txt
	poetry export --without-hashes -f requirements.txt --output requirements-dev.txt --with dev
	poetry export --without-hashes -f requirements.txt --output requirements-doc.txt --with doc

doc:
	@echo "Building docs..."
	mkdocs build

doc_serve:
	@echo "Serving docs..."
	mkdocs serve

tag:
	@echo "Tagging version..."
	poetry version patch
	version=$$(poetry version | grep -Eo "[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+"); \
	git add pyproject.toml; \
	git commit -m "Bump version to $${version}"; \
	git tag $${version}; \
	git push origin main --tags
