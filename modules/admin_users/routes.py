# ============================================================
# GITAM CAMPUS LIFE 2.0
# ADMIN USER MANAGEMENT
# COMPLETE UPGRADED VERSION
# ============================================================

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    render_template,
    session
)

import sqlite3
from functools import wraps

from database import get_db
from auth import login_required


# ============================================================
# BLUEPRINT
# ============================================================

admin_users = Blueprint(
    "admin_users",
    __name__,
    url_prefix="/admin/users"
)


# ============================================================
# ADMIN ACCESS CHECK
# ============================================================

def admin_only(function):

    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):

        role = str(
            session.get("role", "")
        ).strip().lower()

        if role != "admin":

            flash(
                "Admin access required.",
                "error"
            )

            try:
                return redirect(
                    url_for("admin_dashboard")
                )
            except Exception:
                pass

            try:
                return redirect(
                    url_for("dashboard")
                )
            except Exception:
                return redirect("/")

        return function(*args, **kwargs)

    return wrapper


# ============================================================
# SAFE TABLE CHECK
# ============================================================

def table_exists(conn, table_name):

    try:

        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (table_name,)
        ).fetchone()

        return row is not None

    except Exception:

        return False


# ============================================================
# SAFE COLUMN CHECK
# ============================================================

def column_exists(conn, table_name, column_name):

    try:

        rows = conn.execute(
            "PRAGMA table_info(" + table_name + ")"
        ).fetchall()

        for row in rows:

            try:

                if row["name"] == column_name:
                    return True

            except Exception:

                if row[1] == column_name:
                    return True

        return False

    except Exception:

        return False


# ============================================================
# CLEAN USER RELATED RECORDS
# ============================================================

def cleanup_user_records(conn, user_id, username):

    cleanup_targets = [

        # Attendance
        ("attendance", "user_id"),
        ("attendance", "student_id"),
        ("attendance", "username"),
        ("attendance", "student_username"),

        # Leave
        ("leave_requests", "user_id"),
        ("leave_requests", "student_id"),
        ("leave_requests", "username"),
        ("leave_requests", "student_username"),

        # Gate Pass
        ("gate_passes", "user_id"),
        ("gate_passes", "student_id"),
        ("gate_passes", "username"),
        ("gate_passes", "student_username"),

        # Certificates
        ("certificate_requests", "user_id"),
        ("certificate_requests", "student_id"),
        ("certificate_requests", "username"),
        ("certificate_requests", "student_username"),

        # Complaints
        ("complaints", "user_id"),
        ("complaints", "student_id"),
        ("complaints", "username"),
        ("complaints", "student_username"),

        # Notifications
        ("notifications", "user_id"),
        ("notifications", "student_id"),
        ("notifications", "username"),
        ("notifications", "student_username"),

        # Digital ID
        ("digital_ids", "user_id"),
        ("digital_ids", "student_id"),
        ("digital_ids", "username"),
        ("digital_ids", "student_username"),

        # Events
        ("event_registrations", "user_id"),
        ("event_registrations", "student_id"),
        ("event_registrations", "username"),
        ("event_registrations", "student_username"),

        # Old requests
        ("requests", "user_id"),
        ("requests", "student_id"),
        ("requests", "username"),
        ("requests", "student_username"),

        # Old QR attendance
        ("qr_attendance", "user_id"),
        ("qr_attendance", "student_id"),
        ("qr_attendance", "username"),
        ("qr_attendance", "student_username"),

        # Messages
        ("messages", "user_id"),
        ("messages", "sender_id"),
        ("messages", "receiver_id"),
        ("messages", "username"),
        ("messages", "sender"),
        ("messages", "receiver"),

        # Audit
        ("audit_logs", "user_id"),
        ("audit_logs", "username")
    ]


    # --------------------------------------------------------
    # DELETE BY USER ID
    # --------------------------------------------------------

    for table, column in cleanup_targets:

        try:

            if not table_exists(
                conn,
                table
            ):
                continue

            if not column_exists(
                conn,
                table,
                column
            ):
                continue

            conn.execute(
                "DELETE FROM "
                + table
                + " WHERE "
                + column
                + "=?",
                (user_id,)
            )

        except Exception as error:

            print(
                "Cleanup skipped:",
                table,
                column,
                error
            )


    # --------------------------------------------------------
    # DELETE BY USERNAME
    # --------------------------------------------------------

    if username:

        username_targets = [

            ("attendance", "username"),
            ("attendance", "student_username"),

            ("leave_requests", "username"),
            ("leave_requests", "student_username"),

            ("gate_passes", "username"),
            ("gate_passes", "student_username"),

            ("certificate_requests", "username"),
            ("certificate_requests", "student_username"),

            ("complaints", "username"),
            ("complaints", "student_username"),

            ("notifications", "username"),
            ("notifications", "student_username"),

            ("digital_ids", "username"),
            ("digital_ids", "student_username"),

            ("event_registrations", "username"),
            ("event_registrations", "student_username"),

            ("requests", "username"),
            ("requests", "student_username"),

            ("qr_attendance", "username"),
            ("qr_attendance", "student_username"),

            ("messages", "username"),
            ("messages", "sender"),
            ("messages", "receiver"),

            ("audit_logs", "username")
        ]


        for table, column in username_targets:

            try:

                if not table_exists(
                    conn,
                    table
                ):
                    continue

                if not column_exists(
                    conn,
                    table,
                    column
                ):
                    continue

                conn.execute(
                    "DELETE FROM "
                    + table
                    + " WHERE "
                    + column
                    + "=?",
                    (username,)
                )

            except Exception as error:

                print(
                    "Username cleanup skipped:",
                    table,
                    column,
                    error
                )


