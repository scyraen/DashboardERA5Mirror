
.PHONY: run
run:
	streamlit run src/app.py

.PHONY: format 
format:
	black .

.PHONY: lint lint-fix
lint:
	ruff check .
lint-fix:
	ruff check . --fix

.PHONY: clean
clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -prune -exec rm -rf {} +
	find . -name '.DS_Store' -exec rm -rf {} +
	find . -name '.ruff_cache' -exec rm -rf {} +