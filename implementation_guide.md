#### Backend Tests (tests/test_fsrs_integration.py)
```python
import unittest
from datetime import datetime, timezone, timedelta
from app import create_app
from utils.fsrs_helper import FSRSHelper, convert_performance_to_rating
from models.user import User
from models.question import Question
from models.fsrs_card import FSRSCard
from fsrs import Rating, State
import os

class TestFSRSIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Set test environment
        os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/math_learning_test'
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Initialize FSRS helper with test parameters
        cls.fsrs_helper = FSRSHelper()
        
    def setUp(self):
        # Create test user and questions
        self.test_user = User.create_test_user()
        self.test_question = Question.create_test_question()
        
    def tearDown(self):
        # Clean up test data
        User.delete_test_data()
        Question.delete_test_data()
        FSRSCard.delete_test_data()
        
    def test_new_card_creation(self):
        """Test creating a new FSRS card"""
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), 
            str(self.test_question.id)
        )
        
        self.assertIsNotNone(card)
        self.assertEqual(card.user_id, str(self.test_user.id))
        self.assertEqual(card.question_id, str(self.test_question.id))
        self.assertEqual(card.reps, 0)
        self.assertEqual(card.state, State.New.value)
        self.assertIsNotNone(card.due_date)
        
    def test_card_review_cycle(self):
        """Test complete review cycle with different ratings"""
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), 
            str(self.test_question.id)
        )
        
        # Test correct answer (rating 3 = Good)
        updated_card, review_log = self.fsrs_helper.review_card(
            card, Rating.Good.value, datetime.now(timezone.utc)
        )
        
        self.assertEqual(updated_card.reps, 1)
        self.assertGreater(updated_card.stability, card.stability)
        self.assertIsNotNone(review_log)
        self.assertEqual(review_log.rating, Rating.Good.value)
        
        # Test incorrect answer (rating 1 = Again)
        incorrect_card, incorrect_log = self.fsrs_helper.review_card(
            updated_card, Rating.Again.value
        )
        self.assertEqual(incorrect_card.lapses, 1)
        self.assertEqual(incorrect_log.rating, Rating.Again.value)
        
    def test_due_count_endpoint(self):
        """Test getting due card counts"""
        # Create some test cards with different states
        for i in range(3):
            question = Question.create_test_question(f"due_test_{i}")
            fsrs_helper = FSRSHelper()
            card = fsrs_helper.initialize_card_for_question(
                str(self.test_user.id), str(question.id)
            )
            
            # Make some cards due
            if i < 2:
                card.due_date = datetime.now(timezone.utc) - timedelta(hours=1)
                card.save()
        
        response = self.client.get('/api/lessons/due-count',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertIn('due_count', data)
        self.assertIn('new_count', data)
        self.assertIn('learning_count', data)
        self.assertIn('review_count', data)
        self.assertIn('relearning_count', data)
        
        # Should have at least 2 due cards
        self.assertGreaterEqual(data['due_count'], 2)

    def test_card_info_endpoint(self):
        """Test getting detailed card information"""
        # Create and review a card
        question = Question.create_test_question("card_info_test")
        fsrs_helper = FSRSHelper()
        card = fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), str(question.id)
        )
        
        # Review the card
        fsrs_helper.review_card(card, Rating.Good.value)
        
        response = self.client.get(f'/api/lessons/card-info/{question.id}',
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        expected_fields = ['due_date', 'stability', 'difficulty', 'retrievability', 
                          'reps', 'lapses', 'state', 'last_review']
        
        for field in expected_fields:
            self.assertIn(field, data, f"Missing field: {field}")
        
        # Verify data types
        self.assertIsInstance(data['stability'], (int, float))
        self.assertIsInstance(data['difficulty'], (int, float))
        self.assertIsInstance(data['retrievability'], (int, float))
        self.assertIsInstance(data['reps'], int)
        self.assertIsInstance(data['lapses'], int)
        self.assertIsInstance(data['state'], int)

class TestFSRSOptimizer(unittest.TestCase):
    """Test FSRS optimizer functionality (if enabled)"""
    
    def setUp(self):
        self.fsrs_helper = FSRSHelper()
        
    @unittest.skipUnless(
        os.getenv('FSRS_OPTIMIZER_ENABLED', 'false').lower() == 'true',
        "FSRS Optimizer not enabled"
    )
    def test_optimizer_with_review_logs(self):
        """Test FSRS optimizer with review log data"""
        try:
            from fsrs import ReviewLog, Optimizer
        except ImportError:
            self.skipTest("FSRS Optimizer not available")
        
        # Create sample review logs
        review_logs = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(50):  # Create 50 sample reviews
            review_log = ReviewLog(
                rating=Rating(2 + (i % 3)),  # Ratings 2, 3, 4
                elapsed_days=i,
                scheduled_days=max(1, i - 1),
                review_datetime=base_time + timedelta(days=i)
            )
            review_logs.append(review_log)
        
        # Initialize optimizer
        optimizer = Optimizer(review_logs)
        
        # Compute optimal parameters
        optimal_parameters = optimizer.compute_optimal_parameters()
        
        self.assertIsInstance(optimal_parameters, tuple)
        self.assertEqual(len(optimal_parameters), 21)  # FSRS has 21 parameters
        
        # Compute optimal retention
        optimal_retention = optimizer.compute_optimal_retention(optimal_parameters)
        
        self.assertIsInstance(optimal_retention, float)
        self.assertGreater(optimal_retention, 0.0)
        self.assertLess(optimal_retention, 1.0)
        
        # Test using optimized parameters
        optimized_helper = FSRSHelper(optimal_parameters)
        self.assertIsInstance(optimized_helper, FSRSHelper)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
```

#### MongoDB Atlas Production Configuration
```python
# config.py - Production configuration for MongoDB Atlas
import os
from urllib.parse import quote_plus

class Config:
    # MongoDB Atlas Configuration
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
    MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER', 'cluster0.mongodb.net')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'math_learning')
    
    # Construct MongoDB URI for Atlas
    if MONGODB_USERNAME and MONGODB_PASSWORD:
        MONGODB_URI = f"mongodb+srv://{quote_plus(MONGODB_USERNAME)}:{quote_plus(MONGODB_PASSWORD)}@{MONGODB_CLUSTER}/{MONGODB_DB_NAME}?retryWrites=true&w=majority&ssl=true"
    else:
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/math_learning')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24 hours
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # FSRS Configuration
    FSRS_OPTIMIZER_ENABLED = os.getenv('FSRS_OPTIMIZER_ENABLED', 'false').lower() == 'true'
    
    # Application Configuration
    MAX_LESSON_QUESTIONS = int(os.getenv('MAX_LESSON_QUESTIONS', '20'))
    DEFAULT_RETENTION_RATE = float(os.getenv('DEFAULT_RETENTION_RATE', '0.85'))
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Production MongoDB Atlas settings
    MONGODB_CONNECT_TIMEOUT = 10000
    MONGODB_SERVER_SELECTION_TIMEOUT = 5000
    MONGODB_SOCKET_TIMEOUT = 20000
    MONGODB_MAX_POOL_SIZE = 100
    MONGODB_MIN_POOL_SIZE = 10

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
    # Development settings
    MONGODB_MAX_POOL_SIZE = 10
    MONGODB_MIN_POOL_SIZE = 2

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    
    # Use test database
    MONGODB_DB_NAME = 'math_learning_test'
    MONGODB_URI = 'mongodb://localhost:27017/math_learning_test'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

#### Docker Configuration for MongoDB Atlas
```yaml
# docker-compose.yml - Updated for MongoDB Atlas
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: math_learning_api
    restart: unless-stopped
    environment:
      FLASK_ENV: production
      # MongoDB Atlas connection (no local MongoDB needed)
      MONGODB_USERNAME: ${MONGODB_USERNAME}
      MONGODB_PASSWORD: ${MONGODB_PASSWORD}
      MONGODB_CLUSTER: ${MONGODB_CLUSTER}
      MONGODB_DB_NAME: ${MONGODB_DB_NAME}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
      FSRS_OPTIMIZER_ENABLED: ${FSRS_OPTIMIZER_ENABLED}
    ports:
      - "5000:5000"
    networks:
      - app-network
    depends_on:
      - redis  # Add Redis for caching

  redis:
    image: redis:7-alpine
    container_name: math_learning_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: math_learning_web
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network

volumes:
  redis_data:

networks:
  app-network:
    driver: bridge
```

#### Environment Variables Template (.env.example)
```env
# MongoDB Atlas Configuration
MONGODB_USERNAME=your_atlas_username
MONGODB_PASSWORD=your_atlas_password
MONGODB_CLUSTER=cluster0.mongodb.net
MONGODB_DB_NAME=math_learning

# Alternative: Full MongoDB URI (if you prefer)
# MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/math_learning?retryWrites=true&w=majority

# Application Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
SECRET_KEY=your-flask-secret-key-change-this-in-production

# Application Configuration
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# FSRS Configuration
FSRS_OPTIMIZER_ENABLED=true
DEFAULT_RETENTION_RATE=0.85
MAX_LESSON_QUESTIONS=20

# Redis Configuration (for caching)
REDIS_URL=redis://redis:6379/0

# Logging Configuration
LOG_LEVEL=INFO
```

#### Deployment Script for MongoDB Atlas
```bash
#!/bin/bash
# deploy_atlas.sh - Deployment script for MongoDB Atlas

echo "🚀 Deploying Math Learning System with MongoDB Atlas"

