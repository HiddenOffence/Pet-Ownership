from flask import Flask, render_template, request, abort, g
from datetime import datetime 
from math import floor
import sqlite3

app = Flask(__name__)

# Connect database
def get_db():
    db = getattr(g, '_databse', None)
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
    search_term = request.args.get('q', '')
    conn = get_db()
    # Search term - DeepSeek
    if search_term:
        pets = conn.execute('''
            SELECT p.id, p.name, s.name as species 
            FROM Pets p
            JOIN Species s ON p.species_id = s.id
            WHERE p.name LIKE ? OR s.name LIKE ?
        ''', (f'%{search_term}%',f'%{search_term}%')).fetchall()
    else:
        pets = conn.execute('''
            SELECT p.id, p.name, s.name as species 
            FROM Pets p
            JOIN Species s ON p.species_id = s.id
        ''').fetchall()

    conn.close()
    return render_template('home.html', pets=pets, title='HOME', search_term=search_term)

# About page
@app.route('/about_pets')
def about_pets():
    return render_template('about_pets.html', title='ABOUT_PETS', pet=pet, about_pets=about_pets)

# Pets page
@app.route('/pet/<int:pet_id>')
def pet(pet_id):
    conn = get_db()
    
    # Get pet info
    pet = conn.execute('''
        SELECT p.*, s.name as species, s.description as species_desc,
               AVG(r.rating) as avg_rating
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
        LEFT JOIN Reviews r ON p.id = r.pet_id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (pet_id,)).fetchone()
    
    # Get attributes
    attributes = conn.execute('''
        SELECT a.name FROM Attributes a
        JOIN pet_attributes pa ON a.id = pa.attribute_id
        WHERE pa.pet_id = ?
    ''', (pet_id,)).fetchall()
    
    # Get places
    places = conn.execute('''
        SELECT pl.name, pp.price FROM Places pl
        JOIN place_pet pp ON pl.id = pp.place_id
        WHERE pp.pet_id = ?
    ''', (pet_id,)).fetchall()
    
    # Get reviews
    reviews = conn.execute('''
        SELECT reviewer_name, rating, comment FROM Reviews
        WHERE pet_id = ?
    ''', (pet_id,)).fetchall()
    
    conn.close()

    # Convert rating to display
    if pet['avg_rating']:
        full_stars = floor(pet['avg_rating'])
        half_star = 1 if (pet['avg_rating'] - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
    else:
        full_stars = half_star = 0
        empty_stars = 5

    return render_template('pet_profiles.html', 
                         pet=pet, 
                         attributes=attributes,
                         places=places,
                         reviews=reviews)

# Comparison tool
@app.route('/compare')
def compare():
    conn = get_db()
    pets = conn.execute('SELECT id, name FROM Pets').fetchall()
    conn.close()
    return render_template('comparison.html', pets=pets, campare=compare)

# Comparison results
@app.route('/comparison_results', methods=['POST'])
def comparison_results():
    pet1_id = request.form['pet1']
    pet2_id = request.form['pet2']
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get pet 1 data
    pet1 = cursor.execute('''
        SELECT p.name, s.name as species, 
               GROUP_CONCAT(a.name) as attributes
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
        LEFT JOIN pet_attributes pa ON p.id = pa.pet_id
        LEFT JOIN Attributes a ON pa.attribute_id = a.id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (pet1_id,))
    pet1 = cursor.fetchone() 
    
    # Get pet 2 data
    pet2 = cursor.execute('''
        SELECT p.name, s.name as species, 
               GROUP_CONCAT(a.name) as attributes
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
        LEFT JOIN pet_attributes pa ON p.id = pa.pet_id
        LEFT JOIN Attributes a ON pa.attribute_id = a.id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (pet2_id,))
    pet2 = cursor.fetchone()
    
    conn.close()
    return render_template('comparison_results.html', pet1=pet1, pet2=pet2, comparison_results=comparison_results )

# Add Review with validation
@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    reviewer_name = request.form.get('reviewer_name')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    if request.method == 'POST':
        

        # Validation
        errors = []
        if not reviewer_name:
            errors.append('Please enter your name')
        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            errors.append('Please select a valid rating (1-5 stars)')

        if not errors:
            conn = get_db()
            conn.execute('''
            INSERT INTO Reviews (reviewer_name, rating, comment)
            VALUES (?, ?, ?, ?)
        ''', (reviewer_name, int(rating), comment))
        conn.commit()
        conn.close()            

    conn = get_db()
    conn.execute('''
            INSERT INTO Reviews (reviewer_name, rating, comment)
            VALUES (?, ?, ?)
        ''', (reviewer_name, int(rating), comment))
    conn.commit()
    conn.close()
    return render_template('add_reviews.html', 
                        page_title='Reviews', 
                        errors=errors, 
                        add_review=add_review)

# Custom 404 error handler
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)