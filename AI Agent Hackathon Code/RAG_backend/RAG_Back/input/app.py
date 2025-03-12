from flask import Flask, request, jsonify
from flask_cors import CORS
import groq
import json
from pymongo import MongoClient
from datetime import datetime

GROQ_API_KEY = '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'

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB setup
client = MongoClient('mongodb://mongo:27017/')
db = client['user_management']
users_collection = db['users']
activity_collection = db['useractivity']

# Global user tracking (Note: Not thread-safe for production use)
current_user = None

def create_groq_client():
    return groq.Groq(api_key=GROQ_API_KEY)

def log_activity(api_name, request_data, response_data):
    if current_user:
        activity = {
            'username': current_user,
            'api': api_name,
            'request': request_data,
            'response': response_data,
            'timestamp': datetime.utcnow()
        }
        activity_collection.insert_one(activity)

# User Management Endpoints
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400

    users_collection.insert_one({
        "username": username,
        "password": password  # Note: Store hashed passwords in production
    })

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    global current_user
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username, "password": password})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    current_user = username
    log_activity('/login', data, {"message": "Login successful"})
    return jsonify({"message": "Login successful"})

@app.route('/logout', methods=['POST'])
def logout():
    global current_user
    if not current_user:
        return jsonify({"error": "No user logged in"}), 400

    log_activity('/logout', request.get_json(), {"message": "Logout successful"})
    current_user = None
    return jsonify({"message": "Logout successful"})

# Existing API Endpoints with Activity Logging
@app.route('/ask_general_query', methods=['POST'])
def ask_general_query():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        client = create_groq_client()
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Always format your response as valid JSON with an answer key."
                },
                {
                    "role": "user",
                    "content": f"{query}\n\nPlease respond in JSON format with your answer in the 'response' key and 'response' key's datatype as String."
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.3,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )

        json_response = json.loads(response.choices[0].message.content)
        log_activity('/ask_general_query', data, json_response)
        return jsonify(json_response)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON response from AI model"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/text_and_query', methods=['POST'])
