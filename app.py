import os
import json

from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from flask import send_file

import firebase_admin
from firebase_admin import credentials, db

from reportlab.pdfgen import canvas

import google.generativeai as genai


app = Flask(__name__)

# =========================
# Session Configuration
# =========================

app.config['SECRET_KEY'] = 'smartstudysecret'
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

# =========================
# Firebase Setup
# =========================

firebase_credentials = json.loads(
    os.environ["FIREBASE_CREDENTIALS"]
)

if not firebase_admin._apps:

    cred = credentials.Certificate(firebase_credentials)

    firebase_admin.initialize_app(cred, {
        "databaseURL": os.environ.get("FIREBASE_DB_URL")
    })

# =========================
# Gemini AI Setup
# =========================

genai.configure(
    api_key=os.environ.get("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

# =========================
# Store Quiz History
# =========================

quiz_history = []

# =========================
# Home Page
# =========================

@app.route('/')
def home():
    return render_template('index.html')

# =========================
# Register Page
# =========================

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

# =========================
# Login Page
# =========================

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

# =========================
# Logout
# =========================

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

# =========================
# Dashboard
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    return render_template(
        'dashboard.html',
        username=session['user']
    )

# =========================
# REAL AI CHATBOT
# =========================

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():

    user_message = ""
    bot_response = ""

    if request.method == 'POST':

        user_message = request.form['message']

        try:

            response = model.generate_content(
                user_message
            )

            bot_response = response.text

        except Exception as e:

            bot_response = f"Error: {str(e)}"

    return render_template(
        'chatbot.html',
        user_message=user_message,
        bot_response=bot_response
    )

# =========================
# Voice Assistant
# =========================

@app.route('/voice')
def voice():
    return render_template('voice.html')

# =========================
# Notes Generator
# =========================

@app.route('/notes', methods=['GET', 'POST'])
def notes():

    topic = ""
    generated_notes = ""

    if request.method == 'POST':

        topic = request.form['topic']

        try:

            prompt = f"""
            Generate short educational notes on:
            {topic}
            """

            response = model.generate_content(prompt)

            generated_notes = response.text

        except Exception as e:

            generated_notes = f"Error: {str(e)}"

    return render_template(
        'notes.html',
        topic=topic,
        generated_notes=generated_notes
    )

# =========================
# Quiz System
# =========================

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
                    "options": [
                        "Browser",
                        "Programming Language",
                        "Game"
                    ],
                    "answer": "Programming Language"
                },
                {
                    "question": "Which symbol is used for comments?",
                    "options": [
                        "#",
                        "//",
                        "**"
                    ],
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
                }
            ]

        elif topic == "css":

            questions = [
                {
                    "question": "CSS is used for?",
                    "options": [
                        "Styling",
                        "Programming",
                        "Database"
                    ],
                    "answer": "Styling"
                }
            ]

        elif topic == "java":

            questions = [
                {
                    "question": "Java is?",
                    "options": [
                        "Programming Language",
                        "Browser",
                        "Database"
                    ],
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

        if 'submit_quiz' in request.form:

            score = 0

            for i, q in enumerate(questions):

                user_answer = request.form.get(f'q{i}')

                if user_answer == q['answer']:
                    score += 1

            quiz_history.append({
                "topic": topic.upper(),
                "score": score,
                "total": len(questions)
            })

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

# =========================
# Progress Tracker
# =========================

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

# =========================
# Profile
# =========================

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

# =========================
# Download Notes PDF
# =========================

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

# =========================
# Run Flask App
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )