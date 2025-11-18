const groq = require('groq-sdk');

const client = new groq({ apiKey: process.env.GROQ_API_KEY });

async function getGroqResponse(prompt) {
  const chatCompletion = await client.chat.completions.create({
    messages: [
      {
        role: "user",
        content: prompt,
      },
    ],
    model: "llama3-8b-8192",
    // This is a key addition!
    response_format: { type: "json_object" },
  });

  return chatCompletion.choices[0]?.message?.content || "";
}

module.exports = { getGroqResponse };