# ============================================================
# ADMIN USERS MAIN PAGE
# ============================================================

@admin_users.route("/")
@admin_only
def users():

    conn = get_db()

    try:

        search = request.args.get(
            "search",
            ""
        ).strip()

        role = request.args.get(
            "role",
            ""
        ).strip().lower()


        # ----------------------------------------------------
        # USER QUERY
        # ----------------------------------------------------

        query = """
            SELECT
                id,
                username,
                name,
                email,
                role,
                roll_no,
                branch,
                year,
                designation,
                phone,
                profile_image,
                status,
                created_at,
                updated_at
            FROM users
            WHERE 1=1
        """

        params = []


        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        if search:

            query += """
                AND (
                    username LIKE ?
                    OR name LIKE ?
                    OR email LIKE ?
                    OR roll_no LIKE ?
                    OR phone LIKE ?
                )
            """

            search_value = "%" + search + "%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ])


        # ----------------------------------------------------
        # ROLE FILTER
        # ----------------------------------------------------

        if role in (
            "student",
            "faculty",
            "admin"
        ):

            query += """
                AND LOWER(role) = ?
            """

            params.append(role)


        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

        query += """
            ORDER BY id DESC
        """


        users_list = conn.execute(
            query,
            params
        ).fetchall()


        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        total_users = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            """
        ).fetchone()[0]


        total_students = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE LOWER(role) = 'student'
            """
        ).fetchone()[0]


        total_faculty = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE LOWER(role) = 'faculty'
            """
        ).fetchone()[0]


        total_admins = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE LOWER(role) = 'admin'
            """
        ).fetchone()[0]


        active_users = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE LOWER(COALESCE(status, ''))
            IN ('active', 'approved')
            """
        ).fetchone()[0]


        inactive_users = conn.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE LOWER(COALESCE(status, ''))
            NOT IN ('active', 'approved')
            """
        ).fetchone()[0]


        # ----------------------------------------------------
        # PENDING STUDENTS
        # ----------------------------------------------------

        pending_students = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(role) = 'student'
            AND LOWER(COALESCE(status, '')) = 'pending'
            ORDER BY id DESC
            """
        ).fetchall()


        # ----------------------------------------------------
        # PENDING FACULTY
        # ----------------------------------------------------

        pending_faculty = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(role) = 'faculty'
            AND LOWER(COALESCE(status, '')) = 'pending'
            ORDER BY id DESC
            """
        ).fetchall()


        # ----------------------------------------------------
        # APPROVED USERS
        # ----------------------------------------------------

        approved_users = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(COALESCE(status, ''))
            IN ('active', 'approved')
            ORDER BY id DESC
            """
        ).fetchall()


        # ----------------------------------------------------
        # REJECTED USERS
        # ----------------------------------------------------

        rejected_users = conn.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(COALESCE(status, '')) = 'rejected'
            ORDER BY id DESC
            """
        ).fetchall()


    finally:

        conn.close()


    return render_template(
        "admin_users.html",

        users=users_list,

        pending_students=pending_students,
        pending_faculty=pending_faculty,
        approved_users=approved_users,
        rejected_users=rejected_users,

        total_users=total_users,
        total_students=total_students,
        total_faculty=total_faculty,
        total_admins=total_admins,
        active_users=active_users,
        inactive_users=inactive_users,

        search=search,
        selected_role=role
    )


