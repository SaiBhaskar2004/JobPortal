# job_portal_single_file.py

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportal.db'
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

# Job Model
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(50))
    location = db.Column(db.String(50))
    posted_by = db.Column(db.String(80))

# Application Model
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ---------- Templates as strings ----------

index_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Job Portal</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: linear-gradient(135deg, #74ebd5, #ACB6E5); font-family: Arial, sans-serif; }
    .job-card { background: white; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; transition: transform 0.3s; }
    .job-card:hover { transform: translateY(-5px); }
    .nav-link { color: white !important; }
  </style>
</head>
<body class="p-5">
<nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">Job Portal</a>
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav ms-auto">
        {% if session['username'] %}
          <li class="nav-item"><span class="nav-link">Hi, {{session['username']}}</span></li>
          {% if session['role']=='employer' %}
          <li class="nav-item"><a class="nav-link" href="/post_job">Post Job</a></li>
          {% elif session['role']=='admin' %}
          <li class="nav-item"><a class="nav-link" href="/admin">Admin</a></li>
          {% endif %}
          <li class="nav-item"><a class="nav-link" href="/logout">Logout</a></li>
        {% else %}
          <li class="nav-item"><a class="nav-link" href="/login">Login</a></li>
          <li class="nav-item"><a class="nav-link" href="/register">Register</a></li>
        {% endif %}
      </ul>
    </div>
  </div>
</nav>

<h1 class="text-center mb-4">Job Listings</h1>
{% for job in jobs %}
  <div class="job-card">
    <h3>{{ job.title }}</h3>
    <p>{{ job.description }}</p>
    <p><strong>Location:</strong> {{ job.location }} | <strong>Salary:</strong> {{ job.salary }}</p>
    {% if session['role']=='jobseeker' %}
      <a href="{{ url_for('apply', job_id=job.id) }}" class="btn btn-primary">Apply</a>
    {% endif %}
  </div>
{% endfor %}
</body>
</html>
"""

register_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Register</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-5">
  <h2>Register</h2>
  <form method="POST">
    <input type="text" name="username" placeholder="Username" required class="form-control mb-2">
    <input type="password" name="password" placeholder="Password" required class="form-control mb-2">
    <select name="role" class="form-control mb-2">
      <option value="jobseeker">Job Seeker</option>
      <option value="employer">Employer</option>
      <option value="admin">Admin</option>
    </select>
    <button class="btn btn-success">Register</button>
  </form>
</body>
</html>
"""

login_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-5">
  <h2>Login</h2>
  <form method="POST">
    <input type="text" name="username" placeholder="Username" required class="form-control mb-2">
    <input type="password" name="password" placeholder="Password" required class="form-control mb-2">
    <button class="btn btn-primary">Login</button>
  </form>
</body>
</html>
"""

post_job_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Post Job</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-5">
  <h2>Post a Job</h2>
  <form method="POST">
    <input type="text" name="title" placeholder="Job Title" required class="form-control mb-2">
    <textarea name="description" placeholder="Job Description" required class="form-control mb-2"></textarea>
    <input type="text" name="salary" placeholder="Salary" class="form-control mb-2">
    <input type="text" name="location" placeholder="Location" class="form-control mb-2">
    <button class="btn btn-success">Post Job</button>
  </form>
</body>
</html>
"""

admin_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Panel</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-5">
  <h2>Admin Panel</h2>
  <h3>Users</h3>
  <ul>
    {% for user in users %}
      <li>{{ user.username }} ({{ user.role }})</li>
    {% endfor %}
  </ul>
  <h3>Jobs</h3>
  <ul>
    {% for job in jobs %}
      <li>{{ job.title }} by {{ job.posted_by }}</li>
    {% endfor %}
  </ul>
</body>
</html>
"""

# ---------- Routes ----------

@app.route('/')
def index():
    jobs = Job.query.all()
    return render_template_string(index_html, jobs=jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template_string(register_html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            flash('Invalid Credentials')
            return redirect(url_for('login'))
    return render_template_string(login_html)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'username' not in session or session['role'] != 'employer':
        flash('Only employers can post jobs')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        salary = request.form['salary']
        location = request.form['location']
        job = Job(title=title, description=description, salary=salary, location=location, posted_by=session['username'])
        db.session.add(job)
        db.session.commit()
        flash('Job Posted Successfully')
        return redirect(url_for('index'))
    return render_template_string(post_job_html)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    if 'username' not in session or session['role'] != 'jobseeker':
        flash('Only job seekers can apply')
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    application = Application(job_id=job_id, user_id=user.id)
    db.session.add(application)
    db.session.commit()
    flash('Applied Successfully')
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if 'username' not in session or session['role'] != 'admin':
        flash('Admin access only')
        return redirect(url_for('login'))
    users = User.query.all()
    jobs = Job.query.all()
    return render_template_string(admin_html, users=users, jobs=jobs)

# ---------- Main ----------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

