from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import requests
import os
import os
from werkzeug.utils import secure_filename
from collections import Counter
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "App is live"

if __name__ == "__main__":
    app.run(debug=True)

app = Flask(__name__)
app.secret_key = "secret"



#Profile Photo
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# -------------------------------
# DATABASE PATH SETUP
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


# -------------------------------
# ABOUT US
# -------------------------------
@app.route("/about")
def about():
    if "user" not in session:
        return redirect("/")
    return render_template("about.html")
# -------------------------------
# DATABASE SETUP
# -------------------------------
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        full_name TEXT,
        role TEXT,
        about TEXT,
        skills TEXT,
        email TEXT,
        linkedin TEXT,
        profile_photo TEXT,
        github_username TEXT
    )
    """)

    # Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        description TEXT,
        tech TEXT,
        profile_photo TEXT,
        github TEXT
    )
    """)

    # Old database ke liye missing columns add karo
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if "full_name" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    if "role" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT")
    if "about" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN about TEXT")
    if "skills" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN skills TEXT")
    if "email" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "linkedin" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN linkedin TEXT")
    if "github_username" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN github_username TEXT")
    if "profile_photo" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")

    conn.commit()
    conn.close()
create_tables()

# -------------------------------
# PASSWORD CHANGE 
# -------------------------------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        old_password = request.form.get("old_password", "").strip()
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not old_password or not new_password or not confirm_password:
            flash("Please fill all fields")
            return redirect("/change_password")

        if new_password != confirm_password:
            flash("New password and confirm password do not match")
            return redirect("/change_password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE username=?",
            (session["user"],)
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            flash("User not found")
            return redirect("/change_password")

        if user[0] != old_password:
            conn.close()
            flash("Old password is incorrect")
            return redirect("/change_password")

        cursor.execute(
            "UPDATE users SET password=? WHERE username=?",
            (new_password, session["user"])
        )
        conn.commit()
        conn.close()

        flash("Password changed successfully")
        return redirect("/dashboard")

    return render_template("change_password.html")

# -------------------------------
# AUTH ROUTES
# -------------------------------
#login route
@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        login_input = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not login_input or not password:
            flash("Please enter username/email and password")
            return redirect("/")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password FROM users WHERE username=? OR email=?",
            (login_input, login_input)
        )
        user = cursor.fetchone()
        conn.close()

        if user and user[1] == password:
            session["user"] = user[0]
            flash("Login successful")
            return redirect("/dashboard")
        else:
            flash("Invalid username/email or password")
            return redirect("/")

    return render_template("login.html")
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        login_input = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not login_input or not password:
            flash("Please enter username/email and password")
            return redirect("/")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password FROM users WHERE username=? OR email=?",
            (login_input, login_input)
        )
        user = cursor.fetchone()
        conn.close()

        if user and user[1] == password:
            session["user"] = user[0]
            flash("Login successful")
            return redirect("/dashboard")
        else:
            flash("Invalid username/email or password")
            return redirect("/")

    return render_template("login.html")
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            flash("Login successful")
            return redirect("/dashboard")
        else:
            flash("Invalid username or password")
            return redirect("/")

    return render_template("login.html")

#signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("All fields are required")
            return redirect("/signup")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? OR email=?",
            (username, email)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("Username or email already exists. Please login.")
            return redirect("/signup")

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        conn.commit()
        conn.close()

        session["user"] = username
        flash("Signup successful")
        return redirect("/dashboard")

    return render_template("signup.html")
    if "user" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password are required")
            return redirect("/signup")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("Username already exists. Please login.")
            return redirect("/signup")

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        # direct login after successful signup
        session["user"] = username
        flash("Signup successful")
        return redirect("/dashboard")

    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM projects WHERE username=?", (session["user"],))
    projects = cursor.fetchall()

    cursor.execute(
        "SELECT username, email, profile_photo, github_username FROM users WHERE username=?",
        (session["user"],)
    )
    user = cursor.fetchone()

    github_username = user[3] if user and user[3] else None

    conn.close()

    tech_list = []
    for project in projects:
        if project[4]:
            tech_list.extend([tech.strip() for tech in project[4].split(",") if tech.strip()])

    tech_data = Counter(tech_list)

    return render_template(
        "dashboard.html",
        username=session["user"],
        projects=projects,
        tech_data=tech_data,
        github_username=github_username,
        user=user
    )
# -------------------------------
# PROJECT ROUTES
# -------------------------------