# ============================================================
# COMPATIBILITY ENDPOINT
# ============================================================
#
# Some admin dashboard templates use:
#
# url_for("admin_users.admin_users_page")
#
# The main route above is named "users".
# This second endpoint gives the dashboard the name it expects.
#
# ============================================================

@admin_users.route(
    "/page",
    endpoint="admin_users_page"
)
@admin_only
def admin_users_page():

    return users()


# ============================================================
# ADD USER
# ============================================================

@admin_users.route(
    "/add",
    methods=["GET", "POST"]
)
@admin_only
def add_user():

    if request.method == "GET":

        return render_template(
            "admin_add_user.html"
        )


    username = request.form.get(
        "username",
        ""
    ).strip()

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    role = request.form.get(
        "role",
        ""
    ).strip().lower()

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

    designation = request.form.get(
        "designation",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not username or not name or not password:

        flash(
            "Username, name and password are required.",
            "error"
        )

        return redirect(
            url_for(
                "admin_users.add_user"
            )
        )


    if role not in (
        "student",
        "faculty",
        "admin"
    ):

        flash(
            "Invalid user role.",
            "error"
        )

        return redirect(
            url_for(
                "admin_users.add_user"
            )
        )


    # --------------------------------------------------------
    # PASSWORD HASH
    # --------------------------------------------------------

    from werkzeug.security import generate_password_hash

    password_hash = generate_password_hash(
        password
    )


    conn = get_db()

    try:

        existing = conn.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()


        if existing:

            flash(
                "Username already exists.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.add_user"
                )
            )


        conn.execute(
            """
            INSERT INTO users (
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
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
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
                "active"
            )
        )


        conn.commit()


        flash(
            "User created successfully.",
            "success"
        )


    except Exception as error:

        conn.rollback()

        print(
            "ADD USER ERROR:",
            error
        )

        flash(
            "Unable to create user.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.users"
        )
    )


# ============================================================
# APPROVE USER
# ============================================================

@admin_users.route(
    "/approve/<int:user_id>",
    methods=["POST"]
)
@admin_only
def approve_user(user_id):

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT id, name, role
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        if user is None:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        conn.execute(
            """
            UPDATE users
            SET status = 'Active',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (user_id,)
        )


        conn.commit()


        flash(
            user["name"]
            + " has been approved successfully.",
            "success"
        )


    except Exception as error:

        conn.rollback()

        print(
            "APPROVE USER ERROR:",
            error
        )

        flash(
            "Unable to approve user.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.users"
        )
    )


# ============================================================
# REJECT USER
# ============================================================

