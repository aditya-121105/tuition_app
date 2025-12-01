from flask import Flask, render_template, redirect, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from models import StudentAttendance, Marks, Fees
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

app.secret_key = "your_secret_key_here"
# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://tuition_db_bvg8_user:5614G3BZ5E7v3PSkc3GwF7bZxbNu9GaM@dpg-d4mqqichg0os73c2u3o0-a/tuition_db_bvg8"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
with app.app_context():
    db.create_all()

    # ---- Create Default Admin Only Once ----
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(role="teacher").first():
        admin = User(
            name="Admin",
            enrollment_no="ADMIN001",
            password=generate_password_hash("admin123"),
            role="teacher"
        )
        db.session.add(admin)
        db.session.commit()
        print("Default Admin Created: USERNAME: ADMIN001 | PASSWORD: admin123")


SENDER_EMAIL = "kumarkhaniyaaditya123@gmail.com"       # will send mail
RECEIVER_EMAIL = "adityakumarkhaniya143@gmail.com"     # will receive mail
APP_PASSWORD = "vzgclkctxuqkoovk"





def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    # Connect to Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
    server.quit()

# paste the 16-char app password
# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------- Public Routes --------
@app.route("/")
def home():
    ua = request.user_agent.string.lower()
    if "mobile" in ua:
        return render_template("public/index_mobile.html")  # mobile page
    else:
        return render_template("public/index.html")

@app.route("/about")
def about():
    ua = request.user_agent.string.lower()
    if "mobile" in ua:
        return render_template("public/about_mobile.html")  # mobile page
    else:
        return render_template("public/about.html")

from flask import Flask, render_template, redirect, request, flash, url_for
# (you already have this import at the top)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    ua = request.user_agent.string.lower()
    if request.method == "POST":
        name = request.form.get("name")
        number = request.form.get("phone")
        email = request.form.get("email")
        message = request.form.get("message")

        # Email content
        body = f"""
New enquiry from website 📩

Name: {name}
Email: {email}

Message:
{message}
"""

        try:
            send_email("New Contact Form Enquiry", body)
            flash("✅ Message sent successfully! We’ll contact you soon.", "success")
        except Exception as e:
            print("Email error:", e)
            flash("❌ Something went wrong while sending your message. Please try again later.", "danger")

        return redirect("/contact")

    if 'mobile' in ua:
        return render_template("public/contact_mobile.html")
    else:
        return render_template("public/contact.html")


# -------- Auth Routes --------
@app.route("/login", methods=["GET", "POST"])
def login():
    ua = request.user_agent.string.lower()
    if request.method == "POST":
        identifier = request.form.get("identifier")
        password = request.form.get("password")

        # Check if matches enrollment number (works for students AND admin)
        user = User.query.filter_by(enrollment_no=identifier).first()

        # If not found, try matching teacher name (Ex: Admin)
        if not user:
            user = User.query.filter_by(name=identifier).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.role == "teacher":
                return redirect("/teacher/dashboard")
            elif user.role == "student":
                return redirect("/student/dashboard")

        flash("❌ Incorrect login details!", "danger")

    if 'mobile' in ua:
        return render_template("dashboard/login_mobile.html")
    else:
        return render_template("dashboard/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# -------- Dashboard Routes --------
@app.route("/student/dashboard")
@login_required
def student_dashboard():
    ua = request.user_agent.string.lower()
    if current_user.role != "student":
        return "Access Denied", 403
    elif 'mobile' in ua:
        return render_template("dashboard/student_dashboard_mobile.html")
    else:
        return render_template("dashboard/student_dashboard.html")


@app.route("/teacher/attendance", methods=["GET", "POST"])
@login_required
def teacher_attendance():
    if current_user.role != "teacher":
        return "Access Denied", 403
    ua = request.user_agent.string.lower()
    selected_class = request.args.get("class", "all")

    # Fetch unique class list
    classes = sorted(set([s.class_name for s in User.query.filter_by(role="student").all()]))

    # Filter students based on dropdown
    if selected_class == "all":
        students = User.query.filter_by(role="student").order_by(User.class_name).all()
    else:
        students = User.query.filter_by(role="student", class_name=selected_class).all()

    if request.method == "POST":
        from datetime import datetime
        date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()

        for student in students:
            status = request.form.get(f"status_{student.id}")
            attendance = StudentAttendance(student_id=student.id, status=status, date=date)
            db.session.add(attendance)

        db.session.commit()
        flash("Attendance saved successfully!", "success")
        return redirect(f"/teacher/attendance?class={selected_class}")
    elif 'mobile' in ua:
        return render_template("dashboard/teacher_attendance_mobile.html",
                           students=students,
                           classes=classes,
                           selected_class=selected_class)
    else:
        return render_template("dashboard/teacher_attendance.html", students=students,classes=classes, selected_class=selected_class)
from datetime import datetime

def generate_fee_records(student_id, year, monthly_fee, date_joined):
    academic_months = ["July","August","September","October","November","December",
                       "January","February","March"]

    # Convert date_joined to month name
    join_month_name = date_joined.strftime("%B")

    # Collect only months AFTER OR SAME AS join month
    start_recording = False
    for month in academic_months:
        if month == join_month_name:
            start_recording = True

        if start_recording:
            entry = Fees(student_id=student_id, month=month, year=year, status="Pending")
            db.session.add(entry)

    db.session.commit()


import random
import string

def generate_enrollment():
    last_user = User.query.order_by(User.id.desc()).first()
    next_id = (last_user.id + 1) if last_user else 1
    return f"TU2025{next_id:03d}"  # Example: TU2025001

def generate_password():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))




