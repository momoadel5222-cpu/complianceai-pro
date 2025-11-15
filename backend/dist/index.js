import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import dotenv from 'dotenv';
import sanctionsRoutes from './routes/sanctions.js';
import testRoutes from './routes/test.js';
dotenv.config();
const app = express();
const PORT = parseInt(process.env.PORT || '3000', 10);
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'ComplianceAI Pro API is running' });
});
app.use('/api', testRoutes);
app.use('/api/sanctions', sanctionsRoutes);
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
    console.log(`Access via: http://localhost:${PORT}`);
});
