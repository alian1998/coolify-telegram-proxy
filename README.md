# coolify-telegram-proxy

Webshare-style **HTTP + SOCKS5** proxy stack for Coolify. One VPS IP, username/password auth, a private list UI, and Telegram Bot API connectivity.

This is **your** proxy on `88.222.213.240`, not Webshare’s IP pool. One machine = one exit IP. That is enough for Telegram bots.

## What you get

| Protocol | Default port | Example |
| --- | --- | --- |
| HTTP (CONNECT / HTTPS) | `8080` | `http://tgproxy:PASS@88.222.213.240:8080` |
| SOCKS5 | `1080` | `socks5h://tgproxy:PASS@88.222.213.240:1080` |
| Dashboard | `3000` | login with `DASHBOARD_PASSWORD` |

List format (same idea as Webshare download):

```text
88.222.213.240:8080:tgproxy:YOUR_PASS
88.222.213.240:1080:tgproxy:YOUR_PASS
```

## Coolify deploy

1. Copy `.env.example` → set strong `PROXY_PASSWORD`, `DASHBOARD_PASSWORD`, `SESSION_SECRET`.
2. In Coolify: **New Resource → Docker Compose**.
3. Point it at this repo (or paste `docker-compose.yml` + the `proxy/` and `dashboard/` folders).
4. Load the same env vars in Coolify.
5. Publish ports **8080** and **1080** on the VPS. Dashboard `3000` can stay behind a Coolify domain.
6. On the VPS firewall (UFW/security group): allow `8080/tcp` and `1080/tcp`.
7. Open the dashboard, confirm **Telegram API = OK**, copy the connection string into your bot.

Do not expose 8080/1080 without the proxy username/password. Do not leave dashboard password empty.

## Telegram bot (`node-telegram-bot-api`)

HTTP proxy (simplest):

```js
const bot = new TelegramBot(process.env.BOT_TOKEN, {
  polling: true,
  request: { proxy: "http://tgproxy:YOUR_PASS@88.222.213.240:8080" },
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
