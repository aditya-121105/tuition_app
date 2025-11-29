from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()




from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    enrollment_no = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    class_name = db.Column(db.String(50), nullable=True)
    monthly_fee = db.Column(db.Integer, nullable=True)
    parent_phone = db.Column(db.String(15), nullable=True)
    student_phone = db.Column(db.String(15), nullable=True)
    village = db.Column(db.String(50), nullable=True)
    date_joined = db.Column(db.Date, default=datetime.utcnow)


    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


# ---------------------- Attendance ----------------------
class StudentAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(10))  # Present / Absent / Leave

# ---------------------- Marks ----------------------
class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    out_of = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)

# ---------------------- Fees ----------------------
class Fees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False)  # January, February...
    year = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending / Paid
    paid_date = db.Column(db.Date, nullable=True)


# ---------------------- Timetable ----------------------
class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(50), nullable=False)

