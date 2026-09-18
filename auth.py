# ============================================================
# GITAM CAMPUS LIFE
# AUTHENTICATION SYSTEM
# Student + Faculty Registration
# Admin Approval Required
# Login / Registration / Logout
# ============================================================

from functools import wraps

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    flash,
    render_template
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import get_db


# ============================================================
# BLUEPRINT
# ============================================================

auth = Blueprint(
    "auth",
    __name__
)


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("auth.login")
            )

        return view_function(*args, **kwargs)

    return wrapped_view


# ============================================================
# ROLE REQUIRED
# ============================================================

def role_required(*allowed_roles):

    def decorator(view_function):

        @wraps(view_function)
        def wrapped_view(*args, **kwargs):

            if "user_id" not in session:
                flash(
                    "Please login first.",
                    "warning"
                )

                return redirect(
                    url_for("auth.login")
                )

            user_role = session.get("role")

            if user_role not in allowed_roles:

                flash(
                    "You are not authorized to access this page.",
                    "danger"
                )

                if user_role == "student":
                    return redirect(
                        url_for("student_dashboard")
                    )

                elif user_role == "faculty":
                    return redirect(
                        url_for("faculty_dashboard")
                    )

                elif user_role == "admin":
                    return redirect(
                        url_for("admin_dashboard")
                    )

                return redirect(
                    url_for("home")
                )

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


