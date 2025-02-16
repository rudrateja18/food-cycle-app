import sqlite3

# Function to add the status column if it doesn't exist
def add_status_column():
    try:
        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        c.execute('''ALTER TABLE donations ADD COLUMN status TEXT DEFAULT 'Pending' ''')
        conn.commit()
        print("Status column added successfully!")
    except sqlite3.OperationalError:
        print("Status column already exists.")
    finally:
        conn.close()

# Function to update donations that have no status
def update_existing_donations():
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    c.execute('''UPDATE donations SET status = 'Pending' WHERE status IS NULL''')
    conn.commit()
    print("Existing donations updated with 'Pending' status.")
    conn.close()

# Run both functions
add_status_column()
update_existing_donations()

