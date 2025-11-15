from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://complianceai-pro.vercel.app",
            "http://localhost:3000",
            "http://localhost:5173"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health():
    logger.info("Health check endpoint called")
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "port": os.environ.get('PORT', 'unknown')
    }), 200

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "ComplianceAI Backend API",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "screen": "/api/screen"
        }
    }), 200

# Screening endpoint
@app.route('/api/screen', methods=['POST'])
def screen():
    try:
        data = request.get_json()
        logger.info(f"Screening request received: {data}")
        
        # Your screening logic here
        result = {
            "status": "success",
            "message": "Screening completed",
            "data": data
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in screening: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
