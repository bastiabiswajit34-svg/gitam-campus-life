# ============================================================
# GITAM CAMPUS LIFE
# COMPLAINTS MODULE
# COMPLETE CORRECTED VERSION
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

complaints = Blueprint(
    "complaints",
    __name__,
    url_prefix="/complaints"
)


# ============================================================
# HELPERS
# ============================================================

def logged_in():
    return "user_id" in session


def is_admin():
    return session.get("role") == "admin"


def go_home():
    """
    Safe redirect helper.
    """
    try:
        return redirect(url_for("auth.login"))
    except Exception:
        return redirect("/login")


# ============================================================
# MAIN COMPLAINTS PAGE
# ============================================================

@complaints.route("/", methods=["GET", "POST"])
def complaints_page():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if not logged_in():
        return go_home()

    db = None

    try:

        db = get_db()

        # ====================================================
        # POST - SUBMIT COMPLAINT
        # ====================================================

        if request.method == "POST":

            # ------------------------------------------------
            # Read form values
            # ------------------------------------------------

            category = (
                request.form.get("category")
                or request.form.get("complaint_category")
                or "General"
            ).strip()

            subject = (
                request.form.get("subject")
                or request.form.get("title")
                or ""
            ).strip()

            description = (
                request.form.get("description")
                or request.form.get("complaint")
                or ""
            ).strip()

            # ------------------------------------------------
            # Validation
            # ------------------------------------------------

            if not subject:
                flash("Please enter a complaint subject.", "error")
                return redirect(
                    url_for("complaints.complaints_page")
                )

            if not description:
                flash("Please enter the complaint description.", "error")
                return redirect(
                    url_for("complaints.complaints_page")
                )

            # ------------------------------------------------
            # Make sure category is never empty
            # ------------------------------------------------

            if not category:
                category = "General"

            # ------------------------------------------------
            # Insert complaint
            #
            # IMPORTANT:
            # complaints table uses user_id
            # category is NOT NULL
            # ------------------------------------------------

            db.execute(
                """
                INSERT INTO complaints
                (
                    user_id,
                    category,
                    subject,
                    description,
                    status,
                    response
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    category,
                    subject,
                    description,
                    "Pending",
                    None
                )
            )

            db.commit()

            flash(
                "Complaint submitted successfully.",
                "success"
            )

            return redirect(
                url_for("complaints.complaints_page")
            )

        # ====================================================
        # ADMIN VIEW
        # ====================================================

        if is_admin():

            rows = db.execute(
                """
                SELECT
                    c.id,
                    c.user_id,
                    c.category,
                    c.subject,
                    c.description,
                    c.status,
                    c.response,
                    u.name AS user_name,
                    u.username,
                    u.email,
                    u.role,
                    u.roll_no
                FROM complaints c
                LEFT JOIN users u
                    ON c.user_id = u.id
                ORDER BY
                    CASE
                        WHEN c.status = 'Pending' THEN 0
                        WHEN c.status = 'In Progress' THEN 1
                        WHEN c.status = 'Resolved' THEN 2
                        WHEN c.status = 'Rejected' THEN 3
                        ELSE 4
                    END,
                    c.id DESC
                """
            ).fetchall()

            return render_template(
                "complaints.html",
                complaints=rows,
                is_admin=True
            )

        # ====================================================
        # STUDENT / FACULTY VIEW
        # ====================================================

        rows = db.execute(
            """
            SELECT
                id,
                user_id,
                category,
                subject,
                description,
                status,
                response
            FROM complaints
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (session["user_id"],)
        ).fetchall()

        return render_template(
            "complaints.html",
            complaints=rows,
            is_admin=False
        )

    except Exception as e:

        print(
            "[COMPLAINTS ERROR]",
            repr(e)
        )

        if request.method == "POST":
            flash(
                "Unable to submit complaint. Please try again.",
                "error"
            )
            return redirect(
                url_for("complaints.complaints_page")
            )

        flash(
            "Unable to load complaints.",
            "error"
        )

        return redirect(
            url_for("complaints.complaints_page")
        )

    finally:

        # ----------------------------------------------------
        # Close database connection
        # ----------------------------------------------------

        if db is not None:
            try:
                db.close()
            except Exception:
                pass


# ============================================================
# ADMIN ACTION
# ============================================================

