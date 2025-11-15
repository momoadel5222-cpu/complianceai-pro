from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS configuration - allow all /api routes
CORS(app, 
     resources={
         r"/api/*": {
             "origins": "*",  # Allow all origins temporarily for testing
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False
         }
     }
)

@app.route('/api/health', methods=['GET'])
def health():
    logger.info("Health check endpoint called")
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "port": os.environ.get('PORT', 'unknown')
    }), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "ComplianceAI Backend API",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "screen": "/api/screen",
            "sanctions_screen": "/api/sanctions/screen"
        }
    }), 200

@app.route('/api/screen', methods=['POST', 'OPTIONS'])
def screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        logger.info(f"Screening request received: {data}")
        
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

@app.route('/api/sanctions/screen', methods=['POST', 'OPTIONS'])
def sanctions_screen():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        logger.info(f"Sanctions screening request received: {data}")
        
        result = {
            "status": "success",
            "message": "Sanctions screening completed",
            "data": data,
            "matches": []  # Add your sanctions matching logic here
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in sanctions screening: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

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
