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
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

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
  padding: 12px 16px;
  border-radius: 15px;
}
.user {
  align-self: flex-end;
  background: #3b82f6;
}
.ai {
  align-self: flex-start;
  background: #334155;
}
.input-area {
  display: flex;
  gap: 10px;
  padding: 15px;
  background: #1e293b;
}
input {
  flex: 1;
  padding: 12px;
  border-radius: 25px;
  border: 1px solid #475569;
  background: #0f172a;
  color: white;
}
button {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  border: none;
  background: #3b82f6;
  color: white;
}
</style>
</head>

<body>
<div class="header">🤖 Z-Libra Forever AI</div>
<div id="chat"></div>

<div class="input-area">
  <input id="input" placeholder="တစ်ခုခု ပြောလိုက်လေ..."
         onkeydown="if(event.key==='Enter') send()">
  <button onclick="send()">🚀</button>
</div>

<script type="module">
import { GoogleGenerativeAI } from "https://esm.run/@google/generative-ai";

/* ⚠️ DEMO ONLY */
const API_KEY = "AIzaSyBBAkDEDksRSss9382kXWvry2C94z6yoC0";

const genAI = new GoogleGenerativeAI(API_KEY);
const model = genAI.getGenerativeModel({
  model: "gemini-1.5-flash",
  systemInstruction: `
မင်းနာမည် Z-Libra AI ဖြစ်တယ်။
သခင်က မျိုးသူရိန်လင်း။
သူ့ကို "ငါ့ကောင်" "ဟျောင့်" လို့ ခေါ်။
`
});

const chatBox = document.getElementById("chat");

let memory = JSON.parse(localStorage.getItem("zlibra_memory")) || [];

memory.forEach(m => addMessage(m.role, m.text));

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "message " + role;
  div.innerHTML = role === "ai" ? marked.parse(text) : text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return div;
}

function typeText(el, text) {
  let i = 0;
  const timer = setInterval(() => {
    el.innerHTML = marked.parse(text.slice(0, i++));
    chatBox.scrollTop = chatBox.scrollHeight;
    if (i > text.length) clearInterval(timer);
  }, 15);
}

window.send = async () => {
  const input = document.getElementById("input");
  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  input.value = "";

  const aiDiv = addMessage("ai", "");

  try {
    const chat = model.startChat({
      history: memory.map(m => ({
        role: m.role === "user" ? "user" : "model",
        parts: [{ text: m.text }]
      }))
    });

    const result = await chat.sendMessage(text);
    const reply = result.response.text();

    typeText(aiDiv, reply);

    memory.push({ role: "user", text });
    memory.push({ role: "ai", text: reply });

    memory = memory.slice(-40); // 🧠 limit
    localStorage.setItem("zlibra_memory", JSON.stringify(memory));

  } catch (e) {
    aiDiv.textContent = "Error ဖြစ်သွားတယ် ငါ့ကောင် 😵";
    console.error(e);
  }
};
</script>
</body>
</html>