@admin_users.route(
    "/reject/<int:user_id>",
    methods=["POST"]
)
@admin_only
def reject_user(user_id):

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT id, name, role
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        if user is None:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        if str(
            user["role"] or ""
        ).lower() == "admin":

            flash(
                "Administrator accounts cannot be rejected.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        conn.execute(
            """
            UPDATE users
            SET status = 'Rejected',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (user_id,)
        )


        conn.commit()


        flash(
            user["name"]
            + " has been rejected.",
            "success"
        )


    except Exception as error:

        conn.rollback()

        print(
            "REJECT USER ERROR:",
            error
        )

        flash(
            "Unable to reject user.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.users"
        )
    )


# ============================================================
# REMOVE APPROVED USER
# ============================================================

@admin_users.route(
    "/remove/<int:user_id>",
    methods=["POST"]
)
@admin_only
def remove_user(user_id):

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        if user is None:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        user_role = str(
            user["role"] or ""
        ).strip().lower()


        if user_role == "admin":

            flash(
                "Administrator accounts are protected and cannot be removed.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        current_user_id = session.get(
            "user_id"
        )


        if current_user_id is not None:

            try:

                if int(current_user_id) == int(user_id):

                    flash(
                        "You cannot remove your own account.",
                        "error"
                    )

                    return redirect(
                        url_for(
                            "admin_users.users"
                        )
                    )

            except Exception:
                pass


        username = str(
            user["username"] or ""
        ).strip()

        name = str(
            user["name"] or "User"
        ).strip()


        # ----------------------------------------------------
        # CLEAN DEPENDENT RECORDS
        # ----------------------------------------------------

        cleanup_user_records(
            conn,
            user_id,
            username
        )


        # ----------------------------------------------------
        # DELETE USER
        # ----------------------------------------------------

        conn.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )


        conn.commit()


        flash(
            name
            + " has been permanently removed.",
            "success"
        )


    except sqlite3.IntegrityError as error:

        conn.rollback()

        print(
            "USER REMOVAL FOREIGN KEY ERROR:",
            error
        )

        flash(
            "User cannot be removed because another database record still depends on this account.",
            "error"
        )


    except Exception as error:

        conn.rollback()

        print(
            "REMOVE USER ERROR:",
            error
        )

        flash(
            "Unable to remove user.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.users"
        )
    )


# ============================================================
# DELETE REJECTED USER
# ============================================================

@admin_users.route(
    "/delete/<int:user_id>",
    methods=["POST"]
)
@admin_only
def delete_user(user_id):

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT
                id,
                name,
                role,
                status,
                username
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        if user is None:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        role = str(
            user["role"] or ""
        ).strip().lower()

        status = str(
            user["status"] or ""
        ).strip().lower()


        if role == "admin":

            flash(
                "Administrator accounts are protected.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        if status != "rejected":

            flash(
                "Only rejected registrations can be deleted using this option.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        cleanup_user_records(
            conn,
            user_id,
            user["username"]
        )


        conn.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )


        conn.commit()


        flash(
            user["name"]
            + " has been permanently deleted.",
            "success"
        )


    except sqlite3.IntegrityError as error:

        conn.rollback()

        print(
            "DELETE REJECTED USER FOREIGN KEY ERROR:",
            error
        )

        flash(
            "Unable to delete the user because a related database record still exists.",
            "error"
        )


    except Exception as error:

        conn.rollback()

        print(
            "DELETE REJECTED USER ERROR:",
            error
        )

        flash(
            "Unable to delete user.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.users"
        )
    )


# ============================================================
# REMOVE APPROVED USER COMPATIBILITY
# ============================================================

@admin_users.route(
    "/remove-approved/<int:user_id>",
    methods=["POST"]
)
@admin_only
def remove_approved_user(user_id):

    return remove_user(user_id)


# ============================================================
# EDIT USER
# ============================================================

@admin_users.route(
    "/edit/<int:user_id>",
    methods=["GET", "POST"]
)
@admin_only
def edit_user(user_id):

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        if user is None:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        if request.method == "GET":

            return render_template(
                "admin_edit_user.html",
                user=user
            )


        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
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

        designation = request.form.get(
            "designation",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        status = request.form.get(
            "status",
            user["status"] or "Active"
        ).strip()


        if not name:

            flash(
                "Name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.edit_user",
                    user_id=user_id
                )
            )


        conn.execute(
            """
            UPDATE users
            SET
                name = ?,
                email = ?,
                branch = ?,
                year = ?,
                designation = ?,
                phone = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                name,
                email,
                branch,
                year,
                designation,
                phone,
                status,
                user_id
            )
        )


        conn.commit()


        flash(
            "User updated successfully.",
            "success"
        )


    except Exception as error:

        conn.rollback()

        print(
            "EDIT USER ERROR:",
            error
        )

        flash(
            "Unable to update user.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.users"
        )
    )


# ============================================================
# RESET PASSWORD
# ============================================================

@admin_users.route(
    "/reset-password/<int:user_id>",
    methods=["POST"]
)
@admin_only
def reset_password(user_id):

    from werkzeug.security import generate_password_hash


    new_password = request.form.get(
        "new_password",
        ""
    )


    if len(new_password) < 6:

        flash(
            "Password must contain at least 6 characters.",
            "error"
        )

        return redirect(
            url_for(
                "admin_users.edit_user",
                user_id=user_id
            )
        )


    password_hash = generate_password_hash(
        new_password
    )


    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT id, role
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        if user is None:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_users.users"
                )
            )


        conn.execute(
            """
            UPDATE users
            SET
                password = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                password_hash,
                user_id
            )
        )


        conn.commit()


        flash(
            "Password reset successfully.",
            "success"
        )


    except Exception as error:

        conn.rollback()

        print(
            "RESET PASSWORD ERROR:",
            error
        )

        flash(
            "Unable to reset password.",
            "error"
        )


    finally:

        conn.close()


    return redirect(
        url_for(
            "admin_users.edit_user",
            user_id=user_id
        )
    )


# ============================================================
# END OF ADMIN USER MANAGEMENT
# ============================================================