# Check required environment variables
required_vars=("MONGODB_USERNAME" "MONGODB_PASSWORD" "JWT_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var environment variable is not set"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Test MongoDB Atlas connection
echo "🔌 Testing MongoDB Atlas connection..."
python3 -c "
import os
from pymongo import MongoClient
from urllib.parse import quote_plus

username = os.getenv('MONGODB_USERNAME')
password = os.getenv('MONGODB_PASSWORD')
cluster = os.getenv('MONGODB_CLUSTER', 'cluster0.mongodb.net')
db_name = os.getenv('MONGODB_DB_NAME', 'math_learning')

uri = f'mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{cluster}/{db_name}?retryWrites=true&w=majority'

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print('✅ MongoDB Atlas connection successful')
except Exception as e:
    print(f'❌ MongoDB Atlas connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ MongoDB Atlas connection test failed"
    exit 1
fi

# Build and deploy with Docker Compose
echo "🐳 Building and starting services..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Test API health
echo "🏥 Testing API health..."
curl -f http://localhost:5000/api/health || {
    echo "❌ API health check failed"
    docker-compose logs backend
    exit 1
}

# Initialize database indexes
echo "📊 Creating database indexes..."
docker-compose exec backend python -c "
from utils.database import init_db
init_db()
print('✅ Database indexes created')
"

echo "🎉 Deployment completed successfully!"
echo "📊 API: http://localhost:5000"
echo "🌐 Frontend: http://localhost:80"
echo ""
echo "📋 To view logs:"
echo "  Backend: docker-compose logs -f backend"
echo "  Frontend: docker-compose logs -f frontend"
echo "  Redis: docker-compose logs -f redis"
```

### Key Updates Made:

1. **FSRS Library**: Updated to use the correct FSRS API based on the README:
   - `Scheduler` instead of `FSRS` class
   - Proper `Rating` and `State` enums
   - Correct parameter structure (21 parameters)
   - Proper card creation and review methods

2. **MongoDB Atlas Integration**:
   - Connection string format for Atlas
   - Proper SSL and retry settings
   - Environment variable configuration
   - No local MongoDB dependency

3. **Enhanced Error Handling**:
   - Connection retry logic
   - Health checks
   - Proper logging

4. **Production Configuration**:
   - Docker setup without local MongoDB
   - Redis for caching
   - Proper environment variable handling

5. **Testing Framework**:
   - Updated tests to use correct FSRS API
   - Atlas connection testing
   - FSRS optimizer testing (optional)

The implementation now correctly uses the FSRS library as documented in the README and provides seamless MongoDB Atlas integration for production deployment.
        
    def test_performance_to_rating_conversion(self):
        """Test conversion of performance metrics to FSRS ratings"""
        # Test cases: (correct, response_time, difficulty, expected_rating)
        test_cases = [
            (False, 10, 2, Rating.Again.value),      # Incorrect answer
            (True, 5, 1, Rating.Easy.value),         # Quick easy question
            (True, 15, 2, Rating.Good.value),        # Normal performance
            (True, 25, 3, Rating.Hard.value),        # Slow hard question
            (True, 50, 2, Rating.Again.value),       # Very slow (treat as fail)
        ]
        
        for correct, time, difficulty, expected in test_cases:
            rating = convert_performance_to_rating(correct, time, difficulty, 15)
            self.assertEqual(rating, expected, 
                f"Failed for correct={correct}, time={time}s, difficulty={difficulty}")
    
    def test_card_retrievability(self):
        """Test retrievability calculation"""
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), str(self.test_question.id)
        )
        
        # Review card to get some stability
        updated_card, _ = self.fsrs_helper.review_card(card, Rating.Good.value)
        
        # Calculate retrievability
        retrievability = self.fsrs_helper.get_card_retrievability(updated_card)
        
        self.assertIsInstance(retrievability, float)
        self.assertGreaterEqual(retrievability, 0.0)
        self.assertLessEqual(retrievability, 1.0)
        
    def test_scheduler_serialization(self):
        """Test scheduler serialization for database storage"""
        scheduler_dict = self.fsrs_helper.serialize_scheduler()
        
        self.assertIsInstance(scheduler_dict, dict)
        self.assertIn('parameters', scheduler_dict)
        self.assertIn('desired_retention', scheduler_dict)
        
        # Test deserialization
        new_helper = FSRSHelper.from_dict(scheduler_dict)
        self.assertIsInstance(new_helper, FSRSHelper)
        
    def test_user_stats_calculation(self):
        """Test user statistics calculation"""
        # Create and review several cards
        for i in range(5):
            question = Question.create_test_question(f"test_q_{i}")
            card = self.fsrs_helper.initialize_card_for_question(
                str(self.test_user.id), str(question.id)
            )
            
            # Review with different ratings
            rating = Rating.Good.value if i % 2 == 0 else Rating.Again.value
            self.fsrs_helper.review_card(card, rating)
        
        stats = FSRSCard.get_user_stats(str(self.test_user.id))
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['total_cards'], 5)
        self.assertGreaterEqual(stats['total_reps'], 5)
        self.assertIn('retention_rate', stats)
        self.assertIn('avg_stability', stats)
        self.assertIn('avg_difficulty', stats)

class TestLessonAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        os.environ['MONGODB_URI'] = 'mongodb://localhost:27017/math_learning_test'
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
    def setUp(self):
        self.test_user = User.create_test_user()
        self.auth_headers = self.get_auth_headers()
        
    def get_auth_headers(self):
        """Get authentication headers for test requests"""
        from flask_jwt_extended import create_access_token
        with self.app.app_context():
            token = create_access_token(identity=str(self.test_user.id))
        return {'Authorization': f'Bearer {token}'}
        
    def test_start_lesson_endpoint(self):
        """Test starting a new lesson"""
        response = self.client.post('/api/lessons/start', 
            json={
                'skill_ids': ['algebra'],
                'type': 'review'
            },
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('session_id', data)
        self.assertIn('question', data)
        
        # Verify question structure
        question = data['question']
        self.assertIn('id', question)
        self.assertIn('text', question)
        self.assertIn('options', question)
        self.assertIn('difficulty', question)
        
    def test_submit_answer_endpoint(self):
        """Test submitting an answer"""
        # First start a lesson
        start_response = self.client.post('/api/lessons/start',
            json={'skill_ids': ['algebra'], 'type': 'review'},
            headers=self.auth_headers
        )
        self.assertEqual(start_response.status_code, 200)
        start_data = start_response.get_json()
        
        # Submit answer
        response = self.client.post('/api/lessons/submit',
            json={
                'session_id': start_data['session_id'],
                'question_id': start_data['question']['id'],
                'answer_index': 0,
                'response_time': 10
            },
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('correct', data)
        self.assertIn('correct_answer', data)
        
        # Check FSRS-specific data
        if 'retrievability' in data:
            self.assertIsInstance(data['retrievability'], float)
            self.assertGreaterEqual(data['retrievability'], 0.0)
            self.assertLessEqual(data['retrievability'], 1.0)
            
    def test_due_count_### Database Connection Setup (utils/database.py)
```python
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
import logging
import time
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._client:
            self._connect()
    
    def _connect(self, retries=3, delay=1):
        """Connect to MongoDB Atlas with retry logic"""
        mongodb_uri = os.getenv('MONGODB_URI')
        db_name = os.getenv('MONGODB_DB_NAME', 'math_learning')
        
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is required")
        
        for attempt in range(retries):
            try:
                # MongoDB Atlas connection with optimized settings
                self._client = MongoClient(
                    mongodb_uri,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=10000,         # 10 second connection timeout
                    socketTimeoutMS=20000,          # 20 second socket timeout
                    maxPoolSize=50,                 # Maximum connections in pool
                    minPoolSize=5,                  # Minimum connections in pool
                    maxIdleTimeMS=30000,            # Close idle connections after 30s
                    waitQueueTimeoutMS=5000,        # Wait timeout for connection from pool
                    retryWrites=True,               # Enable retryable writes
                    retryReads=True,                # Enable retryable reads
                    w='majority'                    # Write concern majority
                )
                
                # Test the connection
                self._client.admin.command('ping')
                self._db_name = db_name
                
                logger.info("Successfully connected to MongoDB Atlas")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                if attempt == retries - 1:
                    logger.error(f"Failed to connect to MongoDB after {retries} attempts: {e}")
                    raise e
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
    
    @property
    def db(self):
        """Get database instance"""
        if not self._client:
            self._connect()
        return self._client[self._db_name]
    
    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        return self.db[collection_name]
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")
    
    def health_check(self):
        """Check if database connection is healthy"""
        try:
            self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Initialize database manager
db_manager = DatabaseManager()

def init_db():
    """Initialize database with indexes and collections"""
    try:
        db = db_manager.db
        
        # Create indexes for optimal performance
        create_indexes(db)
        
        # Create initial collections if they don't exist
        collections = ['users', 'questions', 'fsrs_cards', 'lesson_reports', 'lesson_sessions']
        existing_collections = db.list_collection_names()
        
        for collection in collections:
            if collection not in existing_collections:
                db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
        
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def create_indexes(db):
    """Create all necessary indexes for optimal performance"""
    
    # Users collection indexes
    try:
        db.users.create_index("email", unique=True)
        db.users.create_index("username", unique=True)
        logger.info("Created users collection indexes")
    except Exception as e:
        logger.warning(f"Users indexes may already exist: {e}")
    
    # Questions collection indexes
    try:
        db.questions.create_index([("skill_category", 1), ("difficulty_level", 1)])
        db.questions.create_index("tags")
        db.questions.create_index("sub_topic")
        logger.info("Created questions collection indexes")
    except Exception as e:
        logger.warning(f"Questions indexes may already exist: {e}")
    
    # FSRS Cards collection indexes - CRITICAL for performance
    try:
        db.fsrs_cards.create_index([("user_id", 1), ("due_date", 1)])
        db.fsrs_cards.create_index([("user_id", 1), ("question_id", 1)], unique=True)
        db.fsrs_cards.create_index([("due_date", 1), ("state", 1)])
        db.fsrs_cards.create_index([("user_id", 1), ("state", 1)])
        logger.info("Created FSRS cards collection indexes")
    except Exception as e:
        logger.warning(f"FSRS cards indexes may already exist: {e}")
    
    # Lesson Reports collection indexes
    try:
        db.lesson_reports.create_index([("user_id", 1), ("timestamp", -1)])
        db.lesson_reports.create_index("session_id")
        db.lesson_reports.create_index([("user_id", 1), ("question_id", 1)])
        logger.info("Created lesson reports collection indexes")
    except Exception as e:
        logger.warning(f"Lesson reports indexes may already exist: {e}")
    
    # Lesson Sessions collection indexes
    try:
        db.lesson_sessions.create_index([("user_id", 1), ("start_time", -1)])
        db.lesson_sessions.create_index([("user_id", 1), ("completed", 1)])
        logger.info("Created lesson sessions collection indexes")
    except Exception as e:
        logger.warning(f"Lesson sessions indexes may already exist: {e}")

# Utility function to get database instance
def get_db():
    """Get database instance"""
    return db_manager.db

# Connection health check for monitoring
def check_db_health():
    """Check database connection health"""
    return db_manager.health_check()
```# Complete Implementation Guide - Math Learning System with Spaced Repetition

## Implementation Checklist for Development LLM

This guide provides all necessary details for implementing the Math Learning System. Each section includes specific code examples, configuration details, and step-by-step instructions.

---

## 1. ENVIRONMENT SETUP & DEPENDENCIES

### Backend Dependencies (requirements.txt)
```txt
Flask==2.3.3
Flask-CORS==4.0.0
Flask-JWT-Extended==4.5.3
pymongo==4.5.0
python-dotenv==1.0.0
bcrypt==4.0.1
fsrs==4.0.0
python-dateutil==2.8.2
numpy==1.24.3
pandas==2.0.3
marshmallow==3.20.1
flask-limiter==3.5.0
```

### Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "vue": "^3.3.4",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.6",
    "axios": "^1.5.0",
    "@headlessui/vue": "^1.7.16",
    "@heroicons/vue": "^2.0.18"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.4.0",
    "vite": "^4.4.9",
    "tailwindcss": "^3.3.3",
    "autoprefixer": "^10.4.15",
    "postcss": "^8.4.29"
  }
}
```

### Environment Configuration
```env
# .env file
# MongoDB Atlas Connection
MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/math_learning?retryWrites=true&w=majority
MONGODB_DB_NAME=math_learning

# For local MongoDB (alternative)
# MONGODB_URI=mongodb://localhost:27017/math_learning

JWT_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_APP=app.py
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional: For FSRS Optimizer
FSRS_OPTIMIZER_ENABLED=true
```

### MongoDB Atlas Setup Instructions
1. **Create MongoDB Atlas Account**:
   - Go to https://www.mongodb.com/cloud/atlas
   - Sign up for a free account
   - Create a new cluster (M0 tier is free)

2. **Configure Network Access**:
   - Go to Network Access in Atlas dashboard
   - Add IP Address: 0.0.0.0/0 (for development) or your specific IPs
   - For production, restrict to your server IPs only

3. **Create Database User**:
   - Go to Database Access
   - Create a new database user with read/write permissions
   - Note the username and password for connection string

4. **Get Connection String**:
   - Go to Clusters → Connect → Connect your application
   - Choose Python driver
   - Copy connection string and update MONGODB_URI in .env

---

## 2. DETAILED BACKEND IMPLEMENTATION

### Project Structure
```
backend/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models/
│   ├── __init__.py
│   ├── user.py          # User model and operations
│   ├── question.py      # Question model and database queries
│   ├── lesson.py        # Lesson logic and FSRS integration
│   └── fsrs_card.py     # FSRS card management
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Authentication endpoints
│   ├── skills.py        # Skill management endpoints
│   ├── lessons.py       # Lesson delivery endpoints
│   └── reports.py       # Progress and reporting endpoints
├── utils/
│   ├── __init__.py
│   ├── database.py      # MongoDB connection utilities
│   ├── fsrs_helper.py   # FSRS algorithm wrapper
│   └── validators.py    # Input validation functions
└── requirements.txt
```

### Core Flask Application (app.py)
```python
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils.database import init_db
from routes.auth import auth_bp
from routes.skills import skills_bp
from routes.lessons import lessons_bp
from routes.reports import reports_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])
    jwt = JWTManager(app)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(skills_bp, url_prefix='/api/skills')
    app.register_blueprint(lessons_bp, url_prefix='/api/lessons')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### FSRS Integration Helper (utils/fsrs_helper.py)
```python
from fsrs import Scheduler, Card, Rating, ReviewLog, State
from datetime import datetime, timezone, timedelta
from models.fsrs_card import FSRSCard
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FSRSHelper:
    def __init__(self, user_parameters=None):
        """
        Initialize FSRS scheduler with custom or default parameters
        Based on the latest FSRS implementation
        """
        # Default FSRS parameters (optimized for general learning)
        default_parameters = (
            0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194,
            0.001, 1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629,
            1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542
        )
        
        parameters = user_parameters if user_parameters else default_parameters
        
        # Initialize scheduler with custom settings for math learning
        self.scheduler = Scheduler(
            parameters=parameters,
            desired_retention=0.85,  # 85% retention rate for math learning
            learning_steps=(
                timedelta(minutes=1),    # First step: 1 minute
                timedelta(minutes=10)    # Second step: 10 minutes
            ),
            relearning_steps=(timedelta(minutes=10),),  # Relearning step
            maximum_interval=36500,  # Maximum ~100 years
            enable_fuzzing=True      # Add randomness to intervals
        )
        
    def create_new_card(self) -> Card:
        """Create a new FSRS card (all new cards are due immediately)"""
        return Card()
    
    def initialize_card_for_question(self, user_id: str, question_id: str) -> FSRSCard:
        """Create a new FSRS card for a user-question pair"""
        # Create new FSRS card object
        card = self.create_new_card()
        
        # Create our database FSRSCard object
        fsrs_card = FSRSCard(
            user_id=user_id,
            question_id=question_id,
            # Card properties from FSRS Card object
            due_date=card.due,
            stability=card.stability,
            difficulty=card.difficulty,
            elapsed_days=card.elapsed_days,
            scheduled_days=card.scheduled_days,
            reps=card.reps,
            lapses=card.lapses,
            state=card.state.value,  # State enum to int
            last_review=card.last_review
        )
        fsrs_card.save()
        return fsrs_card
    
    def get_due_cards(self, user_id: str, limit: int = 20) -> List[FSRSCard]:
        """Get cards that are due for review"""
        return FSRSCard.get_due_cards(user_id, limit)
    
    def review_card(self, fsrs_card: FSRSCard, rating_value: int, 
                   review_time: Optional[datetime] = None) -> Tuple[FSRSCard, ReviewLog]:
        """
        Process a card review using FSRS algorithm
        
        Args:
            fsrs_card: FSRSCard object from database
            rating_value: int (1=Again, 2=Hard, 3=Good, 4=Easy)
            review_time: datetime for when review occurred (UTC)
            
        Returns:
            Tuple of updated FSRSCard and ReviewLog
        """
        if review_time is None:
            review_time = datetime.now(timezone.utc)
            
        # Convert FSRSCard to FSRS Card object
        card = Card(
            due=fsrs_card.due_date,
            stability=fsrs_card.stability,
            difficulty=fsrs_card.difficulty,
            elapsed_days=fsrs_card.elapsed_days,
            scheduled_days=fsrs_card.scheduled_days,
            reps=fsrs_card.reps,
            lapses=fsrs_card.lapses,
            state=State(fsrs_card.state),  # Convert int to State enum
            last_review=fsrs_card.last_review
        )
        
        # Create Rating enum from integer
        rating = Rating(rating_value)
        
        # Process review with FSRS scheduler
        try:
            updated_card, review_log = self.scheduler.review_card(
                card, rating, review_time
            )
            
            # Update FSRSCard object with new values
            fsrs_card.update_from_fsrs_card(updated_card)
            fsrs_card.save()
            
            logger.info(f"Card reviewed: user={user_id}, rating={rating_value}, "
                       f"next_due={updated_card.due}")
            
            return fsrs_card, review_log
            
        except Exception as e:
            logger.error(f"Error reviewing card: {e}")
            raise
    
    def get_card_retrievability(self, fsrs_card: FSRSCard, 
                               current_time: Optional[datetime] = None) -> float:
        """
        Calculate current probability of correctly recalling a card
        
        Returns:
            float: Retrievability between 0 and 1
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
            
        # Convert to FSRS Card object
        card = Card(
            due=fsrs_card.due_date,
            stability=fsrs_card.stability,
            difficulty=fsrs_card.difficulty,
            elapsed_days=fsrs_card.elapsed_days,
            scheduled_days=fsrs_card.scheduled_days,
            reps=fsrs_card.reps,
            lapses=fsrs_card.lapses,
            state=State(fsrs_card.state),
            last_review=fsrs_card.last_review
        )
        
        return self.scheduler.get_card_retrievability(card, current_time)
    
    def calculate_retention_rate(self, user_id: str, days: int = 30) -> float:
        """Calculate user's retention rate over specified period"""
        return FSRSCard.calculate_retention_rate(user_id, days)
    
    def serialize_scheduler(self) -> dict:
        """Serialize scheduler for database storage"""
        return self.scheduler.to_dict()
    
    @classmethod
    def from_dict(cls, scheduler_dict: dict) -> 'FSRSHelper':
        """Create FSRSHelper from serialized scheduler"""
        scheduler = Scheduler.from_dict(scheduler_dict)
        helper = cls.__new__(cls)
        helper.scheduler = scheduler
        return helper

# Utility function for converting lesson performance to FSRS rating
def convert_performance_to_rating(is_correct: bool, response_time: int, 
                                difficulty_level: int, user_avg_time: int = 15) -> int:
    """
    Convert lesson performance to FSRS rating (1-4)
    
    Args:
        is_correct: bool - whether answer was correct
        response_time: int - seconds taken to answer
        difficulty_level: int - question difficulty (1-4)
        user_avg_time: int - user's average response time
    
    Returns:
        int: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy)
    """
    if not is_correct:
        return Rating.Again.value  # 1 - incorrect answer
    
    # Correct answer - determine difficulty based on time and question difficulty
    time_factor = response_time / user_avg_time
    
    # Adjust thresholds based on question difficulty
    difficulty_multiplier = 1 + (difficulty_level - 2) * 0.2  # 0.8 to 1.4
    adjusted_time_factor = time_factor * difficulty_multiplier
    
    if adjusted_time_factor <= 0.5:
        return Rating.Easy.value    # 4 - very quick correct answer
    elif adjusted_time_factor <= 1.0:
        return Rating.Good.value    # 3 - normal speed correct answer  
    elif adjusted_time_factor <= 1.5:
        return Rating.Hard.value    # 2 - slow correct answer
    else:
        return Rating.Again.value   # 1 - very slow (treat as incorrect)
```

### Lesson Routes Implementation (routes/lessons.py)
```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.question import Question
from models.lesson import LessonSession
from utils.fsrs_helper import FSRSHelper, convert_performance_to_rating
from utils.validators import validate_lesson_submission
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
lessons_bp = Blueprint('lessons', __name__)
fsrs_helper = FSRSHelper()

@lessons_bp.route('/start', methods=['POST'])
@jwt_required()
def start_lesson():
    """Start a new lesson session"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    skill_ids = data.get('skill_ids', [])
    lesson_type = data.get('type', 'review')  # 'initial', 'review', 'practice'
    
    try:
        # Create lesson session
        session = LessonSession.create_session(
            user_id=user_id,
            skill_ids=skill_ids,
            lesson_type=lesson_type
        )
        
        # Get first question based on lesson type
        if lesson_type == 'initial':
            # For initial assessment, select questions across skill levels
            question = Question.get_assessment_question(skill_ids)
            if question:
                # Create new FSRS card for new question
                fsrs_helper.initialize_card_for_question(user_id, str(question['_id']))
        else:
            # For review sessions, prioritize due cards
            due_cards = fsrs_helper.get_due_cards(user_id, limit=1)
            if due_cards:
                question = Question.get_by_id(due_cards[0].question_id)
            else:
                # No due cards, select new questions
                question = Question.get_new_question(user_id, skill_ids)
                if question:
                    fsrs_helper.initialize_card_for_question(user_id, str(question['_id']))
        
        if not question:
            return jsonify({'error': 'No questions available'}), 404
        
        session.add_question(str(question['_id']))
        
        return jsonify({
            'session_id': str(session.id),
            'question': {
                'id': str(question['_id']),
                'text': question['question_text'],
                'options': question['options'],
                'difficulty': question['difficulty_level'],
                'skill_category': question['skill_category']
            }
        })
        
    except Exception as e:
        logger.error(f"Error starting lesson: {e}")
        return jsonify({'error': str(e)}), 500

@lessons_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_answer():
    """Submit answer for current question"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate input
    validation_error = validate_lesson_submission(data)
    if validation_error:
        return jsonify({'error': validation_error}), 400
    
    session_id = data['session_id']
    question_id = data['question_id']
    answer_index = data['answer_index']
    response_time = data.get('response_time', 0)
    
    try:
        # Get question and check answer
        question = Question.get_by_id(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        is_correct = answer_index == question['correct_answer']
        
        # Record answer in session
        session = LessonSession.get_by_id(session_id)
        session.record_answer(
            question_id=question_id,
            answer_index=answer_index,
            is_correct=is_correct,
            response_time=response_time
        )
        
        # Update FSRS card based on performance
        fsrs_card = FSRSCard.get_by_user_and_question(user_id, question_id)
        review_log = None
        
        if fsrs_card:
            # Convert performance to FSRS rating
            user_avg_time = session.get_user_average_time() or 15
            rating = convert_performance_to_rating(
                is_correct, response_time, question['difficulty_level'], user_avg_time
            )
            
            # Review the card with FSRS
            updated_card, review_log = fsrs_helper.review_card(
                fsrs_card, rating, datetime.now(timezone.utc)
            )
            
            logger.info(f"Card reviewed: rating={rating}, next_due={updated_card.due_date}")
        
        # Get next question
        next_question = None
        if session.should_continue():
            # Try to get next due card
            due_cards = fsrs_helper.get_due_cards(user_id, limit=5)
            available_cards = [
                card for card in due_cards 
                if card.question_id not in session.completed_questions
            ]
            
            if available_cards:
                next_q = Question.get_by_id(available_cards[0].question_id)
                if next_q:
                    next_question = {
                        'id': str(next_q['_id']),
                        'text': next_q['question_text'],
                        'options': next_q['options'],
                        'difficulty': next_q['difficulty_level'],
                        'skill_category': next_q['skill_category']
                    }
                    session.add_question(str(next_q['_id']))
        
        response_data = {
            'correct': is_correct,
            'correct_answer': question['correct_answer'],
            'explanation': question.get('explanation', ''),
            'next_question': next_question,
            'session_complete': next_question is None
        }
        
        # Add FSRS information if available
        if fsrs_card and review_log:
            # Calculate retrievability for feedback
            retrievability = fsrs_helper.get_card_retrievability(fsrs_card)
            response_data['retrievability'] = round(retrievability, 2)
            response_data['next_review'] = fsrs_card.due_date.isoformat()
        
        if next_question is None:
            # Session complete, generate summary
            response_data['session_summary'] = session.generate_summary()
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({'error': str(e)}), 500

@lessons_bp.route('/due-count', methods=['GET'])
@jwt_required()
def get_due_count():
    """Get count of cards due for review"""
    user_id = get_jwt_identity()
    
    try:
        due_cards = fsrs_helper.get_due_cards(user_id, limit=100)
        new_cards = FSRSCard.get_new_cards(user_id, limit=50)
        
        # Count cards by state
        learning_count = sum(1 for card in due_cards if card.state == 1)
        review_count = sum(1 for card in due_cards if card.state == 2)
        relearning_count = sum(1 for card in due_cards if card.state == 3)
        
        return jsonify({
            'due_count': len(due_cards),
            'new_count': len(new_cards),
            'learning_count': learning_count,
            'review_count': review_count,
            'relearning_count': relearning_count
        })
        
    except Exception as e:
        logger.error(f"Error getting due count: {e}")
        return jsonify({'error': str(e)}), 500

@lessons_bp.route('/card-info/<question_id>', methods=['GET'])
@jwt_required()
def get_card_info(question_id):
    """Get detailed information about a specific card"""
    user_id = get_jwt_identity()
    
    try:
        fsrs_card = FSRSCard.get_by_user_and_question(user_id, question_id)
        if not fsrs_card:
            return jsonify({'error': 'Card not found'}), 404
        
        # Get current retrievability
        retrievability = fsrs_helper.get_card_retrievability(fsrs_card)
        
        return jsonify({
            'due_date': fsrs_card.due_date.isoformat(),
            'stability': round(fsrs_card.stability, 2),
            'difficulty': round(fsrs_card.difficulty, 2),
            'retrievability': round(retrievability, 2),
            'reps': fsrs_card.reps,
            'lapses': fsrs_card.lapses,
            'state': fsrs_card.state,
            'last_review': fsrs_card.last_review.isoformat() if fsrs_card.last_review else None
        })
        
    except Exception as e:
        logger.error(f"Error getting card info: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## 3. DETAILED FRONTEND IMPLEMENTATION

### Project Structure
```
frontend/
├── src/
│   ├── main.js              # Vue app entry point
│   ├── App.vue              # Root component
│   ├── router/
│   │   └── index.js         # Vue Router configuration
│   ├── stores/
│   │   ├── auth.js          # Authentication store
│   │   ├── lesson.js        # Lesson state management
│   │   └── progress.js      # Progress tracking store
│   ├── services/
│   │   ├── api.js           # Axios configuration
│   │   ├── auth.service.js  # Authentication API calls
│   │   ├── lesson.service.js # Lesson API calls
│   │   └── progress.service.js # Progress API calls
│   ├── components/
│   │   ├── common/
│   │   │   ├── LoadingSpinner.vue
│   │   │   ├── ProgressBar.vue
│   │   │   └── AlertMessage.vue
│   │   ├── lesson/
│   │   │   ├── QuestionCard.vue
│   │   │   ├── AnswerOptions.vue
│   │   │   ├── LessonSummary.vue
│   │   │   └── ProgressIndicator.vue
│   │   └── dashboard/
│   │       ├── StatsCard.vue
│   │       ├── SkillProgress.vue
│   │       └── StudyStreak.vue
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── SkillSelectionView.vue
│   │   ├── LessonView.vue
│   │   └── ProgressView.vue
│   └── utils/
│       ├── constants.js     # App constants
│       ├── formatters.js    # Data formatting utilities
│       └── validators.js    # Form validation
├── tailwind.config.js
├── vite.config.js
└── package.json
```

### Main Lesson Component (components/lesson/QuestionCard.vue)
```vue
<template>
  <div class="max-w-4xl mx-auto p-6 bg-white rounded-xl shadow-lg">
    <!-- Progress Indicator -->
    <div class="mb-6">
      <div class="flex justify-between items-center mb-2">
        <span class="text-sm font-medium text-gray-700">
          Question {{ currentQuestionIndex + 1 }} of {{ totalQuestions }}
        </span>
        <span class="text-sm text-gray-500">
          {{ formatTime(elapsedTime) }}
        </span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div 
          class="bg-blue-600 h-2 rounded-full transition-all duration-300"
          :style="{ width: progressPercentage + '%' }"
        ></div>
      </div>
    </div>

    <!-- Question -->
    <div class="mb-8">
      <div class="flex items-start space-x-3 mb-4">
        <div class="flex-shrink-0">
          <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <span class="text-blue-600 font-semibold text-sm">Q</span>
          </div>
        </div>
        <div class="flex-1">
          <h2 class="text-xl font-semibold text-gray-800 leading-relaxed">
            {{ question.text }}
          </h2>
          <div class="mt-2 flex items-center space-x-4 text-sm text-gray-500">
            <span class="flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              {{ question.skill_category }}
            </span>
            <span class="flex items-center">
              <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"/>
              </svg>
              {{ getDifficultyLabel(question.difficulty) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Answer Options -->
    <div class="space-y-3 mb-8">
      <button
        v-for="(option, index) in question.options"
        :key="index"
        @click="selectAnswer(index)"
        :disabled="answerSubmitted"
        :class="getOptionClass(index)"
        class="w-full p-4 text-left rounded-lg border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        <div class="flex items-center">
          <span class="flex-shrink-0 w-6 h-6 rounded-full border-2 mr-3 flex items-center justify-center text-sm font-medium"
                :class="getOptionCircleClass(index)">
            {{ String.fromCharCode(65 + index) }}
          </span>
          <span class="flex-1 text-gray-800">{{ option }}</span>
          <div v-if="answerSubmitted" class="flex-shrink-0 ml-3">
            <svg v-if="index === question.correct_answer" class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <svg v-else-if="index === selectedAnswer && index !== question.correct_answer" class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
          </div>
        </div>
      </button>
    </div>

    <!-- Explanation (shown after answer) -->
    <div v-if="answerSubmitted && question.explanation" class="mb-6 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400">
      <h3 class="font-medium text-blue-900 mb-2">Explanation</h3>
      <p class="text-blue-800">{{ question.explanation }}</p>
    </div>

    <!-- Action Buttons -->
    <div class="flex justify-between items-center">
      <button
        v-if="!answerSubmitted"
        @click="skipQuestion"
        class="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
      >
        Skip Question
      </button>
      <div v-else></div>

      <button
        v-if="!answerSubmitted"
        @click="submitAnswer"
        :disabled="selectedAnswer === null || submitting"
        class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <span v-if="submitting">Submitting...</span>
        <span v-else>Submit Answer</span>
      </button>
      <button
        v-else
        @click="nextQuestion"
        class="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
      >
        <span v-if="hasNextQuestion">Next Question</span>
        <span v-else>Complete Lesson</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'

export default {
  name: 'QuestionCard',
  props: {
    question: {
      type: Object,
      required: true
    },
    currentQuestionIndex: {
      type: Number,
      required: true
    },
    totalQuestions: {
      type: Number,
      required: true
    },
    hasNextQuestion: {
      type: Boolean,
      default: true
    }
  },
  emits: ['answer-submitted', 'question-skipped', 'next-question'],
  setup(props, { emit }) {
    const selectedAnswer = ref(null)
    const answerSubmitted = ref(false)
    const submitting = ref(false)
    const startTime = ref(Date.now())
    const elapsedTime = ref(0)
    let timer = null

    const progressPercentage = computed(() => {
      return ((props.currentQuestionIndex + 1) / props.totalQuestions) * 100
    })

    const selectAnswer = (index) => {
      if (!answerSubmitted.value) {
        selectedAnswer.value = index
      }
    }

    const getOptionClass = (index) => {
      if (!answerSubmitted.value) {
        return selectedAnswer.value === index
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
      }
      
      if (index === props.question.correct_answer) {
        return 'border-green-500 bg-green-50'
      } else if (index === selectedAnswer.value && index !== props.question.correct_answer) {
        return 'border-red-500 bg-red-50'
      } else {
        return 'border-gray-200 bg-gray-50'
      }
    }

    const getOptionCircleClass = (index) => {
      if (!answerSubmitted.value) {
        return selectedAnswer.value === index
          ? 'border-blue-500 bg-blue-500 text-white'
          : 'border-gray-300 text-gray-600'
      }
      
      if (index === props.question.correct_answer) {
        return 'border-green-500 bg-green-500 text-white'
      } else if (index === selectedAnswer.value && index !== props.question.correct_answer) {
        return 'border-red-500 bg-red-500 text-white'
      } else {
        return 'border-gray-300 text-gray-600'
      }
    }

    const getDifficultyLabel = (difficulty) => {
      const labels = {
        1: 'Easy',
        2: 'Medium',
        3: 'Hard',
        4: 'Expert'
      }
      return labels[difficulty] || 'Unknown'
    }

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const submitAnswer = async () => {
      if (selectedAnswer.value === null) return
      
      submitting.value = true
      const responseTime = Math.floor((Date.now() - startTime.value) / 1000)
      
      try {
        await emit('answer-submitted', {
          answer_index: selectedAnswer.value,
          response_time: responseTime
        })
        answerSubmitted.value = true
      } finally {
        submitting.value = false
      }
    }

    const skipQuestion = () => {
      emit('question-skipped')
    }

    const nextQuestion = () => {
      emit('next-question')
    }

    // Timer for elapsed time
    onMounted(() => {
      timer = setInterval(() => {
        elapsedTime.value = Math.floor((Date.now() - startTime.value) / 1000)
      }, 1000)
    })

    onUnmounted(() => {
      if (timer) {
        clearInterval(timer)
      }
    })

    return {
      selectedAnswer,
      answerSubmitted,
      submitting,
      elapsedTime,
      progressPercentage,
      selectAnswer,
      getOptionClass,
      getOptionCircleClass,
      getDifficultyLabel,
      formatTime,
      submitAnswer,
      skipQuestion,
      nextQuestion
    }
  }
}
</script>
```

---

## 4. DATABASE SCHEMA & SAMPLE DATA

### MongoDB Collection Schemas

#### Users Collection
```javascript
{
  _id: ObjectId("..."),
  username: "john_doe",
  email: "john@example.com",
  password_hash: "$2b$12$...",
  selected_skills: ["algebra", "geometry", "calculus"],
  fsrs_parameters: {
    request_retention: 0.85,
    maximum_interval: 36500,
    enable_fuzz: true,
    w: [0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234, 1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407, 2.9466, 0.5034, 0.6567]
  },
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-20T14:22:00Z"),
  last_login: ISODate("2024-01-20T14:22:00Z"),
  study_streak: 5,
  total_questions_answered: 127,
  preferred_lesson_length: 10
}
```

#### Questions Collection
```javascript
{
  _id: ObjectId("..."),
  question_text: "What is the derivative of x^2 + 3x + 5?",
  options: [
    "2x + 3",
    "x^2 + 3",
    "2x + 5",
    "x + 3"
  ],
  correct_answer: 0,
  explanation: "Using the power rule: d/dx(x^2) = 2x, d/dx(3x) = 3, d/dx(5) = 0. Therefore: 2x + 3 + 0 = 2x + 3",
  skill_category: "calculus",
  sub_topic: "derivatives",
  difficulty_level: 2,
  tags: ["power_rule", "polynomial_derivatives", "basic_calculus"],
  estimated_time: 45,
  created_by: "system",
  created_at: ISODate("2024-01-01T00:00:00Z"),
  usage_count: 234,
  success_rate: 0.76,
  metadata: {
    source: "calculus_textbook_ch3",
    chapter: 3,
    section: "3.2",
    cognitive_load: "low",
    prerequisites: ["basic_algebra", "function_notation"]
  }
}
```

#### FSRS Cards Collection
```javascript
{
  _id: ObjectId("..."),
  user_id: ObjectId("..."),
  question_id: ObjectId("..."),
  due_date: ISODate("2024-01-22T09:00:00Z"),
  stability: 4.67,
  difficulty: 6.83,
  elapsed_days: 2,
  scheduled_days: 3,
  reps: 3,
  lapses: 0,
  state: 2,
  last_review: ISODate("2024-01-20T14:30:00Z"),
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-20T14:30:00Z")
}
```

#### Lesson Reports Collection
```javascript
{
  _id: ObjectId("..."),
  user_id: ObjectId("..."),
  session_id: ObjectId("..."),
  question_id: ObjectId("..."),
  response: 2,
  is_correct: false,
  response_time: 23,
  timestamp: ISODate("2024-01-20T14:25:30Z"),
  confidence_level: "medium",
  hints_used: 1,
  skip_reason: null,
  difficulty_perceived: 3,
  session_metadata: {
    lesson_type: "review",
    device_type: "desktop",
    study_environment: "home"
  }
}
```

#### Lesson Sessions Collection
```javascript
{
  _id: ObjectId("..."),
  user_id: ObjectId("..."),
  session_type: "review",
  skill_ids: ["algebra", "geometry"],
  start_time: ISODate("2024-01-20T14:20:00Z"),
  end_time: ISODate("2024-01-20T14:35:00Z"),
  questions_attempted: 8,
  questions_correct: 6,
  total_time_spent: 900,
  completed: true,
  questions_order: [
    ObjectId("..."),
    ObjectId("..."),
    ObjectId("...")
  ],
  performance_metrics: {
    accuracy_rate: 0.75,
    average_response_time: 18.5,
    improvement_score: 0.12
  },
  created_at: ISODate("2024-01-20T14:20:00Z"),
  updated_at: ISODate("2024-01-20T14:35:00Z")
}
```

### Sample Data Seeds

#### Sample Users
```javascript
// users_seed.js
db.users.insertMany([
  {
    username: "demo_user",
    email: "demo@mathlearning.com",
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKjUEpvR4rQT2nu",
    selected_skills: ["algebra", "geometry"],
    fsrs_parameters: {
      request_retention: 0.85,
      maximum_interval: 36500,
      enable_fuzz: true,
      w: [0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234, 1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407, 2.9466, 0.5034, 0.6567]
    },
    created_at: new Date(),
    updated_at: new Date(),
    study_streak: 0,
    total_questions_answered: 0,
    preferred_lesson_length: 10
  }
]);
```

#### Sample Questions (Algebra)
```javascript
// questions_algebra_seed.js
db.questions.insertMany([
  {
    question_text: "Solve for x: 2x + 5 = 13",
    options: ["x = 4", "x = 6", "x = 8", "x = 9"],
    correct_answer: 0,
    explanation: "Subtract 5 from both sides: 2x = 8. Then divide by 2: x = 4",
    skill_category: "algebra",
    sub_topic: "linear_equations",
    difficulty_level: 1,
    tags: ["basic_algebra", "linear_equations", "solving"],
    estimated_time: 30,
    created_by: "system",
    created_at: new Date(),
    usage_count: 0,
    success_rate: 0.85
  },
  {
    question_text: "What is the slope of the line passing through points (2, 3) and (6, 11)?",
    options: ["2", "3", "4", "8"],
    correct_answer: 0,
    explanation: "Slope = (y2 - y1) / (x2 - x1) = (11 - 3) / (6 - 2) = 8 / 4 = 2",
    skill_category: "algebra",
    sub_topic: "linear_functions",
    difficulty_level: 2,
    tags: ["slope", "coordinate_geometry", "linear_functions"],
    estimated_time: 45,
    created_by: "system",
    created_at: new Date(),
    usage_count: 0,
    success_rate: 0.72
  }
]);
```

---

## 5. CONFIGURATION FILES

### Tailwind Configuration (tailwind.config.js)
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'bounce-subtle': 'bounceSubtle 0.6s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

### Vite Configuration (vite.config.js)
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', 'axios'],
          ui: ['@headlessui/vue', '@heroicons/vue'],
        },
      },
    },
  },
})
```

---

## 6. CRITICAL IMPLEMENTATION DETAILS

### FSRS Algorithm Setup & Integration

#### Installing and Configuring FSRS
```python
# requirements.txt entry
fsrs==3.4.1

