SHELL := /bin/sh

NAME ?= baseline
PROMPT ?= public alb, ecs service, rds postgres

.PHONY: help init generate validate validate-file render render-file render-all demo start chat chat-file qa-smoke clean

help:
	@printf "Targets:\n"
	@printf "  make init                          - create local folders\n"
	@printf "  make generate NAME=<n> PROMPT=...  - generate .drawio XML\n"
	@printf "  make validate                      - validate architecture/raw/*.drawio\n"
	@printf "  make render                        - validate then render PNG via Docker\n"
	@printf "  make render-file FILE=<n.drawio>   - validate + render one file\n"
	@printf "  make render-all                    - validate then render PNG+SVG\n"
	@printf "  make demo                          - generate + validate + render\n"
	@printf "  make start                         - interactive mode with startup checks\n"
	@printf "  make chat                          - interactive natural language mode\n"
	@printf "  make chat-file FILE=<n.drawio>     - interactive mode with active file\n"
	@printf "  make qa-smoke                      - run automated smoke QA checks\n"

init:
	@mkdir -p architecture/raw architecture/rendered architecture/specs

generate: init
	@python3 scripts/generate_xml.py --name "$(NAME)" --prompt "$(PROMPT)"

validate:
	@python3 scripts/validate_drawio.py architecture/raw

validate-file:
	@test -n "$(FILE)" || (printf "FILE is required\n" && exit 2)
	@python3 scripts/validate_drawio.py "$(FILE)"

render: validate
	@docker compose -f docker/compose.yml run --rm renderer

render-file: validate-file
	@python3 scripts/archsmith_cli.py --file "$(FILE)" <<'EOF'
:render
:quit
EOF

render-all: validate
	@docker compose -f docker/compose.yml run --rm renderer sh scripts/render.sh architecture/raw architecture/rendered both

demo: generate validate render

start:
	@python3 scripts/archsmith_cli.py --start

chat:
	@python3 scripts/archsmith_cli.py

chat-file:
	@test -n "$(FILE)" || (printf "FILE is required\n" && exit 2)
	@python3 scripts/archsmith_cli.py --file "$(FILE)"

qa-smoke:
	@python3 scripts/qa_smoke.py

clean:
	@rm -f architecture/rendered/*.png architecture/rendered/*.svg
