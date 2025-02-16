import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import traceback


# Create Flask app
app = Flask(__name__)

# Enable session management
app.secret_key = 'your_secret_key_here'  # Change this for production

# Initialize the database
def init_db():
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        # Create donations table
        c.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                food_type TEXT NOT NULL,
                food_category TEXT NOT NULL,
                quantity TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                pickup_time TEXT,
                pickup_date TEXT,
                food_received TEXT,
                admin_feedback TEXT,
                address TEXT NOT NULL,
                contact TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Debug: Print table structure
        c.execute("PRAGMA table_info(donations)")
        columns = c.fetchall()
        print("\nDonations table structure:")
        for col in columns:
            print(col)
        
        # Check if ngo_requests table exists
        c.execute('''
            CREATE TABLE IF NOT EXISTS ngo_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ngo_id INTEGER,
                donation_id INTEGER,
                food_type TEXT,
                food_category TEXT,
                quantity TEXT,
                description TEXT,
                status TEXT DEFAULT 'Pending',
                delivery_address TEXT,
                contact TEXT,
                delivery_date TEXT,
                delivery_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ngo_id) REFERENCES users(id),
                FOREIGN KEY (donation_id) REFERENCES donations(id)
            )
        ''')
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        traceback.print_exc()
    finally:
        conn.close()

def create_tables():
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()

    # Add food_received column to donations table if it doesn't exist
    try:
        c.execute('''ALTER TABLE donations ADD COLUMN food_received TEXT''')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Add contact column to donations table if it doesn't exist
    try:
        c.execute('''ALTER TABLE donations ADD COLUMN contact TEXT''')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.close()

# Initialize database
init_db()

# Call this function when the app starts
create_tables()

def create_ngo_requests_table():
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS ngo_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ngo_id INTEGER,
                donation_id INTEGER,
                delivery_address TEXT,
                contact TEXT,
                status TEXT DEFAULT 'Pending',
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ngo_id) REFERENCES users(id),
                FOREIGN KEY (donation_id) REFERENCES donations(id)
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()

# Call this once when starting your app
create_ngo_requests_table()

@app.context_processor
def inject_functions():
    return dict(is_logged_in=is_logged_in)

# Home page
@app.route('/')
def home():
    if 'user_id' in session:
        if session['role'] == 'donor':
            return redirect(url_for('donor'))
        elif session['role'] == 'ngo':
            return redirect(url_for('ngo'))  # Changed from ngo_dashboard to ngo
        elif session['role'] == 'admin':
            return redirect(url_for('admin'))
    return render_template('home.html')

