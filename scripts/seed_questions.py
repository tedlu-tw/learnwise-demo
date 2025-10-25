from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/math_learning')
client = MongoClient(MONGODB_URI)
db = client['math_learning']

sample_questions = [
    {
        'text': 'What is 2 + 2?',
        'options': ['3', '4', '5', '6'],
        'correct_answer': 1,
        'explanation': 'Basic addition: 2 + 2 = 4',
        'skill_category': 'arithmetic',
        'difficulty': 1,
        'tags': ['addition'],
        'sub_topic': 'basic'
    },
    {
        'text': 'Solve for x: 2x = 10',
        'options': ['2', '5', '10', '8'],
        'correct_answer': 1,
        'explanation': '2x=10 => x=5',
        'skill_category': 'algebra',
        'difficulty': 2,
        'tags': ['equation'],
        'sub_topic': 'linear'
    },
    {
        'text': 'What is the value of $\\sqrt{16}$?',
        'options': ['$2$', '$4$', '$8$', '$16$'],
        'correct_answer': 1,
        'explanation': 'The square root of 16 is 4, since $4^2 = 16$',
        'skill_category': 'algebra',
        'difficulty': 2,
        'tags': ['square_root'],
        'sub_topic': 'radicals'
    },
    {
        'text': 'Solve the quadratic equation: $x^2 - 5x + 6 = 0$',
        'options': ['$x = 1, 6$', '$x = 2, 3$', '$x = -2, -3$', '$x = 0, 5$'],
        'correct_answer': 1,
        'explanation': 'Factoring: $(x-2)(x-3) = 0$, so $x = 2$ or $x = 3$',
        'skill_category': 'algebra',
        'difficulty': 3,
        'tags': ['quadratic'],
        'sub_topic': 'quadratic_equations'
    },
    {
        'text': 'What is the derivative of $f(x) = x^3 + 2x^2 - 5x + 1$?',
        'options': ['$3x^2 + 4x - 5$', '$x^4 + 2x^3 - 5x^2 + x$', '$3x^2 + 2x - 5$', '$x^2 + 4x - 5$'],
        'correct_answer': 0,
        'explanation': 'Using the power rule: $f\'(x) = 3x^2 + 4x - 5$',
        'skill_category': 'calculus',
        'difficulty': 4,
        'tags': ['derivative', 'power_rule'],
        'sub_topic': 'differentiation'
    },
    {
        'text': 'Evaluate the integral: $\\int (2x + 3) dx$',
        'options': ['$x^2 + 3x + C$', '$2x^2 + 3x + C$', '$x^2 + 3x^2 + C$', '$2x + 3x + C$'],
        'correct_answer': 0,
        'explanation': 'Using the power rule for integration: $\\int (2x + 3) dx = x^2 + 3x + C$',
        'skill_category': 'calculus',
        'difficulty': 4,
        'tags': ['integration', 'antiderivative'],
        'sub_topic': 'integration'
    },
    {
        'text': 'What is the area of a circle with radius $r = 5$?',
        'options': ['$10\\pi$', '$25\\pi$', '$5\\pi$', '$100\\pi$'],
        'correct_answer': 1,
        'explanation': 'The area of a circle is $A = \\pi r^2 = \\pi \\cdot 5^2 = 25\\pi$',
        'skill_category': 'geometry',
        'difficulty': 2,
        'tags': ['circle', 'area'],
        'sub_topic': 'circles'
    },
    {
        'text': 'In a right triangle, if one angle is $30°$ and the hypotenuse is $10$, what is the length of the side opposite to the $30°$ angle?',
        'options': ['$5$', '$5\\sqrt{3}$', '$10\\sqrt{3}$', '$\\frac{10}{\\sqrt{3}}$'],
        'correct_answer': 0,
        'explanation': 'In a 30-60-90 triangle, the side opposite to 30° is half the hypotenuse: $\\frac{10}{2} = 5$',
        'skill_category': 'geometry',
        'difficulty': 3,
        'tags': ['trigonometry', 'special_triangles'],
        'sub_topic': 'trigonometry'
    }
]

def seed():
    db.questions.insert_many(sample_questions)
    print("Sample questions seeded.")

if __name__ == "__main__":
    seed()
