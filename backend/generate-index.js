const fs = require('fs');

const indexContent = `const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const compression = require("compression");
require("dotenv").config();

const { supabase } = require("./db");
const sanctionsRouter = require("./routes/sanctions");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(express.json());

// Routes
app.get("/api/health", (req, res) => {
  res.json({ status: "OK", message: "ComplianceAI Pro API is running" });
});

// Test database connection
app.get("/api/test-db", async (req, res) => {
  try {
    const { data, error } = await supabase.from("users").select("count");
    if (error) throw error;
    res.json({ status: "Database connected", count: data });
  } catch (error) {
    res.status(500).json({ status: "Database connection failed", error: error.message });
  }
});

// Sanctions screening routes
app.use("/api/sanctions", sanctionsRouter);

// Start server - bind only to localhost
app.listen(PORT, "127.0.0.1", () => {
  console.log(\`Server running on port \${PORT}\`);
});
`;

fs.writeFileSync('src/index.ts', indexContent);
console.log('File created successfully');
