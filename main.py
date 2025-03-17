from flask import Flask, render_template, redirect, url_for, abort, request, flash
from flask_sqlalchemy import SQLAlchemy
from forms import EventForm, UpdateEventForm, RegistrationForm, LoginForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

# for Models
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = "secret"
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


#asdfsdaf
class User(db.Model, UserMixin):  # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False) # Store password hash
    is_admin = db.Column(db.Boolean, default=False)
    events = db.relationship('Event', backref='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    location = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    events = Event.query.all()
    return render_template('index.html', events=events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_details.html', event=event)

@app.route('/create', methods=['GET', 'POST'])
@login_required  # Protect this route
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            user_id=current_user.id  # Use current_user
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_event.html', form=form)


@app.route('/event/<int:event_id>/update', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user == event.creator or current_user.is_admin:  # Access control
        
        form = UpdateEventForm(obj=event)
        if form.validate_on_submit():
            form.populate_obj(event)
            db.session.commit()
            return redirect(url_for('event_detail', event_id=event.id))
        return render_template('update_event.html', form=form)
    else:
        abort(403)

@app.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user != event.creator and not current_user.is_admin: # Access control
        abort(403)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data) # Hash the password
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data): # Check password
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.first(): # Create default admin user if it doesn't exist
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password('password') # Set initial password
            db.session.add(admin_user)
            db.session.commit()

    app.run(host='0.0.0.0', port=5000, debug=True)  # debug=True for development