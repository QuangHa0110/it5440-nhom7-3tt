.DEFAULT_GOAL := help
SHELL := /bin/bash
UV ?= uv
PART ?= patch
PLANTUML ?= plantuml

.PHONY: help
help:  ## Liệt kê lệnh
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[1m%-12s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup:  ## Cài môi trường và hook pre-commit
	$(UV) sync
	$(UV) run pre-commit install

.PHONY: lint
lint:  ## Ruff: kiểm tra lỗi và định dạng
	$(UV) run ruff check .
	$(UV) run ruff format --check .

.PHONY: fmt
fmt:  ## Ruff: tự sửa lỗi và định dạng
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

.PHONY: typecheck
typecheck:  ## Mypy strict
	$(UV) run mypy

.PHONY: test
test:  ## Chạy pytest (bỏ qua nếu chưa có test)
	$(UV) run pytest || [ $$? -eq 5 ]

.PHONY: check
check: lint typecheck test  ## Cổng trước khi mở PR (giống CI)

.PHONY: diagrams
diagrams:  ## Render sơ đồ PlantUML ra SVG. PLANTUML="java -jar plantuml.jar" nếu chưa cài
	cd docs/diagrams && $(PLANTUML) -tsvg -o out *.puml

.PHONY: bump
bump:  ## Nâng phiên bản + commit + tag. PART=patch|minor|major. Chạy trên main sạch
	@[ "$$(git branch --show-current)" = "main" ] || { echo "bump chỉ chạy trên main"; exit 1; }
	$(UV) run bump-my-version bump $(PART)
