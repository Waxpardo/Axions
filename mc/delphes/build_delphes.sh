#!/usr/bin/env bash
# ============================================================================
# Idempotent local build of Delphes 3.5.0 against the ACTIVE ROOT (LCG_105).
# ============================================================================
#
# Why this exists: the CVMFS Delphes 3.5.0 build (3.5.0-05f0f) was compiled
# against ROOT 6.26.04, while LCG_105 ships ROOT 6.30.02. That ABI gap crashes
# DelphesHepMC2 with a SIGSEGV (exit 139) in the ROOT TFile finalizer at end of
# job -- after the physics output is already written, but enough to make HTCondor
# treat the job as failed. Rebuilding the SAME Delphes 3.5.0 source against the
# active ROOT 6.30 makes the libDelphes/DelphesHepMC2 ABI match the runtime ROOT
# and removes the crash. Physics is unchanged (identical 3.5.0 source).
#
# Design (mirrors the mc/pythia/ local-build precedent):
#   * this script + .gitignore entries are committed; the fetched source tree
#     and compiled binaries (mc/delphes/Delphes-3.5.0/) are gitignored.
#   * fetch-if-absent, build-if-stale, no-op-if-fresh.
#   * a stamp file pins the build to the Delphes version + ROOT version it was
#     built against; if the active ROOT changes, the build is cleaned and redone.
#
# Build system note: Delphes 3.5.0's CMakeLists.txt builds ONLY libDelphes.so
# (no executables), so we MUST use the classic `make`, which builds DelphesHepMC2
# and friends. `make` auto-detects ROOT via root-config, which supplies both
# -std=c++17 and the matching gcc compiler, so no manual flags are needed.
# DelphesHepMC2 has its own internal HepMC2 ASCII parser -- no external HepMC lib.
#
# Usage:
#   bash mc/delphes/build_delphes.sh           # fetch + build (idempotent)
#   bash mc/delphes/build_delphes.sh --clean    # remove source tree + artifacts
# ----------------------------------------------------------------------------
set -euo pipefail

DELPHES_VERSION="3.5.0"
# Exact source that produced the validated CVMFS binary (per its .buildinfo SRC).
DELPHES_TARBALL_URL="https://lcgpackages.web.cern.ch/tarFiles/sources/Delphes-${DELPHES_VERSION}.tar.gz"
# Fallback: GitHub release archive (identical source; extracts to lowercase dir).
DELPHES_TARBALL_URL_FALLBACK="https://github.com/delphes/delphes/archive/refs/tags/${DELPHES_VERSION}.tar.gz"
# Optional integrity pin. LCG publishes no upstream checksum; once you trust a
# downloaded tarball, paste its sha256 here to lock it for future fetches.
DELPHES_SHA256=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC_DIR="$SCRIPT_DIR/Delphes-${DELPHES_VERSION}"
TARBALL="$SCRIPT_DIR/Delphes-${DELPHES_VERSION}.tar.gz"
STAMP="$SCRIPT_DIR/.delphes_build_stamp"

if [[ "${1:-}" == "--clean" ]]; then
  echo ">>> Cleaning local Delphes build (source tree, tarball, stamp)"
  rm -rf "$SRC_DIR" "$TARBALL" "$STAMP" "$SCRIPT_DIR/.extract_tmp"
  echo ">>> Done."
  exit 0
fi

echo ">>> Sourcing environment (env/setup_lcg105.sh) for ROOT/toolchain"
set +u
# shellcheck disable=SC1091
source "$REPO_ROOT/env/setup_lcg105.sh"
set -u

if ! command -v root-config >/dev/null 2>&1; then
  echo "ERROR: root-config not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi
ROOT_VER="$(root-config --version)"
echo ">>> Active ROOT: $ROOT_VER  ($(root-config --cxx))"

WANT_STAMP="delphes=${DELPHES_VERSION} root=${ROOT_VER}"

