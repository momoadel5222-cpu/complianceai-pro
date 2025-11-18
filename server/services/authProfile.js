import jwt from 'jsonwebtoken';

class AuthProfile {
  constructor() {
    this.secret = process.env.JWT_SECRET;
  }

  authenticate(email, password) {
    // DEMO: Replace with real password check
    if (email !== "admin@company.com" || password !== "demo123") {
      throw new Error("Invalid credentials");
    }
    return {
      email,
      token: jwt.sign({ email, orgId: "org_123" }, this.secret, { expiresIn: '1h' })
    };
  }

  verifyToken(token) {
    return jwt.verify(token, this.secret);
  }
}

export default new AuthProfile();
