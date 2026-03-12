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

found=0
for f in "$RAW_DIR"/*.drawio; do
  if [ ! -e "$f" ]; then
    continue
  fi
  found=1
  name=$(basename "$f" .drawio)
  echo "Rendering $f"
  if [ "$FORMAT" = "png" ] || [ "$FORMAT" = "both" ]; then
    drawio --export --format png --transparent --output "$OUT_DIR/$name.png" "$f"
  fi
  if [ "$FORMAT" = "svg" ] || [ "$FORMAT" = "both" ]; then
    drawio --export --format svg --transparent --output "$OUT_DIR/$name.svg" "$f"
  fi
done

if [ "$found" -eq 0 ]; then
  echo "No .drawio files found in $RAW_DIR"
fi
