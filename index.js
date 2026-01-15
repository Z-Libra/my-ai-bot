import express from "express";
import cors from "cors";
import mongoose from "mongoose";
import dotenv from "dotenv";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

/* ===== DATABASE ===== */
mongoose.connect(process.env.MONGO_URI);

const UserSchema = new mongoose.Schema({
  name: String,
  memory: Array,
  createdAt: { type: Date, default: Date.now }
});

const User = mongoose.model("User", UserSchema);

/* ===== AI ===== */
const genAI = new GoogleGenerativeAI(process.env.AIzaSyBBAkDEDksRSss9382kXWvry2C94z6yoC0);

/* ===== NAME DETECTOR ===== */
function extractName(text) {
  const match = text.match(/နာမည်\s*(.+)/);
  return match ? match[1].trim() : null;
}

/* ===== CHAT API ===== */
app.post("/chat", async (req, res) => {
  try {
    const { message } = req.body;

    let name = extractName(message);
    let user = null;

    if (name) {
      user = await User.findOne({ name });
      if (!user) {
        user = await User.create({ name, memory: [] });
      }
    }

    const systemPrompt = `
မင်းက Z-Libra AI ဖြစ်တယ်။
User ရဲ့နာမည်က ${user?.name || "မသိ"} ဖြစ်တယ်။
နာမည်ကို အမြဲမှတ်ထားပြီး နူးညံ့စွာ ခေါ်ပြောပါ။
    `;

    const model = genAI.getGenerativeModel({
      model: "gemini-1.5-flash",
      systemInstruction: systemPrompt
    });

    const chat = model.startChat({
      history: user?.memory || []
    });

    const result = await chat.sendMessage(message);
    const reply = result.response.text();

    if (user) {
      user.memory.push({ role: "user", parts: [{ text: message }] });
      user.memory.push({ role: "model", parts: [{ text: reply }] });
      await user.save();
    }

    res.json({ reply });

  } catch (err) {
    res.status(500).json({ error: "AI Error" });
  }
});

/* ===== START ===== */
app.listen(3000, () => {
  console.log("Z-Libra AI backend running");
});
