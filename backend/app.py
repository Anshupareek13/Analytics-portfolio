from flask import Flask, render_template, request, redirect, session, flash
import requests
import os
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["analytics_portfolio"]

users_collection = db["users"]
projects_collection = db["projects"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def project_doc_to_tuple(project):
    return (
        str(project.get("_id")),
        project.get("username", ""),
        project.get("title", ""),
        project.get("description", ""),
        project.get("tech", ""),
        project.get("profile_photo", ""),
        project.get("github", "")
    )


def user_profile_tuple(user):
    if not user:
        return None
    return (
        user.get("full_name", ""),
        user.get("role", ""),
        user.get("about", ""),
        user.get("skills", ""),
        user.get("email", ""),
        user.get("linkedin", ""),
        user.get("github_username", "")
    )


def dashboard_user_tuple(user):
    if not user:
        return None
    return (
        user.get("username", ""),
        user.get("email", ""),
        user.get("profile_photo", ""),
        user.get("github_username", "")
    )


def edit_profile_tuple(user):
    if not user:
        return None
    return (
        user.get("username", ""),
        user.get("email", ""),
        user.get("profile_photo", "")
    )


def complete_profile_tuple(user):
    if not user:
        return ("", "", "", "", "", "", "")
    return (
        user.get("full_name", ""),
        user.get("role", ""),
        user.get("about", ""),
        user.get("skills", ""),
        user.get("email", ""),
        user.get("linkedin", ""),
        user.get("github_username", "")
    )


@app.route("/health")
def health():
    return "OK", 200


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

        user = users_collection.find_one({
            "$or": [
                {"username": login_input},
                {"email": login_input}
            ]
        })

        if user and check_password_hash(user.get("password", ""), password):
            session["user"] = user["username"]
            flash("Login successful")
            return redirect("/dashboard")

        flash("Invalid username/email or password")
        return redirect("/")

    return render_template("login.html")


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

        existing_user = users_collection.find_one({
            "$or": [
                {"username": username},
                {"email": email}
            ]
        })

        if existing_user:
            flash("Username or email already exists. Please login.")
            return redirect("/signup")

        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": generate_password_hash(password),
            "full_name": "",
            "role": "",
            "about": "",
            "skills": "",
            "linkedin": "",
            "profile_photo": "",
            "github_username": "",
            "created_at": datetime.utcnow()
        })

        session["user"] = username
        flash("Signup successful")
        return redirect("/dashboard")

    return render_template("signup.html")


@app.route("/about")
def about():
    if "user" not in session:
        return redirect("/")
    return render_template("about.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    username = session["user"]
    project_docs = list(projects_collection.find({"username": username}))
    projects = [project_doc_to_tuple(project) for project in project_docs]

    user_doc = users_collection.find_one({"username": username})
    user = dashboard_user_tuple(user_doc)
    github_username = user[3] if user and user[3] else None

    tech_list = []
    for project in projects:
        if project[4]:
            tech_list.extend([tech.strip() for tech in project[4].split(",") if tech.strip()])

    tech_data = Counter(tech_list)

    return render_template(
        "dashboard.html",
        username=username,
        projects=projects,
        tech_data=tech_data,
        github_username=github_username,
        user=user
    )


@app.route("/add_project", methods=["GET", "POST"])
def add_project():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        tech = request.form.get("tech", "").strip()
        github = request.form.get("github", "").strip()

        projects_collection.insert_one({
            "username": session["user"],
            "title": title,
            "description": description,
            "tech": tech,
            "profile_photo": "",
            "github": github,
            "created_at": datetime.utcnow()
        })

        flash("Project added successfully")
        return redirect("/dashboard")

    return render_template("add_project.html")


@app.route("/delete_project/<project_id>")
def delete_project(project_id):
    if "user" not in session:
        return redirect("/")

    try:
        projects_collection.delete_one({
            "_id": ObjectId(project_id),
            "username": session["user"]
        })
        flash("Project deleted successfully")
    except Exception:
        flash("Invalid project ID")

    return redirect("/dashboard")


@app.route("/portfolio/<username>")
def portfolio(username):
    user_doc = users_collection.find_one({"username": username})
    profile = user_profile_tuple(user_doc)

    project_docs = list(projects_collection.find({"username": username}))
    projects = [project_doc_to_tuple(project) for project in project_docs]

    tech_list = []
    for project in projects:
        if project[4]:
            tech_list.extend([tech.strip() for tech in project[4].split(",") if tech.strip()])

    tech_data = Counter(tech_list)

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

    return render_template(
        "portfolio.html",
        username=username,
        profile=profile,
        projects=projects,
        tech_data=tech_data,
        profile_score=profile_score,
        portfolio_level=portfolio_level
    )


@app.route("/github/<username>")
def github(username):
    username = username.strip()

    if not username:
        return "GitHub username is missing"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "analytics-portfolio-app"
    }

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    profile_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"

    try:
        profile_response = requests.get(profile_url, headers=headers, timeout=15)
        if profile_response.status_code == 404:
            return f"GitHub user '{username}' not found"
        if profile_response.status_code == 403:
            return "GitHub API rate limit exceeded. Try again later."
        if profile_response.status_code != 200:
            return f"GitHub API profile error: {profile_response.status_code}"

        repos_response = requests.get(repos_url, headers=headers, timeout=15)
        if repos_response.status_code == 403:
            return "GitHub API rate limit exceeded. Try again later."
        if repos_response.status_code != 200:
            return f"GitHub repos fetch error: {repos_response.status_code}"

        repos = repos_response.json()

        repo_list = []
        languages = []

        for repo in repos:
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

    except requests.exceptions.RequestException as e:
        return f"GitHub request failed: {str(e)}"
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(url, timeout=15)

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


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "user" not in session:
        return redirect("/")

    old_username = session["user"]

    if request.method == "POST":
        new_username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        profile_photo = request.files.get("profile_photo")

        if not new_username or not email:
            flash("Username and email are required")
            return redirect("/edit_profile")

        existing_user = users_collection.find_one({
            "username": new_username,
            "username": {"$ne": old_username}
        })
        if existing_user:
            flash("Username already taken")
            return redirect("/edit_profile")

        existing_email = users_collection.find_one({
            "email": email,
            "username": {"$ne": old_username}
        })
        if existing_email:
            flash("Email already in use")
            return redirect("/edit_profile")

        update_data = {
            "username": new_username,
            "email": email
        }

        if profile_photo and profile_photo.filename:
            filename = secure_filename(profile_photo.filename)
            filename = f"{new_username}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_photo.save(save_path)
            photo_path = os.path.join("static", "uploads", filename).replace("\\", "/")
            update_data["profile_photo"] = photo_path

        users_collection.update_one({"username": old_username}, {"$set": update_data})
        projects_collection.update_many({"username": old_username}, {"$set": {"username": new_username}})

        session["user"] = new_username
        flash("Profile updated successfully")
        return redirect("/edit_profile")

    user_doc = users_collection.find_one({"username": old_username})
    user = edit_profile_tuple(user_doc)
    return render_template("edit_profile.html", user=user)