# In your virtual environment
pip install fsrs

# Example initialization in utils/fsrs_helper.py
from fsrs import FSRS, Card, Rating, ReviewLog, State
from datetime import datetime, timezone

class FSRSManager:
    def __init__(self, user_parameters=None):
        """
        Initialize FSRS with custom or default parameters
        user_parameters: dict with FSRS configuration
        """
        default_params = {
            'request_retention': 0.85,  # 85% retention target
            'maximum_interval': 36500,  # ~100 years max interval
            'enable_fuzz': True,        # Add randomness to intervals
            'enable_short_term': True,  # Enable short-term scheduler
            'w': [0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 
                  1.0651, 0.0234, 1.616, 0.1544, 1.0824, 1.9813, 
                  0.0953, 0.2975, 2.2042, 0.2407, 2.9466, 0.5034, 0.6567]
        }
        
        if user_parameters:
            default_params.update(user_parameters)
            
        self.fsrs = FSRS(**default_params)
    
    def create_new_card(self):
        """Create a new FSRS card in 'New' state"""
        return Card()
    
    def review_card(self, card, rating_value, now=None):
        """
        Review a card with FSRS algorithm
        rating_value: 1=Again, 2=Hard, 3=Good, 4=Easy
        """
        if now is None:
            now = datetime.now(timezone.utc)
            
        rating = Rating(rating_value)
        
        # Perform the review
        updated_card, review_log = self.fsrs.review(card, rating, now)
        
        return updated_card, review_log
    
    def get_retrievability(self, card, now=None):
        """Calculate current retrievability (probability of recall)"""
        if now is None:
            now = datetime.now(timezone.utc)
        return self.fsrs.get_retrievability(card, now)
