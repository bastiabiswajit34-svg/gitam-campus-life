# ============================================================
# GITAM CAMPUS LIFE
# ATTENDANCE MODULE
# COMPLETE UPGRADED VERSION
# DATABASE-SAFE
# ============================================================

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database import get_db


# ============================================================
# BLUEPRINT
# ============================================================

attendance = Blueprint(
    "attendance",
    __name__,
    url_prefix="/attendance"
)


# ============================================================
# SESSION HELPERS
# ============================================================

def logged_in():
    return "user_id" in session


def current_role():
    return str(
        session.get("role", "")
    ).strip().lower()


def is_student():
    return current_role() == "student"


def is_faculty():
    return current_role() == "faculty"


def is_admin():
    return current_role() == "admin"


def login_redirect():
    try:
        return redirect(
            url_for("auth.login")
        )
    except Exception:
        return redirect("/login")


def home_redirect():
    try:
        return redirect("/")
    except Exception:
        return redirect("/login")


# ============================================================
# DATABASE HELPERS
# ============================================================

def table_exists(db, table_name):
    try:
        row = db.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = ?
            """,
            (table_name,)
        ).fetchone()

        return row is not None

    except Exception:
        return False


def get_columns(db, table_name):
    columns = []

    try:
        rows = db.execute(
            "PRAGMA table_info(" + table_name + ")"
        ).fetchall()

        for row in rows:
            try:
                columns.append(row["name"])
            except Exception:
                columns.append(row[1])

    except Exception:
        pass

    return columns


def get_attendance_owner_column(columns):
    """
    Your existing database uses student_id.

    user_id is also supported for compatibility,
    but the current database should use student_id.
    """

    if "student_id" in columns:
        return "student_id"

    if "user_id" in columns:
        return "user_id"

    return None


def get_attendance_date_column(columns):
    """
    Your existing database uses attendance_date.

    date is supported only for compatibility with
    other possible schemas.
    """

    if "attendance_date" in columns:
        return "attendance_date"

    if "date" in columns:
        return "date"

    return None


def get_attendance_subject_column(columns):
    if "subject" in columns:
        return "subject"

    return None


def get_current_user(db):
    try:

        user_id = session.get("user_id")

        if not user_id:
            return None

        return db.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

    except Exception:
        return None


# ============================================================
# STATUS NORMALIZER
# ============================================================

def normalize_status(value):

    value = str(
        value or ""
    ).strip().lower()

    status_map = {
        "present": "Present",
        "absent": "Absent",
        "leave": "Leave",
        "late": "Late"
    }

    return status_map.get(
        value,
        str(value or "").strip()
    )


# ============================================================
# ATTENDANCE PAGE
# ============================================================

@attendance.route(
    "/",
    methods=["GET", "POST"]
)
def attendance_page():

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if not logged_in():
        return login_redirect()

    db = None

    try:

        db = get_db()

        # ----------------------------------------------------
        # TABLE CHECK
        # ----------------------------------------------------

        if not table_exists(
            db,
            "attendance"
        ):

            flash(
                "Attendance table is not available.",
                "error"
            )

            return render_template(
                "attendance.html",
                attendance=[],
                attendance_records=[],
                students=[],
                faculty=[],
                role=current_role(),
                user=get_current_user(db),
                present_count=0,
                absent_count=0,
                attendance_percentage=0
            )

        # ----------------------------------------------------
        # READ REAL DATABASE COLUMNS
        # ----------------------------------------------------

        columns = get_columns(
            db,
            "attendance"
        )

        owner_column = get_attendance_owner_column(
            columns
        )

        date_column = get_attendance_date_column(
            columns
        )

        subject_column = get_attendance_subject_column(
            columns
        )

        # ----------------------------------------------------
        # REQUIRED COLUMN CHECK
        # ----------------------------------------------------

        if not owner_column:

            flash(
                "Attendance database is missing student ownership field.",
                "error"
            )

            return render_template(
                "attendance.html",
                attendance=[],
                attendance_records=[],
                students=[],
                faculty=[],
                role=current_role(),
                user=get_current_user(db),
                present_count=0,
                absent_count=0,
                attendance_percentage=0
            )

        if not date_column:

            flash(
                "Attendance database is missing attendance date field.",
                "error"
            )

            return render_template(
                "attendance.html",
                attendance=[],
                attendance_records=[],
                students=[],
                faculty=[],
                role=current_role(),
                user=get_current_user(db),
                present_count=0,
                absent_count=0,
                attendance_percentage=0
            )

        if not subject_column:

            flash(
                "Attendance database is missing subject field.",
                "error"
            )

            return render_template(
                "attendance.html",
                attendance=[],
                attendance_records=[],
                students=[],
                faculty=[],
                role=current_role(),
                user=get_current_user(db),
                present_count=0,
                absent_count=0,
                attendance_percentage=0
            )

        user = get_current_user(db)


        # ====================================================
        # STUDENT
        # ====================================================

        if is_student():

            # ------------------------------------------------
            # STUDENT POST
            # ------------------------------------------------

            if request.method == "POST":

                subject = (
                    request.form.get("subject")
                    or ""
                ).strip()

                attendance_date = (
                    request.form.get("attendance_date")
                    or request.form.get("date")
                    or ""
                ).strip()

                status = (
                    request.form.get("status")
                    or ""
                ).strip()

                # ------------------------------------------------
                # Checkbox compatibility
                # ------------------------------------------------

                if not status:

                    if request.form.get("present"):
                        status = "Present"

                    elif request.form.get("absent"):
                        status = "Absent"

                    elif request.form.get("leave"):
                        status = "Leave"

                    elif request.form.get("late"):
                        status = "Late"

                status = normalize_status(
                    status
                )

                # ------------------------------------------------
                # Validation
                # ------------------------------------------------

                if not subject:

                    flash(
                        "Please enter the subject.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if not attendance_date:

                    flash(
                        "Please select the attendance date.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if status not in (
                    "Present",
                    "Absent",
                    "Leave",
                    "Late"
                ):

                    flash(
                        "Invalid attendance status.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                # ------------------------------------------------
                # Student attendance
                #
                # Current database:
                # student_id
                # subject
                # attendance_date
                # status
                # qr_code
                # ------------------------------------------------

                if owner_column == "student_id":

                    existing = db.execute(
                        f"""
                        SELECT id
                        FROM attendance
                        WHERE student_id = ?
                        AND {date_column} = ?
                        AND subject = ?
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (
                            session["user_id"],
                            attendance_date,
                            subject
                        )
                    ).fetchone()

                    if existing:

                        db.execute(
                            """
                            UPDATE attendance
                            SET status = ?
                            WHERE id = ?
                            """,
                            (
                                status,
                                existing["id"]
                            )
                        )

                    else:

                        db.execute(
                            """
                            INSERT INTO attendance
                            (
                                student_id,
                                subject,
                                attendance_date,
                                status,
                                qr_code
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                session["user_id"],
                                subject,
                                attendance_date,
                                status,
                                None
                            )
                        )

                else:

                    # Compatibility with user_id schema

                    existing = db.execute(
                        f"""
                        SELECT id
                        FROM attendance
                        WHERE user_id = ?
                        AND {date_column} = ?
                        AND subject = ?
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (
                            session["user_id"],
                            attendance_date,
                            subject
                        )
                    ).fetchone()

                    if existing:

                        db.execute(
                            """
                            UPDATE attendance
                            SET status = ?
                            WHERE id = ?
                            """,
                            (
                                status,
                                existing["id"]
                            )
                        )

                    else:

                        if "qr_code" in columns:

                            db.execute(
                                f"""
                                INSERT INTO attendance
                                (
                                    user_id,
                                    subject,
                                    {date_column},
                                    status,
                                    qr_code
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    session["user_id"],
                                    subject,
                                    attendance_date,
                                    status,
                                    None
                                )
                            )

                        else:

                            db.execute(
                                f"""
                                INSERT INTO attendance
                                (
                                    user_id,
                                    subject,
                                    {date_column},
                                    status
                                )
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    session["user_id"],
                                    subject,
                                    attendance_date,
                                    status
                                )
                            )

                db.commit()

                flash(
                    "Attendance recorded successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "attendance.attendance_page"
                    )
                )


            # ------------------------------------------------
            # STUDENT GET
            # ------------------------------------------------

            records = db.execute(
                f"""
                SELECT
                    *
                FROM attendance
                WHERE {owner_column} = ?
                ORDER BY {date_column} DESC, id DESC
                """,
                (
                    session["user_id"],
                )
            ).fetchall()


            # ------------------------------------------------
            # SUMMARY
            # ------------------------------------------------

            present_count = 0
            absent_count = 0

            for record in records:

                status = str(
                    record["status"] or ""
                ).strip().lower()

                if status == "present":
                    present_count += 1

                elif status == "absent":
                    absent_count += 1


            total_count = (
                present_count +
                absent_count
            )

            if total_count > 0:

                attendance_percentage = round(
                    (
                        present_count /
                        total_count
                    ) * 100,
                    2
                )

            else:

                attendance_percentage = 0


            return render_template(
                "attendance.html",
                attendance=records,
                attendance_records=records,
                students=[],
                faculty=[],
                role="student",
                user=user,
                present_count=present_count,
                absent_count=absent_count,
                attendance_percentage=attendance_percentage
            )


        # ====================================================
        # FACULTY
        # ====================================================

        if is_faculty():

            # ------------------------------------------------
            # FACULTY POST
            # Faculty marks STUDENT attendance only.
            # ------------------------------------------------

            if request.method == "POST":

                student_id = (
                    request.form.get("student_id")
                    or request.form.get("user_id")
                    or ""
                ).strip()

                subject = (
                    request.form.get("subject")
                    or ""
                ).strip()

                attendance_date = (
                    request.form.get("attendance_date")
                    or request.form.get("date")
                    or ""
                ).strip()

                status = (
                    request.form.get("status")
                    or ""
                ).strip()

                # ------------------------------------------------
                # Checkbox compatibility
                # ------------------------------------------------

                if not status:

                    if request.form.get("present"):
                        status = "Present"

                    elif request.form.get("absent"):
                        status = "Absent"

                    elif request.form.get("leave"):
                        status = "Leave"

                    elif request.form.get("late"):
                        status = "Late"

                status = normalize_status(
                    status
                )

                # ------------------------------------------------
                # Validation
                # ------------------------------------------------

                if not student_id:

                    flash(
                        "Please select a student.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if not subject:

                    flash(
                        "Please enter the subject.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if not attendance_date:

                    flash(
                        "Please select the attendance date.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if status not in (
                    "Present",
                    "Absent",
                    "Leave",
                    "Late"
                ):

                    flash(
                        "Invalid attendance status.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                # ------------------------------------------------
                # Verify student
                # ------------------------------------------------

                student = db.execute(
                    """
                    SELECT
                        id,
                        name,
                        role
                    FROM users
                    WHERE id = ?
                    """,
                    (
                        student_id,
                    )
                ).fetchone()


                if not student:

                    flash(
                        "Student not found.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                if str(
                    student["role"]
                ).strip().lower() != "student":

                    flash(
                        "Faculty can mark attendance only for students.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                # ------------------------------------------------
                # Current database uses student_id
                # ------------------------------------------------

                if owner_column != "student_id":

                    flash(
                        "Attendance database is not configured for student attendance.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                # ------------------------------------------------
                # Existing record
                # ------------------------------------------------

                existing = db.execute(
                    f"""
                    SELECT id
                    FROM attendance
                    WHERE student_id = ?
                    AND {date_column} = ?
                    AND subject = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (
                        student_id,
                        attendance_date,
                        subject
                    )
                ).fetchone()


                if existing:

                    db.execute(
                        """
                        UPDATE attendance
                        SET status = ?
                        WHERE id = ?
                        """,
                        (
                            status,
                            existing["id"]
                        )
                    )

                else:

                    if "qr_code" in columns:

                        db.execute(
                            f"""
                            INSERT INTO attendance
                            (
                                student_id,
                                subject,
                                {date_column},
                                status,
                                qr_code
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                student_id,
                                subject,
                                attendance_date,
                                status,
                                None
                            )
                        )

                    else:

                        db.execute(
                            f"""
                            INSERT INTO attendance
                            (
                                student_id,
                                subject,
                                {date_column},
                                status
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                student_id,
                                subject,
                                attendance_date,
                                status
                            )
                        )


                db.commit()

                flash(
                    "Student attendance saved successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "attendance.attendance_page"
                    )
                )


            # ------------------------------------------------
            # FACULTY STUDENT LIST
            # ------------------------------------------------

            students = db.execute(
                """
                SELECT
                    id,
                    name,
                    username,
                    roll_no,
                    branch,
                    year
                FROM users
                WHERE LOWER(role) = 'student'
                ORDER BY name ASC
                """
            ).fetchall()


            # ------------------------------------------------
            # FACULTY RECENT ATTENDANCE
            #
            # IMPORTANT:
            # Uses student_id + attendance_date.
            # No a.user_id.
            # No a.date.
            # ------------------------------------------------

            if owner_column == "student_id":

                recent = db.execute(
                    f"""
                    SELECT
                        a.*,
                        u.name AS student_name,
                        u.roll_no,
                        u.branch,
                        u.year
                    FROM attendance a
                    LEFT JOIN users u
                        ON a.student_id = u.id
                    WHERE LOWER(u.role) = 'student'
                    ORDER BY a.{date_column} DESC, a.id DESC
                    LIMIT 100
                    """
                ).fetchall()

            else:

                recent = db.execute(
                    f"""
                    SELECT
                        a.*,
                        u.name AS student_name,
                        u.roll_no,
                        u.branch,
                        u.year
                    FROM attendance a
                    LEFT JOIN users u
                        ON a.user_id = u.id
                    WHERE LOWER(u.role) = 'student'
                    ORDER BY a.{date_column} DESC, a.id DESC
                    LIMIT 100
                    """
                ).fetchall()


            return render_template(
                "attendance.html",
                attendance=recent,
                attendance_records=recent,
                students=students,
                faculty=[],
                role="faculty",
                user=user,
                present_count=0,
                absent_count=0,
                attendance_percentage=0
            )


        # ====================================================
        # ADMIN
        # ====================================================

        if is_admin():

            # ------------------------------------------------
            # ADMIN POST
            # ------------------------------------------------

            if request.method == "POST":

                student_id = (
                    request.form.get("student_id")
                    or request.form.get("user_id")
                    or request.form.get("faculty_id")
                    or ""
                ).strip()

                subject = (
                    request.form.get("subject")
                    or ""
                ).strip()

                attendance_date = (
                    request.form.get("attendance_date")
                    or request.form.get("date")
                    or ""
                ).strip()

                status = (
                    request.form.get("status")
                    or ""
                ).strip()


                # ------------------------------------------------
                # Checkbox compatibility
                # ------------------------------------------------

                if not status:

                    if request.form.get("present"):
                        status = "Present"

                    elif request.form.get("absent"):
                        status = "Absent"

                    elif request.form.get("leave"):
                        status = "Leave"

                    elif request.form.get("late"):
                        status = "Late"


                status = normalize_status(
                    status
                )


                # ------------------------------------------------
                # Validation
                # ------------------------------------------------

                if not student_id:

                    flash(
                        "Please select a student.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if not subject:

                    flash(
                        "Please enter the subject.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if not attendance_date:

                    flash(
                        "Please select the attendance date.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )

                if status not in (
                    "Present",
                    "Absent",
                    "Leave",
                    "Late"
                ):

                    flash(
                        "Invalid attendance status.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                # ------------------------------------------------
                # Verify selected user
                # ------------------------------------------------

                target_user = db.execute(
                    """
                    SELECT
                        id,
                        name,
                        role
                    FROM users
                    WHERE id = ?
                    """,
                    (
                        student_id,
                    )
                ).fetchone()


                if not target_user:

                    flash(
                        "Selected student was not found.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                # ------------------------------------------------
                # Current database uses student_id
                # ------------------------------------------------

                if owner_column != "student_id":

                    flash(
                        "Attendance database is not using the expected student_id field.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "attendance.attendance_page"
                        )
                    )


                # ------------------------------------------------
                # Check existing record
                # ------------------------------------------------

                existing = db.execute(
                    f"""
                    SELECT id
                    FROM attendance
                    WHERE student_id = ?
                    AND {date_column} = ?
                    AND subject = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (
                        student_id,
                        attendance_date,
                        subject
                    )
                ).fetchone()


                # ------------------------------------------------
                # UPDATE
                # ------------------------------------------------

                if existing:

                    db.execute(
                        """
                        UPDATE attendance
                        SET status = ?
                        WHERE id = ?
                        """,
                        (
                            status,
                            existing["id"]
                        )
                    )


                # ------------------------------------------------
                # INSERT
                # ------------------------------------------------

                else:

                    if "qr_code" in columns:

                        db.execute(
                            f"""
                            INSERT INTO attendance
                            (
                                student_id,
                                subject,
                                {date_column},
                                status,
                                qr_code
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                student_id,
                                subject,
                                attendance_date,
                                status,
                                None
                            )
                        )

                    else:

                        db.execute(
                            f"""
                            INSERT INTO attendance
                            (
                                student_id,
                                subject,
                                {date_column},
                                status
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                student_id,
                                subject,
                                attendance_date,
                                status
                            )
                        )


                db.commit()

                flash(
                    "Attendance saved successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "attendance.attendance_page"
                    )
                )


            # ------------------------------------------------
            # ADMIN STUDENTS
            # ------------------------------------------------

            students = db.execute(
                """
                SELECT
                    id,
                    name,
                    username,
                    roll_no,
                    branch,
                    year
                FROM users
                WHERE LOWER(role) = 'student'
                ORDER BY name ASC
                """
            ).fetchall()


            # ------------------------------------------------
            # ADMIN FACULTY
            # ------------------------------------------------

            faculty = db.execute(
                """
                SELECT
                    id,
                    name,
                    username,
                    designation,
                    branch
                FROM users
                WHERE LOWER(role) = 'faculty'
                ORDER BY name ASC
                """
            ).fetchall()


            # ------------------------------------------------
            # ADMIN RECENT ATTENDANCE
            #
            # Current database:
            # student_id
            # attendance_date
            # ------------------------------------------------

            if owner_column == "student_id":

                recent = db.execute(
                    f"""
                    SELECT
                        a.*,
                        u.name AS user_name,
                        u.role AS user_role,
                        u.roll_no,
                        u.branch,
                        u.year,
                        u.designation
                    FROM attendance a
                    LEFT JOIN users u
                        ON a.student_id = u.id
                    ORDER BY a.{date_column} DESC, a.id DESC
                    LIMIT 150
                    """
                ).fetchall()

            else:

                recent = db.execute(
                    f"""
                    SELECT
                        a.*,
                        u.name AS user_name,
                        u.role AS user_role,
                        u.roll_no,
                        u.branch,
                        u.year,
                        u.designation
                    FROM attendance a
                    LEFT JOIN users u
                        ON a.user_id = u.id
                    ORDER BY a.{date_column} DESC, a.id DESC
                    LIMIT 150
                    """
                ).fetchall()


            return render_template(
                "attendance.html",
                attendance=recent,
                attendance_records=recent,
                students=students,
                faculty=faculty,
                role="admin",
                user=user,
                present_count=0,
                absent_count=0,
                attendance_percentage=0
            )


        # ====================================================
        # UNKNOWN ROLE
        # ====================================================

        flash(
            "Your account role is not authorized for attendance.",
            "error"
        )

        return home_redirect()


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print(
            "[ATTENDANCE ERROR]",
            repr(e)
        )

        try:

            if db is not None:
                db.rollback()

        except Exception:
            pass

        flash(
            "Unable to load or save attendance.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_page"
            )
        )


    # ========================================================
    # DATABASE CLOSE
    # ========================================================

    finally:

        if db is not None:

            try:
                db.close()
            except Exception:
                pass


# ============================================================
# COMPATIBILITY ROUTE
# ============================================================

@attendance.route(
    "/record",
    methods=["GET", "POST"]
)
def record():

    if not logged_in():
        return login_redirect()

    return attendance_page()


# ============================================================
# STUDENT ATTENDANCE
# ============================================================

@attendance.route(
    "/student",
    methods=["GET"]
)
def student_attendance():

    if not logged_in():
        return login_redirect()

    if not is_student():

        flash(
            "Student access required.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_page"
            )
        )

    return redirect(
        url_for(
            "attendance.attendance_page"
        )
    )


# ============================================================
# FACULTY ATTENDANCE
# ============================================================

@attendance.route(
    "/faculty",
    methods=["GET"]
)
def faculty_attendance():

    if not logged_in():
        return login_redirect()

    if not is_faculty():

        flash(
            "Faculty access required.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_page"
            )
        )

    return redirect(
        url_for(
            "attendance.attendance_page"
        )
    )


# ============================================================
# ADMIN ATTENDANCE
# ============================================================

@attendance.route(
    "/admin",
    methods=["GET"]
)
def admin_attendance():

    if not logged_in():
        return login_redirect()

    if not is_admin():

        flash(
            "Admin access required.",
            "error"
        )

        return redirect(
            url_for(
                "attendance.attendance_page"
            )
        )

    return redirect(
        url_for(
            "attendance.attendance_page"
        )
    )


# ============================================================
# MODULE LOADED
# ============================================================

print(
    "[OK] Attendance module loaded."
)
