# coolify-telegram-proxy

Webshare-style **HTTP + SOCKS5** proxy stack for Coolify. One **your VPS IP**, username/password auth, a private list UI, and Telegram Bot API connectivity.

## IP masking (your VPS)

Bot er real IP (PC, mobile, office) hide hoye **ekta stable VPS IP** diye `api.telegram.org` e request jay.

```text
Bot (any network) → your proxy (88.222.213.240:18080) → api.telegram.org
                         ↑
                   Telegram ekhane shudhu ei IP dekhe
```

- **No extra Webshare/Singapore proxy needed** — upstream optional.
- Same IP for all bots = consistent, less random blocking.
- `Getway-support-autoworker` already supports `TELEGRAM_HTTP_PROXY` env.

Bot app (Coolify) e add koro:

```env
TELEGRAM_HTTP_PROXY=http://tgproxy:YOUR_PROXY_PASS@88.222.213.240:18080
```

Template: `examples/support-bot.env`

## What you get

| Protocol | Coolify port | Example |
| --- | --- | --- |
| HTTP (CONNECT / HTTPS) | `18080` | `http://tgproxy:PASS@88.222.213.240:18080` |
| SOCKS5 | `1080` | `socks5h://tgproxy:PASS@88.222.213.240:1080` |
| Dashboard | `3000` | login with `DASHBOARD_PASSWORD` |

List format (Webshare-style download):

```text
88.222.213.240:18080:tgproxy:YOUR_PASS
88.222.213.240:1080:tgproxy:YOUR_PASS
```

## Coolify deploy

1. Copy `.env.example` → set strong `PROXY_PASSWORD`, `DASHBOARD_PASSWORD`, `SESSION_SECRET`.
2. In Coolify: **New Resource → Docker Compose** → this repo, branch `master`.
3. Set env vars (especially `HTTP_PUBLISH_PORT=18080` if `8080` is taken).
4. Publish ports **18080** and **1080** on the VPS. Dashboard **3000**.
5. VPS firewall: allow `18080/tcp`, `1080/tcp`, `3000/tcp`.
6. Open dashboard → **Telegram API = OK** → copy proxy URL into bot env → redeploy bot.

Do not expose proxy ports without username/password. Do not leave dashboard password empty.

## Optional foreign exit (upstream)

Only if India datacenter IP is still blocked. Leave `UPSTREAM_PROXY_HOST` empty to use **your VPS IP only**.

```env
UPSTREAM_PROXY_TYPE=http
UPSTREAM_PROXY_HOST=p.webshare.io
UPSTREAM_PROXY_PORT=80
UPSTREAM_PROXY_USERNAME=your-user
UPSTREAM_PROXY_PASSWORD=your-pass
```

## Telegram bot (`node-telegram-bot-api`)

HTTP proxy (simplest):

```js
const bot = new TelegramBot(process.env.BOT_TOKEN, {
  polling: true,
  request: { proxy: "http://tgproxy:YOUR_PASS@88.222.213.240:18080" },
});
```

SOCKS5 (needs `socks-proxy-agent`):

```js
const { SocksProxyAgent } = require("socks-proxy-agent");
const agent = new SocksProxyAgent("socks5h://tgproxy:YOUR_PASS@88.222.213.240:1080");
const bot = new TelegramBot(process.env.BOT_TOKEN, {
  polling: true,
  request: { agent },
});
```

If the bot also uses `axios` for `getFileLink`, set the same proxy on axios.

Example file: `examples/telegram-bot.js`.

## Extra users

Same IP, extra logins for different bots:

```env
PROXY_USERS=support:pass-one,alerts:pass-two
```

Username/password: letters, numbers, `.` `_` `-` only.

## Local run

```bash
cp .env.example .env
# edit passwords
docker compose up --build
```

Dashboard: `http://127.0.0.1:3000`

## Security

- Auth is required on HTTP and SOCKS5. An open proxy will get your VPS abused.
- Dashboard shows live credentials — keep `DASHBOARD_PASSWORD` private.
- This proxy can reach the public internet (Webshare-style). It is not limited to Telegram.
