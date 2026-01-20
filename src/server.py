"""
Flask MongoDB API Template Server

This is a minimal Flask + MongoDB API that follows patterns established in api_utils.
It implements two domains:
- Grade: GET one, GET many endpoints
- TestRun: POST, GET one, GET many, PATCH endpoints

This server demonstrates:
- Config singleton initialization
- MongoIO singleton connection
- Flask route registration
- Prometheus metrics integration
- JWT token authentication and authorization
- Graceful shutdown handling
"""
import sys
import os
import signal
from flask import Flask, send_from_directory
import logging
logger = logging.getLogger(__name__)

# Initialize Config Singleton and MongoIO Singleton
from py_utils import Config, MongoIO
config = Config.get_instance()
mongo = MongoIO.get_instance()
config.set_enumerators(mongo.get_documents(config.ENUMERATORS_COLLECTION_NAME))
config.set_versions(mongo.get_documents(config.VERSIONS_COLLECTION_NAME))

# Initialize Flask App
from py_utils import MongoJSONEncoder
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Apply Prometheus monitoring middleware - exposes /metrics endpoint (default)
metrics = PrometheusMetrics(app)

# Register Routes
logger.info("Registering Routes")

from py_utils import create_config_routes
app.register_blueprint(create_config_routes(), url_prefix='/api/config')
logger.info("  /api/config")

if config.ENABLE_LOGIN:
    from py_utils import create_dev_login_routes
    app.register_blueprint(create_dev_login_routes())
    logger.info("  /dev-login")

from src.routes.grade_routes import create_grade_routes
app.register_blueprint(create_grade_routes(), url_prefix='/api/grade')
logger.info("  /api/grade")

from src.routes.testrun_routes import create_testrun_routes
app.register_blueprint(create_testrun_routes(), url_prefix='/api/testrun')
logger.info("  /api/testrun")

# Serve static documentation files from docs directory
# Use absolute path based on working directory (PYTHONPATH) for reliability in containers
BASE_DIR = os.environ.get('PYTHONPATH', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

# Ensure docs directory exists and log the path for debugging
if not os.path.exists(DOCS_DIR):
    logger.warning(f"Docs directory not found at {DOCS_DIR}, trying alternative path calculation")
    # Fallback to relative path calculation
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DOCS_DIR = os.path.join(BASE_DIR, 'docs')
    
if os.path.exists(DOCS_DIR):
    logger.info(f"Serving docs from: {DOCS_DIR}")
else:
    logger.error(f"Docs directory not found at {DOCS_DIR}")

@app.route('/docs/<path:filename>')
def serve_docs(filename):
    """Serve static files from the docs directory."""
    return send_from_directory(DOCS_DIR, filename)

logger.info("  /docs/<path>")
logger.info("  /metrics")
logger.info("Routes Registered")

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    """Handle graceful shutdown on SIGTERM/SIGINT."""
    global mongo
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    
    # Disconnect from MongoDB if connected
    if mongo is not None:
        logger.info("Closing MongoDB connection.")
        try:
            mongo.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
    
    logger.info("Shutdown complete.")
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Expose app for Gunicorn or direct execution
if __name__ == "__main__":
    api_port = config.EVALUATOR_API_PORT
    logger.info(f"Starting Flask server on port {api_port}")
    app.run(host="0.0.0.0", port=api_port, debug=False)