```

#### Performance-to-Rating Conversion Logic
```python
def convert_performance_to_rating(is_correct, response_time, difficulty_level, user_avg_time=15):
    """
    Convert lesson performance to FSRS rating (1-4)
    
    Args:
        is_correct: bool - whether answer was correct
        response_time: int - seconds taken to answer
        difficulty_level: int - question difficulty (1-4)
        user_avg_time: int - user's average response time
    
    Returns:
        int: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy)
    """
    if not is_correct:
        return 1  # Again - incorrect answer
    
    # Correct answer - determine difficulty based on time and question difficulty
    time_factor = response_time / user_avg_time
    
    # Adjust thresholds based on question difficulty
    difficulty_multiplier = 1 + (difficulty_level - 2) * 0.2  # 0.8 to 1.4
    adjusted_time_factor = time_factor * difficulty_multiplier
    
    if adjusted_time_factor <= 0.5:
        return 4  # Easy - very quick correct answer
    elif adjusted_time_factor <= 1.0:
        return 3  # Good - normal speed correct answer  
    elif adjusted_time_factor <= 1.5:
        return 2  # Hard - slow correct answer
    else:
        return 1  # Again - very slow correct answer (treat as incorrect)
```

### Database Indexing Requirements
```javascript
// MongoDB indexes for optimal performance
// Run these commands in MongoDB shell