@app.route("/teacher/dashboard")
@login_required
def teacher_dashboard():
    ua = request.user_agent.string.lower()
    if current_user.role != "teacher":
        return "Access Denied", 403

    # All students
    students = User.query.filter_by(role="student").all()
    total_students = len(students)

    # Expected monthly income
    monthly_income = sum(s.monthly_fee or 0 for s in students)

    # Pending fees
    pending_fees = 0
    for s in students:
        # Pending fees (only valid months: join month → current month)
        from datetime import datetime
        current_month_name = datetime.now().strftime("%B")

        pending_fees = 0
        for s in students:
            all_pending = Fees.query.filter_by(student_id=s.id, status="Pending").all()

            valid_pending = [
                r for r in all_pending
                if month_index(s.date_joined.strftime("%B")) <= month_index(r.month) <= month_index(current_month_name)
            ]

            pending_fees += len(valid_pending) * (s.monthly_fee or 0)

    # Class-wise count
    class_summary = {}
    for s in students:
        if s.class_name:
            class_summary[s.class_name] = class_summary.get(s.class_name, 0) + 1

    # Attendance % (placeholder until attendance analyzer is built)
    present_percentage = 89
    if 'mobile' in ua:
        return render_template("dashboard/teacher_dashboard_mobile.html",
                               total_students=total_students,
                               monthly_income=monthly_income,
                               pending_fees=pending_fees,
                               present_percentage=present_percentage,
                               class_summary=class_summary)
    else:
        return render_template("dashboard/teacher_dashboard.html",
                               total_students=total_students,
                               monthly_income=monthly_income,
                               pending_fees=pending_fees,
                               present_percentage=present_percentage,
                               class_summary=class_summary)


@app.route("/student/attendance")
@login_required
def student_attendance():
    ua = request.user_agent.string.lower()
    if current_user.role != "student":
        return "Access Denied", 403

    records = StudentAttendance.query.filter_by(student_id=current_user.id).all()

    if 'mobile' in ua:
        return render_template("dashboard/student_attendance_mobile.html", records=records)
    else:
        return render_template("dashboard/student_attendance.html", records=records)

@app.route("/teacher/marks", methods=["GET", "POST"])
@login_required
def teacher_marks():
    if current_user.role != "teacher":
        return "Access Denied", 403

    students = User.query.filter_by(role="student").all()

    if request.method == "POST":
        subject = request.form.get("subject")
        selected_class = request.form.get("class")
        date = request.form.get("date")

        selected_students = [s for s in students if s.class_name == selected_class]

        from datetime import datetime
        for s in selected_students:
            status = request.form.get(f"status_{s.id}")
            score = request.form.get(f"score_{s.id}")
            outof = request.form.get(f"outof_{s.id}")

            if status == "Absent":
                continue

            if score and outof:
                entry = Marks(
                    student_id=s.id,
                    subject=subject,
                    score=int(score),
                    out_of=int(outof),
                    date=datetime.strptime(date, "%Y-%m-%d")
                )
                db.session.add(entry)

        db.session.commit()
        flash("Marks submitted successfully!", "success")
        return redirect("/teacher/marks")
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/teacher_marks_mobile.html", students=students)
    else:
        return render_template("dashboard/teacher_marks.html", students=students)


