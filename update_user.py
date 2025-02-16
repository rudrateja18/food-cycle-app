import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('food_cycle.db')
c = conn.cursor()

# Update the user's role to 'admin'
c.execute("UPDATE users SET role = 'admin' WHERE username = 'rudra'")
conn.commit()
conn.close()

print("User 'rudra' has been updated to admin role successfully.")
