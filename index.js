import fetch from "node-fetch";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

let offset = 0;

async function sendMessage(chatId, text) {
  await fetch(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text })
  });
}

async function getUpdates() {
  const res = await fetch(
    `https://api.telegram.org/bot${TELEGRAM_TOKEN}/getUpdates?timeout=30&offset=${offset}`
  );
  const data = await res.json();
  return data.result || [];
}

async function runBot() {
  console.log("🤖 Gemini Telegram Bot started");

  while (true) {
    try {
      const updates = await getUpdates();

      for (const update of updates) {
        offset = update.update_id + 1;

        const msg = update.message;
        if (!msg || !msg.text) continue;

        const chatId = msg.chat.id;
        const text = msg.text;

        const model = genAI.getGenerativeModel({
          model: "gemini-1.5-flash",
          systemInstruction: `
မင်းက Z-Libra AI ဖြစ်တယ်။
User ကို နူးညံ့ပြီး မိတ်ဆွေလို ပြောပါ။
`
        });

        const result = await model.generateContent(text);
        const reply = result.response.text();

        await sendMessage(chatId, reply);
      }
    } catch (e) {
      console.log("Error:", e.message);
    }
  }
}

runBot();