@app.route("/student/marks")
@login_required
def student_marks():
    if current_user.role != "student":
        return "Access Denied", 403

    records = Marks.query.filter_by(student_id=current_user.id).all()
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/student_marks_mobile.html", records=records)
    else:
        return render_template("dashboard/student_marks.html", records=records)

def month_index(month):
    order = ["July","August","September","October","November","December",
             "January","February","March"]
    return order.index(month)

@app.route("/teacher/fees", methods=["GET"])
@login_required
def teacher_fees():
    if current_user.role != "teacher":
        return "Access Denied", 403

    class_filter = request.args.get("class")

    query = User.query.filter_by(role="student")
    if class_filter:
        query = query.filter_by(class_name=class_filter)

    students = query.all()

    current_year = 2025  # you can make dynamic later

    data = []
    for s in students:
        current_month_name = datetime.now().strftime("%B")

        pending_records = [
            r for r in Fees.query.filter_by(student_id=s.id, status="Pending").all()
            if month_index(s.date_joined.strftime("%B")) <= month_index(r.month) <= month_index(current_month_name)
        ]

        paid_record = Fees.query.filter_by(student_id=s.id, year=current_year, month=datetime.now().strftime("%B")).first()

        total_pending_amount = len(pending_records) * s.monthly_fee

        data.append({
            "student": s,
            "pending_count": len(pending_records),
            "pending_months": [r.month for r in pending_records],
            "monthly_status": "Paid" if paid_record and paid_record.status=="Paid" else "Pending",
            "total_amount": total_pending_amount
        })

    classes = sorted(set(s.class_name for s in User.query.filter_by(role="student").all()))
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/teacher_fee_list_mobile.html", data=data, classes=classes, current_class=class_filter)
    else:
        return render_template("dashboard/teacher_fee_list.html", data=data, classes=classes)

import csv
from flask import Response

@app.route("/teacher/fees/export")
@login_required
def export_pending():
    if current_user.role != "teacher":
        return "Access Denied", 403

    class_filter = request.args.get("class")

    students = User.query.filter_by(role="student")
    if class_filter:
        students = students.filter_by(class_name=class_filter)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(["Name", "Class", "Total Pending Amount", "Pending Months"])

    for s in students:
        current_month_name = datetime.now().strftime("%B")

        pending = [
            p for p in Fees.query.filter_by(student_id=s.id, status="Pending").all()
            if month_index(s.date_joined.strftime("%B")) <= month_index(p.month) <= month_index(current_month_name)
        ]

        if pending:
            months = ", ".join(r.month for r in pending)
            writer.writerow([
                s.name,
                s.class_name,
                len(pending) * s.monthly_fee,
                months
            ])

    output.seek(0)
    ua = request.user_agent.string.lower()
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pending_fees.csv"}
    )

@app.route("/teacher/fees/<int:student_id>")
@login_required
def single_student_fee(student_id):
    if current_user.role != "teacher":
        return "Access Denied", 403

    student = User.query.get(student_id)
    all_records = Fees.query.filter_by(student_id=student_id).all()
    records = sorted(all_records, key=lambda r: month_index(r.month))

    # Optional: hide months before join month
    records = [r for r in records if month_index(r.month) >= month_index(student.date_joined.strftime("%B"))]
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/teacher_single_fee_mobile.html", student=student, records=records)
    else:
        return render_template("dashboard/teacher_single_fee.html", student=student, records=records)

@app.route("/teacher/fees/update", methods=["POST"])
@login_required
def update_fee_status():
    if current_user.role != "teacher":
        return "Access Denied", 403

    record_id = request.form.get("record_id")
    fee_record = Fees.query.get(record_id)

    from datetime import datetime
    fee_record.status = "Paid"
    fee_record.paid_date = datetime.now().date()

    db.session.commit()

    return redirect(f"/teacher/fees/{fee_record.student_id}")


