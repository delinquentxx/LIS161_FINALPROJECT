from flask import Flask, render_template, request, url_for, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectField, TextAreaField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from io import BytesIO
from logging import FileHandler,WARNING

from data import *

app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
file_handler = FileHandler('error.txt')
file_handler.setLevel(WARNING)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flipp.db'
app.config['SECRET_KEY'] = 'dbaeb1093fa44a11b34ef90987c5312f'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Announcement(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    committee = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String, nullable=False)

class Gallery(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    filename = db.Column(db.String(30), nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)
    description = db.Column(db.String, nullable=False)

class Minutes(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    filename = db.Column(db.String(30), nullable=False)
    file = db.Column(db.LargeBinary, nullable=False)
    details = db.Column(db.String, nullable=False)

class RegisterForm(FlaskForm):
    studentid = StringField(validators=[InputRequired(), Length
        (min=10, max=10)], render_kw={"placeholder": "Student ID"})
    email = StringField(validators=[InputRequired(), Length
        (min=7, max=40)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length
        (min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, studentid):
        existing_user_studentid = User.query.filter_by(
            studentid=studentid.data).first()

        if existing_user_studentid:
            raise ValidationError(
                "That Student ID already exists. Please login instead.")

class LoginForm(FlaskForm):
    studentid = StringField(validators=[InputRequired(), Length
        (min=10, max=10)], render_kw={"placeholder": "Student ID"})
    password = PasswordField(validators=[InputRequired(), Length
        (min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

class CreateAnnouncementForm(FlaskForm):
    date = DateField(validators=[InputRequired()], render_kw={"placeholder": "Date"})
    committee = SelectField(choices=[('Executive Committee'), ('Internal Affairs Committee'), ('External Affairs Committee'), ('Records and Documentations Management Committee'), ('Treasury and Possessions Development Committee')], validators=[InputRequired()], render_kw={"placeholder": "Committee"})
    message = TextAreaField(validators=[InputRequired()], render_kw={"placeholder": "Message"})

    submit = SubmitField("Post Announcement")

class UpdatePasswordForm(FlaskForm):
    studentid = StringField(validators=[InputRequired(), Length(min=10, max=10)], render_kw={"placeholder": "Student ID"})
    password = PasswordField(validators=[InputRequired(), Length (min=4, max=20)], render_kw={"placeholder": "Password"})
    new_password = PasswordField(validators=[InputRequired(), Length (min=4, max=20)], render_kw={"placeholder": "Enter New Password"})
    submit = SubmitField('Update')



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(studentid=form.studentid.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash((form.password.data))
        new_user = User(studentid=form.studentid.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template("home.html")


@app.route('/dashboard', methods=["GET"])
@login_required
def dashboard():
    announcements = Announcement.query.all()
    return render_template("dashboard.html", announcements=announcements)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateAnnouncementForm()

    if form.validate_on_submit():
        new_announcement = Announcement(date=form.date.data, committee=form.committee.data, message=form.message.data)
        db.session.add(new_announcement)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create.html', form=form)


@app.route('/delete_announcement', methods=['GET'])
@login_required
def delete_announcement():
    return render_template("delete_announcement.html")

@app.route('/process_delete_announcement', methods=['post'])
@login_required
def process_delete_announcement():
    announcement_id = request.form['AID']
    announcement_to_delete = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement_to_delete)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/gallery', methods=["GET", "POST"])
@login_required
def gallery():
    pictures = Gallery.query.all()
    return render_template("gallery.html", pictures=pictures)

@app.route('/upload_picture', methods=['GET', 'POST'])
@login_required
def upload_picture():

    if request.method == 'POST':
        file = request.files['image']
        date = request.form['date']
        description = request.form['description']

        new_upload = Gallery(date=date, filename=file.filename, image=file.read(), description=description)
        db.session.add(new_upload)
        db.session.commit()
        return redirect(url_for('gallery'))


    return render_template('upload_picture.html')

@app.route('/download-picture/<int:gallery_id>', methods=['GET', 'POST'])
@login_required
def download_picture(gallery_id):
    image = Gallery.query.filter_by(id=gallery_id).first()
    return send_file(BytesIO(image.image), attachment_filename=image.filename, as_attachment=True)

@app.route('/delete-picture/<int:gallery_id>', methods=['GET', 'POST'])
@login_required
def delete_picture(gallery_id):
    picture = Gallery.query.get_or_404(gallery_id)
    db.session.delete(picture)
    db.session.commit()
    return redirect(url_for('gallery'))

@app.route('/minutes', methods=["GET"])
@login_required
def minutes():
    files = Minutes.query.all()
    return render_template("minutes.html", files=files)

@app.route('/upload_minutes', methods=['GET', 'POST'])
@login_required
def upload_minutes():

    if request.method == 'POST':
        file = request.files['file']
        date = request.form['date']
        details = request.form['details']

        new_upload = Minutes(date=date, filename=file.filename, file=file.read(), details=details)
        db.session.add(new_upload)
        db.session.commit()
        return redirect(url_for('minutes'))


    return render_template('upload_minute.html')

@app.route('/download-file/<int:file_id>', methods=['GET', 'POST'])
@login_required
def download_file(file_id):
    file = Minutes.query.filter_by(id=file_id).first()
    return send_file(BytesIO(file.file), attachment_filename=file.filename, as_attachment=True)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(studentid=form.studentid.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                hashed_password = bcrypt.generate_password_hash((form.new_password.data))
                current_user.password = hashed_password
                db.session.commit()
        return redirect(url_for("profile"))

    return render_template('profile.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)