# ============================================================
# LOGIN
# ============================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not username or not password:

            flash(
                "Please enter username and password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # FIND USER
        # ----------------------------------------------------

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        # ----------------------------------------------------
        # USER NOT FOUND
        # ----------------------------------------------------

        if user is None:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # CHECK ACCOUNT STATUS
        # ----------------------------------------------------

        status = str(
            user["status"] or ""
        ).strip().lower()

        # ----------------------------------------------------
        # PENDING ACCOUNT
        # ----------------------------------------------------

        if status in (
            "pending",
            "pending approval"
        ):

            flash(
                "Your registration is waiting for administrator approval.",
                "warning"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # REJECTED ACCOUNT
        # ----------------------------------------------------

        if status in (
            "rejected",
            "declined"
        ):

            flash(
                "Your registration was rejected by the administrator.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # ONLY ACTIVE / APPROVED USERS CAN LOGIN
        # ----------------------------------------------------

        if status not in (
            "active",
            "approved"
        ):

            flash(
                "Your account is not approved yet. Please contact the administrator.",
                "warning"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # PASSWORD CHECK
        # ----------------------------------------------------

        try:

            password_correct = check_password_hash(
                user["password"],
                password
            )

        except Exception:

            password_correct = False

        if not password_correct:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        # ----------------------------------------------------
        # CREATE LOGIN SESSION
        # ----------------------------------------------------

        session.clear()

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        session["name"] = user["name"]

        session["role"] = user["role"]

        session["email"] = user["email"]

        session["roll_no"] = user["roll_no"]

        # Optional user information
        try:
            session["branch"] = user["branch"]
        except Exception:
            session["branch"] = ""

        try:
            session["year"] = user["year"]
        except Exception:
            session["year"] = ""

        try:
            session["designation"] = user["designation"]
        except Exception:
            session["designation"] = ""

        # ----------------------------------------------------
        # WELCOME MESSAGE
        # ----------------------------------------------------

        flash(
            f"Welcome to GITAM Campus Life, {user['name']}!",
            "success"
        )

        # ----------------------------------------------------
        # ROLE-BASED DASHBOARD
        # ----------------------------------------------------

        if user["role"] == "student":

            return redirect(
                url_for("student_dashboard")
            )

        elif user["role"] == "faculty":

            return redirect(
                url_for("faculty_dashboard")
            )

        elif user["role"] == "admin":

            return redirect(
                url_for("admin_dashboard")
            )

        # ----------------------------------------------------
        # INVALID ROLE
        # ----------------------------------------------------

        session.clear()

        flash(
            "Invalid user role.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # ========================================================
    # IMPORTANT GET RESPONSE
    # ========================================================

    return render_template(
        "login.html"
    )


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        roll_no = request.form.get(
            "roll_no",
            ""
        ).strip()

        branch = request.form.get(
            "branch",
            ""
        ).strip()

        year = request.form.get(
            "year",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not name:

            flash(
                "Full name is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # CREATE STUDENT ACCOUNT
        # ----------------------------------------------------

        return create_pending_user(
            username=username,
            password=password,
            name=name,
            email=email,
            role="student",
            roll_no=roll_no,
            branch=branch,
            year=year,
            phone=phone
        )

    # ========================================================
    # GET REQUEST
    # THIS WAS MISSING IN YOUR OLD FILE
    # ========================================================

    return render_template(
        "register.html"
    )


# ============================================================
# FACULTY REGISTRATION
# ============================================================

@auth.route("/faculty-register", methods=["GET", "POST"])
def faculty_register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        designation = request.form.get(
            "designation",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        branch = request.form.get(
            "branch",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not name:

            flash(
                "Full name is required.",
                "danger"
            )

            return render_template(
                "faculty_register.html"
            )

        if not username:

            flash(
                "Username is required.",
                "danger"
            )

            return render_template(
                "faculty_register.html"
            )

        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "faculty_register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "faculty_register.html"
            )

        if not designation:

            flash(
                "Designation is required.",
                "danger"
            )

            return render_template(
                "faculty_register.html"
            )

        # ----------------------------------------------------
        # CREATE FACULTY ACCOUNT
        # ----------------------------------------------------

        return create_pending_user(
            username=username,
            password=password,
            name=name,
            email=email,
            role="faculty",
            roll_no="",
            branch=branch,
            year="",
            phone=phone,
            designation=designation
        )

    # ========================================================
    # GET REQUEST
    # ========================================================

    return render_template(
        "faculty_register.html"
    )


# ============================================================
# CREATE PENDING USER
# ============================================================

def create_pending_user(
    username,
    password,
    name,
    email,
    role,
    roll_no="",
    branch="",
    year="",
    phone="",
    designation=""
):

    conn = get_db()

    # --------------------------------------------------------
    # CHECK USERNAME
    # --------------------------------------------------------

    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    if existing_user:

        conn.close()

        if role == "faculty":

            return render_template(
                "faculty_register.html",
                error="Username already exists. Please choose another username."
            )

        return render_template(
            "register.html",
            error="Username already exists. Please choose another username."
        )

    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    if email:

        existing_email = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_email:

            conn.close()

            if role == "faculty":

                return render_template(
                    "faculty_register.html",
                    error="Email is already registered."
                )

            return render_template(
                "register.html",
                error="Email is already registered."
            )

    # --------------------------------------------------------
    # PASSWORD HASH
    # --------------------------------------------------------

    password_hash = generate_password_hash(
        password
    )

    # --------------------------------------------------------
    # INSERT USER
    #
    # New student/faculty accounts are Pending.
    # Admin must approve them before login.
    # --------------------------------------------------------

    try:

        conn.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                name,
                email,
                role,
                roll_no,
                branch,
                year,
                designation,
                phone,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                password_hash,
                name,
                email,
                role,
                roll_no,
                branch,
                year,
                designation,
                phone,
                "Pending"
            )
        )

        conn.commit()

        conn.close()

    except Exception as error:

        print(
            "Registration error:",
            error
        )

        try:
            conn.rollback()
        except Exception:
            pass

        try:
            conn.close()
        except Exception:
            pass

        if role == "faculty":

            return render_template(
                "faculty_register.html",
                error="Registration failed. Please try again."
            )

        return render_template(
            "register.html",
            error="Registration failed. Please try again."
        )

    # --------------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------------

    if role == "faculty":

        flash(
            "Faculty registration submitted successfully. Please wait for administrator approval.",
            "success"
        )

    else:

        flash(
            "Student registration submitted successfully. Please wait for administrator approval.",
            "success"
        )

    return redirect(
        url_for("auth.login")
    )


# ============================================================
# LOGOUT
# ============================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return None

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return user


# ============================================================
# END OF AUTHENTICATION SYSTEM
# ============================================================