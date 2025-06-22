from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date
from db_config import connect_db
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "supersecretkey"


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    # Get user info from 'users' table
    cursor.execute("""
        SELECT username, name, age
        FROM users
        WHERE id = %s
    """, (session["user_id"],))
    user = cursor.fetchone()

    # Get user's custom panels from 'custom_panels' table
    cursor.execute("""
        SELECT id, name
        FROM custom_panels
        WHERE user_id = %s
    """, (session["user_id"],))
    custom_panels = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("main1.html", user=user, custom_panels=custom_panels)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/college", methods=["GET", "POST"])
def college():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    entry_date = request.args.get("date", date.today().isoformat())

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        content = request.form.get("content", "")
        # Check if entry exists
        cursor.execute("""
            SELECT id FROM notebook_entries
            WHERE user_id = %s AND section_type = 'college' AND entry_date = %s
        """, (user_id, entry_date))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE notebook_entries
                SET content_html = %s
                WHERE id = %s
            """, (content, existing['id']))
        else:
            cursor.execute("""
                INSERT INTO notebook_entries
                (user_id, section_type, entry_date, content_html)
                VALUES (%s, 'college', %s, %s)
            """, (user_id, entry_date, content))
        connection.commit()

    # Fetch existing content
    cursor.execute("""
        SELECT content_html FROM notebook_entries
        WHERE user_id = %s AND section_type = 'college' AND entry_date = %s
    """, (user_id, entry_date))
    entry = cursor.fetchone()
    content_html = entry['content_html'] if entry else ""

    cursor.close()
    connection.close()

    return render_template("college.html", content=content_html, selected_date=entry_date)



@app.route("/personal", methods=["GET", "POST"])
def personal():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    entry_date = request.args.get("date", date.today().isoformat())

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":
        content = request.form.get("content", "")
        # Check if entry exists
        cursor.execute("""
            SELECT id FROM notebook_entries
            WHERE user_id = %s AND section_type = 'personal' AND entry_date = %s
        """, (user_id, entry_date))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE notebook_entries
                SET content_html = %s
                WHERE id = %s
            """, (content, existing['id']))
        else:
            cursor.execute("""
                INSERT INTO notebook_entries
                (user_id, section_type, entry_date, content_html)
                VALUES (%s, 'personal', %s, %s)
            """, (user_id, entry_date, content))
        connection.commit()

    # Fetch saved content
    cursor.execute("""
        SELECT content_html FROM notebook_entries
        WHERE user_id = %s AND section_type = 'personal' AND entry_date = %s
    """, (user_id, entry_date))
    entry = cursor.fetchone()
    content_html = entry['content_html'] if entry else ""

    cursor.close()
    connection.close()

    return render_template("personal.html", content=content_html, selected_date=entry_date)


@app.route("/watchlist", methods=["GET", "POST"])
def watchlist():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = connect_db()
    cursor = connection.cursor(dictionary=True)

    # Handle adding new items
    if request.method == "POST" and "title" in request.form:
        title = request.form["title"]
        category = request.form["category"]
        season = request.form["season"]
        cursor.execute("""
            INSERT INTO watchlist (user_id, title, category, season, status)
            VALUES (%s, %s, %s, %s, 'planning')
        """, (session["user_id"], title, category, season))
        connection.commit()

    # Handle status filter from dropdown
    selected_filter = request.args.get("status", "all")

    if selected_filter == "watched":
        cursor.execute("SELECT * FROM watchlist WHERE user_id = %s AND status = 'watched'", (session["user_id"],))
    elif selected_filter == "planning":
        cursor.execute("SELECT * FROM watchlist WHERE user_id = %s AND status = 'planning'", (session["user_id"],))
    else:
        cursor.execute("SELECT * FROM watchlist WHERE user_id = %s", (session["user_id"],))

    items = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("watchlist.html", items=items, selected_filter=selected_filter)




