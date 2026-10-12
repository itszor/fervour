#!/bin/sh
# Build Fervour from your own copy of the game:
#     ./build.sh "Fervour (19xx)(-).zip"     (or the .adf)
# then: cd recomp && ./fervour
# The steps are recipe.json's "build", run by SuperSpider's tools/weave.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERSPIDER="${SUPERSPIDER:-$HOME/stuff/superspider}"
[ $# -gt 0 ] || { echo "usage: $0 GAME.zip | DISC.adf" >&2; exit 2; }
(cd "$SUPERSPIDER" && dune build)
WEAVE_RECIPES="$HERE" exec python3 -I "$SUPERSPIDER/tools/weave.py" build "$@"