from datetime import datetime

@app.route("/student/profile")
@login_required
def student_profile():
    if current_user.role != "student":
        return "Access Denied", 403
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/student_profile_mobile.html", student=current_user)
    else:
        return render_template("dashboard/student_profile.html", student=current_user)

@app.route("/student/fees", methods=["GET", "POST"])
@login_required
def student_fees():
    if current_user.role != "student":
        return "Access Denied", 403

    all_records = Fees.query.filter_by(student_id=current_user.id).all()

    # Month limits
    join_month_index = month_index(current_user.date_joined.strftime("%B"))
    current_month_index = month_index(datetime.now().strftime("%B"))

    # Filter records only between (Join Month → Current Month)
    valid_records = [
        r for r in all_records
        if join_month_index <= month_index(r.month) <= current_month_index
    ]

    # First pending month
    first_pending = next((r for r in valid_records if r.status == "Pending"), None)

    if request.method == "POST":
        if first_pending:
            first_pending.status = "Paid"
            first_pending.paid_date = datetime.today().date()
            db.session.commit()
            flash("Payment Successful!", "success")
            return redirect("/student/fees")

    total_pending = sum(1 for r in valid_records if r.status == "Pending") * current_user.monthly_fee
    total_paid = sum(1 for r in valid_records if r.status == "Paid") * current_user.monthly_fee
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/student_fees_mobile.html",
                               records=valid_records,
                               monthly_fee=current_user.monthly_fee,
                               total_pending=total_pending,
                               total_paid=total_paid,
                               first_pending=first_pending)
    else:
        return render_template("dashboard/student_fees.html",
                               records=valid_records,
                               monthly_fee=current_user.monthly_fee,
                               total_pending=total_pending,
                               total_paid=total_paid,
                               first_pending=first_pending)

from reportlab.pdfgen import canvas
from flask import send_file
import io

@app.route("/receipt/<int:fee_id>")
@login_required
def download_receipt(fee_id):
    fee = Fees.query.get(fee_id)

    if not fee or fee.student_id != current_user.id:
        return "Access Denied", 403

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, 780, "Tuition Fee Receipt")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 730, f"Student Name: {current_user.name}")
    pdf.drawString(50, 710, f"Enrollment No: {current_user.enrollment_no}")
    pdf.drawString(50, 690, f"Class: {current_user.class_name}")
    pdf.drawString(50, 670, f"Month: {fee.month} {fee.year}")
    pdf.drawString(50, 650, f"Amount Paid: ₹{current_user.monthly_fee}")
    pdf.drawString(50, 630, f"Payment Date: {fee.paid_date}")

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"Receipt_{fee.month}_{fee.year}.pdf", mimetype='application/pdf')


from werkzeug.security import generate_password_hash

@app.route("/teacher/add_student", methods=["GET", "POST"])
@login_required
def add_student():
    if current_user.role != "teacher":
        return "Access Denied", 403

    generated_enrollment = None
    generated_password = None

    if request.method == "POST":
        name = request.form.get("name")
        class_name = request.form.get("class")
        monthly_fee = request.form.get("monthly_fee")
        parent_phone = request.form.get("parent_phone")
        student_phone = request.form.get("student_phone")
        village = request.form.get("village")

        # Enrollment No
        enrollment = generate_enrollment()

        # Password = NAME + last 4 digits of parent phone
        last4 = parent_phone[-4:] if len(parent_phone) >= 4 else parent_phone
        plain_password = (name.split()[0].upper() + last4)  # Only first name + last4

        hashed_password = generate_password_hash(plain_password)

        new_student = User(
            name=name,
            enrollment_no=enrollment,
            password=hashed_password,
            role="student",
            class_name=class_name,
            monthly_fee=int(monthly_fee),
            parent_phone=parent_phone,
            student_phone=student_phone,
            village=village
        )

        db.session.add(new_student)
        db.session.commit()

        # Generate monthly fee rows automatically
        generate_fee_records(new_student.id, 2025, monthly_fee, new_student.date_joined)

        generated_enrollment = enrollment
        generated_password = plain_password  # Show student password once
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/add_student_mobile.html",
                           enrollment=generated_enrollment,
                           password=generated_password)
    else:
        return render_template("dashboard/add_student.html",
                               enrollment=generated_enrollment,
                               password=generated_password)


