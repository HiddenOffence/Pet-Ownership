from flask import Flask, render_template, request, redirect, url_for, g, jsonify
import sqlite3

app = Flask(__name__)


# Connect database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('pets.db')
    db.row_factory = sqlite3.Row
    # Creats tables if they dont exist
    c = db.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS Pets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name TEXT NOT NULL,
    species_id INT NOT NULL,
    lifespan TEXT,
    difficulty INTEGER,
    cost_setup DECIMAL(6,2),
    daily_time_min INTEGER,
    space_required TEXT,
    temperament TEXT,
    notes TEXT,
    FOREIGN KEY (species_id) REFERENCES Species(id));
              ''')

    c.execute('''CREATE TABLE IF NOT EXISTS Species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT);
    ''')

    c.execute('''CREATE TABLE IF NOT EXISTS Attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT); ''')

    c.execute('''CREATE TABLE IF NOT EXISTS Places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT);
    ''')

    c.execute('''CREATE TABLE IF NOT EXISTS pet_attributes (
    pet_id INT,
    attributes_id INT,
    cost DECIMAL(6,2),
    PRIMARY KEY (pet_id, attributes_id),
    FOREIGN KEY (pet_id) REFERENCES Pets(id),
    FOREIGN KEY (attributes_id) REFERENCES Places(id));''')

    c.execute('''CREATE TABLE IF NOT EXISTS place_pet (
    pet_id INT,
    place_id INT,
    cost DECIMAL(6,2),
    PRIMARY KEY (pet_id, place_id),
    FOREIGN KEY (pet_id) REFERENCES Pets(id),
    FOREIGN KEY (place_id) REFERENCES Places(id));''')

    c.execute('''CREATE TABLE IF NOT EXISTS Reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reviewer_name TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    pet_name TEXT NOT NULL,
    species TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES Pets(id));
    ''')

    return db


# Close Database connection
@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_databse', None)
    if db is not None:
        db.close()


@app.route('/test_pets')
def test_pets():
    conn = get_db()
    try:
        # Get all pets with their IDs and names
        pets = conn.execute('SELECT id, name FROM Pets').fetchall()

        # Create a simple HTML response
        html = "<h1>Pets in Database</h1><ul>"
        for pet in pets:
            html += f"<li>ID: {pet['id']}, Name: {pet['name']}</li>"
        html += "</ul>"

        # Add test links
        html += "<h2>Test Comparisons</h2><ul>"
        if len(pets) >= 2:
            html += f"<li><a href='/compare_results?first={pets[0]['id']}&second={pets[1]['id']}'>Compare {pets[0]['name']} vs {pets[1]['name']}</a></li>"
        if len(pets) >= 3:
            html += f"<li><a href='/compare_results?first={pets[1]['id']}&second={pets[2]['id']}'>Compare {pets[1]['name']} vs {pets[2]['name']}</a></li>"
        html += "</ul>"

        return html
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()


# Homepage
@app.route('/')
def home():
    conn = get_db()
    try:
        featured = conn.execute(
            '''SELECT name,
            lifespan,
            temperament,
            cost_setup FROM Pets
            ORDER BY difficulty ASC LIMIT 3
        ''').fetchall()
        latest_reviews = conn.execute(
            '''SELECT pet_name, 
            reviewer_name, rating,
            comment FROM Reviews
            ORDER BY created_at DESC LIMIT 3
        ''').fetchall()
    except Exception:
        featured, latest_reviews = [], []
        conn.close()
    return render_template('home.html', title='HOME',
                           featured=featured, reviews=latest_reviews)


# Browse pet page - search-GPT
@app.route('/browse')
def browse():
    search_text = request.args.get('search')
    difficulty_choice = request.args.get('difficulty')

    sql = '''
    SELECT id,
    name,
    species_id,
    lifespan,
    cost_setp,
    daily_time_min
    FROM Pets WHERE 1=1'''

    filters = []
    params = []

    if search_text and search_text.strip() != "":
        filters.append('(name LIKE ? OR temperament LIKE ?)')
        term = f"%{search_text.strip()}%"
        params.extend([term, term])

    if difficulty_choice and difficulty_choice.strip() != "":
        try:
            diff_num = int(difficulty_choice)
            filters.append('difficulty = ?')
            params.append(diff_num)
        except:
            pass

    if filters:
        sql += ' WHERE ' + ' AND '.join(filters)

    sql += ' ORDER BY cost_setup ASC'

    conn = get_db()
    try:
        pets = conn.execute(sql, params).fetchall()
    except Exception:
        pets = []

        conn.close()

    return render_template('browse.html', pets=pets, search=search_text)


# About page
@app.route('/about')
def about():
    about_content = {
        "title": "About Our Pet Guide",
        "mission": "Helping you find the perfect low-maintenance pet companion",
        "description": "Our platform provides comprehensive information about various pets to help you make an informed decision."
    }
    return render_template('about_pets.html', about=about_content)


# Pets profile page
@app.route('/pet/<pet_name>')
def pet_profile(pet_name):
    conn = get_db()
    try:
        pet = conn.execute('''SELECT id,
                           name,
                           species_id
                           FROM Pets
                           JOIN Species ON Pets.species_id = Species.id
                           WHERE name = ?''', (pet_name,)).fetchone()
        reviews = conn.execute(
            '''SELECT reviewer_name,
            rating,
            comment,
            created_at
            FROM Reviews WHERE pet_name = ? ORDER BY created_at DESC''',
            (pet_name,)
        ).fetchall()
    except Exception:
        pet, reviews = None, []
       
    conn.close()

    if pet is None:
        return render_template('404.html'), 404

    return render_template('pet.html', pet=pet, reviews=reviews)


# Comparison tool
@app.route('/compare')
def compare():
    conn = get_db()
    try:
        pets = conn.execute('''SELECT id,
                            name FROM Pets
                            ORDER BY name
                            ''').fetchall()
        # Get some popular comparisons for the page
        popular_comparisons = [
            (1, 2, "Hamster", "Guinea Pig"),
            (3, 4, "Betta Fish", "Leopard Gecko"),
            (1, 5, "Hamster", "Parakeet")
        ]

    except Exception as e:
        print("Error fetching pets:", e)
        pets = []
        popular_comparisons = []

        conn.close()

    return render_template('compare.html',
                           pets=pets, popular_comparisons=popular_comparisons)


# Comparison results page
@app.route('/comparison_results')
def comparison_results():
    # Get the pet names from URL parameters
    first_name = request.args.get('first', '')
    second_name = request.args.get('second', '')

    # Basic validation
    if not first_name or not second_name:
        return render_template('error.html',
                               message='Please select two pets to compare.')

    if first_name == second_name:
        return render_template('error.html',
                               message='Please select two different pets to compare.')

    conn = get_db()

    try:
        # Get pets by name instead of ID
        pet1 = conn.execute('SELECT name FROM Pets WHERE name = ?',
                            (first_name,)).fetchone()
        pet2 = conn.execute('SELECT name FROM Pets WHERE name = ?',
                            (second_name,)).fetchone()

        # Check if pets were found
        if not pet1 or not pet2:
            not_found = []
            if not pet1:
                not_found.append(first_name)
            if not pet2:
                not_found.append(second_name)
            return render_template('error.html', 
                                   message=f"Pets not found: {', '.join(not_found)}")

        # Convert to dictionaries with default values for None fields
        pet1_dict = dict(pet1)
        pet2_dict = dict(pet2)

        # Set default values for None fields to avoid comparison errors
        numeric_fields = ['cost_setup', 'daily_time_min', 'difficulty']
        for field in numeric_fields:
            if pet1_dict.get(field) is None:
                pet1_dict[field] = 0
            if pet2_dict.get(field) is None:
                pet2_dict[field] = 0

        return render_template('comparison_results.html',
                               pet1=pet1_dict, pet2=pet2_dict)

    except Exception as e:
        print("Error in comparison:", e)
        return render_template('error.html',
                               message='An error occurred while comparing pets.')
    finally:
        conn.close()


# Add Review with validation
@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if request.method == 'GET':
        conn = get_db()
        try:
            pets = conn.execute('SELECT id, name FROM Pets').fetchall()
        except Exception as e:
            print("Error:", e)
            pets = []
        finally:
            conn.close()
        return render_template('add_review.html', pets=pets)

    elif request.method == 'POST':
        pet_id = request.form.get('pet_id')
        reviewer_name = request.form.get('reviewer_name') or "Anonymous"
        rating = request.form.get('rating') or "5"
        comment = request.form.get('comment') or ""

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                rating = 5
        except:
            return redirect('/')

        conn = get_db()
        try:
            conn.execute('''INSERT INTO Reviews
                        (pet_id, reviewer_name, rating, comment) VALUES (?,?,?,?)''',
                        (pet_id, reviewer_name, rating, comment))
            conn.commit()
        except Exception as e:
            print("Error adding review:", e)
            conn.rollback()
            return redirect('/add_review')
        finally:
            conn.close()

        # redirects to thank-you page
        return render_template('review_thankyou.html')


@app.route('/api/pets')
def api_pets():
    conn = get_db()
    try:
        rows = conn.execute('''SELECT
                p.id, p.name, p.lifespan, p.difficulty, p.cost_setup,
                p.daily_time_min, p.space_required, p.temperament, p.notes,
                s.name as species_name
                FROM Pets p
                LEFT JOIN Species s ON p.species_id = s.id
                ORDER BY p.name''').fetchall()
        data = [dict(row) for row in rows]
    except Exception as e:
        print("Error in API:", e)
        data = []
    finally:
        conn.close()
    return jsonify({"pets": data})


# Custom 404 error handler
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
