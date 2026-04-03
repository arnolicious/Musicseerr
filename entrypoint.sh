#!/bin/sh
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

groupmod -o -g "$PGID" musicseerr 2>/dev/null || true
usermod -o -u "$PUID" musicseerr 2>/dev/null || true

TARGET_UID=$(id -u musicseerr)
TARGET_GID=$(id -g musicseerr)

# Only chown directories whose top-level ownership differs from the target.
# Nested mismatches from manual edits require a rebuild or manual chown.
for dir in /app/cache /app/config; do
    if [ -d "$dir" ]; then
        CURRENT=$(stat -c '%u:%g' "$dir")
        if [ "$CURRENT" != "$TARGET_UID:$TARGET_GID" ]; then
            chown -R musicseerr:musicseerr "$dir"
        fi
    fi
done

exec gosu musicseerr:musicseerr "$@"
