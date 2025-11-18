import express from 'express';
import { requireAuth } from '../middleware/authMiddleware.js';
import { J1 } from '../services/screeningService.js';
import { Tm } from '../data/userRepository.js';

const router = express.Router();

// Public login endpoint
router.post('/login', express.json(), async (req, res) => {
  try {
    const { email, password } = req.body;
    const authResult = await import('../services/authProfile.js').then(m => m.default.authenticate(email, password));
    res.json(authResult);
  } catch (error) {
    res.status(401).json({ error: error.message });
  }
});

// Protected users endpoint
router.get('/users', requireAuth, async (req, res) => {
  try {
    const screening = await J1("users", req.user.email);
    if (!screening.isAllowed) return res.status(403).json({ error: "Access denied" });

    const users = await Tm.find(req.user, {}, screening.rlsFilter);
    res.json({ data: users });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Server error" });
  }
});

export default router;
