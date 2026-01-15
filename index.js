import express from "express";
import fetch from "node-fetch";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const app = express();
app.use(express.json());

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

/* ===== Telegram Send ===== */
async function sendMessage(chatId, text) {
  const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text
    })
  });
}

/* ===== Webhook ===== */
app.post("/webhook", async (req, res) => {
  const message = req.body.message;
  if (!message) return res.sendStatus(200);

  const chatId = message.chat.id;
  const userText = message.text || "";

  try {
    const model = genAI.getGenerativeModel({
      model: "gemini-1.5-flash",
      systemInstruction: `
မင်းက Z-Libra AI ဖြစ်တယ်။
User ကို နူးညံ့ပြီး မိတ်ဆွေလို ပြောပါ။
`
    });

    const result = await model.generateContent(userText);
    const reply = result.response.text();

    await sendMessage(chatId, reply);
  } catch (err) {
    await sendMessage(chatId, "အခုစဉ်းစားနေတုန်းပါရှင် 🤍");
  }

  res.sendStatus(200);
});

app.get("/", (req, res) => {
  res.send("Telegram Gemini Bot Running");
});

app.listen(3000, () => {
  console.log("Bot server running");
});
