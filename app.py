from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from geopy.distance import geodesic
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = 'supersecretkey'


cloudinary.config(
  cloud_name="dgtaf4krh",
  api_key="781973345294475",
  api_secret="vURcZBmjM3R_SFHmOoG4M6qVfbE"
)


# SQLite DB setup
basedir = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(basedir, 'db'), exist_ok=True)  # Ensure db directory exists
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    issues = db.relationship('Issue', back_populates='user')


class Issue(db.Model):
    __tablename__ = 'issue'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_name = db.Column(db.String(200))  # Human-readable location
    category = db.Column(db.String(50), nullable=False)
    photos = db.Column(db.PickleType)
    anonymous = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Posted')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    flagged_by = db.Column(db.PickleType, default=list)
    is_hidden = db.Column(db.Boolean, default=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='issues')

    flags = db.relationship('Flag', backref='issue', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "category": self.category,
            "photos": self.photos,
            "status": self.status,
            "anonymous": self.anonymous,
            "created_at": self.created_at.isoformat()
        }

class Flag(db.Model):
    __tablename__ = 'flags'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'))

    user = db.relationship("User")

with app.app_context():
    db.create_all()

# ---------------- ROUTES ---------------- #
@app.route('/')
def home():
    return render_template('map.html', username=session.get('username'))


@app.route('/api/issues')
def get_issues():
    user_lat = float(request.args.get('lat'))
    user_lng = float(request.args.get('lng'))
    max_distance_km = float(request.args.get('distance', 5))

    all_issues = Issue.query.filter_by(is_hidden=False).all()

    def within_radius(issue):
        return geodesic((user_lat, user_lng), (issue.latitude, issue.longitude)).km <= max_distance_km

    visible_issues = [issue.to_dict() for issue in all_issues if within_radius(issue)]
    return jsonify(visible_issues)

@app.route('/add_dummy')
def add_dummy():
    test_issue = Issue(
        title="Broken Street Light",
        description="Light not working on 5th Avenue",
        latitude=19.072,
        longitude=72.873,
        location_name="5th Avenue, Mumbai",
        category="Lighting",
        photos=[],
        status="Reported"
    )
    db.session.add(test_issue)
    db.session.commit()
    return "Dummy issue added!"

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))
        location_name = request.form.get("location_name")
        anonymous = request.form.get("anonymous") == "on"

        # Handle photos
        photos = request.files.getlist("photos")
        photo_urls = []

        for photo in photos[:5]:
            if photo and photo.filename != "":
                upload_result = cloudinary.uploader.upload(photo)
                photo_urls.append(upload_result["secure_url"])

        user_id = session.get("user_id")
        if not user_id:
            flash("You must be logged in to report an issue.")
            return redirect(url_for("login"))

        new_issue = Issue(
            title=title,
            description=description,
            category=category,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            photos=photo_urls,
            anonymous=anonymous,
            status="Posted",
            user_id=user_id
        )
        db.session.add(new_issue)
        db.session.commit()
        flash("Issue reported successfully.")
        return redirect(url_for("home"))

    return render_template("report.html")

@app.route('/edit_issue')
def edit_issue():
    return "Issue editing functionality is not implemented yet."

@app.route("/issue/<int:issue_id>")
def view_issue(issue_id):
    issue = db.session.get(Issue, issue_id)  # or: Issue.query.get(issue_id)
    if not issue:
        abort(404)
    return render_template("issue_page.html", issue=issue)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please log in to view your profile.")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user_issues = Issue.query.filter_by(user_id=user.id).order_by(Issue.created_at.desc()).all()

    return render_template('profile.html', user=user, issues=user_issues)


@app.route('/issues')
def view_all_issues():
    issues = Issue.query.filter_by(is_hidden=False).order_by(Issue.created_at.desc()).all()
    return render_template('all_issues.html', issues=issues)

def is_strong_password(password):
    import re
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        errors = {}

        if password != confirm_password:
            errors['password'] = "Passwords do not match."

        if not is_strong_password(password):
            errors['password'] = "Password must be at least 8 characters long and contain a special character, uppercase, lowercase letters, and numbers."

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            errors['username'] = "Username already exists."

        if errors:
            return render_template('register.html', errors=errors, 
                                   username=username, email=email, phone=phone)

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f"Welcome, {username}!")
            if user.email.endswith('@admin.com'):
                return redirect('/admin')
            else:
                return redirect('/')
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user_id' not in session:
        flash("Please log in to access the admin panel.")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user or not user.email.endswith('@admin.com'):
        flash("You do not have permission to access the admin panel.")
        return redirect(url_for('home'))

    issues = Issue.query.all()

    # 🧠 Status Counts
    total_issues = len(issues)
    flagged_issues = Issue.query.join(Flag).group_by(Issue.id).all()
    resolved_issues = Issue.query.filter_by(status='Resolved').count()
    in_progress_issues = Issue.query.filter_by(status='In-Progress').count()

    # 🧠 Category counts
    category_counts = db.session.query(
        Issue.category, func.count(Issue.id)
    ).group_by(Issue.category).all()

    category_dict = {cat: count for cat, count in category_counts}

    return render_template(
        'admin.html',
        issues=issues,
        username=user.username,
        total_issues=total_issues,
        flagged_issues=flagged_issues,
        resolved_issues=resolved_issues,
        in_progress_issues=in_progress_issues,
        category_dict=category_dict
    )


@app.route('/admin/update_status/<int:issue_id>', methods=['POST'])
def change_status(issue_id):
    new_status = request.form['status']
    issue = Issue.query.get(issue_id)
    if issue:
        issue.status = new_status
        db.session.commit()
        flash(f"Status updated to {new_status}")
    else:
        flash("Issue not found")
    return redirect(url_for('admin'))

@app.route('/flag/<int:issue_id>', methods=['POST'])
def flag_issue(issue_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Check if user has already flagged this issue
    existing_flag = db.session.query(Flag).filter_by(user_id=session['user_id'], issue_id=issue_id).first()
    if existing_flag:
        flash('You have already flagged this issue.')
        return redirect(url_for('home'))

    # Create a new flag
    new_flag = Flag(user_id=session['user_id'], issue_id=issue_id)
    db.session.add(new_flag)
    db.session.commit()

    flash('Issue flagged successfully.')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
