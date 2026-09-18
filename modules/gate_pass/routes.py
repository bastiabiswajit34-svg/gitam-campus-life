# ============================================================
# GITAM CAMPUS LIFE
# GATE PASS MODULE
# COMPLETE UPGRADED VERSION
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

gate_pass = Blueprint(
    "gate_pass",
    __name__,
    url_prefix="/gate-pass"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def logged_in():
    return "user_id" in session


def is_admin():
    return str(
        session.get("role", "")
    ).strip().lower() == "admin"


def go_home():
    try:
        return redirect(
            url_for("home")
        )
    except Exception:
        return redirect("/")


# ============================================================
# GATE PASS MAIN PAGE
# ============================================================

@gate_pass.route(
    "/",
    methods=["GET", "POST"]
)
def gate_pass_page():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if not logged_in():

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )


    user_id = session["user_id"]

    role = str(
        session.get("role", "")
    ).strip().lower()


    db = get_db()


    try:

        # ====================================================
        # ADMIN VIEW
        # ====================================================

        if role == "admin":

            # Admin cannot submit gate pass
            if request.method == "POST":

                flash(
                    "Administrator cannot submit a student/faculty gate pass.",
                    "error"
                )

                return redirect(
                    url_for("gate_pass.gate_pass_page")
                )


            # ------------------------------------------------
            # SHOW ALL GATE PASS REQUESTS
            # ------------------------------------------------

            passes = db.execute(
                """
                SELECT
                    gp.id,
                    gp.student_id,
                    gp.purpose,
                    gp.exit_date,
                    gp.return_date,
                    gp.status,
                    gp.qr_code,

                    u.name AS student_name,
                    u.username,
                    u.roll_no,
                    u.role

                FROM gate_passes gp

                LEFT JOIN users u
                    ON gp.student_id = u.id

                ORDER BY
                    CASE
                        WHEN LOWER(
                            COALESCE(gp.status, '')
                        ) = 'pending'
                        THEN 0
                        ELSE 1
                    END,
                    gp.id DESC
                """
            ).fetchall()


            return render_template(
                "gate_pass.html",
                gate_passes=passes
            )


        # ====================================================
        # STUDENT / FACULTY SUBMISSION
        # ====================================================

        if request.method == "POST":

            purpose = request.form.get(
                "purpose",
                ""
            ).strip()

            exit_date = request.form.get(
                "exit_date",
                ""
            ).strip()

            return_date = request.form.get(
                "return_date",
                ""
            ).strip()


            # ------------------------------------------------
            # VALIDATE PURPOSE
            # ------------------------------------------------

            if not purpose:

                flash(
                    "Please enter the purpose.",
                    "error"
                )

                return redirect(
                    url_for("gate_pass.gate_pass_page")
                )


            # ------------------------------------------------
            # VALIDATE EXIT DATE
            # ------------------------------------------------

            if not exit_date:

                flash(
                    "Please select the exit date.",
                    "error"
                )

                return redirect(
                    url_for("gate_pass.gate_pass_page")
                )


            # ------------------------------------------------
            # VALIDATE RETURN DATE
            # ------------------------------------------------

            if not return_date:

                flash(
                    "Please select the return date.",
                    "error"
                )

                return redirect(
                    url_for("gate_pass.gate_pass_page")
                )


            # ------------------------------------------------
            # VALIDATE DATE RANGE
            # ------------------------------------------------

            if return_date < exit_date:

                flash(
                    "Return date cannot be before exit date.",
                    "error"
                )

                return redirect(
                    url_for("gate_pass.gate_pass_page")
                )


            # =================================================
            # SAVE GATE PASS
            # =================================================

            db.execute(
                """
                INSERT INTO gate_passes
                (
                    student_id,
                    purpose,
                    exit_date,
                    return_date,
                    status,
                    qr_code
                )
                VALUES
                (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    purpose,
                    exit_date,
                    return_date,
                    "Pending",
                    None
                )
            )


            db.commit()


            flash(
                "Gate pass submitted successfully.",
                "success"
            )


            return redirect(
                url_for("gate_pass.gate_pass_page")
            )


        # ====================================================
        # SHOW MY GATE PASS REQUESTS
        # ====================================================

        passes = db.execute(
            """
            SELECT
                id,
                purpose,
                exit_date,
                return_date,
                status,
                qr_code

            FROM gate_passes

            WHERE student_id = ?

            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()


        return render_template(
            "gate_pass.html",
            gate_passes=passes
        )


    except Exception as error:

        db.rollback()

        print(
            "================================================"
        )
        print(
            "GATE PASS MODULE ERROR:"
        )
        print(
            error
        )
        print(
            "================================================"
        )


        flash(
            "Unable to process the gate pass request.",
            "error"
        )


        return redirect(
            url_for("gate_pass.gate_pass_page")
        )


    finally:

        db.close()


# ============================================================
# ADMIN APPROVE / REJECT / PENDING
# ============================================================

@gate_pass.route(
    "/admin/action/<int:request_id>/<action>",
    methods=["GET", "POST"]
)
def admin_action(
    request_id,
    action
):

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if not logged_in():

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )


    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    if not is_admin():

        flash(
            "Administrator access required.",
            "error"
        )

        return go_home()


    # --------------------------------------------------------
    # NORMALIZE ACTION
    # --------------------------------------------------------

    action = str(
        action or ""
    ).strip().lower()


    # --------------------------------------------------------
    # DETERMINE STATUS
    # --------------------------------------------------------

    if action == "approve":

        new_status = "Approved"


    elif action == "reject":

        new_status = "Rejected"


    elif action == "pending":

        new_status = "Pending"


    else:

        flash(
            "Invalid gate pass action.",
            "error"
        )

        return redirect(
            url_for("gate_pass.gate_pass_page")
        )


    db = get_db()


    try:

        # ====================================================
        # FIND REQUEST
        # ====================================================

        record = db.execute(
            """
            SELECT
                id,
                student_id,
                purpose,
                exit_date,
                return_date,
                status

            FROM gate_passes

            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()


        # ----------------------------------------------------
        # REQUEST NOT FOUND
        # ----------------------------------------------------

        if record is None:

            flash(
                "Gate pass request not found.",
                "error"
            )

            return redirect(
                url_for("gate_pass.gate_pass_page")
            )


        old_status = str(
            record["status"] or ""
        ).strip()


        # ====================================================
        # UPDATE STATUS
        # ====================================================

        db.execute(
            """
            UPDATE gate_passes

            SET status = ?

            WHERE id = ?
            """,
            (
                new_status,
                request_id
            )
        )


        db.commit()


        # ====================================================
        # VERIFY UPDATE
        # ====================================================

        updated_record = db.execute(
            """
            SELECT
                id,
                status

            FROM gate_passes

            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()


        if updated_record is None:

            flash(
                "Gate pass update could not be verified.",
                "error"
            )

            return redirect(
                url_for("gate_pass.gate_pass_page")
            )


        updated_status = str(
            updated_record["status"] or ""
        ).strip()


        if updated_status.lower() != new_status.lower():

            flash(
                "Gate pass status was not updated.",
                "error"
            )

            return redirect(
                url_for("gate_pass.gate_pass_page")
            )


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        if new_status == "Approved":

            flash(
                "Gate pass approved successfully.",
                "success"
            )


        elif new_status == "Rejected":

            flash(
                "Gate pass rejected successfully.",
                "success"
            )


        else:

            flash(
                "Gate pass changed to pending.",
                "success"
            )


        # ----------------------------------------------------
        # DEBUG INFORMATION
        # ----------------------------------------------------

        print(
            "GATE PASS STATUS:",
            "ID =", request_id,
            "|",
            old_status,
            "->",
            new_status
        )


        return redirect(
            url_for("gate_pass.gate_pass_page")
        )


    except Exception as error:

        db.rollback()

        print(
            "================================================"
        )
        print(
            "GATE PASS ADMIN ACTION ERROR:"
        )
        print(
            error
        )
        print(
            "================================================"
        )


        flash(
            "Unable to update gate pass.",
            "error"
        )


        return redirect(
            url_for("gate_pass.gate_pass_page")
        )


    finally:

        db.close()


# ============================================================
# DIRECT APPROVE ROUTE
# ============================================================

@gate_pass.route(
    "/approve/<int:request_id>",
    methods=["GET", "POST"]
)
def approve(request_id):

    return admin_action(
        request_id,
        "approve"
    )


# ============================================================
# DIRECT REJECT ROUTE
# ============================================================

@gate_pass.route(
    "/reject/<int:request_id>",
    methods=["GET", "POST"]
)
def reject(request_id):

    return admin_action(
        request_id,
        "reject"
    )


# ============================================================
# DIRECT PENDING ROUTE
# ============================================================

@gate_pass.route(
    "/pending/<int:request_id>",
    methods=["GET", "POST"]
)
def pending(request_id):

    return admin_action(
        request_id,
        "pending"
    )


# ============================================================
# END OF GATE PASS MODULE
# ============================================================