@app.route("/add_project", methods=["GET", "POST"])
def add_project():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        tech = request.form.get("tech", "").strip()
        github = request.form.get("github", "").strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO projects (username, title, description, tech, github)
        VALUES (?, ?, ?, ?, ?)
        """, (session["user"], title, description, tech, github))

        conn.commit()
        conn.close()

        flash("Project added successfully")
        return redirect("/dashboard")

    return render_template("add_project.html")


# -------------------------------
# PORTFOLIO PAGE
# -------------------------------

@app.route("/portfolio/<username>")
def portfolio(username):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT full_name, role, about, skills, email, linkedin, github_username
        FROM users
        WHERE username=?
    """, (username,))
    profile = cursor.fetchone()

    cursor.execute("SELECT * FROM projects WHERE username=?", (username,))
    projects = cursor.fetchall()

    tech_list = []
    for project in projects:
        if project[4]:
            tech_list.extend([tech.strip() for tech in project[4].split(",") if tech.strip()])

    tech_data = Counter(tech_list)

    # Portfolio score calculation
    profile_score = 0

    total_projects = len(projects)
    unique_tech = len(tech_data)

    if profile:
        full_name = profile[0]
        role = profile[1]
        about = profile[2]
        skills = profile[3]
        email = profile[4]
        linkedin = profile[5]
        github_username = profile[6]
    else:
        full_name = role = about = skills = email = linkedin = github_username = None

    if total_projects >= 1:
        profile_score += 20
    if total_projects >= 3:
        profile_score += 10
    if total_projects >= 5:
        profile_score += 10

    if unique_tech >= 1:
        profile_score += 10
    if unique_tech >= 3:
        profile_score += 10

    filled_fields = 0
    for field in [full_name, role, about, skills, email, linkedin, github_username]:
        if field:
            filled_fields += 1

    profile_score += filled_fields * 4

    if profile_score > 100:
        profile_score = 100

    if profile_score < 40:
        portfolio_level = "Beginner"
    elif profile_score < 60:
        portfolio_level = "Intermediate"
    elif profile_score < 80:
        portfolio_level = "Strong Portfolio"
    else:
        portfolio_level = "Industry Ready"

    conn.close()

    return render_template(
        "portfolio.html",
        username=username,
        profile=profile,
        projects=projects,
        tech_data=tech_data,
        profile_score=profile_score,
        portfolio_level=portfolio_level
    )

# -------------------------------
# GITHUB ANALYTICS
# -------------------------------

@app.route("/github/<username>")
def github(username):
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url)

    if response.status_code != 200:
        return "GitHub user not found or API error"

    repos = response.json()

    repo_list = []
    languages = []

    for repo in repos:
        if isinstance(repo, dict):
            repo_list.append({
                "name": repo.get("name"),
                "url": repo.get("html_url"),
                "language": repo.get("language")
            })

            if repo.get("language"):
                languages.append(repo.get("language"))

    language_data = Counter(languages)

    return render_template(
        "github.html",
        repos=repo_list,
        username=username,
        language_data=language_data
    )


@app.route("/delete_project/<int:id>")
def delete_project(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Sirf current logged-in user ka project delete ho
    cursor.execute("DELETE FROM projects WHERE id=? AND username=?", (id, session["user"]))

    conn.commit()
    conn.close()

    flash("Project deleted successfully")
    return redirect("/dashboard")

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        profile_photo = request.files.get("profile_photo")

        if not new_username or not email:
            conn.close()
            flash("Username and email are required")
            return redirect("/edit_profile")

        old_username = session["user"]

        # username check
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND username!=?",
            (new_username, old_username)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("Username already taken")
            return redirect("/edit_profile")

        # email check
        cursor.execute(
            "SELECT * FROM users WHERE email=? AND username!=?",
            (email, old_username)
        )
        existing_email = cursor.fetchone()

        if existing_email:
            conn.close()
            flash("Email already in use")
            return redirect("/edit_profile")

        photo_path = None

        if profile_photo and profile_photo.filename:
            filename = secure_filename(profile_photo.filename)
            filename = f"{new_username}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_photo.save(save_path)
            photo_path = os.path.join("static", "uploads", filename).replace("\\", "/")

        if photo_path:
            cursor.execute("""
                UPDATE users
                SET username=?, email=?, profile_photo=?
                WHERE username=?
            """, (new_username, email, photo_path, old_username))
        else:
            cursor.execute("""
                UPDATE users
                SET username=?, email=?
                WHERE username=?
            """, (new_username, email, old_username))

        cursor.execute(
            "UPDATE projects SET username=? WHERE username=?",
            (new_username, old_username)
        )

        conn.commit()
        conn.close()

        session["user"] = new_username
        flash("Profile updated successfully")
        return redirect("/edit_profile")

    cursor.execute(
        "SELECT username, email, profile_photo FROM users WHERE username=?",
        (session["user"],)
    )
    user = cursor.fetchone()
    conn.close()

    return render_template("edit_profile.html", user=user)


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "").strip()

        if not username or not new_password:
            flash("Please fill all fields")
            return redirect("/forgot_password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user:
            cursor.execute(
                "UPDATE users SET password=? WHERE username=?",
                (new_password, username)
            )
            conn.commit()
            conn.close()
            flash("Password updated successfully. Please login.")
            return redirect("/")
        else:
            conn.close()
            flash("Username not found")
            return redirect("/forgot_password")

    return render_template("forgot_password.html")


@app.route("/complete_profile", methods=["GET", "POST"])
def complete_profile():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "").strip()
        about = request.form.get("about", "").strip()
        skills = request.form.get("skills", "").strip()
        email = request.form.get("email", "").strip()
        linkedin = request.form.get("linkedin", "").strip()
        github_username = request.form.get("github_username", "").strip()

        cursor.execute("""
            UPDATE users
            SET full_name=?, role=?, about=?, skills=?, email=?, linkedin=?, github_username=?
            WHERE username=?
        """, (full_name, role, about, skills, email, linkedin, github_username, session["user"]))

        conn.commit()
        conn.close()

        flash("Profile updated successfully")
        return redirect("/dashboard")

    cursor.execute("""
        SELECT full_name, role, about, skills, email, linkedin, github_username
        FROM users
        WHERE username=?
    """, (session["user"],))
    user_data = cursor.fetchone()

    conn.close()

    return render_template("complete_profile.html", user_data=user_data)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully")
    return redirect("/")


