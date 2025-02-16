import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('food_cycle.db')

# Create a cursor object to interact with the database
cursor = conn.cursor()

# Execute a query to get all donations
cursor.execute('SELECT * FROM donations')

# Fetch all results
donations = cursor.fetchall()

# Print the donations
for donation in donations:
    print(donation)

# Close the database connection
conn.close()
