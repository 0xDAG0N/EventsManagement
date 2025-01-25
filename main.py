from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

from forms import EventForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = "secret"
db = SQLAlchemy(app)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"Event( '{self.title}', '{self.date}')"


@app.route('/')
@app.route('/index')
def index():
    events = Event.query.all()
    return render_template('index.html', events=events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_details.html', event=event)

@app.route('/create', methods=['GET', 'POST'])
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event()
        event.title = form.title.data
        event.description = form.description.data
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_event.html', form=form)

if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(host='0.0.0.0', port=5000)
