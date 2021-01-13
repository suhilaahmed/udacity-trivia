import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # set up CORS, allowing all origins
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


    # CORS Headers

    @app.after_request
    def after_request(response):
        """
        Modify Access-Control headers after each request
        """
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories', methods=['GET'])
    def get_categories():
        """
        GET '/categories'
        Fetches a dictionary of categories in which the keys are the ids and the value is the corresponding string of the category
        Request Arguments: None
        Returns: An object with a single key, categories, that contains a object of id: category_string key:value pairs.
       response: {
            "success": true,
            "categories": {
                '1' : "Science",
                '2' : "Art",
                '3' : "Geography",
                '4' : "History",
                '5' : "Entertainment",
                '6' : "Sports"
        }
        """
        categories = {}
        for category in Category.query.all():
            categories[category.id] = category.type
        if len(categories) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'categories': categories}), 200

    @app.route('/questions', methods=['GET'])
    def get_questions():
        """
        GET '/questions'
        Fetches a dictionary of questions in which each question is represented by an question object.
        Request Arguments: (Optional, default is 1) An integer representing the current page where each page contains a maximum of 10 questions
        Returns: An object which includes a list of current questions, list of categories and total number of questions
         response: {
            "success": true,
            "questions": [
                {
                    "id": 1,
                    "question": "Who built this API?",
                    "answer": "Dev-Nebe",
                    "category": 1,
                    "difficulty": 2
                },
                {
                    "id": 2,
                    "question": "What programming language was this API built in?",
                    "answer": "Python",
                    "category": 1,
                    "difficulty": 2
                }]
            "total_questions": 2,
            "current_category": None,
            "categories": {
                '1' : "Science",
                '2' : "Art",
                '3' : "Geography",
                '4' : "History",
                '5' : "Entertainment",
                '6' : "Sports"
            }
        }
        """
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * 10
        end = start + 10

        questions = Question.query.all()
        formatted_questions = [question.format() for question in questions]
        current_questions = formatted_questions[start:end]

        if len(current_questions) == 0:
            abort(404)

        categories = {}
        for category in Category.query.all():
            categories[category.id] = category.type
        if len(categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(formatted_questions),
            'current_category': None,
            'categories': categories,
        }), 200

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        DELETE '/questions'
        Delete a question with a specific ID
        Request Arguments: None
        Returns: An object which includes a key - message - indicating that the question was deleted successfully.
        Sample response: {
            "success": true,
            "deleted": 1
            "message": "Deleted Successfully"
        }
        """
        try:
            question = Question.query.get(question_id)
            if question is None:
                abort(404)

            question.delete()
        except:
            abort(500)
        return jsonify({
            'success': True,
            'deleted': question_id,
            'message': "Deleted Successfully"}), 200

    @app.route('/questions', methods=['POST'])
    def add_new_question():
        """
        POST '/questions'
        Add new question to a specific category
        Request Arguments: None
        Request Body: A JSON object containing the following keys - question, answer, category, and difficulty. The values associated with these keys should be of type string, string, int, and int respectively.
        request body: {
            "question": "What is the longest river in the world?",
            "answer": "Nile River",
            "category": 3,
            "difficulty": 4
        }

        Returns: An object which includes a key - message - indicating that the question was added successfully.
        response: {
            "success": true,
            "created": 1
            "message": "Created Successfully"
        }
        """
        body = request.get_json()

        question = body.get('question')
        answer = body.get('answer')
        category = body.get('category')
        difficulty = body.get('difficulty')
        if question == '' or answer == '' or category == '' or difficulty == '':
            abort(400)

        try:
            new_question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
            new_question.insert()

            return jsonify({
                'success': True,
                'created': new_question.id,
                'message': "Created Successfully"}), 201

        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_for_question():
        """
        POST '/questions/search'
        Searches for a question in the database.
        Request Arguments: None
        Request Body: A JSON object containing a single key: value pair. The key is 'searchTerm' and the value contains the search_query
        request bpdy: {
            "searchTerm": "liver"
        }
        Returns: A JSON object which includes a key - questions - that points to a list of questions where each question is represented by a dictionary.
        response: {
            'success': True,
            'questions': [
                {
                    'id': 10,
                    'question': 'Which is the only team to play in every soccer World Cup tournament?',
                    'answer': 'Brazil',
                    'category': 6,
                    'difficulty': 3
                },
                {
                    'id': 11,
                    'question': 'Which country won the first ever soccer World Cup in 1930?',
                    'answer': 'Uruguay',
                    'category': 6,
                    'difficulty': 4
                }
            ],
            'message': "Questions Found Successful"
        }
        """
        body = request.get_json()
        search_term = body.get('searchTerm')
        if search_term == '':
            abort(400)

        search_results = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()

        if len(search_results) == 0:
            abort(404)
        formatted_result = [question.format() for question in search_results]

        return jsonify({
            'success': True,
            'questions': formatted_result,
            'message': "Questions Found Successful"}), 200

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        """
         GET '/categories/{{int:id}}/questions'
         Returns a list of all the questions belongs to a specific category.
         Request Arguments: None
         Returns: A JSON object which includes a key - questions - that points to a list of questions for the requested category.
         response: {
            'success': True,
            'questions': [
                {
                    'id': 10,
                    'question': 'Which is the only team to play in every soccer World Cup tournament?',
                    'answer': 'Brazil',
                    'category': 6,
                    'difficulty': 3
                }
            ],
            'total_questions': 1,
            'current_category': 6
        """
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * 10
        end = start + 10
        category = Category.query.filter_by(id=category_id).one_or_none()
        if category is None:
            abort(404)

        questions = Question.query.filter_by(category=category_id).all()
        formatted_questions = [question.format() for question in questions]
        current_questions = formatted_questions[start:end]

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'current_category': category.type
        }), 200

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_question():
        """
         POST '/quizzes'
         Returns a random question for the quiz, within the given category or all categories, that is not in the list of previous questions.
         Request Arguments: None
         Request Body: A JSON object containing the following keys - previous_questions, quiz_category.
         request body: {
            "previous_questions": [1,18,5],
            "quiz_category": 1,
        }
        Returns: A JSON object which includes a key - questions - that points to a list of questions for the requested category. Each question is represented by a dictionary.
        Sample response: {
            'success': True,
            'question': [
                {
                    'id': 10,
                    'question': 'What boxer's original name is Cassius Clay?',
                    'answer': 'Muhammad Ali',
                    'category': 4,
                    'difficulty': 1
                }
            ]
        }
        """
        body = request.get_json()
        if not body:
            abort(400)
        category = body.get('quiz_category')
        prev_questions = body.get('previous_questions')

        if category is None or prev_questions is None:
            abort(400)

        if category.get('id') == 0:
            questions = Question.query.all()

        else:
            questions = Question.query.filter_by(category=category.get('id')).all()

        total_questions = len(questions)
        next_question = questions[random.randint(0, len(questions) - 1)]

        while next_question.id in prev_questions:
            next_question = questions[random.randint(0, len(questions) - 1)]
            if len(prev_questions) == total_questions:
                return jsonify({
                    'success': True
                })

        return jsonify({
            'success': True,
            'question': next_question.format(),
        }), 200

    # Error Handlers

    # Error handler for resource not found error
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource Not Found'
        }), 404

    # Error handler for internal server error
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Internal Server Error'
        }), 500

    # Error handler for bad request
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad Request'
        }), 400

    # Error handler for Unprocessable entity
    @app.errorhandler(422)
    def unprocessable_error(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable Entity'
        }), 422

    # Error handler for method not allowed
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'Method Not Allowed'
        }), 405

    return app