@app.route("/complete_profile", methods=["GET", "POST"])
def complete_profile():
    if "user" not in session:
        return redirect("/")

    username = session["user"]

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "").strip()
        about = request.form.get("about", "").strip()
        skills = request.form.get("skills", "").strip()
        email = request.form.get("email", "").strip()
        linkedin = request.form.get("linkedin", "").strip()
        github_username = request.form.get("github_username", "").strip()

        users_collection.update_one(
            {"username": username},
            {"$set": {
                "full_name": full_name,
                "role": role,
                "about": about,
                "skills": skills,
                "email": email,
                "linkedin": linkedin,
                "github_username": github_username
            }}
        )

        flash("Profile updated successfully")
        return redirect("/dashboard")

    user_doc = users_collection.find_one({"username": username})
    user_data = complete_profile_tuple(user_doc)
    return render_template("complete_profile.html", user_data=user_data)


@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "user" not in session:
        return redirect("/")

    username = session["user"]

    # user delete
    users_collection.delete_one({"username": username})

    # user ke sare projects delete
    projects_collection.delete_many({"username": username})

    # session clear
    session.clear()

    flash("Your account has been deleted successfully")
    return redirect("/")



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

        user = users_collection.find_one({"username": session["user"]})
        if not user:
            flash("User not found")
            return redirect("/change_password")

        if not check_password_hash(user.get("password", ""), old_password):
            flash("Old password is incorrect")
            return redirect("/change_password")

        users_collection.update_one(
            {"username": session["user"]},
            {"$set": {"password": generate_password_hash(new_password)}}
        )

        flash("Password changed successfully")
        return redirect("/dashboard")

    return render_template("change_password.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "").strip()

        if not username or not new_password:
            flash("Please fill all fields")
            return redirect("/forgot_password")

        user = users_collection.find_one({"username": username})

        if user:
            users_collection.update_one(
                {"username": username},
                {"$set": {"password": generate_password_hash(new_password)}}
            )
            flash("Password updated successfully. Please login.")
            return redirect("/")
        else:
            flash("Username not found")
            return redirect("/forgot_password")

    return render_template("forgot_password.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully")
    return redirect("/")


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
    combined_text = f"{project_title} {project_description} {project_tech} {domain}".lower()

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        if skill.lower() in combined_text:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    skill_score = int((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0

    bonus = 0
    if project_description and len(project_description.strip()) > 40:
        bonus += 10

    tech_count = len([t.strip() for t in project_tech.split(",") if t.strip()]) if project_tech else 0
    if tech_count >= 3:
        bonus += 10
    elif tech_count >= 2:
        bonus += 5

    final_score = min(skill_score + bonus, 100)

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

    username = session["user"]
    project_docs = list(projects_collection.find({"username": username}))
    projects = [project_doc_to_tuple(project) for project in project_docs]

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
            return render_template(
                "ats.html",
                projects=projects,
                roles=ROLE_SKILLS.keys(),
                result=None,
                selected_project_id=selected_project_id,
                selected_role=selected_role,
                selected_domain=selected_domain
            )

        try:
            project_doc = projects_collection.find_one({
                "_id": ObjectId(selected_project_id),
                "username": username
            })
        except Exception:
            project_doc = None

        if not project_doc:
            flash("Project not found")
        else:
            project = project_doc_to_tuple(project_doc)
            result = analyze_project_for_role(
                project_title=project[2] or "",
                project_description=project[3] or "",
                project_tech=project[4] or "",
                role=selected_role,
                domain=selected_domain
            )
            result["project"] = project

    return render_template(
        "ats.html",
        projects=projects,
        roles=ROLE_SKILLS.keys(),
        result=result,
        selected_project_id=selected_project_id,
        selected_role=selected_role,
        selected_domain=selected_domain
    )


if __name__ == "__main__":
    app.run(debug=True)