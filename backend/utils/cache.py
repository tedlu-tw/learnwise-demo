# Redis cache manager stub for questions (backend/utils/cache.py)
# For future implementation
import redis
import pickle

class CacheManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db)

    def cache_questions(self, skill_ids, questions, ttl=3600):
        key = self._get_questions_key(skill_ids)
        self.client.setex(key, ttl, pickle.dumps(questions))

    def get_cached_questions(self, skill_ids):
        key = self._get_questions_key(skill_ids)
        cached = self.client.get(key)
        return pickle.loads(cached) if cached else None

    def _get_questions_key(self, skill_ids):
        return 'questions:' + ':'.join(sorted(skill_ids))

# Usage (future):
# cache = CacheManager()
# cache.cache_questions(['Algebra'], questions)
# questions = cache.get_cached_questions(['Algebra'])