# Register page
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                      (username, hashed_password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists!"
        conn.close()
        if role == 'ngo':
            return redirect(url_for('ngo_dashboard'))
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        
        try:
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = c.fetchone()
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                
                if user[3] == 'donor':
                    return redirect(url_for('donor'))
                elif user[3] == 'ngo':
                    return redirect(url_for('ngo'))  # Changed from ngo_dashboard to ngo
                elif user[3] == 'admin':
                    return redirect(url_for('admin'))
            else:
                flash('Invalid username or password')
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login')
        finally:
            conn.close()
    
    return render_template('login.html')

# Logout page
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def is_logged_in():
    return 'user_id' in session

# Donor Dashboard
@app.route('/donor')
def donor():
    if 'user_id' not in session or session['role'] != 'donor':
        return redirect(url_for('login'))
    return render_template('donor.html')

# New Donation for Donor
@app.route('/new_donation', methods=['GET', 'POST'])
def new_donation():
    if request.method == 'POST':
        food_category = request.form['food_category']
        quantity = request.form['quantity']
        description = request.form['description']
        pickup_address = request.form['pickup_address']
        contact = request.form['contact']
        
        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        c.execute('INSERT INTO donations (food_category, quantity, description, pickup_address, status, contact, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (food_category, quantity, description, pickup_address, 'Pending', contact, session['user_id']))
        conn.commit()
        conn.close()
        
        return redirect(url_for('thank_you'))
    return render_template('new_donation.html')

# Thank you page route
@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

# Donor History Page
@app.route('/donor_history')
def donor_history():
    if not is_logged_in() or session.get('role') != 'donor':
        return redirect(url_for('login'))

    donor_id = session['user_id']
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()

    c.execute('''
        SELECT 
            id,
            food_category,
            quantity,
            description,
            pickup_address,
            status,
            phone_number,
            pickup_time,
            pickup_date,
            admin_feedback,
            food_received
        FROM donations 
        WHERE user_id = ?
        ORDER BY id DESC
    ''', (donor_id,))
    
    donations = c.fetchall()
    conn.close()

    return render_template('donor_history.html', donations=donations)

@app.route('/ngo')
def ngo():
    if 'user_id' not in session or session['role'] != 'ngo':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        print("\n=== NGO DASHBOARD DEBUG ===")
        
        # Removed food_type from the query
        c.execute('''
            SELECT 
                d.id,
                d.food_category,
                d.quantity,
                d.description,
                d.status
            FROM donations d
            WHERE d.status = 'Accepted'
            AND NOT EXISTS (
                SELECT 1 
                FROM ngo_requests nr 
                WHERE nr.donation_id = d.id 
                AND nr.status != 'Declined'
            )
            ORDER BY d.id DESC
        ''')
        
        donations = c.fetchall()
        print(f"\nAvailable donations: {len(donations)}")
        for don in donations:
            print(f"\nDonation ID: {don[0]}")
            print(f"Category: {don[1]}")
            print(f"Quantity: {don[2]}")
            print(f"Description: {don[3]}")
            
    except Exception as e:
        print(f"NGO Dashboard Error: {str(e)}")
        donations = []
    finally:
        conn.close()
        
    return render_template('ngo.html', donations=donations)

@app.route('/accept_donor/<int:donation_id>')
def accept_donor(donation_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        # Print current status
        c.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
        donation = c.fetchone()
        print("Before accepting - Donation:", donation)
        
        # Update the status
        c.execute('''
            UPDATE donations 
            SET status = 'accepted'  # Using lowercase to match existing flow
            WHERE id = ?
        ''', (donation_id,))
        
        conn.commit()
        
        # Verify the update
        c.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
        updated = c.fetchone()
        print("After accepting - Donation:", updated)
        
    except Exception as e:
        print(f"Error accepting donation: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
    
    return redirect(url_for('admin_donors'))

@app.route('/request_donation/<int:donation_id>', methods=['POST'])
def request_donation(donation_id):
    if 'user_id' not in session or session['role'] != 'ngo':
        return redirect(url_for('login'))
    
    delivery_address = request.form.get('delivery_address')
    contact = request.form.get('contact')

    print(f"\n=== REQUEST DONATION DEBUG ===")
    print(f"NGO ID: {session['user_id']}")
    print(f"Donation ID: {donation_id}")
    print(f"Address: {delivery_address}")
    print(f"Contact: {contact}")

    if not delivery_address or not contact:
        flash('Delivery address and contact are required!')
        return redirect(url_for('ngo'))

    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        # Check if donation exists and is available
        c.execute('SELECT * FROM donations WHERE id = ? AND status = "Accepted"', (donation_id,))
        donation = c.fetchone()
        print(f"Found donation: {donation}")
        
        if donation:
            # Insert request
            c.execute('''
                INSERT INTO ngo_requests (
                    ngo_id,
                    donation_id,
                    status,
                    delivery_address,
                    contact
                ) VALUES (?, ?, "Pending", ?, ?)
            ''', (
                session['user_id'],
                donation_id,
                delivery_address,
                contact
            ))
            
            request_id = c.lastrowid
            print(f"Created request ID: {request_id}")
            
            conn.commit()
            flash('Request submitted successfully!')
        else:
            flash('This donation is no longer available.')
            print("Donation not available")
            
    except Exception as e:
        print(f"Request Error: {str(e)}")
        flash('Error submitting request.')
        conn.rollback()
    finally:
        conn.close()
    
    return redirect(url_for('ngo_history'))

@app.route('/ngo_history')
def ngo_history():
    if 'user_id' not in session or session['role'] != 'ngo':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        print("\n=== NGO HISTORY DEBUG ===")
        c.execute('''
            SELECT 
                nr.id,
                nr.donation_id,
                nr.status,
                nr.delivery_address,
                nr.contact,
                nr.delivery_date,
                nr.delivery_time,
                d.food_category,
                d.quantity,
                d.description,
                d.status as donation_status
            FROM ngo_requests nr
            JOIN donations d ON nr.donation_id = d.id
            WHERE nr.ngo_id = ?
            ORDER BY nr.id DESC
        ''', (session['user_id'],))
        
        requests = c.fetchall()
        print(f"Found {len(requests)} requests")
        
        if requests:
            print("\nSample request:")
            print(f"- ID: {requests[0][0]}")
            print(f"- Status: {requests[0][2]}")
            print(f"- Delivery Date: {requests[0][5]}")
            print(f"- Delivery Time: {requests[0][6]}")
        
    except Exception as e:
        print(f"History error: {str(e)}")
        requests = []
    finally:
        conn.close()
        
    return render_template('ngo_history.html', requests=requests)

# Admin Dashboard
@app.route('/admin')
def admin():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    # Get donor donations with user information
    c.execute('''
        SELECT d.id, d.user_id, d.food_category, d.quantity, d.description, 
               d.pickup_address, d.status, d.contact, d.pickup_time, d.pickup_date, 
               d.admin_feedback, d.food_received, u.username 
        FROM donations d 
        JOIN users u ON d.user_id = u.id 
        WHERE u.role = 'donor'
        ORDER BY d.id DESC
    ''')
    donor_donations = c.fetchall()
    print("Fetched donor donations:", donor_donations)
    
    # Get NGO requests with all necessary details
    c.execute('''
        SELECT 
            nr.id,
            nr.ngo_id,
            nr.donation_id,
            nr.delivery_address,
            nr.contact,
            nr.status,
            nr.delivery_time,
            nr.delivery_date,
            nr.admin_feedback,
            nr.food_delivered,
            u.username as ngo_name,
            d.food_category,
            d.quantity,
            d.description
        FROM ngo_requests nr
        JOIN users u ON nr.ngo_id = u.id
        JOIN donations d ON nr.donation_id = d.id
        ORDER BY nr.id DESC
    ''')
    ngo_requests = c.fetchall()
    print("NGO Requests:", ngo_requests)  # Debug print
    
    # Initialize status dictionaries
    donor_status = {
        'pending': [],
        'accepted': [],
        'completed': [],
        'declined': []
    }
    
    # Categorize donations
    for donation in donor_donations:
        status = donation[6]  # status is at index 6
        print(f"Processing donation {donation[0]} with status: {status}")
        
        if status:
            status = status.lower().strip()
            if status in donor_status:
                donor_status[status].append(donation)
                print(f"Added donation {donation[0]} to {status}")
    
    # Print counts for debugging
    for status, donations in donor_status.items():
        print(f"{status.capitalize()} donations count: {len(donations)}")
    
    ngo_status = {
        'pending': [],
        'accepted': [],
        'completed': [],
        'declined': []
    }
    
    for request in ngo_requests:
        status = request[5]  # status is at index 5
        print(f"NGO Request {request[0]} status: {status}")  # Debug print
        
        if status:
            status = status.lower().strip()
            if status in ngo_status:
                ngo_status[status].append(request)
                print(f"Added request to {status}")  # Debug print
    
    # Print counts for debugging
    for status, requests in ngo_status.items():
        print(f"NGO {status} requests count: {len(requests)}")
    
    conn.close()
    return render_template('admin.html', 
                         donor_status=donor_status,
                         ngo_status=ngo_status)

# Admin Donor Management
@app.route('/admin_donors')
def admin_donors():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        # Get all donor donations
        c.execute('''
            SELECT 
                d.id,
                u.username,
                d.food_category,
                d.quantity,
                d.description,
                d.pickup_address,
                d.status,
                d.pickup_time,
                d.pickup_date,
                d.food_received,
                d.admin_feedback,
                d.contact
            FROM donations d
            JOIN users u ON d.user_id = u.id
            WHERE u.role = 'donor'
            ORDER BY d.id DESC
        ''')
        
        donations = c.fetchall()
        
        # Categorize donations
        donor_status = {
            'pending': [],      # New donations waiting for admin approval
            'accepted': [],     # Donations accepted by admin with pickup details
            'completed_declined': []  # Donations either completed or declined
        }
        
        for donation in donations:
            status = donation[6].lower() if donation[6] else 'pending'
            
            if status == 'pending':
                donor_status['pending'].append(donation)
            elif status == 'accepted':
                donor_status['accepted'].append(donation)
            else:  # completed or declined
                donor_status['completed_declined'].append(donation)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        donor_status = {'pending': [], 'accepted': [], 'completed_declined': []}
    finally:
        conn.close()
    
    return render_template('admin_donors.html', donor_status=donor_status)

@app.route('/admin_ngos')
def admin_ngos():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        print("\n=== DEBUG: Fetching NGO Requests ===")

        # Added delivery_date and delivery_time to the query
        c.execute('''
            SELECT 
                nr.id,
                nr.ngo_id,
                nr.donation_id,
                nr.status,
                nr.delivery_address,
                nr.contact,
                u.username as ngo_name,
                d.food_category,
                d.quantity,
                d.description,
                d.status as donation_status,
                nr.delivery_date,
                nr.delivery_time
            FROM ngo_requests nr
            JOIN users u ON nr.ngo_id = u.id
            JOIN donations d ON nr.donation_id = d.id
            ORDER BY 
                CASE nr.status
                    WHEN 'Pending' THEN 1
                    WHEN 'Accepted' THEN 2
                    ELSE 3
                END,
                nr.id DESC
        ''')
        
        requests = c.fetchall()

        # Debug: Print fetched data
        print(f"\nTotal requests found: {len(requests)}")
        for req in requests:
            print(f"\nRequest ID: {req[0]}")
            print(f"- NGO: {req[6]}")  # username
            print(f"- Status: {req[3]}")  # request status
            print(f"- Category: {req[7]}")  # food_category
            print(f"- Quantity: {req[8]}")  # quantity
            print(f"- Description: {req[9]}")  # description
            print(f"- Address: {req[4]}")  # delivery_address
            print(f"- Contact: {req[5]}")  # contact

        # Categorize requests
        ngo_status = {'pending': [], 'accepted': [], 'completed_declined': []}
        
        for req in requests:
            status = req[3].lower() if req[3] else 'pending'  # Status at index 3
            if status == 'pending':
                ngo_status['pending'].append(req)
            elif status == 'accepted':
                ngo_status['accepted'].append(req)
            else:
                ngo_status['completed_declined'].append(req)
        
        print(f"\nRequest Counts:")
        print(f"- Pending: {len(ngo_status['pending'])}")
        print(f"- Accepted: {len(ngo_status['accepted'])}")
        print(f"- Completed/Declined: {len(ngo_status['completed_declined'])}")

    except Exception as e:
        print(f"\nError in admin_ngos: {str(e)}")
        print("Exception details:", e.__class__.__name__)
        ngo_status = {'pending': [], 'accepted': [], 'completed_declined': []}
    finally:
        conn.close()
        
    return render_template('admin_ngos.html', ngo_status=ngo_status)

# Update Donor Donation Status
@app.route('/update_donation/<int:donation_id>', methods=['POST'])
def update_donation(donation_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        if 'status' in request.form:  # From Pending section
            status = request.form.get('status')
            pickup_time = request.form.get('pickup_time')
            pickup_date = request.form.get('pickup_date')
            
            # Update based on status choice
            c.execute('''
                UPDATE donations 
                SET status = ?,
                    pickup_time = ?,
                    pickup_date = ?
                WHERE id = ?
            ''', (status, pickup_time, pickup_date, donation_id))
            
            print(f"Updated donation {donation_id} to {status}")
            
        elif 'food_received' in request.form:  # From Accepted section
            food_received = request.form.get('food_received')
            admin_feedback = request.form.get('admin_feedback')
            status = 'Completed' if food_received == 'Yes' else 'Declined'
            
            c.execute('''
                UPDATE donations 
                SET status = ?,
                    food_received = ?,
                    admin_feedback = ?
                WHERE id = ?
            ''', (status, food_received, admin_feedback, donation_id))
        
        conn.commit()
        flash('Status updated successfully!')
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating donation: {str(e)}")
        flash('Error updating status.')
    finally:
        conn.close()
    
    return redirect(url_for('admin_donors'))

# Update NGO Request Status
@app.route('/update_ngo_request/<int:request_id>', methods=['POST'])
def update_ngo_request(request_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    new_status = request.form.get('status')
    delivery_date = request.form.get('delivery_date')
    delivery_time = request.form.get('delivery_time')
    
    print(f"\n=== UPDATING REQUEST {request_id} ===")
    print(f"New Status: {new_status}")
    print(f"Delivery Date: {delivery_date}")
    print(f"Delivery Time: {delivery_time}")
    
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()

    try:
        # Get current request details for logging
        c.execute('SELECT * FROM ngo_requests WHERE id = ?', (request_id,))
        current_request = c.fetchone()
        print(f"Current request: {current_request}")
        
        # Update the status and delivery details
        c.execute('''
            UPDATE ngo_requests 
            SET status = ?,
                delivery_date = ?,
                delivery_time = ?
            WHERE id = ?
        ''', (new_status, delivery_date, delivery_time, request_id))
        
        # Verify the update
        c.execute('SELECT * FROM ngo_requests WHERE id = ?', (request_id,))
        updated_request = c.fetchone()
        print(f"Updated request: {updated_request}")
        
        conn.commit()
        flash(f"Request updated with status: {new_status}, delivery on {delivery_date} at {delivery_time}")
        
    except Exception as e:
        print(f"Update NGO Request Error: {str(e)}")
        print("Exception details:", e.__class__.__name__)
        flash("Error updating request status.")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('admin_ngos'))

@app.route('/submit_donation', methods=['POST'])
def submit_donation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get form data
        data = {
            'user_id': session['user_id'],
            'food_type': request.form.get('food_type'),
            'food_category': request.form.get('food_category'),
            'quantity': request.form.get('quantity'),
            'description': request.form.get('description'),
            'address': request.form.get('address'),
            'contact': request.form.get('contact'),
            'status': 'Pending'
        }
        
        # Debug: Print submission data
        print("\nSubmitting donation:")
        print(data)
        
        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        
        # Insert donation
        c.execute('''
            INSERT INTO donations (
                user_id, food_type, food_category, quantity, 
                description, status, address, contact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['user_id'], data['food_type'], data['food_category'],
            data['quantity'], data['description'], data['status'],
            data['address'], data['contact']
        ))
        
        # Get the ID of the inserted donation
        donation_id = c.lastrowid
        print(f"Inserted donation ID: {donation_id}")
        
        # Verify the insertion
        c.execute('SELECT * FROM donations WHERE id = ?', (donation_id,))
        new_donation = c.fetchone()
        print(f"Verified new donation: {new_donation}")
        
        conn.commit()
        flash('Donation submitted successfully!')
        
    except Exception as e:
        print(f"Error submitting donation: {str(e)}")
        traceback.print_exc()
        flash('Error submitting donation.')
        return redirect(url_for('donor'))
    finally:
        conn.close()
    
    return redirect(url_for('donor_history'))

@app.route('/debug_ngo_requests')
def debug_ngo_requests():
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM ngo_requests")
    requests = c.fetchall()
    
    conn.close()
    
    if requests:
        return jsonify(requests)  # Return JSON response
    else:
        return "No NGO requests found."

@app.route('/submit_ngo_request', methods=['POST'])
def submit_ngo_request():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        food_type = request.form.get('food_type')
        food_category = request.form.get('food_category')
        quantity = request.form.get('quantity')
        description = request.form.get('description')
        address = request.form.get('address')
        contact = request.form.get('contact')
        
        conn = sqlite3.connect('food_cycle.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO ngo_requests 
            (ngo_id, food_type, food_category, quantity, description, status, address, contact) 
            VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)
        ''', (session['user_id'], food_type, food_category, quantity, description, address, contact))
        
        conn.commit()
        conn.close()
        
        flash('Request submitted successfully!')
        return redirect(url_for('ngo_history'))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Error submitting request.')
        return redirect(url_for('ngo_dashboard'))

# Add this temporary debug route to check database
@app.route('/debug_db')
def debug_db():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        # Check donations table structure
        c.execute("PRAGMA table_info(donations)")
        donations_structure = c.fetchall()
        print("\nDonations table structure:", donations_structure)
        
        # Check all donations
        c.execute("SELECT * FROM donations")
        all_donations = c.fetchall()
        print("\nAll donations:", all_donations)
        
        # Check accepted donations specifically
        c.execute("SELECT * FROM donations WHERE status = 'accepted' OR status = 'Accepted'")
        accepted_donations = c.fetchall()
        print("\nAccepted donations:", accepted_donations)
        
        # Check if ngo_requests table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ngo_requests'")
        ngo_table_exists = c.fetchone()
        print("\nNGO requests table exists:", bool(ngo_table_exists))
        
        if ngo_table_exists:
            c.execute("SELECT * FROM ngo_requests")
            ngo_requests = c.fetchall()
            print("\nNGO requests:", ngo_requests)
            
    except Exception as e:
        print(f"Debug error: {str(e)}")
    finally:
        conn.close()
    
    return "Check console for debug output"

@app.route('/debug_requests')
def debug_requests():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('food_cycle.db')
    c = conn.cursor()
    
    try:
        print("\n=== DATABASE DEBUG ===")
        
        # Check ngo_requests table
        c.execute("SELECT * FROM ngo_requests")
        requests = c.fetchall()
        print(f"\nNGO Requests found: {len(requests)}")
        for req in requests:
            print(f"\nRequest ID: {req[0]}")
            print(f"NGO ID: {req[1]}")
            print(f"Donation ID: {req[2]}")
            print(f"Status: {req[3]}")
            
        # Check related donations
        c.execute('''
            SELECT d.id, d.food_type, d.status, d.user_id
            FROM donations d
            WHERE d.status = 'Accepted'
        ''')
        donations = c.fetchall()
        print(f"\nAccepted Donations found: {len(donations)}")
        for don in donations:
            print(f"\nDonation ID: {don[0]}")
            print(f"Food Type: {don[1]}")
            print(f"Status: {don[2]}")
            
        # Check users table
        c.execute("SELECT id, username, role FROM users WHERE role = 'ngo'")
        ngos = c.fetchall()
        print(f"\nNGOs found: {len(ngos)}")
        for ngo in ngos:
            print(f"\nNGO ID: {ngo[0]}")
            print(f"Username: {ngo[1]}")
            
    except Exception as e:
        print(f"Debug error: {str(e)}")
    finally:
        conn.close()
    
    return "Check console for debug output"

if __name__ == "__main__":
    init_db()  # Initialize database on startup
    app.run(debug=True)
