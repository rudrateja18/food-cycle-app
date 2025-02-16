import sqlite3

def add_ngo_column():
    try:
        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        c.execute('''ALTER TABLE donations ADD COLUMN ngo_id INTEGER''')  # Add ngo_id column
        conn.commit()
        print("ngo_id column added successfully!")
    except sqlite3.OperationalError:
        print("ngo_id column already exists.")
    finally:
        conn.close()

add_ngo_column()
