"""
Flask MongoDB API Template Server

This is a Flask + MongoDB API template that follows patterns established in api_utils.
It implements three domains following the Creator Dashboard architecture:
- Control: POST, GET many (with name query), GET one, PATCH one endpoints
- Create: POST, GET many, GET one endpoints
- Consume: GET many, GET one endpoints (read-only)

This server demonstrates:
- Config singleton initialization
- MongoIO singleton connection
- Flask route registration
- Prometheus metrics integration
- JWT token authentication and authorization
- Graceful shutdown handling
- RBAC placeholder pattern for future implementation
"""
import sys
import os
import signal
from flask import Flask, send_from_directory
import logging
logger = logging.getLogger(__name__)

# Initialize Config Singleton and MongoIO Singleton
from api_utils import Config, MongoIO
config = Config.get_instance()
mongo = MongoIO.get_instance()
config.set_enumerators(mongo.get_documents(config.ENUMERATORS_COLLECTION_NAME))
config.set_versions(mongo.get_documents(config.VERSIONS_COLLECTION_NAME))

# Initialize Flask App
from api_utils import MongoJSONEncoder
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Apply Prometheus monitoring middleware - exposes /metrics endpoint (default)
metrics = PrometheusMetrics(app)

# Register Routes
logger.info("Registering Routes")

from api_utils import create_config_routes
app.register_blueprint(create_config_routes(), url_prefix='/api/config')
logger.info("  /api/config")

if config.ENABLE_LOGIN:
    from api_utils import create_dev_login_routes
    app.register_blueprint(create_dev_login_routes())
    logger.info("  /dev-login")

from src.routes.control_routes import create_control_routes
app.register_blueprint(create_control_routes(), url_prefix='/api/control')
logger.info("  /api/control")

from src.routes.create_routes import create_create_routes
app.register_blueprint(create_create_routes(), url_prefix='/api/create')
logger.info("  /api/create")

from src.routes.consume_routes import create_consume_routes
app.register_blueprint(create_consume_routes(), url_prefix='/api/consume')
logger.info("  /api/consume")

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

@app.route('/docs')
@app.route('/docs/')
def serve_docs_root():
    """Serve the API explorer at /docs root."""
    return send_from_directory(DOCS_DIR, 'explorer.html')

@app.route('/docs/<path:filename>')
def serve_docs(filename):
    """Serve static files from the docs directory."""
    return send_from_directory(DOCS_DIR, filename)

logger.info("  /docs")
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
    api_port = config.TEMPLATE_API_PORT
    logger.info(f"Starting Flask server on port {api_port}")
    app.run(host="0.0.0.0", port=api_port, debug=False)

