#!/usr/bin/env sh
set -eu

RAW_DIR="${1:-architecture/raw}"
OUT_DIR="${2:-architecture/rendered}"
FORMAT="${3:-png}"

case "$FORMAT" in
  png|svg|both) ;;
  *)
    echo "Invalid format '$FORMAT' (use: png|svg|both)" >&2
    exit 1
    ;;
esac

if [ ! -d "$RAW_DIR" ]; then
  echo "Missing raw directory: $RAW_DIR" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

drawio_export() {
  fmt="$1"
  src="$2"
  out="$3"

  if command -v xvfb-run >/dev/null 2>&1; then
    if [ "$(id -u)" = "0" ]; then
      xvfb-run -a drawio --no-sandbox --export --format "$fmt" --transparent --output "$out" "$src"
    else
      xvfb-run -a drawio --export --format "$fmt" --transparent --output "$out" "$src"
    fi
  else
    if [ "$(id -u)" = "0" ]; then
      drawio --no-sandbox --export --format "$fmt" --transparent --output "$out" "$src"
    else
      drawio --export --format "$fmt" --transparent --output "$out" "$src"
    fi
  fi
}

found=0
for f in "$RAW_DIR"/*.drawio; do
  if [ ! -e "$f" ]; then
    continue
  fi
  found=1
  name=$(basename "$f" .drawio)
  echo "Rendering $f"
  if [ "$FORMAT" = "png" ] || [ "$FORMAT" = "both" ]; then
    drawio_export png "$f" "$OUT_DIR/$name.png"
  fi
  if [ "$FORMAT" = "svg" ] || [ "$FORMAT" = "both" ]; then
    drawio_export svg "$f" "$OUT_DIR/$name.svg"
  fi
done

if [ "$found" -eq 0 ]; then
  echo "No .drawio files found in $RAW_DIR"
fi
