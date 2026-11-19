#!/usr/bin/env bash
set -Eeuo pipefail

project=/opt/hot-gap-aggregator
static_root=/var/www/hot-gap
archive=/home/deploy/hot-gap-horizon.tar.gz
backup="$project/.deploy-backups/$(date +%Y%m%d-%H%M%S)-before-horizon"
stage="$(mktemp -d /tmp/hot-gap-horizon.XXXXXX)"
installed=0
files=(app/capture_horizon.py web/src/App.tsx web/src/HorizonView.tsx)

install -d -m 700 "$backup"
for relative in "${files[@]}"; do
  if [[ -f "$project/$relative" ]]; then
    install -D -p "$project/$relative" "$backup/project/$relative"
  fi
done
install -D -p "$static_root/index.html" "$backup/static/index.html"
if [[ -f /etc/cron.d/hot-gap-horizon ]]; then
  install -p /etc/cron.d/hot-gap-horizon "$backup/cron"
fi
if [[ -f "$static_root/data/server-horizon.json" ]]; then
  install -p "$static_root/data/server-horizon.json" "$backup/snapshot.json"
fi

cleanup() {
  status=$?
  if (( installed == 0 )); then
    for relative in "${files[@]}"; do
      if [[ -f "$backup/project/$relative" ]]; then
        install -D -o root -g root -m 644 "$backup/project/$relative" "$project/$relative"
      else
        rm -f -- "$project/$relative"
      fi
    done
    install -o root -g root -m 644 "$backup/static/index.html" "$static_root/index.html"
    if [[ -f "$backup/cron" ]]; then
      install -o root -g root -m 644 "$backup/cron" /etc/cron.d/hot-gap-horizon
    else
      rm -f -- /etc/cron.d/hot-gap-horizon
    fi
    if [[ -f "$backup/snapshot.json" ]]; then
      install -o root -g root -m 644 "$backup/snapshot.json" "$static_root/data/server-horizon.json"
    else
      rm -f -- "$static_root/data/server-horizon.json"
    fi
    echo "Deployment failed; restored $backup" >&2
  fi
  # Exact task-created staging directory only.
  [[ "$stage" == /tmp/hot-gap-horizon.* ]] && rm -rf -- "$stage"
  exit "$status"
}
trap cleanup EXIT

tar -xzf "$archive" -C "$stage"
source_root="$stage/hot-gap-aggregator"
for relative in "${files[@]}"; do
  install -D -o root -g root -m 644 "$source_root/$relative" "$project/$relative"
done
cd "$project"
.venv/bin/python -m py_compile app/capture_horizon.py
.venv/bin/python -m app.capture_horizon --output "$static_root/data/server-horizon.json"
# Add hashed assets before switching the HTML. Leave previous assets available
# so already-open pages and rollback HTML continue to work.
install -d -o root -g root -m 755 "$static_root/assets"
for asset in "$source_root"/web/dist/assets/*; do
  install -o root -g root -m 644 "$asset" "$static_root/assets/"
done
install -o root -g root -m 644 "$source_root/web/dist/index.html" "$static_root/.horizon-index.next"
mv -T "$static_root/.horizon-index.next" "$static_root/index.html"
install -o root -g root -m 644 "$source_root/deploy/server/hot-gap-horizon.cron" /etc/cron.d/hot-gap-horizon
sed -i 's/\r$//' /etc/cron.d/hot-gap-horizon
installed=1
echo "Installed Horizon Chinese briefings, attributed excerpts, and lazy website tab"
echo "Independent feed update: every 6 hours at minute 17 (server timezone)"
echo "Backup: $backup"