@complaints.route(
    "/admin/action/<int:complaint_id>/<action>",
    methods=["GET", "POST"]
)
def admin_action(complaint_id, action):

    # --------------------------------------------------------
    # Admin check
    # --------------------------------------------------------

    if not logged_in():
        return go_home()

    if not is_admin():
        flash(
            "Admin access required.",
            "error"
        )
        return redirect(
            url_for("complaints.complaints_page")
        )

    # --------------------------------------------------------
    # Allowed actions
    # --------------------------------------------------------

    allowed_actions = {
        "resolve": "Resolved",
        "resolved": "Resolved",
        "reject": "Rejected",
        "rejected": "Rejected",
        "pending": "Pending",
        "in-progress": "In Progress",
        "in_progress": "In Progress",
        "progress": "In Progress"
    }

    new_status = allowed_actions.get(
        action.lower()
    )

    if new_status is None:
        flash(
            "Invalid complaint action.",
            "error"
        )
        return redirect(
            url_for("complaints.complaints_page")
        )

    db = None

    try:

        db = get_db()

        # ----------------------------------------------------
        # Check complaint exists
        # ----------------------------------------------------

        complaint = db.execute(
            """
            SELECT id
            FROM complaints
            WHERE id = ?
            """,
            (complaint_id,)
        ).fetchone()

        if complaint is None:

            flash(
                "Complaint not found.",
                "error"
            )

            return redirect(
                url_for("complaints.complaints_page")
            )

        # ----------------------------------------------------
        # Optional admin response
        # ----------------------------------------------------

        response_text = (
            request.form.get("response")
            or request.form.get("admin_response")
            or None
        )

        if response_text:
            response_text = response_text.strip()

        # ----------------------------------------------------
        # Update status
        # ----------------------------------------------------

        if response_text:

            db.execute(
                """
                UPDATE complaints
                SET
                    status = ?,
                    response = ?
                WHERE id = ?
                """,
                (
                    new_status,
                    response_text,
                    complaint_id
                )
            )

        else:

            db.execute(
                """
                UPDATE complaints
                SET status = ?
                WHERE id = ?
                """,
                (
                    new_status,
                    complaint_id
                )
            )

        db.commit()

        # ----------------------------------------------------
        # Verify update
        # ----------------------------------------------------

        updated = db.execute(
            """
            SELECT status
            FROM complaints
            WHERE id = ?
            """,
            (complaint_id,)
        ).fetchone()

        if updated is None:

            flash(
                "Complaint update could not be verified.",
                "error"
            )

        elif updated["status"] != new_status:

            flash(
                "Complaint status was not updated.",
                "error"
            )

        else:

            flash(
                f"Complaint marked as {new_status}.",
                "success"
            )

        return redirect(
            url_for("complaints.complaints_page")
        )

    except Exception as e:

        print(
            "[COMPLAINT ADMIN ERROR]",
            repr(e)
        )

        flash(
            "Unable to update complaint.",
            "error"
        )

        return redirect(
            url_for("complaints.complaints_page")
        )

    finally:

        if db is not None:
            try:
                db.close()
            except Exception:
                pass


# ============================================================
# COMPATIBILITY ROUTES
# ============================================================

@complaints.route(
    "/approve/<int:complaint_id>",
    methods=["GET", "POST"]
)
def approve(complaint_id):

    if not logged_in() or not is_admin():
        return go_home()

    db = None

    try:

        db = get_db()

        db.execute(
            """
            UPDATE complaints
            SET status = 'In Progress'
            WHERE id = ?
            """,
            (complaint_id,)
        )

        db.commit()

        flash(
            "Complaint marked as In Progress.",
            "success"
        )

    except Exception as e:

        print(
            "[COMPLAINT APPROVE ERROR]",
            repr(e)
        )

        flash(
            "Unable to update complaint.",
            "error"
        )

    finally:

        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    return redirect(
        url_for("complaints.complaints_page")
    )


# ============================================================

@complaints.route(
    "/resolve/<int:complaint_id>",
    methods=["GET", "POST"]
)
def resolve(complaint_id):

    if not logged_in() or not is_admin():
        return go_home()

    db = None

    try:

        db = get_db()

        db.execute(
            """
            UPDATE complaints
            SET status = 'Resolved'
            WHERE id = ?
            """,
            (complaint_id,)
        )

        db.commit()

        flash(
            "Complaint resolved successfully.",
            "success"
        )

    except Exception as e:

        print(
            "[COMPLAINT RESOLVE ERROR]",
            repr(e)
        )

        flash(
            "Unable to resolve complaint.",
            "error"
        )

    finally:

        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    return redirect(
        url_for("complaints.complaints_page")
    )


# ============================================================

@complaints.route(
    "/reject/<int:complaint_id>",
    methods=["GET", "POST"]
)
def reject(complaint_id):

    if not logged_in() or not is_admin():
        return go_home()

    db = None

    try:

        db = get_db()

        db.execute(
            """
            UPDATE complaints
            SET status = 'Rejected'
            WHERE id = ?
            """,
            (complaint_id,)
        )

        db.commit()

        flash(
            "Complaint rejected.",
            "success"
        )

    except Exception as e:

        print(
            "[COMPLAINT REJECT ERROR]",
            repr(e)
        )

        flash(
            "Unable to reject complaint.",
            "error"
        )

    finally:

        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    return redirect(
        url_for("complaints.complaints_page")
    )


# ============================================================

@complaints.route(
    "/pending/<int:complaint_id>",
    methods=["GET", "POST"]
)
def pending(complaint_id):

    if not logged_in() or not is_admin():
        return go_home()

    db = None

    try:

        db = get_db()

        db.execute(
            """
            UPDATE complaints
            SET status = 'Pending'
            WHERE id = ?
            """,
            (complaint_id,)
        )

        db.commit()

        flash(
            "Complaint moved back to Pending.",
            "success"
        )

    except Exception as e:

        print(
            "[COMPLAINT PENDING ERROR]",
            repr(e)
        )

        flash(
            "Unable to update complaint.",
            "error"
        )

    finally:

        if db is not None:
            try:
                db.close()
            except Exception:
                pass

    return redirect(
        url_for("complaints.complaints_page")
    )


# ============================================================
# MODULE LOADED MESSAGE
# ============================================================

print("[OK] Complaints module loaded.")
