# Math Learning System - Spaced Repetition Workflow

## System Overview
A math learning platform that uses spaced repetition algorithms to optimize learning retention through adaptive questioning and personalized lesson scheduling.

## Technology Stack

### Core Algorithm
- **FSRS (Free Spaced Repetition Scheduler)**: Python implementation using `open-spaced-repetition/Py-FSRS` module
- Advanced spaced repetition algorithm that adapts to individual learning patterns

### Backend
- **Flask (Python)**: Lightweight web framework for API development
- RESTful API endpoints for lesson management and user interactions
- Integration with FSRS algorithm for intelligent question scheduling

### Frontend
- **Vue.js**: Progressive JavaScript framework for reactive user interfaces
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- Responsive design for optimal learning experience across devices

### Database
- **MongoDB**: NoSQL document database for flexible data storage
- Collections for users, questions, lesson reports, and algorithm state
- Scalable architecture for handling large question databases

## Main Workflow Components

### 1. User Entry & Setup
```
User Login/Registration
    ↓
Select Skill Sets to Learn
    ↓
Initial Assessment (First Lesson)
```

### 2. Core Learning Loop
```
Algorithm Generation/Enhancement
    ↓
Lesson Delivery
    ↓  
Lesson Report Generation
    ↓
Interactive Results Presentation
    ↓
Algorithm Update (feeds back to top)
```

## Detailed Process Flow

### Phase 1: Initialization
1. **User Entry**: User accesses the system
2. **Skill Selection**: User chooses specific math skill sets to focus on
3. **First Lesson**: Initial assessment to establish baseline knowledge
4. **Initial Report**: Performance data collected from first lesson
5. **Algorithm Initialization**: Spaced repetition algorithm configured based on initial performance

### Phase 2: Adaptive Learning Cycle
1. **Algorithm Processing**: 
   - Analyzes previous lesson reports
   - Determines optimal question difficulty and timing
   - Selects questions from database based on spaced repetition principles

2. **Lesson Delivery**:
   - Multiple choice questions presented to user
   - Questions sourced from comprehensive questions database
   - Difficulty and topic adapted to user's current proficiency

3. **Lesson Report Generation**:
   - Captures user responses and performance metrics
   - Records time spent, accuracy, and difficulty level
   - Analyzes learning progress and retention patterns

4. **Interactive Results**:
   - User receives immediate feedback
   - Progress visualization and performance insights
   - Recommendations for next learning session

5. **Algorithm Enhancement**:
   - Machine learning component updates based on new data
   - Refines spacing intervals and question selection
   - Improves personalization for future lessons

## Technical Architecture

### Backend Architecture (Flask)
```
Flask Application
├── API Routes
│   ├── /api/auth (user authentication)
│   ├── /api/skills (skill set management)
│   ├── /api/lessons (lesson delivery and completion)
│   ├── /api/reports (performance data)
│   └── /api/questions (question database access)
├── FSRS Integration
│   ├── Algorithm initialization
│   ├── Card scheduling logic
│   └── Performance tracking
├── MongoDB Integration
│   ├── User data management
│   ├── Question database queries
│   └── Lesson report storage
└── Business Logic
    ├── User progress calculation
    ├── Question selection
    └── Report generation
```

### Frontend Architecture (Vue.js + Tailwind)
```
Vue.js Application
├── Components
│   ├── SkillSelector.vue
│   ├── LessonInterface.vue
│   ├── QuestionCard.vue
│   ├── ProgressDashboard.vue
│   └── ResultsDisplay.vue
├── Views
│   ├── Login.vue
│   ├── SkillSelection.vue
│   ├── LearningSession.vue
│   └── Dashboard.vue
├── State Management (Vuex/Pinia)
│   ├── User state
│   ├── Lesson state
│   └── Progress state
└── API Services
    ├── Authentication service
    ├── Lesson service
    └── Progress service
```

### Database Schema (MongoDB)
```
Collections:
├── users
│   ├── _id, username, email
│   ├── selected_skills[]
│   ├── fsrs_parameters
│   └── created_at, updated_at
├── questions
│   ├── _id, question_text
│   ├── options[], correct_answer
│   ├── skill_category, difficulty_level
│   └── metadata{tags, topic}
├── lesson_reports
│   ├── _id, user_id, question_id
│   ├── response, is_correct, response_time
│   ├── lesson_session_id
│   └── timestamp
├── fsrs_cards
│   ├── _id, user_id, question_id
│   ├── due_date, stability, difficulty
│   ├── elapsed_days, scheduled_days
│   └── reps, lapses, state
└── user_progress
    ├── _id, user_id, skill_id
    ├── mastery_level, total_questions
    ├── correct_answers, average_time
    └── last_session_date
```

## Implementation Details

