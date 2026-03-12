SHELL := /bin/sh

NAME ?= baseline
PROMPT ?= public alb, ecs service, rds postgres

.PHONY: help init generate validate render render-all demo clean

help:
	@printf "Targets:\n"
	@printf "  make init                          - create local folders\n"
	@printf "  make generate NAME=<n> PROMPT=...  - generate .drawio XML\n"
	@printf "  make validate                      - validate architecture/raw/*.drawio\n"
	@printf "  make render                        - validate then render PNG via Docker\n"
	@printf "  make render-all                    - validate then render PNG+SVG\n"
	@printf "  make demo                          - generate + validate + render\n"

init:
	@mkdir -p architecture/raw architecture/rendered architecture/specs

generate: init
	@python3 scripts/generate_xml.py --name "$(NAME)" --prompt "$(PROMPT)"

validate:
	@python3 scripts/validate_drawio.py architecture/raw

render: validate
	@docker compose -f docker/compose.yml run --rm renderer

render-all: validate
	@docker compose -f docker/compose.yml run --rm renderer sh scripts/render.sh architecture/raw architecture/rendered both

demo: generate validate render

clean:
	@rm -f architecture/rendered/*.png architecture/rendered/*.svg
