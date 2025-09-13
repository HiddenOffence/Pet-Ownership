from flask import Flask, render_template, request, redirect, url_for, g
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
    daily_time_minutes INTEGER,
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
    finally:
        conn.close()

    if pet is None:
        return render_template('404.html'), 404

    return render_template('pet.html', pet=pet, reviews=reviews)


# Comparison tool
@app.route('/compare')
def compare():
    conn = get_db()
    try:
        pets = conn.execute('SELECT id, name FROM Pets').fetchall()
    except Exception as e:
        print("Error:", e)
        pets = []

        conn.close()

    return render_template('compare.html', pets=pets)


@app.route('/compare_results')
def compare_results():
    first_id = request.args.get('first')
    second_id = request.args.get('second')

    conn = get_db()
    pets = []

    try:
        # Get first pet
        if first_id:
            p1 = conn.execute('''
                SELECT Pets.*, Species.name AS species
                FROM Pets
                JOIN Species ON Pets.species_id = Species.id
                WHERE Pets.id = ?
            ''', (first_id,)).fetchone()
            if p1:
                pets.append(p1)

        # Get second pet
        if second_id:
            p2 = conn.execute('''
                SELECT Pets.*, Species.name AS species
                FROM Pets
                JOIN Species ON Pets.species_id = Species.id
                WHERE Pets.id = ?
            ''', (second_id,)).fetchone()
            if p2:
                pets.append(p2)

    except Exception as e:
        print("Compare error:", e)
        pets = []
    finally:
        conn.close()

    if len(pets) == 2:
        return render_template('comparison_results.html', pet1=pets[0], pet2=pets[1])
    else:
        return redirect('/compare')


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
            conn.execute('INSERT INTO Reviews (pet_id, reviewer_name, rating, comment) VALUES (?,?,?,?)',
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
        rows = conn.execute('SELECT pets.id, pets.name, species.name AS species_name FROM Pets JOIN Species ON pets.species_id = species.id').fetchall()
        data = [dict(r) for r in rows]
    except Exception:
        data = []
    finally:
        conn.close()
    return {"pets": data}


# Custom 404 error handler
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)