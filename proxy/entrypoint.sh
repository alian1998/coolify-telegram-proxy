#!/bin/sh
set -eu

HTTP_PORT="${HTTP_PORT:-8080}"
SOCKS_PORT="${SOCKS_PORT:-1080}"
MAXCONN="${MAXCONN:-200}"

validate_cred() {
  name="$1"
  value="$2"
  case "$value" in
    *[!A-Za-z0-9._-]*)
      echo "Invalid ${name}: use only letters, numbers, dot, underscore, hyphen." >&2
      exit 1
      ;;
    "")
      echo "${name} is empty." >&2
      exit 1
      ;;
  esac
}

USERS_LINE=""
FIRST_USER=""

add_user() {
  u="$1"
  p="$2"
  validate_cred "username" "$u"
  validate_cred "password" "$p"
  if [ -n "$USERS_LINE" ]; then
    USERS_LINE="${USERS_LINE} ${u}:CL:${p}"
  else
    USERS_LINE="${u}:CL:${p}"
    FIRST_USER="$u"
  fi
}

if [ -n "${PROXY_USERNAME:-}" ] || [ -n "${PROXY_PASSWORD:-}" ]; then
  if [ -z "${PROXY_USERNAME:-}" ] || [ -z "${PROXY_PASSWORD:-}" ]; then
    echo "Set both PROXY_USERNAME and PROXY_PASSWORD." >&2
    exit 1
  fi
  add_user "$PROXY_USERNAME" "$PROXY_PASSWORD"
fi

if [ -n "${PROXY_USERS:-}" ]; then
  OLDIFS="$IFS"
  IFS=","
  # shellcheck disable=SC2086
  set -- $PROXY_USERS
  IFS="$OLDIFS"
  for pair in "$@"; do
    u="${pair%%:*}"
    p="${pair#*:}"
    if [ "$u" = "$p" ] || [ -z "$u" ] || [ -z "$p" ]; then
      echo "Invalid PROXY_USERS entry '${pair}'. Use user:pass,user2:pass2" >&2
      exit 1
    fi
    add_user "$u" "$p"
  done
fi

if [ -z "$USERS_LINE" ]; then
  echo "No proxy users configured. Set PROXY_USERNAME/PROXY_PASSWORD or PROXY_USERS." >&2
  exit 1
fi

CFG="/tmp/3proxy.cfg"
cat > "$CFG" <<EOF
nscache 65536
nserver 1.1.1.1
nserver 8.8.8.8
nserver 9.9.9.9
timeouts 1 5 30 60 180 1800 15 60
log /dev/stdout D
logformat "- %U %C:%c %R:%r %O %I %T"
maxconn ${MAXCONN}
auth strong
users ${USERS_LINE}
allow *
proxy -n -a -p${HTTP_PORT} -i0.0.0.0
socks -p${SOCKS_PORT} -i0.0.0.0
EOF

echo "3proxy starting HTTP :${HTTP_PORT} SOCKS5 :${SOCKS_PORT} user=${FIRST_USER}"
exec 3proxy "$CFG"
