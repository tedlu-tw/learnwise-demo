// Sample data seed script for MongoDB (run with mongosh)
db = db.getSiblingDB('learnwise-demo')

// // Sample users
// db.users.insertMany([
//   {
//     username: "demo",
//     email: "demo@example.com",
//     password_hash: "$2b$12$B.j6OjpS6Hwi3BrGG8e5oeNqdWLYBHv31IbEIU2uvKichlJAs0OE6", // Replace with real bcrypt hash
//     selected_skills: ["Algebra", "Geometry"],
//     created_at: new Date(),
//     updated_at: new Date(),
//     role: "user",
//     total_questions_answered: 0
//   }
// ])

// Sample questions
db.questions.insertMany([
  {
    question_text: "What is 2 + 2?",
    options: ["3", "4", "5", "6"],
    correct_answer: 1,
    skill_category: "Algebra",
    difficulty_level: 1,
    metadata: { tags: ["addition"], topic: "arithmetic" }
  },
  {
    question_text: "What is the area of a circle with radius 1?",
    options: ["π", "2π", "π^2", "1"],
    correct_answer: 0,
    skill_category: "Geometry",
    difficulty_level: 2,
    metadata: { tags: ["area"], topic: "geometry" }
  },
  {
    question_text: "What is the value of x in the equation 2x + 3 = 7?",
    options: ["1", "2", "3", "4"],
    correct_answer: 1,
    skill_category: "Algebra",
    difficulty_level: 1,
    metadata: { tags: ["linear equations"], topic: "algebra" }
  },
  {
    question_text: "What is the perimeter of a rectangle with length 5 and width 3?",
    options: ["8", "15", "16", "10"],
    correct_answer: 2,
    skill_category: "Geometry",
    difficulty_level: 1,
    metadata: { tags: ["perimeter"], topic: "geometry" }
  },
  {
    question_text: "What is 15 × 3?",
    options: ["45", "18", "12", "35"],
    correct_answer: 0,
    skill_category: "Arithmetic",
    difficulty_level: 1,
    metadata: { tags: ["multiplication"], topic: "arithmetic" }
  },
  {
    question_text: "If the radius of a circle is 4, what is its area?",
    options: ["8π", "16π", "4π", "12π"],
    correct_answer: 1,
    skill_category: "Geometry",
    difficulty_level: 2,
    metadata: { tags: ["area"], topic: "geometry" }
  },
  {
    question_text: "What is the solution to the equation x^2 = 9?",
    options: ["1", "3", "-3 and 3", "9"],
    correct_answer: 2,
    skill_category: "Algebra",
    difficulty_level: 2,
    metadata: { tags: ["quadratic equations"], topic: "algebra" }
  },
  {
    question_text: "What is 100 divided by 4?",
    options: ["20", "25", "40", "50"],
    correct_answer: 1,
    skill_category: "Arithmetic",
    difficulty_level: 1,
    metadata: { tags: ["division"], topic: "arithmetic" }
  }
])

print('Sample users and questions inserted.')