@app.route("/toggle_watch_status/<int:item_id>", methods=["POST"])
def toggle_watch_status(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = connect_db()
    cursor = connection.cursor()

    # Fetch current status
    cursor.execute("SELECT status FROM watchlist WHERE id = %s AND user_id = %s", (item_id, session["user_id"]))
    current = cursor.fetchone()

    if current:
        new_status = 'planning' if current[0] == 'watched' else 'watched'
        cursor.execute("UPDATE watchlist SET status = %s WHERE id = %s", (new_status, item_id))
        connection.commit()

    connection.close()
    return redirect(url_for("watchlist"))

@app.route("/edit_watch/<int:item_id>", methods=["POST"])
def edit_watch(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form["title"]
    category = request.form["category"]
    season = request.form["season"]

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE watchlist
        SET title = %s, category = %s, season = %s
        WHERE id = %s AND user_id = %s
    """, (title, category, season, item_id, session["user_id"]))
    connection.commit()
    connection.close()

    return redirect(url_for("watchlist"))

@app.route("/delete_watch/<int:item_id>", methods=["POST"])
def delete_watch(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM watchlist WHERE id = %s AND user_id = %s", (item_id, session["user_id"]))
    connection.commit()
    connection.close()

    return redirect(url_for("watchlist"))




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        age = request.form["age"]

        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return render_template("register.html", error="Username already taken")

        # Hash the password
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user
        cursor.execute("INSERT INTO users (username, password_hash, name, age) VALUES (%s, %s, %s, %s)",
                       (username, password_hash, name, age))
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and bcrypt.check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            session["age"] = user["age"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/")
def home():
    return render_template("home.html")


@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM tasks WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()

    cursor.execute("SELECT * FROM timetable WHERE user_id = %s", (user_id,))
    classes = cursor.fetchall()

    cursor.execute("SELECT * FROM watchlist WHERE user_id = %s", (user_id,))
    watchlist = cursor.fetchall()


    connection.close()

    return render_template('main.html', tasks=tasks, classes=classes, username=session.get('username'))



@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form['content']
    date = request.form['date']
    time = request.form['time']
    user_id = session['user_id']

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO tasks (user_id, content, date, time, is_habit, is_checked) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, content, date, time, False, False)
    )
    connection.commit()
    connection.close()

    return redirect(url_for('main'))


@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    connection.commit()
    connection.close()

    return redirect(url_for('main'))


@app.route('/set_habit/<int:task_id>', methods=['POST'])
def set_habit(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE tasks SET is_habit = TRUE WHERE id = %s AND user_id = %s",
        (task_id, session['user_id'])
    )
    connection.commit()
    connection.close()

    return redirect(url_for('main'))


@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form['content']
    date = request.form['date']
    time = request.form['time']

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE tasks SET content=%s, date=%s, time=%s WHERE id=%s AND user_id=%s",
        (content, date, time, task_id, session['user_id'])
    )
    connection.commit()
    connection.close()

    return redirect(url_for('main'))


@app.route('/toggle_check/<int:task_id>', methods=['POST'])
def toggle_check(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    is_checked = request.form.get('is_checked') == 'on'

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE tasks SET is_checked = %s WHERE id = %s AND user_id = %s",
        (is_checked, task_id, session['user_id'])
    )
    connection.commit()
    connection.close()

    return '', 204  # Return no content for async request


@app.route('/add_class', methods=['POST'])
def add_class():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    subject = request.form['subject']
    day = request.form['day']
    start_time = request.form['start_time']
    end_time = request.form['end_time']

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO timetable (user_id, subject, day, start_time, end_time) VALUES (%s, %s, %s, %s, %s)",
        (session['user_id'], subject, day, start_time, end_time)
    )
    connection.commit()
    connection.close()
    return redirect(url_for('main'))


@app.route('/add_watch', methods=['POST'])
def add_watch():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    media_type = request.form['type']
    status = request.form['status']

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO watchlist (user_id, title, type, status) VALUES (%s, %s, %s, %s)",
        (session['user_id'], title, media_type, status)
    )
    connection.commit()
    connection.close()
    return redirect(url_for('main'))


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    age = request.form['age']

    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET name = %s, age = %s WHERE id = %s", (name, age, session['user_id']))
    connection.commit()
    connection.close()

    return redirect(url_for('main'))


