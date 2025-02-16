import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('food_cycle.db')
c = conn.cursor()

# Fetch all users from the database
c.execute("SELECT * FROM users")
users = c.fetchall()

# Print all users
for user in users:
    print(user)

# Close connection
conn.close()
