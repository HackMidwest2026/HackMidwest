#!/bin/bash
# Builds the kz-lite save states release zip.
#
# usage: release/make-release.sh <gru.exe> <gru-linux> [version]
#
# Needs glankk's n64 toolchain (mips64-gcc etc.) in PATH to build kz.
# gru.exe / gru-linux are standalone gru builds, see release/build-gru.sh.
set -e
here=$(cd "$(dirname "$0")" && pwd)
gru_exe="$1"; gru_linux="$2"; version="${3:-1}"
[ -f "$gru_exe" ] && [ -f "$gru_linux" ] || { echo "usage: $0 <gru.exe> <gru-linux> [version]"; exit 1; }

name="kz-lite-savestates-v$version"
work=$(mktemp -d)
pkg="$work/$name"

# build kz-lite and its hooks for every supported rom
cd "$here/../kz"
export PACKAGE_VERSION="lite-savestates-$version"
for v in NZSE NZSJ NZSJ10; do
    make "kz-lite-$v" "patch/gsc/kz-lite-$v/hooks.gsc"
done

cp -r "$here/package" "$pkg"
mkdir -p "$pkg/bin"
cp "$gru_exe" "$pkg/bin/gru.exe"
cp "$gru_linux" "$pkg/bin/gru"
cp patch/gsc/zero_patch_lite.gsc "$pkg/data/" 2>/dev/null || { mkdir -p "$pkg/data"; cp patch/gsc/zero_patch_lite.gsc "$pkg/data/"; }
for v in NZSE NZSJ NZSJ10; do
    d="$pkg/data/kz-lite-$v"
    mkdir -p "$d"
    cp "bin/kz-lite-$v/kz.bin" "patch/gsc/kz-lite-$v/hooks.gsc" "patch/gsc/kz-lite-$v/ups_size_patch.gsc" "$d/"
done

mkdir -p "$here/dist"
rm -f "$here/dist/$name.zip"
(cd "$work" && zip -qr "$here/dist/$name.zip" "$name")
rm -rf "$work"
echo "built release/dist/$name.zip"
