/**
 * Example: connect node-telegram-bot-api through this stack's HTTP proxy.
 *
 *   npm i node-telegram-bot-api
 *   BOT_TOKEN=123:abc HTTP_PROXY=http://tgproxy:PASS@VPS_IP:8080 node examples/telegram-bot.js
 */

const TelegramBot = require("node-telegram-bot-api");

const token = process.env.BOT_TOKEN;
const proxy = process.env.HTTP_PROXY;

if (!token || !proxy) {
  console.error("Set BOT_TOKEN and HTTP_PROXY");
  process.exit(1);
}

const bot = new TelegramBot(token, {
  polling: true,
  request: { proxy },
});

bot.on("message", (msg) => {
  bot.sendMessage(msg.chat.id, "Proxy is working.");
});

bot.on("polling_error", (err) => {
  console.error("polling_error", err.message);
});
