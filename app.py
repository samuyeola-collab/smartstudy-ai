import os

from flask import Flask, render_template, request, redirect, session

from flask_session import Session

import firebase_admin
from firebase_admin import credentials, db
from flask import send_file
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Session Configuration
app.config['SECRET_KEY'] = 'smartstudysecret'

app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

# Firebase Setup
#cred = credentials.Certificate(
 #   "smartstudyai-50437-firebase-adminsdk-fbsvc-c92cef1af6.json"
#)

#firebase_admin.initialize_app(cred, {
 #   'databaseURL': 'https://smartstudyai-50437-default-rtdb.firebaseio.com/'
#})

# Store Quiz History
quiz_history = []

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    message = ""

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        ref = db.reference('users')

        ref.push({
            'username': username,
            'email': email,
            'password': password
        })

        message = "Registration Successful ✅"

    return render_template(
        'register.html',
        message=message
    )

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    message = ""

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        ref = db.reference('users')

        users = ref.get()

        if users:

            for key, user in users.items():

                if user['email'] == email and user['password'] == password:

                    session['user'] = user['username']
                    session['email'] = user['email']

                    return redirect('/dashboard')

        message = "Invalid Email or Password ❌"

    return render_template(
        'login.html',
        message=message
    )

# Logout
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

# Dashboard Page
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    return render_template(
        'dashboard.html',
        username=session['user']
    )

# Chatbot Page
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():

    user_message = ""
    bot_response = ""

    if request.method == 'POST':

        user_message = request.form['message']

        message = user_message.lower()

        if "python" in message:

            bot_response = """
Python is a powerful programming language.

It is used in:
- Artificial Intelligence
- Web Development
- Data Science
- Automation
- Machine Learning
"""

        elif "ai" in message or "artificial intelligence" in message:

            bot_response = """
Artificial Intelligence (AI) enables machines to simulate human intelligence.

AI is used in:
- Chatbots
- Voice assistants
- Self-driving cars
- Image recognition
- Recommendation systems
"""

        elif "html" in message:

            bot_response = """
HTML (HyperText Markup Language) is used to create the structure of web pages.
"""

        elif "css" in message:

            bot_response = """
CSS (Cascading Style Sheets) is used to style and design websites.
"""

        elif "java" in message:

            bot_response = """
Java is an object-oriented programming language.

It is used for:
- Android apps
- Desktop applications
- Enterprise software
"""

        elif "database" in message:

            bot_response = """
A database is used to store and manage data.

Popular databases:
- MySQL
- MongoDB
- Firebase
"""

        elif "hello" in message or "hi" in message:

            bot_response = """
Hello 👋
How can I help you today?
"""

        else:

            bot_response = """
Sorry 😅
I am still learning this topic.
"""

    return render_template(
        'chatbot.html',
        user_message=user_message,
        bot_response=bot_response
    )

# Voice Assistant
@app.route('/voice')
def voice():
    return render_template('voice.html')

# Notes Generator
@app.route('/notes', methods=['GET', 'POST'])
def notes():

    topic = ""
    generated_notes = ""

    if request.method == 'POST':

        topic = request.form['topic']

        t = topic.lower()

        if "python" in t:

            generated_notes = """
Python Notes:

• Python is a high-level programming language.
• Used in AI, automation, and web development.
"""

        elif "ai" in t:

            generated_notes = """
Artificial Intelligence Notes:

• AI enables machines to simulate intelligence.
• Used in chatbots, robotics, and automation.
"""

        elif "html" in t:

            generated_notes = """
HTML Notes:

• HTML creates the structure of web pages.
"""

        elif "css" in t:

            generated_notes = """
CSS Notes:

• CSS styles and designs web pages.
"""

        elif "java" in t:

            generated_notes = """
Java Notes:

• Java is object-oriented programming language.
"""

        else:

            generated_notes = """
Sorry 😅
Notes not available yet.
"""

    return render_template(
        'notes.html',
        topic=topic,
        generated_notes=generated_notes
    )

# Quiz System
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():

    topic = ""
    questions = []
    score = None

    if request.method == 'POST':

        topic = request.form.get('topic', '').lower()

        if topic == "python":

            questions = [
                {
                    "question": "What is Python?",
                    "options": ["Browser", "Programming Language", "Game"],
                    "answer": "Programming Language"
                },
                {
                    "question": "Which symbol is used for comments?",
                    "options": ["#", "//", "**"],
                    "answer": "#"
                }
            ]

        elif topic == "html":

            questions = [
                {
                    "question": "HTML stands for?",
                    "options": [
                        "HyperText Markup Language",
                        "HighText Machine Language",
                        "Hyper Transfer Language"
                    ],
                    "answer": "HyperText Markup Language"
                },
                {
                    "question": "HTML is used for?",
                    "options": ["Styling", "Structure", "Database"],
                    "answer": "Structure"
                }
            ]

        elif topic == "css":

            questions = [
                {
                    "question": "CSS is used for?",
                    "options": ["Styling", "Programming", "Database"],
                    "answer": "Styling"
                }
            ]

        elif topic == "java":

            questions = [
                {
                    "question": "Java is?",
                    "options": ["Programming Language", "Browser", "Database"],
                    "answer": "Programming Language"
                }
            ]

        elif topic == "ai":

            questions = [
                {
                    "question": "AI stands for?",
                    "options": [
                        "Artificial Intelligence",
                        "Automatic Information",
                        "Advanced Internet"
                    ],
                    "answer": "Artificial Intelligence"
                }
            ]

        # Calculate Score
        if 'submit_quiz' in request.form:

            score = 0

            for i, q in enumerate(questions):

                user_answer = request.form.get(f'q{i}')

                if user_answer == q['answer']:
                    score += 1

            # Save Local Progress
            quiz_history.append({
                "topic": topic.upper(),
                "score": score,
                "total": len(questions)
            })

            # Save Firebase Progress
            ref = db.reference('quiz_scores')

            ref.push({
                'topic': topic,
                'score': score,
                'total': len(questions)
            })

    return render_template(
        'quiz.html',
        topic=topic,
        questions=questions,
        score=score
    )

# Progress Tracker
# Progress Tracker
@app.route('/progress')
def progress():

    total_quizzes = len(quiz_history)

    total_score = 0
    total_questions = 0

    for item in quiz_history:

        total_score += item['score']
        total_questions += item['total']

    percentage = 0

    if total_questions > 0:

        percentage = round(
            (total_score / total_questions) * 100
        )

    remaining_percentage = 100 - percentage

    return render_template(
        'progress.html',
        quiz_history=quiz_history,
        total_quizzes=total_quizzes,
        percentage=percentage,
        remaining_percentage=remaining_percentage
    )

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/login')

    total_quizzes = len(quiz_history)

    return render_template(
        'profile.html',
        username=session['user'],
        email=session['email'],
        total_quizzes=total_quizzes
    )

@app.route('/download_notes/<topic>')
def download_notes(topic):

    file_name = f"{topic}_notes.pdf"

    c = canvas.Canvas(file_name)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 800, "SmartStudy AI Notes")

    c.setFont("Helvetica", 14)
    c.drawString(100, 760, f"Topic: {topic}")

    notes = f"""
    These are AI generated notes for {topic}.

    1. Introduction
    2. Important Concepts
    3. Advantages
    4. Applications
    5. Conclusion

    SmartStudy AI 🚀
    """

    text = c.beginText(100, 720)
    text.setFont("Helvetica", 12)

    for line in notes.split('\n'):
        text.textLine(line)

    c.drawText(text)

    c.save()

    return send_file(file_name, as_attachment=True)


# Run Flask App


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)