### FSRS Algorithm Integration
```python
# Example Flask endpoint using Py-FSRS
from fsrs import FSRS, Card, Rating, ReviewLog

@app.route('/api/lesson/next-question', methods=['GET'])
def get_next_question():
    f = FSRS()
    # Get due cards for user
    due_cards = get_user_due_cards(user_id)
    
    # Select card based on FSRS scheduling
    next_card = f.next_card(due_cards)
    question = get_question_by_id(next_card.question_id)
    
    return jsonify({
        'question': question,
        'card_id': next_card.id
    })

@app.route('/api/lesson/submit-answer', methods=['POST'])
def submit_answer():
    f = FSRS()
    card = get_card_by_id(request.json['card_id'])
    rating = Rating(request.json['rating'])  # Good, Again, Hard, Easy
    
    # Update card using FSRS
    new_card, review_log = f.review(card, rating)
    save_card_and_log(new_card, review_log)
    
    return jsonify({'success': True})
```

### Vue.js Component Example
```javascript
// LessonInterface.vue
<template>
  <div class="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800">{{ question.text }}</h2>
    </div>
    
    <div class="space-y-3">
      <button
        v-for="(option, index) in question.options"
        :key="index"
        @click="selectAnswer(index)"
        class="w-full p-4 text-left bg-gray-50 hover:bg-blue-50 
               rounded-md transition-colors duration-200"
      >
        {{ option }}
      </button>
    </div>
    
    <div class="mt-6 flex justify-between">
      <span class="text-sm text-gray-500">
        Progress: {{ currentQuestion }}/{{ totalQuestions }}
      </span>
      <button
        @click="submitAnswer"
        :disabled="!selectedAnswer"
        class="px-6 py-2 bg-blue-600 text-white rounded-md 
               hover:bg-blue-700 disabled:opacity-50"
      >
        Submit
      </button>
    </div>
  </div>
</template>
```
- Repository of multiple choice math questions
- Categorized by skill set and difficulty level
- Tagged with metadata for algorithm selection

### FSRS Algorithm Implementation
- **Initial State**: FSRS parameters initialized based on first lesson performance
- **Learning State**: Continuously evolving using FSRS learning algorithms
- **Core Functions**:
  - Calculates optimal review intervals using FSRS scheduling
  - Adapts to individual memory patterns and retention rates
  - Prioritizes cards/questions based on forgetting curves
- **Python Integration**: `open-spaced-repetition/Py-FSRS` module handles all scheduling logic

### Lesson Report System
- **Data Collection**: Response accuracy, timing, user behavior
- **Analysis**: Performance trends and learning patterns
- **Feedback Loop**: Feeds data back to algorithm for optimization

### Interactive Results Interface
- Real-time performance feedback
- Progress tracking and visualization
- Personalized learning recommendations

## Data Flow with Technology Stack

### Complete System Flow
```
Vue.js Frontend
    ↓ (HTTP Requests)
Flask API Server
    ↓ (FSRS Algorithm Calls)
Py-FSRS Module
    ↓ (Data Persistence)
MongoDB Database
    ↓ (Query Results)
Flask API Server
    ↓ (JSON Response)
Vue.js Frontend
```

### Detailed Technical Flow

1. **User Authentication**: Vue.js → Flask /api/auth → MongoDB users collection
2. **Skill Selection**: Vue.js → Flask /api/skills → MongoDB questions collection (filtered by skills)
3. **First Lesson**: Vue.js → Flask /api/lessons → FSRS initialization → MongoDB fsrs_cards creation
4. **Algorithm Processing**: 
   - Flask calls Py-FSRS module
   - FSRS queries MongoDB fsrs_cards collection
   - Calculates due cards and optimal scheduling
5. **Lesson Delivery**: Flask /api/lessons → MongoDB questions collection → Vue.js rendering
6. **Answer Submission**: Vue.js → Flask /api/lessons/submit → FSRS card update → MongoDB persistence
7. **Report Generation**: Flask aggregates data from lesson_reports → MongoDB queries → Vue.js dashboard
8. **Interactive Results**: Vue.js components display progress using Tailwind styling

## Deployment Considerations

### Backend (Flask + FSRS)
- Python virtual environment with required dependencies
- Flask application server (Gunicorn for production)
- FSRS module installation: `pip install open-spaced-repetition`
- MongoDB connection and indexing optimization
- API rate limiting and authentication middleware

### Frontend (Vue.js + Tailwind)
- Node.js environment for development
- Vue CLI or Vite build system
- Tailwind CSS configuration and optimization
- Production build with asset optimization
- CDN deployment for static assets

### Database (MongoDB)
- Proper indexing on user_id, due_date, and question categories
- Data backup and recovery procedures
- Scalability planning for large question datasets
- Performance monitoring and optimization