# --- no-op if already built against the active ROOT -------------------------
if [[ -x "$SRC_DIR/DelphesHepMC2" && -f "$STAMP" && "$(cat "$STAMP")" == "$WANT_STAMP" ]]; then
  echo ">>> Delphes ${DELPHES_VERSION} already built against ROOT ${ROOT_VER} -- up to date."
  echo "    Binary: $SRC_DIR/DelphesHepMC2"
  exit 0
fi

# --- ROOT changed since last build: clean before rebuilding -----------------
if [[ -f "$STAMP" && "$(cat "$STAMP")" != "$WANT_STAMP" && -d "$SRC_DIR" ]]; then
  echo ">>> Stamp mismatch (have '$(cat "$STAMP")', want '$WANT_STAMP') -- cleaning before rebuild"
  ( cd "$SRC_DIR" && make clean >/dev/null 2>&1 || true )
  rm -f "$STAMP"
fi

# --- fetch-if-absent --------------------------------------------------------
if [[ ! -d "$SRC_DIR" ]]; then
  if [[ ! -f "$TARBALL" ]]; then
    echo ">>> Downloading Delphes ${DELPHES_VERSION} source"
    if ! curl -fL -o "$TARBALL" "$DELPHES_TARBALL_URL"; then
      echo ">>> Primary URL failed; trying GitHub fallback"
      curl -fL -o "$TARBALL" "$DELPHES_TARBALL_URL_FALLBACK"
    fi
  fi
  GOT_SHA="$(sha256sum "$TARBALL" | awk '{print $1}')"
  if [[ -n "$DELPHES_SHA256" ]]; then
    echo ">>> Verifying sha256"
    if [[ "$GOT_SHA" != "$DELPHES_SHA256" ]]; then
      echo "ERROR: sha256 mismatch -- expected $DELPHES_SHA256, got $GOT_SHA" >&2
      exit 1
    fi
  else
    echo ">>> (no sha256 pinned) downloaded tarball sha256: $GOT_SHA"
    echo "    To lock it, set DELPHES_SHA256 at the top of this script."
  fi
  echo ">>> Extracting (normalizing top-level dir to Delphes-${DELPHES_VERSION}/)"
  TMP_EXTRACT="$SCRIPT_DIR/.extract_tmp"
  rm -rf "$TMP_EXTRACT"; mkdir -p "$TMP_EXTRACT"
  tar -xzf "$TARBALL" -C "$TMP_EXTRACT"
  EXTRACTED="$(find "$TMP_EXTRACT" -mindepth 1 -maxdepth 1 -type d | head -1)"
  if [[ -z "$EXTRACTED" ]]; then
    echo "ERROR: tarball did not extract to a directory" >&2
    exit 1
  fi
  mv "$EXTRACTED" "$SRC_DIR"
  rm -rf "$TMP_EXTRACT"
fi

# --- build (classic Makefile; root-config supplies c++17 + matching gcc) -----
echo ">>> Building Delphes ${DELPHES_VERSION} (make -j$(nproc)) against ROOT ${ROOT_VER}"
( cd "$SRC_DIR" && make -j"$(nproc)" )

if [[ ! -x "$SRC_DIR/DelphesHepMC2" ]]; then
  echo "ERROR: build finished but $SRC_DIR/DelphesHepMC2 was not produced" >&2
  exit 1
fi

echo ">>> Verifying DelphesHepMC2 links against the active ROOT (${ROOT_VER}):"
ldd "$SRC_DIR/DelphesHepMC2" | grep -i root || echo "    (no ROOT libs reported by ldd?)"

echo "$WANT_STAMP" > "$STAMP"
echo ">>> Build complete."
echo "    DelphesHepMC2 : $SRC_DIR/DelphesHepMC2"
echo "    libDelphes.so : $SRC_DIR/libDelphes.so"
echo "    Stamp         : $WANT_STAMP"
