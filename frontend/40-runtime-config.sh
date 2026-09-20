#!/bin/sh
set -eu
API_BASE_URL=${API_BASE_URL:-}
API_PROXY_URL=${API_PROXY_URL:-http://127.0.0.1:8000}
validate_origin() {
    case "$1" in *[!A-Za-z0-9:/.-]*) return 1 ;; esac
    printf '%s' "$1" | grep -Eq '^https?://[A-Za-z0-9.-]+(:[0-9]+)?$'
}
if [ -n "$API_BASE_URL" ] && ! validate_origin "$API_BASE_URL"; then
    echo 'API_BASE_URL must be an HTTP(S) origin without a trailing slash or path.' >&2
    exit 1
fi
# Direct-browser mode does not depend on a sibling backend container/DNS name.
if [ -n "$API_BASE_URL" ]; then
    API_PROXY_URL=$API_BASE_URL
fi
if ! validate_origin "$API_PROXY_URL"; then
    echo 'API_PROXY_URL must be an HTTP(S) origin without a trailing slash or path.' >&2
    exit 1
fi
# Validated origins contain no JSON, shell or nginx control characters.
printf '{"apiBaseUrl":"%s"}\n' "$API_BASE_URL" > /usr/share/nginx/html/app-config.json
export API_BASE_URL API_PROXY_URL
envsubst '${API_BASE_URL} ${API_PROXY_URL}' < /etc/nginx/app.conf.template > /etc/nginx/conf.d/default.conf
