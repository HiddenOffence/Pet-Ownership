from flask import Flask, render_template, request, redirect, g, \
    jsonify, abort
from datetime import datetime
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

    c.execute('''CREATE TABLE IF NOT EXISTS Places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT);
    ''')

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
            html += f"<li><a href='/compare_results?first={pets[0]['id']}&\
                second={pets[1]['id']}'>\
                    Compare {pets[0]['name']} vs {pets[1]['name']}</a></li>"
        if len(pets) >= 3:
            html += f"<li><a href='/compare_results?first={pets[1]['id']}&\
                second={pets[2]['id']}'>\
                    Compare {pets[1]['name']} vs {pets[2]['name']}</a></li>"
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
        featured = conn.execute('''SELECT name,
                                difficulty, cost_setup,
                                daily_time_min, temperament
                                FROM Pets ORDER BY difficulty ASC LIMIT 3
                                ''').fetchall()

        latest_reviews = conn.execute('''SELECT pet_name,
                                      reviewer_name, rating, comment
                                      FROM Reviews
                                      LIMIT 3
                                      ''').fetchall()

    except Exception as e:
        print("Error fetching home data:", e)
        featured, latest_reviews = [], []
    finally:
        conn.close()

    return render_template('home.html',
                           featured=featured, reviews=latest_reviews)


# Browse pet page - search-Deepseek
@app.route('/browse')
def browse():
    # Get query parameters
    search_query = request.args.get('search', '')
    difficulty_filter = request.args.get('difficulty', '')
    sort_by = request.args.get('sort', 'name')

    # Build SQL query
    sql = '''SELECT id,
name,
species_id,
lifespan,
difficulty,
cost_setup,
daily_time_min,
space_required,
temperament,
notes
FROM Pets
WHERE 1=1'''
    params = []

    # Add search filter
    if search_query:
        sql += ''' AND (name LIKE ?
OR temperament LIKE ?
OR species LIKE ?
OR lifespan LIKE ?
OR space_required LIKE ?)'''
        search_term = f'%{search_query}%'
        params.extend([search_term, search_term, search_term])

    # Add difficulty filter
    if difficulty_filter:
        sql += ''' AND difficulty = ?'''
        params.append(int(difficulty_filter))

    # Add sorting
    if sort_by == 'name':
        sql += ''' ORDER BY name ASC'''
    elif sort_by == 'difficulty':
        sql += ''' ORDER BY difficulty ASC, name ASC'''
    elif sort_by == 'cost_setup':
        sql += ''' ORDER BY cost_setup ASC, name ASC'''
    elif sort_by == 'daily_time_min':
        sql += ''' ORDER BY daily_time_min ASC, name ASC'''

    conn = get_db()
    try:
        pets = conn.execute(sql, params).fetchall()
        pets = [dict(pet) for pet in pets]  # Convert to dictionaries
    except Exception as e:
        print("Error fetching pets:", e)
        pets = []
    finally:
        conn.close()

    return render_template('browse.html',
                           pets=pets,
                           search_query=search_query,
                           difficulty_filter=difficulty_filter,
                           sort_by=sort_by)


# Debug search
@app.route('/debug_search')
def debug_search():
    search_query = request.args.get('q', '')
    conn = get_db()
    try:
        # Test the search query
        pets = conn.execute(
            '''SELECT name,
               species_id,
               lifespan,
               difficulty,
               cost_setup,
               daily_time_min,
               space_required,
               temperament,
               notes FROM Pets WHERE name LIKE ? OR temperament LIKE ?''',
            (f'%{search_query}%', f'%{search_query}%')
        ).fetchall()

        result = f"<h1>Search Results for '{search_query}'</h1>"
        result += f"<p>Found {len(pets)} results</p>"

        for pet in pets:
            result += f"<pre>{dict(pet)}</pre><hr>"

        return result
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()


# About page
@app.route('/about')
def about():
    about_content = {
        "title":
        "About Our Pet Guide",
        "mission":
        "Helping you find the perfect low-maintenance pet companion",
        "description":
        "Our platform provides comprehensive information about various pets to help you make an informed decision."
    }
    return render_template('about_pets.html', about=about_content)


# Pets profile page
@app.route('/pet/<int:pet_id>')
def pet_profile(pet_id):
    conn = get_db()
    try:
        pet = conn.execute('''SELECT id,
                            name,
                            species_id,
                            lifespan,
                            difficulty,
                            cost_setup,
                            daily_time_min,
                            space_required,
                            temperament,
                            notes FROM Pets
                            WHERE id = ?''', (pet_id,)).fetchone()
        print(dict(pet))
        if pet is not None:
            print("got here")
            return render_template('pet_profiles.html', pet=dict(pet))
        else:
            return render_template('error.html',
                                   message=(f'Pet with ID {pet_id} not found. \
                                       <a href="/browse">Browse all pets</a>'))
    except Exception as e:
        print("Error fetching pet:", e)
        return render_template('error.html',
                               message='Error loading pet information. \
                                   Please try again.')
    finally:
        conn.close()


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
    if not first_name or not second_name or first_name == second_name:
        abort(404)

    conn = get_db()

    try:
        # Get pets by name instead of ID
        pet1 = conn.execute('''SELECT Pets.*,
                            Species.name AS species,
                            Species.description AS
                            species_desc
                            FROM Pets
                            JOIN Species
                            ON Pets.species_id = Species.id
                            WHERE Pets.name = ?''',
                            (first_name,)).fetchone()
        pet2 = conn.execute('''SELECT Pets.*,
                            Species.name AS species,
                            Species.description
                            AS species_desc
                            FROM Pets
                            JOIN Species ON Pets.species_id = Species.id
                            WHERE Pets.name = ?''', 
                            (second_name,)).fetchone()

        # Check if pets were found
        if not pet1 or not pet2:
            not_found = []
            if not pet1:
                not_found.append(first_name)
            if not pet2:
                not_found.append(second_name)

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
        abort(404)
    finally:
        conn.close()


# Add Review with validation
@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    reviewer_name = request.form.get("reviewer_name")
    pet_name = request.form.get('pet_name')
    species = request.form.get('species')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    if request.method == 'POST':
        conn = get_db()
        c = conn.cursor()
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                rating = 5
        except Exception:
            return redirect('/')
        try:
            c.execute('''INSERT INTO Reviews
                      (pet_name, species, reviewer_name, rating, comment)
                      VALUES (?, ?, ?, ?, ?)''',
                      (pet_name, species, reviewer_name, rating, comment))
            conn.commit()
        except sqlite3.IntegrityError:
            c.execute('''UPDATE Orders SET pet_name = ?,
                      species = ?,
                      reviewer_name = ?,
                      rating = ?,
                      comment = ?
                      WHERE reviewer_name = ?''',
                      (pet_name, species, reviewer_name, rating, comment))
            conn.commit()
        conn.close()
        # redirects to thank-you page
        return redirect('/review_thankyou')
    return render_template('add_review.html')


@app.route('/review_thankyou')
def review_thankyou():
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
