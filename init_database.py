import sqlite3
import os


def init_database():
    # Remove existing database to start fresh
    if os.path.exists('pets.db'):
        os.remove('pets.db')

    conn = sqlite3.connect('pets.db')
    c = conn.cursor()

    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS Species (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS Pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        species_id INTEGER,
        lifespan TEXT,
        difficulty INTEGER,
        cost_setup DECIMAL(6,2),
        daily_time_min INTEGER,
        space_required TEXT,
        temperament TEXT,
        notes TEXT,
        FOREIGN KEY (species_id) REFERENCES Species(id)
    )''')

    # Insert sample species
    species = [
        ('Syrian Hamster', 'Solitary, nocturnal rodents native to arid areas of northern Syria and southern Turkey'),
        ('Domestic Guinea Pig', 'Social rodents originating from the Andes region of South America'),
        ('Betta splendens', 'Colorful freshwater fish known for their elaborate fins and territorial behavior'),
        ('Leopard Gecko', 'Ground-dwelling lizards native to the rocky dry grassland regions of Afghanistan, Pakistan, India, and Iran'),
        ('Budgerigar', 'Small, long-tailed parrots native to Australia, commonly known as parakeets')
    ]

    c.executemany('INSERT INTO Species (name, description) VALUES (?, ?)', species)

    # Insert sample pets with complete data
    pets = [
        ('Hamster', 1, '2-3 years', 2, 75.00, 15, '24x12 inch cage', 'Nocturnal, can be nippy if startled', 'Need exercise wheel, chew toys. Not ideal for young children.'),
        ('Guinea Pig', 2, '5-7 years', 3, 150.00, 35, '30x36 inch cage', 'Social, vocal, gentle', 'Need vitamin C supplements, better in pairs, require fresh vegetables daily.'),
        ('Betta Fish', 3, '3-5 years', 2, 80.00, 8, '5-gallon tank', 'Territorial, colorful, interactive', 'Need heated tank (78-80°F), filtered water, cannot be kept with other bettas.'),
        ('Leopard Gecko', 4, '15-20 years', 3, 250.00, 15, '20-gallon tank', 'Docile, nocturnal, handleable', 'Need heated tank with warm and cool areas, eat insects dusted with calcium powder.'),
        ('Parakeet', 5, '5-10 years', 3, 200.00, 40, '18x18x18 inch cage', 'Social, intelligent, can learn to talk', 'Need out-of-cage time, social so better in pairs, require varied diet beyond seeds.')
    ]

    c.executemany('''INSERT INTO Pets (name, species_id, lifespan, difficulty, cost_setup, daily_time_min, space_required, temperament, notes) 
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', pets)

    # Verify the data was inserted correctly
    print("Species in database:")
    for row in c.execute('SELECT * FROM Species'):
        print(row)

    print("\nPets in database:")
    for row in c.execute('SELECT * FROM Pets'):
        print(row)

    conn.commit()
    conn.close()
    print("\nDatabase initialized with sample data!")


if __name__ == '__main__':
    init_database()