// Users collection
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })

// Questions collection  
db.questions.createIndex({ "skill_category": 1, "difficulty_level": 1 })
db.questions.createIndex({ "tags": 1 })
db.questions.createIndex({ "sub_topic": 1 })

// FSRS Cards collection - CRITICAL for performance
db.fsrs_cards.createIndex({ "user_id": 1, "due_date": 1 })
db.fsrs_cards.createIndex({ "user_id": 1, "question_id": 1 }, { unique: true })
db.fsrs_cards.createIndex({ "due_date": 1, "state": 1 })

// Lesson Reports collection
db.lesson_reports.createIndex({ "user_id": 1, "timestamp": -1 })
db.lesson_reports.createIndex({ "session_id": 1 })
db.lesson_reports.createIndex({ "user_id": 1, "question_id": 1 })

// Lesson Sessions collection
db.lesson_sessions.createIndex({ "user_id": 1, "start_time": -1 })
db.lesson_sessions.createIndex({ "user_id": 1, "completed": 1 })
```

### State Management (Pinia Store Examples)

#### Authentication Store (stores/auth.js)
```javascript
import { defineStore } from 'pinia'
import { authService } from '@/services/auth.service'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    isAuthenticated: false,
    loading: false,
    error: null
  }),

  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated && !!state.token
  },

  actions: {
    async login(credentials) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.login(credentials)
        this.token = response.data.access_token
        this.user = response.data.user
        this.isAuthenticated = true
        
        localStorage.setItem('token', this.token)
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.error || 'Login failed'
        throw error
      } finally {
        this.loading = false
      }
    },

    async register(userData) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.register(userData)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.error || 'Registration failed'
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
      
      // Optional: call logout endpoint
      try {
        await authService.logout()
      } catch (error) {
        console.warn('Logout request failed:', error)
      }
    },

    async fetchUserProfile() {
      if (!this.token) return
      
      try {
        const response = await authService.getProfile()
        this.user = response.data
        this.isAuthenticated = true
      } catch (error) {
        console.error('Failed to fetch user profile:', error)
        this.logout()
      }
    },

    clearError() {
      this.error = null
    }
  }
})
```

#### Lesson Store (stores/lesson.js)
```javascript
import { defineStore } from 'pinia'
import { lessonService } from '@/services/lesson.service'

export const useLessonStore = defineStore('lesson', {
  state: () => ({
    currentSession: null,
    currentQuestion: null,
    sessionHistory: [],
    loading: false,
    error: null,
    sessionStats: {
      questionsAnswered: 0,
      correctAnswers: 0,
      totalTime: 0,
      averageTime: 0
    }
  }),

  getters: {
    accuracyRate: (state) => {
      if (state.sessionStats.questionsAnswered === 0) return 0
      return (state.sessionStats.correctAnswers / state.sessionStats.questionsAnswered) * 100
    },
    
    hasActiveSession: (state) => !!state.currentSession,
    
    sessionProgress: (state) => {
      if (!state.currentSession) return 0
      return (state.sessionStats.questionsAnswered / state.currentSession.target_questions) * 100
    }
  },

  actions: {
    async startLesson(lessonType, skillIds) {
      this.loading = true
      this.error = null
      
      try {
        const response = await lessonService.startLesson({
          type: lessonType,
          skill_ids: skillIds
        })
        
        this.currentSession = {
          id: response.data.session_id,
          type: lessonType,
          skills: skillIds,
          target_questions: 10, // Default, can be configured
          started_at: new Date()
        }
        
        this.currentQuestion = response.data.question
        this.resetSessionStats()
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.error || 'Failed to start lesson'
        throw error
      } finally {
        this.loading = false
      }
    },

    async submitAnswer(answerData) {
      this.loading = true
      this.error = null
      
      try {
        const response = await lessonService.submitAnswer({
          session_id: this.currentSession.id,
          question_id: this.currentQuestion.id,
          ...answerData
        })
        
        // Update session stats
        this.sessionStats.questionsAnswered++
        if (response.data.correct) {
          this.sessionStats.correctAnswers++
        }
        this.sessionStats.totalTime += answerData.response_time || 0
        this.sessionStats.averageTime = this.sessionStats.totalTime / this.sessionStats.questionsAnswered
        
        // Update question history
        this.sessionHistory.push({
          question: this.currentQuestion,
          answer: answerData,
          result: response.data,
          timestamp: new Date()
        })
        
        // Set next question or complete session
        if (response.data.next_question) {
          this.currentQuestion = response.data.next_question
        } else {
          // Session complete
          this.currentQuestion = null
          this.currentSession.completed_at = new Date()
          this.currentSession.summary = response.data.session_summary
        }
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.error || 'Failed to submit answer'
        throw error
      } finally {
        this.loading = false
      }
    },

    async skipQuestion() {
      // Implementation for skipping questions
      this.sessionStats.questionsAnswered++
      // Move to next question logic
    },

    completeSession() {
      if (this.currentSession) {
        this.currentSession.completed_at = new Date()
        this.currentQuestion = null
      }
    },

    resetSession() {
      this.currentSession = null
      this.currentQuestion = null
      this.sessionHistory = []
      this.resetSessionStats()
      this.error = null
    },

    resetSessionStats() {
      this.sessionStats = {
        questionsAnswered: 0,
        correctAnswers: 0,
        totalTime: 0,
        averageTime: 0
      }
    },

    clearError() {
      this.error = null
    }
  }
})
```

---

## 7. API ENDPOINTS SPECIFICATION

### Authentication Endpoints

#### POST /api/auth/register
```python
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user
    
    Body: {
        "username": "string",
        "email": "string", 
        "password": "string"
    }
    
    Returns: {
        "message": "User created successfully",
        "user_id": "string"
    }
    """
    data = request.get_json()
    
    # Validation
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user exists
    if User.find_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 409
    
    if User.find_by_username(data['username']):
        return jsonify({'error': 'Username already taken'}), 409
    
    try:
        user = User.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': str(user.id)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### POST /api/auth/login
```python
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    
    Body: {
        "email": "string",
        "password": "string"
    }
    
    Returns: {
        "access_token": "string",
        "user": {
            "id": "string",
            "username": "string",
            "email": "string",
            "selected_skills": ["string"]
        }
    }
    """
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.find_by_email(data['email'])
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    user.update_last_login()
    
    # Create access token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'selected_skills': user.selected_skills,
            'study_streak': user.study_streak
        }
    })
```

### Lesson Management Endpoints

#### GET /api/lessons/due-count
```python
@lessons_bp.route('/due-count', methods=['GET'])
@jwt_required()
def get_due_count():
    """
    Get count of due cards for review
    
    Returns: {
        "due_count": int,
        "new_count": int,
        "review_count": int
    }
    """
    user_id = get_jwt_identity()
    
    try:
        due_cards = fsrs_helper.get_due_cards(user_id, limit=100)
        new_cards = FSRSCard.get_new_cards(user_id, limit=50)
        
        return jsonify({
            'due_count': len(due_cards),
            'new_count': len(new_cards),
            'review_count': len(due_cards)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### GET /api/lessons/progress-summary
```python
@lessons_bp.route('/progress-summary', methods=['GET'])
@jwt_required()
def get_progress_summary():
    """
    Get user's learning progress summary
    
    Returns: {
        "total_questions": int,
        "correct_answers": int,
        "accuracy_rate": float,
        "study_streak": int,
        "skills_progress": {
            "skill_name": {
                "mastery_level": float,
                "questions_answered": int,
                "last_session": "ISO_date"
            }
        }
    }
    """
    user_id = get_jwt_identity()
    
    try:
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Calculate progress for each skill
        skills_progress = {}
        for skill in user.selected_skills:
            progress = UserProgress.get_skill_progress(user_id, skill)
            skills_progress[skill] = {
                'mastery_level': progress.mastery_level if progress else 0.0,
                'questions_answered': progress.total_questions if progress else 0,
                'last_session': progress.last_session_date.isoformat() if progress and progress.last_session_date else None
            }
        
        return jsonify({
            'total_questions': user.total_questions_answered,
            'correct_answers': user.total_correct_answers,
            'accuracy_rate': user.get_accuracy_rate(),
            'study_streak': user.study_streak,
            'skills_progress': skills_progress
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 8. DEPLOYMENT & TESTING INSTRUCTIONS

### Local Development Setup

#### Backend Setup
```bash
# Create virtual environment
python -m venv math_learning_env
source math_learning_env/bin/activate  # On Windows: math_learning_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export MONGODB_URI=mongodb://localhost:27017/math_learning
export JWT_SECRET_KEY=your-development-secret-key

# Initialize database with sample data
python scripts/init_db.py
python scripts/seed_questions.py

# Run Flask development server
flask run --host=0.0.0.0 --port=5000
```

#### Frontend Setup
```bash
# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Production Deployment

#### Docker Configuration (docker-compose.yml)
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: math_learning_db
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: math_learning
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    ports:
      - "27017:27017"
    networks:
      - app-network

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: math_learning_api
    restart: unless-stopped
    environment:
      FLASK_ENV: production
      MONGODB_URI: mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/math_learning?authSource=admin
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "5000:5000"
    depends_on:
      - mongodb
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: math_learning_web
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network

volumes:
  mongodb_data:

networks:
  app-network:
    driver: bridge
```

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Testing Framework

#### Backend Tests (tests/test_fsrs_integration.py)
```python
import unittest
from datetime import datetime, timezone, timedelta
from app import create_app
from utils.fsrs_helper import FSRSHelper
from models.user import User
from models.question import Question
from models.fsrs_card import FSRSCard

class TestFSRSIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.fsrs_helper = FSRSHelper()
        
    def setUp(self):
        # Create test user and questions
        self.test_user = User.create_test_user()
        self.test_question = Question.create_test_question()
        
    def tearDown(self):
        # Clean up test data
        User.delete_test_data()
        Question.delete_test_data()
        FSRSCard.delete_test_data()
        
    def test_new_card_creation(self):
        """Test creating a new FSRS card"""
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), 
            str(self.test_question.id)
        )
        
        self.assertIsNotNone(card)
        self.assertEqual(card.user_id, str(self.test_user.id))
        self.assertEqual(card.question_id, str(self.test_question.id))
        self.assertEqual(card.reps, 0)
        
    def test_card_review_cycle(self):
        """Test complete review cycle with different ratings"""
        card = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), 
            str(self.test_question.id)
        )
        
        # Test correct answer (rating 3 = Good)
        updated_card, review_log = self.fsrs_helper.review_card(card, 3)
        
        self.assertEqual(updated_card.reps, 1)
        self.assertGreater(updated_card.stability, card.stability)
        self.assertIsNotNone(review_log)
        
        # Test incorrect answer (rating 1 = Again)
        incorrect_card, incorrect_log = self.fsrs_helper.review_card(updated_card, 1)
        self.assertEqual(incorrect_card.lapses, 1)
        
    def test_due_cards_selection(self):
        """Test getting due cards for review"""
        # Create multiple cards with different due dates
        card1 = self.fsrs_helper.initialize_card_for_question(
            str(self.test_user.id), str(self.test_question.id)
        )
        
        # Make card1 due by setting due_date to past
        card1.due_date = datetime.now(timezone.utc) - timedelta(hours=1)
        card1.save()
        
        due_cards = self.fsrs_helper.get_due_cards(str(self.test_user.id))
        
        self.assertGreater(len(due_cards), 0)
        self.assertIn(card1.id, [card.id for card in due_cards])

class TestLessonAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
    def setUp(self):
        self.test_user = User.create_test_user()
        self.auth_headers = self.get_auth_headers()
        
    def get_auth_headers(self):
        """Get authentication headers for test requests"""
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(self.test_user.id))
        return {'Authorization': f'Bearer {token}'}
        
    def test_start_lesson_endpoint(self):
        """Test starting a new lesson"""
        response = self.client.post('/api/lessons/start', 
            json={
                'skill_ids': ['algebra'],
                'type': 'review'
            },
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('session_id', data)
        self.assertIn('question', data)
        
    def test_submit_answer_endpoint(self):
        """Test submitting an answer"""
        # First start a lesson
        start_response = self.client.post('/api/lessons/start',
            json={'skill_ids': ['algebra'], 'type': 'review'},
            headers=self.auth_headers
        )
        start_data = start_response.get_json()
        
        # Submit answer
        response = self.client.post('/api/lessons/submit',
            json={
                'session_id': start_data['session_id'],
                'question_id': start_data['question']['id'],
                'answer_index': 0,
                'response_time': 10
            },
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('correct', data)
        
if __name__ == '__main__':
    unittest.main()
```

#### Frontend Tests (src/tests/components/QuestionCard.test.js)
```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import QuestionCard from '@/components/lesson/QuestionCard.vue'

describe('QuestionCard', () => {
  let wrapper
  const mockQuestion = {
    id: '1',
    text: 'What is 2 + 2?',
    options: ['3', '4', '5', '6'],
    correct_answer: 1,
    explanation: 'Basic addition: 2 + 2 = 4',
    skill_category: 'arithmetic',
    difficulty: 1
  }
  
  beforeEach(() => {
    wrapper = mount(QuestionCard, {
      props: {
        question: mockQuestion,
        currentQuestionIndex: 0,
        totalQuestions: 10,
        hasNextQuestion: true
      }
    })
  })
  
  it('renders question text correctly', () => {
    expect(wrapper.text()).toContain('What is 2 + 2?')
  })
  
  it('renders all answer options', () => {
    const options = wrapper.findAll('button')
    expect(options).toHaveLength(mockQuestion.options.length + 2) // +2 for submit/next buttons
  })
  
  it('allows selecting an answer', async () => {
    const firstOption = wrapper.find('button')
    await firstOption.trigger('click')
    
    expect(wrapper.vm.selectedAnswer).toBe(0)
  })
  
  it('emits answer-submitted event when submitting', async () => {
    // Select an answer
    wrapper.vm.selectedAnswer = 1
    await wrapper.vm.$nextTick()
    
    // Find and click submit button
    const submitButton = wrapper.find('button:contains("Submit Answer")')
    await submitButton.trigger('click')
    
    expect(wrapper.emitted('answer-submitted')).toBeTruthy()
    expect(wrapper.emitted('answer-submitted')[0][0]).toEqual({
      answer_index: 1,
      response_time: expect.any(Number)
    })
  })
  
  it('shows correct answer after submission', async () => {
    wrapper.vm.selectedAnswer = 0 // Wrong answer
    wrapper.vm.answerSubmitted = true
    await wrapper.vm.$nextTick()
    
    // Should highlight correct answer in green
    const options = wrapper.findAll('.border-green-500')
    expect(options.length).toBeGreaterThan(0)
  })
  
  it('displays progress correctly', () => {
    expect(wrapper.text()).toContain('Question 1 of 10')
    expect(wrapper.vm.progressPercentage).toBe(10)
  })
})
```

### Performance Testing

#### Load Testing Script (scripts/load_test.py)
```python
import requests
import time
import json
import concurrent.futures
from datetime import datetime

class LoadTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def login_user(self, email, password):
        """Login and return auth token"""
        response = self.session.post(f"{self.base_url}/api/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return token
        else:
            raise Exception(f"Login failed: {response.text}")
            
    def start_lesson(self):
        """Start a lesson and return session data"""
        response = self.session.post(f"{self.base_url}/api/lessons/start", json={
            "skill_ids": ["algebra"],
            "type": "review"
        })
        return response.json() if response.status_code == 200 else None
        
    def submit_answer(self, session_id, question_id, answer_index=0):
        """Submit an answer"""
        response = self.session.post(f"{self.base_url}/api/lessons/submit", json={
            "session_id": session_id,
            "question_id": question_id,
            "answer_index": answer_index,
            "response_time": 5
        })
        return response.json() if response.status_code == 200 else None
        
    def complete_lesson_cycle(self, user_credentials):
        """Complete a full lesson cycle"""
        start_time = time.time()
        
        try:
            # Login
            self.login_user(**user_credentials)
            
            # Start lesson
            lesson_data = self.start_lesson()
            if not lesson_data:
                return {"error": "Failed to start lesson", "duration": time.time() - start_time}
            
            session_id = lesson_data["session_id"]
            questions_answered = 0
            
            # Answer questions until lesson complete
            while lesson_data.get("question") and questions_answered < 5:  # Limit for testing
                question = lesson_data["question"]
                result = self.submit_answer(session_id, question["id"])
                
                if not result:
                    break
                    
                questions_answered += 1
                lesson_data = result
                
                if result.get("session_complete"):
                    break
                    
            duration = time.time() - start_time
            return {
                "success": True,
                "questions_answered": questions_answered,
                "duration": duration
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "duration": time.time() - start_time
            }
            
    def run_concurrent_test(self, num_users=10, test_users=None):
        """Run concurrent load test"""
        if not test_users:
            test_users = [
                {"email": f"test{i}@example.com", "password": "testpass"}
                for i in range(num_users)
            ]
            
        print(f"Starting load test with {num_users} concurrent users...")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(self.complete_lesson_cycle, user)
                for user in test_users[:num_users]
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        if successful:
            avg_duration = sum(r["duration"] for r in successful) / len(successful)
            avg_questions = sum(r["questions_answered"] for r in successful) / len(successful)
        else:
            avg_duration = 0
            avg_questions = 0
            
        print(f"\nLoad Test Results:")
        print(f"Total time: {total_time:.2f}s")
        print(f"Successful sessions: {len(successful)}/{num_users}")
        print(f"Failed sessions: {len(failed)}")
        print(f"Average session duration: {avg_duration:.2f}s")
        print(f"Average questions per session: {avg_questions:.1f}")
        
        if failed:
            print(f"\nFailures:")
            for i, failure in enumerate(failed[:5]):  # Show first 5 failures
                print(f"  {i+1}. {failure.get('error', 'Unknown error')}")
                
        return {
            "total_time": total_time,
            "successful": len(successful),
            "failed": len(failed),
            "avg_duration": avg_duration,
            "avg_questions": avg_questions
        }

if __name__ == "__main__":
    tester = LoadTester()
    
    # Create test users first (you'll need to implement user creation)
    # Or use existing test users
    
    results = tester.run_concurrent_test(num_users=20)
    
    # Save results
    with open(f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(results, f, indent=2)
```

---

## 9. TROUBLESHOOTING GUIDE

### Common Issues and Solutions

#### FSRS Algorithm Issues

**Problem**: Cards not being scheduled correctly
```python
# Debug FSRS card state
def debug_fsrs_card(user_id, question_id):
    card = FSRSCard.get_by_user_and_question(user_id, question_id)
    if card:
        print(f"Card State: {card.state}")
        print(f"Due Date: {card.due_date}")
        print(f"Stability: {card.stability}")
        print(f"Difficulty: {card.difficulty}")
        print(f"Reps: {card.reps}")
        print(f"Lapses: {card.lapses}")
        
        # Check if card is actually due
        now = datetime.now(timezone.utc)
        is_due = card.due_date <= now
        print(f"Is Due: {is_due}")
        
        # Calculate retrievability
        fsrs = FSRS()
        retrievability = fsrs.get_retrievability(card.to_fsrs_card(), now)
        print(f"Retrievability: {retrievability}")
```

**Problem**: Performance-to-rating conversion not working properly
```python
# Test rating conversion with various scenarios
test_cases = [
    (True, 5, 1, 15),   # Quick easy question
    (True, 20, 3, 15),  # Slow hard question
    (False, 10, 2, 15), # Wrong answer
    (True, 15, 2, 15),  # Average performance
]

for is_correct, response_time, difficulty, avg_time in test_cases:
    rating = convert_performance_to_rating(is_correct, response_time, difficulty, avg_time)
    print(f"Correct: {is_correct}, Time: {response_time}s, Difficulty: {difficulty} → Rating: {rating}")
```

#### Database Performance Issues

**Problem**: Slow query performance
```javascript
// Add these indexes if queries are slow
db.fsrs_cards.createIndex({ "user_id": 1, "due_date": 1, "state": 1 })
db.questions.createIndex({ "skill_category": 1, "difficulty_level": 1, "tags": 1 })
db.lesson_reports.createIndex({ "user_id": 1, "timestamp": -1, "is_correct": 1 })

// Monitor slow queries
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().limit(5).sort({ ts: -1 }).pretty()
```

**Problem**: MongoDB connection issues
```python
# Connection retry logic
from pymongo.errors import ConnectionFailure
import time

def get_db_connection(retries=3, delay=1):
    for attempt in range(retries):
        try:
            client = MongoClient(MONGODB_URI)
            # Test connection
            client.admin.command('ping')
            return client
        except ConnectionFailure as e:
            if attempt == retries - 1:
                raise e
            print(f"Connection attempt {attempt + 1} failed, retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
```

#### Frontend Issues

**Problem**: API calls failing with CORS errors
```javascript
// Ensure proper CORS configuration in Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173', 'http://localhost:3000'])

# Or in production
CORS(app, origins=['https://yourdomain.com'])
```

**Problem**: State management issues in Pinia
```javascript
// Debug store state
import { useAuthStore } from '@/stores/auth'

export function debugStores() {
  const authStore = useAuthStore()
  
  console.log('Auth Store State:', {
    user: authStore.user,
    token: authStore.token,
    isAuthenticated: authStore.isAuthenticated
  })
  
  // Check localStorage
  console.log('LocalStorage token:', localStorage.getItem('token'))
}
```

### Error Monitoring and Logging

#### Backend Error Handling
```python
import logging
from functools import wraps
from flask import request, jsonify

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
    """Decorator to log errors in route handlers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function

# Usage
@lessons_bp.route('/start', methods=['POST'])
@jwt_required()
@log_errors
def start_lesson():
    # Route implementation
    pass
```

#### Frontend Error Handling
```javascript
// Global error handler for Vue
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err)
  console.error('Component info:', info)
  
  // Send to monitoring service
  if (import.meta.env.PROD) {
    // Send error to monitoring service like Sentry
    console.error('Production error:', { err, info })
  }
}

// API error interceptor
import axios from 'axios'

axios.interceptors.response.use(
  response => response,
  error => {
    const { response, request, message } = error
    
    if (response) {
      // Server responded with error status
      console.error('API Error Response:', {
        status: response.status,
        data: response.data,
        url: request.responseURL
      })
      
      // Handle specific error codes
      if (response.status === 401) {
        // Unauthorized - redirect to login
        const authStore = useAuthStore()
        authStore.logout()
      }
    } else if (request) {
      // Network error
      console.error('Network Error:', message)
    } else {
      console.error('Request Error:', message)
    }
    
    return Promise.reject(error)
  }
)
```

---

## 10. OPTIMIZATION RECOMMENDATIONS

### Backend Optimizations

#### Caching Strategy
```python
from functools import lru_cache
import redis
import json
import pickle

# Redis cache for frequently accessed data
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class CacheManager:
    @staticmethod
    def get_questions_cache_key(skill_ids, difficulty=None):
        key_parts = ['questions'] + sorted(skill_ids)
        if difficulty:
            key_parts.append(f'diff_{difficulty}')
        return ':'.join(key_parts)
    
    @staticmethod
    def cache_questions(skill_ids, questions, ttl=3600):
        """Cache questions for specific skills"""
        key = CacheManager.get_questions_cache_key(skill_ids)
        redis_client.setex(key, ttl, pickle.dumps(questions))
    
    @staticmethod
    def get_cached_questions(skill_ids):
        """Get cached questions"""
        key = CacheManager.get_questions_cache_key(skill_ids)
        cached = redis_client.get(key)
        return pickle.loads(cached) if cached else None

# Cache FSRS calculations
@lru_cache(maxsize=1000)
def calculate_retrievability(stability, difficulty, elapsed_days):
    """Cache expensive retrievability calculations"""
    # FSRS retrievability calculation
    return (1 + elapsed_days / (9 * stability)) ** -1

# Database query optimization
class OptimizedQuestionService:
    @staticmethod
    def get_questions_by_skills(skill_ids, limit=50):
        # Check cache first
        cached = CacheManager.get_cached_questions(skill_ids)
        if cached:
            return cached
        
        # Query database with optimized aggregation
        pipeline = [
            {'$match': {'skill_category': {'$in': skill_ids}}},
            {'$sample': {'size': limit}},
            {'$project': {
                'question_text': 1,
                'options': 1,
                'correct_answer': 1,
                'skill_category': 1,
                'difficulty_level': 1,
                'explanation': 1
            }}
        ]
        
        questions = list(db.questions.aggregate(pipeline))
        
        # Cache results
        CacheManager.cache_questions(skill_ids, questions)
        
        return questions
```

### FSRS Card Model (models/fsrs_card.py)
```python
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from utils.database import get_db
from fsrs import Card, State
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class FSRSCard:
    def __init__(self, user_id=None, question_id=None, due_date=None, stability=None,
                 difficulty=None, elapsed_days=None, scheduled_days=None, reps=None,
                 lapses=None, state=None, last_review=None, _id=None):
        self._id = _id
        self.user_id = user_id
        self.question_id = question_id
        self.due_date = due_date or datetime.now(timezone.utc)
        self.stability = stability or 0.0
        self.difficulty = difficulty or 0.0
        self.elapsed_days = elapsed_days or 0
        self.scheduled_days = scheduled_days or 0
        self.reps = reps or 0
        self.lapses = lapses or 0
        self.state = state or State.New.value  # 1 = New, 2 = Learning, 3 = Review, 4 = Relearning
        self.last_review = last_review
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    @property
    def id(self):
        return self._id
    
    def save(self):
        """Save or update the FSRS card in database"""
        db = get_db()
        self.updated_at = datetime.now(timezone.utc)
        
        card_data = {
            'user_id': ObjectId(self.user_id),
            'question_id': ObjectId(self.question_id),
            'due_date': self.due_date,
            'stability': self.stability,
            'difficulty': self.difficulty,
            'elapsed_days': self.elapsed_days,
            'scheduled_days': self.scheduled_days,
            'reps': self.reps,
            'lapses': self.lapses,
            'state': self.state,
            'last_review': self.last_review,
            'updated_at': self.updated_at
        }
        
        if self._id:
            # Update existing card
            db.fsrs_cards.update_one(
                {'_id': self._id},
                {'$set': card_data}
            )
        else:
            # Create new card
            card_data['created_at'] = self.created_at
            result = db.fsrs_cards.insert_one(card_data)
            self._id = result.inserted_id
        
        logger.debug(f"Saved FSRS card: {self._id}")
    
    def update_from_fsrs_card(self, fsrs_card: Card):
        """Update this object from an FSRS Card object"""
        self.due_date = fsrs_card.due
        self.stability = fsrs_card.stability
        self.difficulty = fsrs_card.difficulty
        self.elapsed_days = fsrs_card.elapsed_days
        self.scheduled_days = fsrs_card.scheduled_days
        self.reps = fsrs_card.reps
        self.lapses = fsrs_card.lapses
        self.state = fsrs_card.state.value
        self.last_review = fsrs_card.last_review
    
    def to_fsrs_card(self) -> Card:
        """Convert to FSRS Card object"""
        return Card(
            due=self.due_date,
            stability=self.stability,
            difficulty=self.difficulty,
            elapsed_days=self.elapsed_days,
            scheduled_days=self.scheduled_days,
            reps=self.reps,
            lapses=self.lapses,
            state=State(self.state),
            last_review=self.last_review
        )
    
    @classmethod
    def get_by_id(cls, card_id: str) -> Optional['FSRSCard']:
        """Get card by ID"""
        db = get_db()
        card_data = db.fsrs_cards.find_one({'_id': ObjectId(card_id)})
        
        if card_data:
            return cls._from_dict(card_data)
        return None
    
    @classmethod
    def get_by_user_and_question(cls, user_id: str, question_id: str) -> Optional['FSRSCard']:
        """Get card by user and question ID"""
        db = get_db()
        card_data = db.fsrs_cards.find_one({
            'user_id': ObjectId(user_id),
            'question_id': ObjectId(question_id)
        })
        
        if card_data:
            return cls._from_dict(card_data)
        return None
    
    @classmethod
    def get_due_cards(cls, user_id: str, limit: int = 20) -> List['FSRSCard']:
        """Get cards that are due for review"""
        db = get_db()
        now = datetime.now(timezone.utc)
        
        cursor = db.fsrs_cards.find({
            'user_id': ObjectId(user_id),
            'due_date': {'$lte': now}
        }).sort('due_date', 1).limit(limit)
        
        return [cls._from_dict(card_data) for card_data in cursor]
    
    @classmethod
    def get_new_cards(cls, user_id: str, limit: int = 10) -> List['FSRSCard']:
        """Get new cards (state = 1) for user"""
        db = get_db()
        
        cursor = db.fsrs_cards.find({
            'user_id': ObjectId(user_id),
            'state': State.New.value
        }).limit(limit)
        
        return [cls._from_dict(card_data) for card_data in cursor]
    
    @classmethod
    def get_cards_by_state(cls, user_id: str, state: int, limit: int = 50) -> List['FSRSCard']:
        """Get cards by specific state"""
        db = get_db()
        
        cursor = db.fsrs_cards.find({
            'user_id': ObjectId(user_id),
            'state': state
        }).limit(limit)
        
        return [cls._from_dict(card_data) for card_data in cursor]
    
    @classmethod
    def calculate_retention_rate(cls, user_id: str, days: int = 30) -> float:
        """Calculate user's retention rate over specified period"""
        db = get_db()
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all reviews in the period
        pipeline = [
            {
                '$match': {
                    'user_id': ObjectId(user_id),
                    'last_review': {'$gte': start_date},
                    'reps': {'$gt': 0}  # Only cards that have been reviewed
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_reviews': {'$sum': '$reps'},
                    'total_lapses': {'$sum': '$lapses'}
                }
            }
        ]
        
        result = list(db.fsrs_cards.aggregate(pipeline))
        
        if result and result[0]['total_reviews'] > 0:
            total_reviews = result[0]['total_reviews']
            total_lapses = result[0]['total_lapses']
            retention_rate = (total_reviews - total_lapses) / total_reviews
            return max(0.0, min(1.0, retention_rate))  # Clamp between 0 and 1
        
        return 0.0
    
    @classmethod
    def get_user_stats(cls, user_id: str) -> dict:
        """Get comprehensive user statistics"""
        db = get_db()
        
        pipeline = [
            {'$match': {'user_id': ObjectId(user_id)}},
            {
                '$group': {
                    '_id': None,
                    'total_cards': {'$sum': 1},
                    'new_cards': {
                        '$sum': {'$cond': [{'$eq': ['$state', State.New.value]}, 1, 0]}
                    },
                    'learning_cards': {
                        '$sum': {'$cond': [{'$eq': ['$state', State.Learning.value]}, 1, 0]}
                    },
                    'review_cards': {
                        '$sum': {'$cond': [{'$eq': ['$state', State.Review.value]}, 1, 0]}
                    },
                    'relearning_cards': {
                        '$sum': {'$cond': [{'$eq': ['$state', State.Relearning.value]}, 1, 0]}
                    },
                    'total_reps': {'$sum': '$reps'},
                    'total_lapses': {'$sum': '$lapses'},
                    'avg_stability': {'$avg': '$stability'},
                    'avg_difficulty': {'$avg': '$difficulty'}
                }
            }
        ]
        
        result = list(db.fsrs_cards.aggregate(pipeline))
        
        if result:
            stats = result[0]
            # Calculate retention rate
            if stats['total_reps'] > 0:
                retention_rate = (stats['total_reps'] - stats['total_lapses']) / stats['total_reps']
            else:
                retention_rate = 0.0
            
            stats['retention_rate'] = round(retention_rate, 3)
            stats['avg_stability'] = round(stats.get('avg_stability', 0.0), 2)
            stats['avg_difficulty'] = round(stats.get('avg_difficulty', 0.0), 2)
            
            return stats
        
        return {
            'total_cards': 0,
            'new_cards': 0,
            'learning_cards': 0,
            'review_cards': 0,
            'relearning_cards': 0,
            'total_reps': 0,
            'total_lapses': 0,
            'retention_rate': 0.0,
            'avg_stability': 0.0,
            'avg_difficulty': 0.0
        }
    
    @classmethod
    def _from_dict(cls, card_data: dict) -> 'FSRSCard':
        """Create FSRSCard from database document"""
        return cls(
            _id=card_data['_id'],
            user_id=str(card_data['user_id']),
            question_id=str(card_data['question_id']),
            due_date=card_data['due_date'],
            stability=card_data['stability'],
            difficulty=card_data['difficulty'],
            elapsed_days=card_data['elapsed_days'],
            scheduled_days=card_data['scheduled_days'],
            reps=card_data['reps'],
            lapses=card_data['lapses'],
            state=card_data['state'],
            last_review=card_data.get('last_review')
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self._id) if self._id else None,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'stability': self.stability,
            'difficulty': self.difficulty,
            'elapsed_days': self.elapsed_days,
            'scheduled_days': self.scheduled_days,
            'reps': self.reps,
            'lapses': self.lapses,
            'state': self.state,
            'last_review': self.last_review.isoformat() if self.last_review else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def delete_test_data(cls):
        """Delete test data - only use in testing"""
        db = get_db()
        db.fsrs_cards.delete_many({'user_id': {'$regex': 'test_'}})
```

### Frontend Optimizations

#### Component Lazy Loading
```javascript
// router/index.js - Lazy load route components
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/lesson',
    name: 'Lesson',
    component: () => import('@/views/LessonView.vue'),
    meta: { requiresAuth: true }
  }
]

// Preload critical routes
router.beforeEach((to, from, next) => {
  // Preload dashboard when user logs in
  if (to.name === 'Login') {
    import('@/views/DashboardView.vue')
  }
  next()
})
```

#### API Response Optimization
```javascript
// services/lesson.service.js - Request optimization
class LessonService {
  constructor() {
    this.cache = new Map()
    this.abortController = null
  }
  
  async startLesson(data) {
    // Cancel previous request if still pending
    if (this.abortController) {
      this.abortController.abort()
    }
    
    this.abortController = new AbortController()
    
    try {
      const response = await api.post('/lessons/start', data, {
        signal: this.abortController.signal
      })
      
      return response.data
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request cancelled')
        return null
      }
      throw error
    } finally {
      this.abortController = null
    }
  }
  
  // Cache lesson progress
  async getProgressSummary(useCache = true) {
    const cacheKey = 'progress_summary'
    
    if (useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)
      if (Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 minutes
        return cached.data
      }
    }
    
    const response = await api.get('/lessons/progress-summary')
    
    // Cache the response
    this.cache.set(cacheKey, {
      data: response.data,
      timestamp: Date.now()
    })
    
    return response.data
  }
}
```

#### Performance Monitoring
```javascript
// utils/performance.js
class PerformanceMonitor {
  static measureRender(componentName, fn) {
    const start = performance.now()
    const result = fn()
    const end = performance.now()
    
    if (end - start > 16) { // Longer than one frame at 60fps
      console.warn(`Slow render in ${componentName}: ${(end - start).toFixed(2)}ms`)
    }
    
    return result
  }
  
  static measureAsync(name, promise) {
    const start = performance.now()
    
    return promise.finally(() => {
      const duration = performance.now() - start
      console.log(`${name} took ${duration.toFixed(2)}ms`)
      
      // Send to analytics in production
      if (import.meta.env.PROD && duration > 1000) {
        // Send slow operation data to monitoring service
        console.warn(`Slow operation: ${name} - ${duration}ms`)
      }
    })
  }
}

// Usage in components
export default {
  async mounted() {
    await PerformanceMonitor.measureAsync(
      'Dashboard data loading',
      this.loadDashboardData()
    )
  },
  
  methods: {
    updateProgress() {
      PerformanceMonitor.measureRender('Progress update', () => {
        // Update logic here
        this.progressData = this.calculateProgress()
      })
    }
  }
}
```

---

## 11. SECURITY CONSIDERATIONS

### Authentication & Authorization
```python
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
import bcrypt

# Secure password hashing
class PasswordManager:
    @staticmethod
    def hash_password(password):
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Role-based access control
def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            user = User.get_by_id(user_id)
            if not user or user.role != required_role:
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Input validation
from marshmallow import Schema, fields, validate, ValidationError

class LessonStartSchema(Schema):
    skill_ids = fields.List(fields.String(), required=True, 
                           validate=validate.Length(min=1, max=10))
    type = fields.String(required=True, 
                        validate=validate.OneOf(['initial', 'review', 'practice']))

def validate_input(schema_class):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            try:
                data = schema.load(request.get_json())
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({'error': 'Validation failed', 'details': err.messages}), 400
        return decorated_function
    return decorator

# Usage
@lessons_bp.route('/start', methods=['POST'])
@jwt_required()
@validate_input(LessonStartSchema)
def start_lesson():
    data = request.validated_data
    # Use validated data
```

### Data Protection
```python
# Encrypt sensitive data at rest
from cryptography.fernet import Fernet
import os

class DataEncryption:
    def __init__(self):
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated encryption key: {key.decode()}")
        else:
            key = key.encode()
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypt string data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt string data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

# Apply rate limiting to sensitive endpoints
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login implementation
    pass

@lessons_bp.route('/start', methods=['POST'])
@limiter.limit("10 per minute")
@jwt_required()
def start_lesson():
    # Lesson start implementation
    pass
```

---

## 12. FINAL CHECKLIST FOR IMPLEMENTATION

### Pre-Development Setup
- [ ] Create virtual environment and install Python dependencies
- [ ] Set up Node.js environment and install frontend dependencies
- [ ] Configure MongoDB database with proper indexes
- [ ] Set up environment variables and configuration files
- [ ] Create initial database collections and sample data

### Backend Implementation
- [ ] Implement Flask application structure with blueprints
- [ ] Set up FSRS integration with proper card management
- [ ] Create user authentication system with JWT
- [ ] Implement lesson management endpoints
- [ ] Add progress tracking and reporting features
- [ ] Set up proper error handling and logging
- [ ] Implement caching for performance optimization

### Frontend Implementation
- [ ] Create Vue.js application with proper routing
- [ ] Set up Pinia stores for state management
- [ ] Implement authentication flow with token management
- [ ] Create lesson interface components
- [ ] Add progress tracking dashboard
- [ ] Implement responsive design with Tailwind CSS
- [ ] Add proper error handling and loading states

### Testing & Quality Assurance
- [ ] Write unit tests for FSRS integration
- [ ] Create API endpoint tests
- [ ] Add frontend component tests
- [ ] Perform load testing with concurrent users
- [ ] Test error scenarios and edge cases
- [ ] Verify responsive design across devices

### Security & Performance
- [ ] Implement proper authentication and authorization
- [ ] Add input validation and sanitization
- [ ] Set up rate limiting for API endpoints
- [ ] Optimize database queries with indexes
- [ ] Add caching for frequently accessed data
- [ ] Configure CORS properly for production

### Deployment Preparation
- [ ] Create Docker containers for all services
- [ ] Set up production environment variables
- [ ] Configure reverse proxy and SSL certificates
- [ ] Set up database backups and monitoring
- [ ] Create deployment scripts and documentation
- [ ] Test production deployment in staging environment

This comprehensive implementation guide provides all the necessary details for another LLM to successfully build the Math Learning System with spaced repetition. Each section includes specific code examples, configuration details, and step-by-step instructions to ensure successful implementation.

---

## 13. ADDITIONAL RESOURCES & REFERENCES

### FSRS Algorithm Resources
- **Official Repository**: https://github.com/open-spaced-repetition/py-fsrs
- **FSRS Documentation**: https://docs.fsrs.rs/
- **Research Paper**: "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling"
- **Parameter Optimization**: Use FSRS Optimizer for custom parameters based on user data

### Vue.js & Frontend Resources
- **Vue.js Documentation**: https://vuejs.org/guide/
- **Pinia Documentation**: https://pinia.vuejs.org/
- **Tailwind CSS Documentation**: https://tailwindcss.com/docs
- **Vite Configuration**: https://vitejs.dev/config/

### Flask & Backend Resources
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Flask-JWT-Extended**: https://flask-jwt-extended.readthedocs.io/
- **PyMongo Documentation**: https://pymongo.readthedocs.io/
- **MongoDB Best Practices**: https://docs.mongodb.com/manual/administration/production-notes/

### Development Tools
- **VS Code Extensions**: Vue Language Features (Volar), Python, MongoDB for VS Code
- **Testing Tools**: Vitest for frontend, pytest for backend
- **API Testing**: Postman or Insomnia for API endpoint testing
- **Database Tools**: MongoDB Compass for database management

---

## 14. SAMPLE IMPLEMENTATION TIMELINE

### Week 1-2: Foundation Setup
**Days 1-3: Environment Setup**
- Set up development environment (Python virtual env, Node.js)
- Install and configure MongoDB
- Create project structure for both frontend and backend
- Set up version control (Git)

**Days 4-7: Basic Backend Structure**
- Implement Flask application with blueprints
- Set up MongoDB connection and basic models
- Create user authentication endpoints (register/login)
- Basic JWT token handling

**Days 8-14: FSRS Integration**
- Install and configure py-FSRS
- Create FSRS card models and database operations
- Implement basic card creation and review logic
- Write unit tests for FSRS integration

### Week 3-4: Core Features
**Days 15-21: Lesson Management**
- Implement lesson start/submit endpoints
- Create question selection algorithms
- Add performance tracking and reporting
- Integrate FSRS with lesson flow

**Days 22-28: Frontend Foundation**
- Set up Vue.js application with routing
- Create authentication components and flow
- Implement Pinia stores for state management
- Basic UI components with Tailwind CSS

### Week 5-6: User Interface
**Days 29-35: Lesson Interface**
- Create question display components
- Implement answer submission flow
- Add progress tracking UI
- Create lesson completion summary

**Days 36-42: Dashboard & Progress**
- Build user dashboard with statistics
- Implement skill selection interface
- Add progress visualization components
- Create responsive design for mobile devices

### Week 7-8: Polish & Testing
**Days 43-49: Testing & Bug Fixes**
- Write comprehensive test suites
- Perform load testing
- Fix bugs and optimize performance
- Add error handling and edge cases

**Days 50-56: Deployment Preparation**
- Create Docker containers
- Set up production configuration
- Prepare deployment scripts
- Document API endpoints and usage

---

## 15. TROUBLESHOOTING DECISION TREE

### When FSRS Cards Are Not Working Correctly

**Is the card being created properly?**
```
YES → Check due date calculation
NO  → Debug card initialization process
```

**Are due dates being calculated correctly?**
```
YES → Check card state transitions
NO  → Debug FSRS parameters and review logic
```

**Are performance ratings being converted properly?**
```
YES → Check FSRS algorithm parameters
NO  → Debug performance-to-rating conversion function
```

### When API Calls Are Failing

**Is the error a 401 Unauthorized?**
```
YES → Check JWT token validity and refresh logic
NO  → Continue to next check
```

**Is the error a 404 Not Found?**
```
YES → Verify API endpoint URLs and routing
NO  → Continue to next check
```

**Is the error a 500 Internal Server Error?**
```
YES → Check server logs for detailed error information
NO  → Check network connectivity and CORS settings
```

### When Database Queries Are Slow

**Are proper indexes created?**
```
NO  → Create indexes on frequently queried fields
YES → Continue to next check
```

**Are queries using indexes effectively?**
```
NO  → Optimize query structure and use explain()
YES → Check if data volume requires pagination
```

**Is connection pooling configured properly?**
```
NO  → Configure MongoDB connection pooling
YES → Consider implementing caching layer
```

---

## 16. ADVANCED FEATURES TO IMPLEMENT LATER

### Phase 2 Enhancements
1. **Advanced Analytics Dashboard**
   - Learning curve visualization
   - Retention rate analysis
   - Performance comparison with other users
   - Skill mastery progression charts

2. **Adaptive Difficulty System**
   - Dynamic difficulty adjustment based on performance
   - Personalized question generation
   - Custom learning paths per user

3. **Social Features**
   - Study groups and collaborative learning
   - Leaderboards and achievements
   - Peer comparison and motivation

4. **Content Management System**
   - Admin interface for managing questions
   - Bulk question import/export
   - Question quality metrics and feedback

### Phase 3 Advanced Features
1. **AI-Powered Insights**
   - Learning style detection
   - Personalized study recommendations
   - Predictive analytics for learning outcomes

2. **Mobile Application**
   - Native iOS/Android apps
   - Offline study capabilities
   - Push notifications for study reminders

3. **Integration Features**
   - LTI integration for educational platforms
   - API for third-party applications
   - Export data to other learning systems

---

## 17. MAINTENANCE AND MONITORING

### Regular Maintenance Tasks

**Daily:**
- Monitor application logs for errors
- Check database performance metrics
- Verify backup completion
- Monitor user activity and system performance

**Weekly:**
- Review and update FSRS parameters based on user data
- Analyze user feedback and feature requests
- Update question database with new content
- Performance optimization based on usage patterns

**Monthly:**
- Security updates and dependency upgrades
- Database optimization and cleanup
- User retention and engagement analysis
- System capacity planning and scaling decisions

### Key Metrics to Monitor

**Technical Metrics:**
- Response time for API endpoints
- Database query performance
- Error rates and types
- Server resource utilization

**User Metrics:**
- Daily/monthly active users
- Session duration and frequency
- Question completion rates
- User retention rates

**Learning Metrics:**
- Average accuracy rates by skill
- Time to mastery per topic
- Retention rates after different intervals
- FSRS algorithm effectiveness

---

## CONCLUSION

This implementation guide provides a complete roadmap for building a sophisticated math learning system with spaced repetition. The combination of Flask backend with FSRS algorithm integration, Vue.js frontend with modern UI components, and MongoDB for flexible data storage creates a robust platform for personalized learning.

The guide includes everything needed for successful implementation:

- **Complete technical specifications** with exact code examples
- **Database schemas** with sample data and indexing strategies
- **Frontend components** with responsive design and state management
- **Testing frameworks** for both backend and frontend validation
- **Security implementations** following best practices
- **Performance optimizations** for scalability
- **Deployment configurations** for production environments

By following this guide systematically, any LLM or development team can create a production-ready math learning platform that leverages the power of spaced repetition for optimal learning outcomes. The modular architecture allows for easy extension and customization based on specific requirements or educational goals.

Remember to adapt the implementations based on your specific use case, scale requirements, and user needs. The foundation provided here is robust enough to support significant user bases while remaining flexible for future enhancements and feature additions.