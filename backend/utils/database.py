from flask import current_app, request, jsonify
import logging
from functools import wraps
import os
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function

def get_db():
    """Get database connection with proper parsing of MongoDB URI"""
    DEFAULT_DB_NAME = 'learnwise-demo'  # Changed default database name
    
    try:
        mongodb_uri = current_app.config['MONGODB_URI']
        # Parse the URI to extract the path component
        parsed_uri = urlparse(mongodb_uri)
        
        # Extract database name from path, removing any query parameters
        path = parsed_uri.path.lstrip('/')
        db_name = path.split('?')[0] if '?' in path else path
        
        # If no database in URI, check environment variable or use default
        if not db_name:
            db_name = os.getenv('MONGODB_DATABASE', DEFAULT_DB_NAME)
            
        logger.info(f"Connecting to database: {db_name}")
        
        if not db_name:
            logger.warning("No database name found in URI or environment, using default")
            db_name = DEFAULT_DB_NAME
            
        return current_app.mongo.get_database(db_name)
        
    except Exception as e:
        logger.error(f"Error getting database connection: {str(e)}")
        # If there's an error, try the default database as fallback
        logger.info(f"Attempting fallback to default database: {DEFAULT_DB_NAME}")
        return current_app.mongo.get_database(DEFAULT_DB_NAME)
