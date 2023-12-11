import json
from abc import ABC, abstractmethod
import random
from flask import Flask 
from flask import render_template, request, redirect, url_for

app = Flask(__name__)

used_questions = []

def difficulty_para_palavra(difficulty):
    if difficulty == 1:
        return "Fácil"
    elif difficulty == 2:
        return "Moderado"
    elif difficulty == 3:
        return "Difícil"
    else:
        return "Desconhecido"

class Question:
    def __init__(self, id, question, response, difficulty, dica):
        self.id = id
        self.question = question
        self.response = response
        self.difficulty = difficulty
        self.dica = dica
        self.attempts = 0

    def display(self):
        print(f"question (Nível: {difficulty_para_palavra(self.difficulty)}):")
        print(self.question)
        for i, resposta in enumerate(self.response, start=1):
            print(f"{i}. {resposta['alt']}")

    def check_resposta(self, user_resposta):
        try:
            user_resposta = int(user_resposta)
            if 1 <= user_resposta <= len(self.response):
                resposta_selecionada = self.response[user_resposta - 1]
                if resposta_selecionada["correct"]:
                    points_manager.add_points(10)  
                    self.attempts = 0  # Resetar contagem de tentativas após resposta correta
                    return True
        except (ValueError, IndexError):
            pass

        self.attempts += 1
        return False
    
    def __str__(self):
        result = f"question (Nível: {difficulty_para_palavra(self.difficulty)}):\n"
        result += f"{self.question}\n"
        for i, resposta in enumerate(self.response, start=1):
            result += f"{i}. {resposta['alt']}\n"
        return result
 
class PointsSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PointsSingleton, cls).__new__(cls)
            cls._instance.total_points = 0
        return cls._instance

    def add_points(self, points):
        self.total_points += points

    def get_total_points(self):
        return self.total_points  
    
points_manager = PointsSingleton()     

class ShuffleStrategy(ABC):
    @abstractmethod
    def shuffle(self, questions):
        pass

class RandomShuffleStrategy(ShuffleStrategy):
    def shuffle(self, questions):
        return random.sample(questions, len(questions))

class DifficultyShuffleStrategy(ShuffleStrategy):
    def shuffle(self, questions):
        questions.sort(key=lambda q: q.difficulty)

def load_questions_from_json(quiz, quantity, difficulty=None):
    with open(quiz, 'r') as quiz_file:
        data = json.load(quiz_file)

    questions_data = data["questions"]
    questions = []

    for question_data in questions_data:
        id = question_data["id"]
        question = question_data["question"]
        response = question_data["response"]
        question_difficulty = question_data["difficulty"]
        dica = question_data["dica"]

        if difficulty is None or question_difficulty == difficulty:
            questions.append(Question(id, question, response, question_difficulty, dica))

    return random.sample(questions, quantity) if quantity is not None else questions
# Evita perguntas repetidas
def shuffle_questions(questions, shuffle_strategy):
     global used_questions 
     shuffled_questions = shuffle_strategy.shuffle(questions)

   
     shuffled_questions = [q for q in shuffled_questions if q not in used_questions]

     if not shuffled_questions:
        used_questions = []

     used_questions.extend(shuffled_questions) 
     return shuffled_questions


@app.route("/", methods=['POST', 'GET'])
def home(): 
    return render_template('index.html')

@app.route("/menu", methods=['GET', 'POST'])
def menu():
    question = None
    if request.method == 'POST':
        user_quantity = int(request.form['quantity'])
        user_difficulty = int(request.form['difficulty'])

        # Carregue uma pergunta de exemplo para a variável question
        all_questions = load_questions_from_json('quiz.json', quantity=1, difficulty=user_difficulty)
        question = all_questions[0]

        # Use 'menu' como o endpoint no redirecionamento
        return redirect(url_for('menu', quantity=user_quantity, difficulty=user_difficulty))

    return render_template('menu.html', question=question)

@app.route("/quiz", methods=['POST', 'GET'])
def hello_world():
    global used_questions
    user_quantity = int(request.args.get('quantity', 1))
    user_difficulty = int(request.args.get('difficulty', 1))  

    if request.method == 'POST':
        user_quantity = int(request.form['quantity'])
        user_difficulty = int(request.form['difficulty'])


    all_questions = load_questions_from_json('quiz.json', quantity=user_quantity, difficulty=user_difficulty)

    questions = [q for q in all_questions]

    shuffle_strategy = RandomShuffleStrategy()
    shuffled_questions = shuffle_questions(questions, shuffle_strategy)

    current_question_index = int(request.args.get('index', 0))
    first_attempt = not request.args.get('retry')

    if request.method == 'POST':
        user_answer = int(request.form['user_answer'])
        

        current_question = shuffled_questions[current_question_index]
        
        

        if current_question.check_resposta(user_answer):
            feedback = "Resposta correta!"
            current_question_index += 1
        else:
            feedback = "Tente novamente na próxima pergunta."
            current_question_index += 1

        if current_question_index >= len(shuffled_questions):
            return redirect(url_for('final_page'))

        current_question_index = min(current_question_index, len(shuffled_questions) - 1)

    else:
        current_question = shuffled_questions[current_question_index]
        feedback = None

    options_with_indices = enumerate(current_question.response, start=1)
    retry_parameter = '' if first_attempt else '&retry=true'

    feedback_quiz = f"{points_manager.get_total_points()}"
    return render_template(
        'quiz.html',
        question=current_question,
        options_with_indices=options_with_indices,
        feedback=feedback,
        total_questions=len(shuffled_questions),
        current_index=current_question_index + 1,
        user_quantity=user_quantity,
        retry_parameter=retry_parameter,
        feedback_quiz=feedback_quiz,
        
    )
    
# Rota para a página final
@app.route("/final")
def final_page():
    final_feedback = f"Quiz concluído! Pontuação total: {points_manager.get_total_points()}"
    points_manager.total_points = 0
    return render_template('final.html', final_feedback=final_feedback)
   



if __name__ == "__main__":
    app.run(debug=True, port=8000)