@app.route("/teacher/students")
@login_required
def student_list():
    if current_user.role != "teacher":
        return "Access Denied", 403

    search_query = request.args.get("search", "")
    class_filter = request.args.get("class_filter", "")
    page = request.args.get("page", 1, type=int)

    query = User.query.filter_by(role="student")

    # Apply search filter
    if search_query:
        query = query.filter(
            (User.name.ilike(f"%{search_query}%")) |
            (User.enrollment_no.ilike(f"%{search_query}%")) |
            (User.village.ilike(f"%{search_query}%"))
        )

    # Apply class filter
    if class_filter and class_filter != "all":
        query = query.filter_by(class_name=class_filter)

    # Pagination: 10 students per page
    students = query.paginate(page=page, per_page=10)

    # Collect unique class list for dropdown
    classes = [row.class_name for row in User.query.filter_by(role="student").distinct(User.class_name).all()]
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template(
            "dashboard/student_list_mobile.html",
            students=students,
            classes=classes,
            selected_class=class_filter,
            search_query=search_query
        )
    else:
        return render_template(
            "dashboard/student_list.html",
            students=students,
            classes=classes,
            selected_class=class_filter,
            search_query=search_query
        )

import pandas as pd
from flask import make_response

@app.route("/teacher/students/export/csv")
@login_required
def export_students_csv():
    if current_user.role != "teacher":
        return "Access Denied", 403

    students = User.query.filter_by(role="student").all()

    data = [
        {
            "Enrollment No": s.enrollment_no,
            "Name": s.name,
            "Class": s.class_name,
            "Mobile": s.student_phone,
            "Parent Phone": s.parent_phone,
            "Village": s.village,
            "Monthly Fee": s.monthly_fee
        }
        for s in students
    ]

    df = pd.DataFrame(data)
    response = make_response(df.to_csv(index=False))
    response.headers["Content-Disposition"] = "attachment; filename=students.csv"
    response.headers["Content-Type"] = "text/csv"

    return response

from flask import make_response
import pandas as pd
from io import BytesIO


from flask import make_response
import pandas as pd
from io import BytesIO


@app.route("/teacher/students/export/excel")
@login_required
def export_students_excel():
    if current_user.role != "teacher":
        return "Access Denied", 403

    students = User.query.filter_by(role="student").all()

    data = []
    for s in students:
        pending_months = Fees.query.filter_by(student_id=s.id, status="Pending").all()
        pending_list = ", ".join([f"{p.month} {p.year}" for p in pending_months])
        total_pending = len(pending_months) * (s.monthly_fee or 0)

        data.append({
            "Name": s.name,
            "Class": s.class_name,
            "Pending Months": pending_list,
            "Total Pending Amount": total_pending,
            "Phone": s.student_phone,
            "Village": s.village
        })

    df = pd.DataFrame(data)

    # → Write to Excel in memory
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    # → Send file to user
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=students_fees_report.xlsx"
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response

from werkzeug.security import generate_password_hash


@app.route("/teacher/edit_student/<int:student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    if current_user.role != "teacher":
        return "Access Denied", 403

    student = User.query.get_or_404(student_id)

    if request.method == "POST":
        student.name = request.form.get("name")
        student.class_name = request.form.get("class_name")
        student.monthly_fee = request.form.get("monthly_fee")
        student.parent_phone = request.form.get("parent_phone")
        student.student_phone = request.form.get("student_phone")
        student.village = request.form.get("village")

        db.session.commit()
        flash("Student details updated successfully!", "success")
        return redirect("/teacher/students")

    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("dashboard/edit_student_mobile.html", student=student)
    else:
        return render_template("dashboard/edit_student.html", student=student)


@app.route("/teacher/delete_student/<int:student_id>")
@login_required
def delete_student(student_id):
    if current_user.role != "teacher":
        return "Access Denied", 403

    student = User.query.get_or_404(student_id)

    # delete related data
    StudentAttendance.query.filter_by(student_id=student_id).delete()
    Marks.query.filter_by(student_id=student_id).delete()
    Fees.query.filter_by(student_id=student_id).delete()

    db.session.delete(student)
    db.session.commit()

    flash("Student removed successfully!", "danger")
    return redirect("/teacher/students")


from models import Timetable

# ------------ Teacher Timetable Page ------------
@app.route("/teacher/timetable", methods=["GET", "POST"])
@login_required
def teacher_timetable():

    if current_user.role != "teacher":
        return "Access Denied", 403

    classes = sorted(set([s.class_name for s in User.query.filter_by(role="student").all()]))

    selected_class = request.args.get("class")
    ua = request.user_agent.string.lower()

    # Fetch only when class selected
    records = Timetable.query.filter_by(class_name=selected_class).order_by(Timetable.day).all() if selected_class else []

    # --- Mobile View
    if "mobile" in ua:
        return render_template(
            "dashboard/teacher_timetable_mobile.html",
            classes=classes, selected_class=selected_class, records=records
        )

    # --- Desktop View (currently you are using mobile UI for both)
    return render_template(
        "dashboard/teacher_timetable.html",
        classes=classes, selected_class=selected_class, records=records
    )



@app.route("/teacher/timetable/add", methods=["POST"])
@login_required
def add_timetable():
    if current_user.role != "teacher":
        return "Access Denied", 403

    class_name = request.form.get("class_name")
    day = request.form.get("day")
    subject = request.form.get("subject")
    time = request.form.get("time")

    entry = Timetable(class_name=class_name, day=day, subject=subject, time=time)
    db.session.add(entry)
    db.session.commit()

    return redirect(f"/teacher/timetable?class={class_name}")



# ------------ Delete Timetable Entry ------------
@app.route("/teacher/timetable/delete/<id>")
@login_required
def delete_timetable(id):
    entry = Timetable.query.get(id)
    class_name = entry.class_name

    db.session.delete(entry)
    db.session.commit()

    return redirect(f"/teacher/timetable?class={class_name}")






from random import choice

@app.route("/timetable")
def view_timetable_classes():
    ua = request.user_agent.string.lower()
    classes = sorted(list(set([s.class_name for s in User.query.filter_by(role="student").all()])))

    # List of rotating quotes
    quotes = [
        "✨ Education is the passport to the future — invest in learning!",
        "📚 Small progress every day leads to big success.",
        "🚀 Success is not luck — it’s consistency and discipline.",
        "🌱 Learning never stops — grow a little every day.",
        "🔥 Winners are not born, they are trained and consistent.",
        "👑 Knowledge is power — and discipline controls that power.",
        "📘 Study now so your future self will thank you."
    ]

    random_quote = choice(quotes)
    if "mobile" in ua:
        return render_template("public/timetable_classes_mobile.html", classes=classes, quote=random_quote)
    else:
        return render_template("public/timetable_classes.html", classes=classes, quote=random_quote)


@app.route("/timetable/<class_name>")
def view_class_timetable(class_name):
    ua = request.user_agent.string.lower()

    records = Timetable.query.filter_by(class_name=class_name).order_by(Timetable.day).all()
    if 'mobile' in ua:
        return render_template("public/timetable_view_mobile.html", class_name=class_name, records=records)
    else:
        return render_template("public/timetable_view.html", class_name=class_name, records=records)
@app.route("/classes")
def classes():
    ua = request.user_agent.string.lower()
    if 'mobile' in ua:
        return render_template("public/classes_mobile.html")
    else:
        return render_template("public/classes.html")

import os
from flask import send_from_directory

@app.route("/gallery")
def gallery():
    ua = request.user_agent.string.lower()
    folder_path = os.path.join(app.static_folder, "picnic")

    # allowed image formats
    allowed_ext = ('.png', '.jpg', '.jpeg', '.webp')

    images = [f"picnic/{img}" for img in os.listdir(folder_path) if img.lower().endswith(allowed_ext)]
    if 'mobile' in ua:
        return render_template("public/gallery_mobile.html", images=sorted(images))
    else:
        return render_template("public/gallery.html", images=sorted(images))
if __name__ == "__main__":
    app.run(debug=True)
