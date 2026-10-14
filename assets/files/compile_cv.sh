#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
tex_file="${1:-${script_dir}/cv_en.tex}"

if [[ "$tex_file" != /* ]]; then
  tex_file="$(cd -- "$(dirname -- "$tex_file")" && pwd)/$(basename -- "$tex_file")"
fi

if [[ ! -f "$tex_file" ]]; then
  printf 'Error: TeX file not found: %s\n' "$tex_file" >&2
  exit 1
fi

if [[ "${tex_file##*.}" != "tex" ]]; then
  printf 'Error: expected a .tex file: %s\n' "$tex_file" >&2
  exit 1
fi

if [[ $# -ge 2 ]]; then
  output_pdf="$2"
elif [[ "$(basename -- "$tex_file")" == "cv_en.tex" ]]; then
  output_pdf="${script_dir}/CV202609_EN.pdf"
else
  output_pdf="$(dirname -- "$tex_file")/$(basename -- "$tex_file" .tex).pdf"
fi

if [[ "$output_pdf" != /* ]]; then
  output_pdf="$(pwd)/$output_pdf"
fi

if command -v tectonic >/dev/null 2>&1; then
  tectonic_cmd="$(command -v tectonic)"
elif [[ -x /Applications/ChatGPT.app/Contents/Resources/tectonic/tectonic ]]; then
  tectonic_cmd="/Applications/ChatGPT.app/Contents/Resources/tectonic/tectonic"
else
  printf 'Error: Tectonic was not found. Install it or add it to PATH.\n' >&2
  exit 1
fi

tex_dir="$(dirname -- "$tex_file")"
tex_name="$(basename -- "$tex_file" .tex)"
build_dir="$(mktemp -d "${TMPDIR:-/tmp}/cv-build.XXXXXX")"
trap 'rm -rf "$build_dir"' EXIT

"$tectonic_cmd" --outdir "$build_dir" "$tex_file"
mkdir -p -- "$(dirname -- "$output_pdf")"
cp -- "$build_dir/${tex_name}.pdf" "$output_pdf"
printf 'Wrote %s\n' "$output_pdf"
