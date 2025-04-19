from flask import Flask, render_template, jsonify, request, session
import mysql.connector
from mysql.connector import Error
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='ufc_game',
            user='root',
            password='swagman84'
        )
        print("Database connection successful!")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

@app.route('/')
def home():
    try:
        connection = get_db_connection()
        if connection is None:
            return "Database connection failed", 500
        
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Get a random fighter with all their details
            cursor.execute("SELECT * FROM ufc_fighters ORDER BY RAND() LIMIT 1")
            fighter = cursor.fetchone()
            cursor.fetchall()  # Clear any remaining results
            
            if fighter:
                # Store the fighter in session
                session['target_fighter'] = fighter
            
        finally:
            cursor.close()
            connection.close()
        
        return render_template('main.html')
        
    except Error as e:
        print(f"Error selecting initial fighter: {e}")
        return "Database error", 500

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    try:
        guess = request.json.get('fighter_name', '').lower()
        
        if not guess:
            return jsonify({"success": False, "error": "No guess provided"})
        
        # Check if there's a current fighter to guess
        if 'target_fighter' not in session:
            return jsonify({"success": False, "error": "No fighter selected. Click 'New Fighter' to start"})
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({"success": False, "error": "Database connection failed"})
        
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Get the guessed fighter's details with exact name match
            cursor.execute("SELECT * FROM ufc_fighters WHERE LOWER(name) = %s", (guess,))
            guessed_fighter = cursor.fetchone()
            cursor.fetchall()  # Clear any remaining results
            
            if not guessed_fighter:
                return jsonify({"success": False, "error": "Fighter not found"})
            
            # Format the response data
            response_data = {
                "success": True,
                "fighter": {
                    "name": guessed_fighter['name'],
                    "weight": guessed_fighter['weight'],
                    "height": guessed_fighter['height'],
                    "reach": guessed_fighter['reach'],
                    "stance": guessed_fighter['stance'],
                    "age": guessed_fighter['age'],
                    "wins": guessed_fighter['wins'],
                    "losses": guessed_fighter['losses'],
                    "gender": guessed_fighter['gender'],
                    "active": guessed_fighter['active']
                },
                "target_fighter": {
                    "name": session['target_fighter']['name'],
                    "weight": session['target_fighter']['weight'],
                    "height": session['target_fighter']['height'],
                    "reach": session['target_fighter']['reach'],
                    "stance": session['target_fighter']['stance'],
                    "age": session['target_fighter']['age'],
                    "wins": session['target_fighter']['wins'],
                    "losses": session['target_fighter']['losses'],
                    "gender": session['target_fighter']['gender'],
                    "active": session['target_fighter']['active']
                },
                "isCorrect": guessed_fighter['name'].lower() == session['target_fighter']['name'].lower()
            }
            
            return jsonify(response_data)
            
        finally:
            cursor.close()
            connection.close()
        
    except Error as e:
        print(f"Error processing guess: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/new_fighter')
def new_fighter():
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({"success": False, "error": "Database connection failed"})
        
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Get a random fighter with all their details
            cursor.execute("SELECT * FROM ufc_fighters ORDER BY RAND() LIMIT 1")
            fighter = cursor.fetchone()
            cursor.fetchall()  # Clear any remaining results
            
            if fighter:
                # Store the fighter in session
                session['target_fighter'] = fighter
                # Return success and the fighter details
                return jsonify({
                    "success": True,
                    "fighter": {
                        "name": fighter['name'],
                        "weight": fighter['weight'],
                        "height": fighter['height'],
                        "reach": fighter['reach'],
                        "stance": fighter['stance'],
                        "age": fighter['age'],
                        "wins": fighter['wins'],
                        "losses": fighter['losses'],
                        "gender": fighter['gender'],
                        "active": fighter['active']
                    }
                })
            else:
                return jsonify({"success": False, "error": "No fighters found in database"})
            
        finally:
            cursor.close()
            connection.close()
        
    except Error as e:
        print(f"Error selecting new fighter: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/test')
def test_database():
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({"error": "Database connection failed"})
        
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM ufc_fighters LIMIT 5")
        results = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return jsonify({"test_names": results})
    except Error as e:
        return jsonify({"error": str(e)})

@app.route('/search_fighters')
def search_fighters():
    query = request.args.get('query', '')
    print(f"Received search query: {query}")
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify([])
        
        cursor = connection.cursor()
        
        try:
            search_query = "SELECT name FROM ufc_fighters WHERE name LIKE %s ORDER BY name LIMIT 5"
            search_param = f"%{query}%"
            print(f"Executing query: {search_query}")
            print(f"With parameter: {search_param}")
            
            cursor.execute(search_query, (search_param,))
            results = [row[0] for row in cursor.fetchall()]
            print(f"Found matches: {results}")
            
            return jsonify(results)
            
        finally:
            cursor.close()
            connection.close()
        
    except Error as e:
        print(f"Error searching fighters: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True) 