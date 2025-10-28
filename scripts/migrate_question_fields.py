from pymongo import MongoClient
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mongodb_uri():
    # You may need to adjust this based on your configuration
    return "mongodb://localhost:27017/innoserve"

def migrate_question_fields():
    try:
        # Connect to MongoDB
        client = MongoClient(get_mongodb_uri())
        db = client.get_default_database()
        
        # Find all questions that have correct_answer but not correct_indices
        questions_to_update = db.questions.find({
            'correct_answer': {'$exists': True},
            'correct_indices': {'$exists': False}
        })
        
        update_count = 0
        for question in questions_to_update:
            # Update the document to use correct_indices
            result = db.questions.update_one(
                {'_id': question['_id']},
                {
                    '$set': {
                        'correct_indices': question['correct_answer'],
                        'updated_at': datetime.utcnow()
                    },
                    '$unset': {'correct_answer': ""}
                }
            )
            if result.modified_count > 0:
                update_count += 1
                
        logger.info(f"Migration completed. Updated {update_count} questions.")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        raise
    finally:
        client.close()

if __name__ == "__main__":
    migrate_question_fields()
