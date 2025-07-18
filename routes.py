from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('pets.db')
    conn.row_factory = sqlite3.Row  # Get results as dictionaries
    return conn

# Homepage - Show all pets
@app.route('/')
def home():
    conn = get_db()
    pets = conn.execute('''
        SELECT p.id, p.name, s.name as species 
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
    ''').fetchall()
    conn.close()
    return render_template('index.html', pets=pets)

# Single pet page
@app.route('/pet/<int:pet_id>')
def pet(pet_id):
    conn = get_db()
    
    # Get pet info
    pet = conn.execute('''
        SELECT p.*, s.name as species, s.description as species_desc
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
        WHERE p.id = ?
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
    return render_template('pet.html', 
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
    return render_template('compare.html', pets=pets)

@app.route('/compare_results', methods=['POST'])
def compare_results():
    pet1_id = request.form['pet1']
    pet2_id = request.form['pet2']
    
    conn = get_db()
    
    # Get pet 1 data
    pet1 = conn.execute('''
        SELECT p.name, s.name as species, 
               GROUP_CONCAT(a.name) as attributes
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
        LEFT JOIN pet_attributes pa ON p.id = pa.pet_id
        LEFT JOIN Attributes a ON pa.attribute_id = a.id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (pet1_id,)).fetchone()
    
    # Get pet 2 data
    pet2 = conn.execute('''
        SELECT p.name, s.name as species, 
               GROUP_CONCAT(a.name) as attributes
        FROM Pets p
        JOIN Species s ON p.species_id = s.id
        LEFT JOIN pet_attributes pa ON p.id = pa.pet_id
        LEFT JOIN Attributes a ON pa.attribute_id = a.id
        WHERE p.id = ?
        GROUP BY p.id
    ''', (pet2_id,)).fetchone()
    
    conn.close()
    return render_template('compare_results.html', pet1=pet1, pet2=pet2)

if __name__ == '__main__':
    app.run(debug=True)