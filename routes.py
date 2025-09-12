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
    adress TEXT);
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
        featured = conn.execute('SELECT pets, species.name AS species_name FROM Pets AS pets JOIN Species AS species ON pets.species_id = species.id ORDER BY pets.cost_setup ASC LIMIT 3').fetchall()
    except Exception:
        featured = []
    conn.close()
    return render_template('home.html', title='HOME', featured=featured)


# Browse pet page
@app.route('/browse')
def browse():
    search_text = request.args.get('search')
    difficulty_choice = request.args.get('difficulty')

    sql = '''SELECT pets, species.name AS species_name, AVG(reviews.rating) AS avg_rating
    FROM Pets AS pets
    JOIN Species AS species ON pets.species_id = species.id
    LEFT JOIN Reviews AS reviews ON reviews.pet_id = pets.id
    '''
    filters = []
    params = []

    if search_text is not None and search_text.strip() != "":
        filters.append('(pets.name LIKE ? OR species.name LIKE ? OR pets.temperament LIKE ?)')
        term = f'%{search_text.strip()}%'
        params.extend([term, term, term])

    if difficulty_choice is not None and difficulty_choice != "":
        # try/except used to avoid crash if it's not a number
        try:
            diff_num = int(difficulty_choice)
            filters.append('species.general_difficulty = ?')
            params.append(diff_num)
        except:
            pass

    if filters:
        sql += ' WHERE ' + ' AND '.join(filters)

    sql += ' GROUP BY pets.id ORDER BY pets.cost_setup ASC;'

    conn = get_db()
    try:
        pets = conn.execute(sql, params).fetchall()
    except Exception:
        pets = []
    conn.close()

    return render_template('browse.html', pets=pets, search=search_text)


# About page
@app.route('/about_pets')
def about_pets():
    return render_template('about_pets.html', title='ABOUT_PETS', pet=pet, about_pets=about_pets)


# Pets profile page
@app.route('/pet/<pet_name>')
def pet_profile(pet_name):
    conn = get_db()
    try:
        pet = conn.execute('''
            SELECT pets.id, species.name AS species_name, species.typical_lifespan, species.general_difficulty
            FROM Pets AS pets JOIN Species AS species ON pets.species_id = species.id
            WHERE pets.id = ?
        ''', (pet_name,)).fetchone()

        reviews = conn.execute('SELECT * FROM Reviews WHERE pet_id = ? ORDER BY created_at DESC', (pet_name,)).fetchall()
        # calculate average rating safely
        avg = conn.execute('SELECT AVG(rating) as avg_rating FROM Reviews WHERE pet_id = ?', (pet_name,)).fetchone()
        avg_rating = round(avg["avg_rating"], 1) if avg["avg_rating"] is not None else None
    except Exception:
        conn.close()
        return render_template('404.html'), 404
    conn.close()

    if pet is None:
        return render_template('404.html'), 404

    return render_template('pet.html', pet=pet, reviews=reviews, avg_rating=avg_rating)


# Comparison tool
@app.route('/compare')
def compare():
    first_id = request.args.get('first')
    second_id = request.args.get('second')
    conn = get_db()
    try:
        pets = []
        # get first if provided
        if first_id is not None and first_id != "":
            try:
                p1 = conn.execute('SELECT pets.*, species.name as species_name FROM Pets pets JOIN Species species ON pets.species_id = species.id WHERE pets.id = ?', (int(first_id),)).fetchone()
                if p1:
                    pets.append(p1)
            except:
                pass
        if second_id is not None and second_id != "":
            try:
                p2 = conn.execute('SELECT pets.*, species.name as species_name FROM Pets pets JOIN Species species ON pets.species_id = species.id WHERE pets.id = ?', (int(second_id),)).fetchone()
                if p2:
                    pets.append(p2)
            except:
                pass

        # fallback: first two pets
        if len(pets) < 2:
            pets = conn.execute('SELECT pets.*, species.name as species_name FROM Pets pets JOIN Species species ON pets.species_id = species.id LIMIT 2').fetchall()
    except Exception:
        pets = []
    finally:
        conn.close()

    return render_template('compare.html', pets=pets)


# Add Review with validation
@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    pet_name = request.form.get('pet_name')
    reviewer_name = request.form.get('reviewer_name') or "Anonymous"
    rating = request.form.get('rating') or "5"
    comment = request.form.get('comment') or ""

        # validate pet_id and rating using try/except so app doesn't crash
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            rating = 5
    except:
        return redirect(url_for('home'))

    conn = get_db()
    try:
        conn.execute('INSERT INTO Reviews (pet_name, reviewer_name, rating, comment) VALUES (?,?,?,?)', (pet_name, reviewer_name, rating, comment))
        conn.commit()
    except Exception:
        # if insert fails, don't crash - redirect to pet page
        conn.rollback()

        conn.close()

        return redirect(url_for('pet_profile', pet_name=pet_name))


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