def text_and_query():
    try:
        data = request.get_json()
        text = data.get('text')
        query = data.get('query')
        
        if not text or not query:
            return jsonify({"error": "Both text and query parameters are required"}), 400

        client = create_groq_client()
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Analyze the provided text and answer the question. 
                                Format your response as JSON with these keys:
                                - "analysis": summary of the text
                                - "answer": direct answer to the query
                                - "confidence": confidence percentage"""
                },
                {
                    "role": "user",
                    "content": f"TEXT:\n{text}\n\nQUESTION: {query}\n\nRespond in valid JSON format."
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.2,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

        json_response = json.loads(response.choices[0].message.content)
        log_activity('/text_and_query', data, json_response)
        return jsonify(json_response)

    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse AI model response"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_activities', methods=['GET'])
def get_user_activities():
    global current_user
    
    if not current_user:
        return jsonify({"error": "No user logged in"}), 401
    
    try:
        # Filter for specific APIs with field projection
        activities = list(activity_collection.find(
            {
                "username": current_user,
                "api": {"$in": ["/ask_general_query", "/text_and_query"]}
            },
            {
                "_id": 0,
                "request": 1,
                "response": 1,
                "timestamp": 1
            }
        ).sort("timestamp", -1))

        # Convert datetime to ISO format
        for activity in activities:
            activity['timestamp'] = activity['timestamp'].isoformat()

        log_activity('/get_activities', {}, {"activity_count": len(activities)})
        return jsonify({"activities": activities})
    
    except Exception as e:
        log_activity('/get_activities', {}, {"error": str(e)})
        return jsonify({"error": str(e)}), 500
    
# Existing API Endpoints with Activity Logging
@app.route('/make_quiz', methods=['POST'])
def make_quiz():
    global current_user
    
    if not current_user:
        return jsonify({"error": "No user logged in"}), 401

    try:
        # Get user's previous interactions
        activities = list(activity_collection.find(
            {"username": current_user, "api": {"$in": ["/ask_general_query", "/text_and_query"]}},
            {"_id": 0, "request": 1, "response": 1}
        ).sort("timestamp", -1).limit(10))  # Limit to last 10 interactions

        # Get previous quiz questions
        prev_quizzes = list(activity_collection.find(
            {"username": current_user, "api": "/make_quiz"},
            {"_id": 0, "response": 1}
        ))

        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        client = create_groq_client()
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert quiz generator. Generate exactly 5 MCQs in this strict JSON format:
                    {
                    "quiz": [
                        {
                        "question": "question text",
                        "choices": {
                            "choice1": "option 1",
                            "choice2": "option 2", 
                            "choice3": "option 3",
                            "choice4": "option 4"
                        },
                        "answer": "correct choice key (e.g., choice1)",
                        "explanation": "brief reasoning for correct answer"
                        }
                    ]
                    }
                    Follow these rules:
                    1. 4 questions based on user's history and current query
                    2. 1 question from related domain but not in history
                    3. No repetition from previous quizzes
                    4. Clear distinction between correct and incorrect options
                    5. Explanations under 50 words"""
                },
                {
                    "role": "user",
                    "content": f"""Generate quiz based on:
                    - Current query: {query}
                    - User history: {json.dumps(activities)}
                    - Previous quizzes: {json.dumps(prev_quizzes)}
                    Create 5 MCQs following all rules above."""
                }
            ],
            model="mixtral-8x7b-32768",
            temperature=0.5,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )

        # Parse and validate response
        json_response = json.loads(response.choices[0].message.content)
        
        # Ensure proper formatting
        if "quiz" not in json_response or len(json_response["quiz"]) != 5:
            raise ValueError("Invalid quiz format from AI model")

        # Log and return response
        log_activity('/make_quiz', {"query": query}, json_response)
        return jsonify(json_response)

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON response from AI model"}), 500
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':

    app.run(host="0.0.0.0", debug=True, port=8090)
    client = create_groq_client()
    response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant. Always format your response as valid JSON with an answer key and this is your knowledge base: The course CSE 578 (Fall 2024), taught by Chris Bryan with TA Utkarsh Singh, meets Tuesdays and Thursdays from 1:30–2:45 PM. Key activities include attending lectures, engaging with research papers (e.g., A Brief History of Data Visualization), and participating in Slack discussions. Students complete 5-6 solo programming assignments using D3.v7 and GitHub, with penalties for late submissions, and take two exams (10% each) covering lecture content, papers, and basic D3 syntax. Communication is centralized on Slack, while Canvas hosts schedules and assignments. The major deliverable is a group project where teams of 4-5 implement or extend a visualization research paper (published post-2015 in venues like IEEE VIS or CHI). Requirements include adding a new dataset and an original feature, with deliverables such as interactive scrollytelling stories or animated visualizations. MS/PhD students can propose research-oriented projects aimed at publication, coordinated with advisors or lab members. The course emphasizes task abstraction as a design foundation, structured through Munzner’s nested model: (1) defining the domain situation (e.g., movie enthusiasts seeking recommendations), (2) specifying data/task abstractions (e.g., combining audience and critic ratings into an overall_score), (3) selecting idioms like stacked bar charts or interactive scatterplots, and (4) optimizing algorithms for efficiency. Tasks are categorized into low-level actions (retrieve, filter, cluster) and broader goals (explore trends, locate outliers), with examples ranging from analyzing GDP data to understanding vaccine distribution. To manage complexity, students apply facet and reduce strategies. Faceting splits data into coordinated views: juxtaposing side-by-side charts (e.g., FiveThirtyEight’s World Cup comparisons), partitioning by attributes (e.g., state or age), or superimposing layers (e.g., maps with roads over regions). Reduction simplifies data via filtering (threshold-based elimination), aggregation (histograms, boxplots), or dimensionality reduction (PCA, t-SNE). Design principles like Shneiderman’s mantra (overview first, zoom/filter, details on demand) and tools like D3’s brushing/linking or cross-filtering (e.g., NYT’s Rent vs. Buy Calculator) guide implementation. These concepts directly align with the group project, where students balance task abstraction (defining domain goals and abstract actions) with technical execution (using facet/reduce techniques for interactivity and scalability). For example, extending a research paper might involve small multiples for comparison, dimensionality reduction for high-dimensional data, or dynamic layering for focus+context navigation. The course equips students to tackle real-world visualization challenges, blending theoretical frameworks with practical D3.js skills to create publishable, user-driven visual stories."
        },
        {
            "role": "user",
            "content": ""
        }
        ],
        model="mixtral-8x7b-32768",
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"}
    )
    json_response = json.loads(response.choices[0].message.content)