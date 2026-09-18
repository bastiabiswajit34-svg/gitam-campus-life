# ============================================================
# GITAM CAMPUS LIFE
# MAIN APPLICATION
# ============================================================

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from config import (
    SECRET_KEY,
    APP_NAME,
    APP_VERSION,
    CREATOR
)

from database import (
    init_db,
    get_db
)

from auth import (
    auth,
    login_required
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY


# ============================================================
# BASIC CONFIGURATION
# ============================================================

app.config["APP_NAME"] = APP_NAME
app.config["APP_VERSION"] = APP_VERSION
app.config["CREATOR"] = CREATOR


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:

    init_db()

    print("[OK] Database initialized successfully.")

except Exception as e:

    print("[ERROR] Database initialization failed:")
    print(e)


# ============================================================
# AUTHENTICATION MODULE
# ============================================================

try:

    app.register_blueprint(auth)

    print("[OK] Auth module loaded.")

except Exception as e:

    print("[ERROR] Auth module failed:")
    print(e)


# ============================================================
# ATTENDANCE MODULE
# ============================================================

try:

    from modules.attendance.routes import attendance

    app.register_blueprint(attendance)

    print("[OK] Attendance module loaded.")

except Exception as e:

    print("[ERROR] Attendance module failed:")
    print(e)


# ============================================================
# LEAVE MODULE
# ============================================================

try:

    from modules.leave.routes import leave

    app.register_blueprint(leave)

    print("[OK] Leave module loaded.")

except Exception as e:

    print("[ERROR] Leave module failed:")
    print(e)


# ============================================================
# GATE PASS MODULE
# ============================================================

try:

    from modules.gate_pass.routes import gate_pass

    app.register_blueprint(gate_pass)

    print("[OK] Gate Pass module loaded.")

except Exception as e:

    print("[ERROR] Gate Pass module failed:")
    print(e)


# ============================================================
# CERTIFICATE MODULE
# ============================================================

try:

    from modules.certificates.routes import certificates

    app.register_blueprint(certificates)

    print("[OK] Certificates module loaded.")

except Exception as e:

    print("[ERROR] Certificates module failed:")
    print(e)


# ============================================================
# COMPLAINTS MODULE
# ============================================================

try:

    from modules.complaints.routes import complaints

    app.register_blueprint(complaints)

    print("[OK] Complaints module loaded.")

except Exception as e:

    print("[ERROR] Complaints module failed:")
    print(e)


# ============================================================
# NOTICES MODULE
# ============================================================

try:

    from modules.notices.routes import notices

    app.register_blueprint(notices)

    print("[OK] Notices module loaded.")

except Exception as e:

    print("[ERROR] Notices module failed:")
    print(e)


# ============================================================
# NOTIFICATIONS MODULE
# ============================================================

try:

    from modules.notifications.routes import notifications

    app.register_blueprint(notifications)

    print("[OK] Notifications module loaded.")

except Exception as e:

    print("[ERROR] Notifications module failed:")
    print(e)


# ============================================================
# DIGITAL ID MODULE
# ============================================================

try:

    from modules.digital_id.routes import digital_id

    app.register_blueprint(digital_id)

    print("[OK] Digital ID module loaded.")

except Exception as e:

    print("[ERROR] Digital ID module failed:")
    print(e)


# ============================================================
# VISITOR MODULE
# ============================================================

try:

    from modules.visitor.routes import visitor

    app.register_blueprint(visitor)

    print("[OK] Visitor module loaded.")

except Exception as e:

    print("[ERROR] Visitor module failed:")
    print(e)


# ============================================================
# EVENTS MODULE
# ============================================================

try:

    from modules.events.routes import events

    app.register_blueprint(events)

    print("[OK] Events module loaded.")

except Exception as e:

    print("[ERROR] Events module failed:")
    print(e)


# ============================================================
# ADMIN USER MANAGEMENT
# ============================================================

try:

    from modules.admin_users.routes import admin_users

    app.register_blueprint(admin_users)

    print("[OK] Admin Users module loaded.")

except Exception as e:

    print("[ERROR] Admin Users module failed:")
    print(e)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "base.html"
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/student/dashboard")
@login_required
def student_dashboard():

    # --------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------

    role = str(
        session.get("role", "")
    ).strip().lower()


    if role != "student":

        flash(
            "Student access required.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # --------------------------------------------------------
    # GET CURRENT USER
    # --------------------------------------------------------

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
        """,
        (
            session.get("user_id"),
        )
    ).fetchone()

    db.close()


    # --------------------------------------------------------
    # USER NOT FOUND
    # --------------------------------------------------------

    if not user:

        session.clear()

        flash(
            "User account not found.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render_template(
        "student_dashboard.html",
        user=user
    )


# ============================================================
# FACULTY DASHBOARD
# ============================================================

@app.route("/faculty/dashboard")
@login_required
def faculty_dashboard():

    # --------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------

    role = str(
        session.get("role", "")
    ).strip().lower()


    if role != "faculty":

        flash(
            "Faculty access required.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    # --------------------------------------------------------
    # GET CURRENT USER
    # --------------------------------------------------------

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
        """,
        (
            session.get("user_id"),
        )
    ).fetchone()

    db.close()


    # --------------------------------------------------------
    # USER NOT FOUND
    # --------------------------------------------------------

    if not user:

        session.clear()

        flash(
            "User account not found.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    return render_template(
        "faculty_dashboard.html",
        user=user
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():

    # --------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------

    role = str(
        session.get("role", "")
    ).strip().lower()


    if role != "admin":

        flash(
            "Administrator access required.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    db = get_db()


    # ========================================================
    # USER COUNTS
    # ========================================================

    students_result = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM users
        WHERE lower(role) = 'student'
        """
    ).fetchone()


    faculty_result = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM users
        WHERE lower(role) = 'faculty'
        """
    ).fetchone()


    pending_users_result = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM users
        WHERE lower(COALESCE(status, '')) = 'pending'
        """
    ).fetchone()


    # ========================================================
    # REQUEST COUNTS
    # ========================================================

    pending_leave = 0
    pending_gate_pass = 0
    pending_certificates = 0
    pending_complaints = 0
    pending_visitors = 0


    # --------------------------------------------------------
    # LEAVE
    # --------------------------------------------------------

    try:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM leave_requests
            WHERE lower(status) = 'pending'
            """
        ).fetchone()

        pending_leave = result["total"]

    except Exception:

        pending_leave = 0


    # --------------------------------------------------------
    # GATE PASS
    # --------------------------------------------------------

    try:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM gate_passes
            WHERE lower(status) = 'pending'
            """
        ).fetchone()

        pending_gate_pass = result["total"]

    except Exception:

        pending_gate_pass = 0


    # --------------------------------------------------------
    # CERTIFICATES
    # --------------------------------------------------------

    try:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM certificate_requests
            WHERE lower(status) = 'pending'
            """
        ).fetchone()

        pending_certificates = result["total"]

    except Exception:

        pending_certificates = 0


    # --------------------------------------------------------
    # COMPLAINTS
    # --------------------------------------------------------

    try:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM complaints
            WHERE lower(status) = 'pending'
            """
        ).fetchone()

        pending_complaints = result["total"]

    except Exception:

        pending_complaints = 0


    # --------------------------------------------------------
    # VISITORS
    # --------------------------------------------------------

    try:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE lower(status) = 'pending'
            """
        ).fetchone()

        pending_visitors = result["total"]

    except Exception:

        pending_visitors = 0


    # ========================================================
    # EVENT COUNT
    # ========================================================

    total_events = 0

    try:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM events
            """
        ).fetchone()

        total_events = result["total"]

    except Exception:

        total_events = 0


    # ========================================================
    # TOTAL REQUESTS
    # ========================================================

    pending_requests = (
        pending_leave
        + pending_gate_pass
        + pending_certificates
        + pending_complaints
    )


    db.close()


    # ========================================================
    # RENDER ADMIN DASHBOARD
    # ========================================================

    return render_template(
        "admin_dashboard.html",

        students=students_result["total"],

        faculty=faculty_result["total"],

        pending_users=pending_users_result["total"],

        pending_requests=pending_requests,

        pending_leave=pending_leave,

        pending_gate_pass=pending_gate_pass,

        pending_certificates=pending_certificates,

        pending_complaints=pending_complaints,

        pending_visitors=pending_visitors,

        total_events=total_events
    )


# ============================================================
# 404 ERROR
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "base.html"
    ), 404


# ============================================================
# 500 ERROR
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    return (
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Server Error</title>

            <style>

                body {
                    font-family: Arial;
                    background: #eef8f1;
                    text-align: center;
                    padding: 60px 20px;
                }

                .box {
                    max-width: 600px;
                    margin: auto;
                    background: white;
                    padding: 35px;
                    border-radius: 15px;
                    box-shadow: 0 5px 20px rgba(0,0,0,.08);
                }

                h1 {
                    color: #b42318;
                }

                a {
                    display: inline-block;
                    margin-top: 20px;
                    background: #087f3f;
                    color: white;
                    padding: 12px 18px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                }

            </style>

        </head>

        <body>

            <div class="box">

                <h1>
                    Something went wrong
                </h1>

                <p>
                    The server encountered an unexpected error.
                </p>

                <a href="/">
                    Return Home
                </a>

            </div>

        </body>
        </html>
        """,
        500
    )


# ============================================================
# APPLICATION INFORMATION
# ============================================================

print("=" * 60)

print("GITAM CAMPUS LIFE")

print("Version:", APP_VERSION)

print("Creator:", CREATOR)

print("=" * 60)