# -------------------------------
# TRIAL ROUTE FOR TESTING
# -------------------------------
ROLE_SKILLS = {
    "data analyst": ["python", "sql", "excel", "power bi", "pandas", "numpy", "data visualization"],
    "data scientist": ["python", "pandas", "numpy", "machine learning", "statistics", "matplotlib", "sklearn"],
    "machine learning engineer": ["python", "numpy", "pandas", "sklearn", "tensorflow", "pytorch", "ml"],
    "web developer": ["html", "css", "javascript", "flask", "django", "react", "bootstrap"],
    "full stack developer": ["html", "css", "javascript", "flask", "react", "node", "sql", "api"],
    "backend developer": ["python", "flask", "django", "api", "sql", "database", "authentication"],
    "frontend developer": ["html", "css", "javascript", "react", "ui", "responsive design"],
    "android developer": ["java", "kotlin", "android", "firebase", "api"],
    "cloud engineer": ["aws", "docker", "kubernetes", "devops", "linux", "ci/cd"],
}

def analyze_project_for_role(project_title, project_description, project_tech, role, domain):
    role_key = role.lower().strip()
    required_skills = ROLE_SKILLS.get(role_key, [])

    # project text combine
    combined_text = f"{project_title} {project_description} {project_tech} {domain}".lower()

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        if skill.lower() in combined_text:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    if required_skills:
        skill_score = int((len(matched_skills) / len(required_skills)) * 100)
    else:
        skill_score = 0

    # Bonus scoring based on project richness
    bonus = 0

    if project_description and len(project_description.strip()) > 40:
        bonus += 10

    tech_count = len([t.strip() for t in project_tech.split(",") if t.strip()]) if project_tech else 0
    if tech_count >= 3:
        bonus += 10
    elif tech_count >= 2:
        bonus += 5

    final_score = skill_score + bonus
    if final_score > 100:
        final_score = 100

    if final_score >= 80:
        level = "High Level 🚀"
        feedback = "Your project is strongly aligned with this role."
    elif final_score >= 50:
        level = "Medium Level ⚡"
        feedback = "Your project is decent, but it can be improved for better role alignment."
    else:
        level = "Low Level ⚠️"
        feedback = "Your project needs more relevant skills and stronger implementation details."

    return {
        "score": final_score,
        "level": level,
        "feedback": feedback,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "required_skills": required_skills
    }

@app.route("/ats", methods=["GET", "POST"])
def ats():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, description, tech, github FROM projects WHERE username=?", (session["user"],))
    projects = cursor.fetchall()

    result = None
    selected_project_id = None
    selected_role = ""
    selected_domain = ""

    if request.method == "POST":
        selected_project_id = request.form.get("project_id", "").strip()
        selected_role = request.form.get("job_role", "").strip()
        selected_domain = request.form.get("domain", "").strip()

        if not selected_project_id or not selected_role:
            flash("Please select a project and job role")
            conn.close()
            return render_template(
                "ats.html",
                projects=projects,
                roles=ROLE_SKILLS.keys(),
                result=None,
                selected_project_id=selected_project_id,
                selected_role=selected_role,
                selected_domain=selected_domain
            )

        cursor.execute(
            "SELECT id, title, description, tech, github FROM projects WHERE id=? AND username=?",
            (selected_project_id, session["user"])
        )
        project = cursor.fetchone()

        if not project:
            flash("Project not found")
        else:
            result = analyze_project_for_role(
                project_title=project[1] or "",
                project_description=project[2] or "",
                project_tech=project[3] or "",
                role=selected_role,
                domain=selected_domain
            )
            result["project"] = project

    conn.close()

    return render_template(
        "ats.html",
        projects=projects,
        roles=ROLE_SKILLS.keys(),
        result=result,
        selected_project_id=selected_project_id,
        selected_role=selected_role,
        selected_domain=selected_domain
    )

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)