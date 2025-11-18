import authProfile from '../services/authProfile.js';

export const requireAuth = (req, res, next) => {
  const token = req.headers.authorization?.replace("Bearer ", "");
  
  if (!token) {
    return res.status(401).json({ error: "No token provided" });
  }

  try {
    req.user = authProfile.verifyToken(token);
    next();
  } catch (err) {
    return res.status(401).json({ error: "Invalid token" });
  }
};
