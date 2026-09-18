# ============================================================
# GITAM CAMPUS LIFE
# LEAVE REQUEST MODULE
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

leave = Blueprint(
    "leave",
    __name__,
    url_prefix="/leave"
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
        return redirect(url_for("home"))
    except Exception:
        return redirect("/")


# ============================================================
# LEAVE MAIN PAGE
# ============================================================

@leave.route("/", methods=["GET", "POST"])
def leave_page():

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
        # ADMIN
        # ====================================================

        if role == "admin":

            # Admin cannot submit a leave request
            if request.method == "POST":

                flash(
                    "Administrator cannot submit a student leave request.",
                    "error"
                )

                return redirect(
                    url_for("leave.leave_page")
                )


            # ------------------------------------------------
            # SHOW ALL REQUESTS
            # ------------------------------------------------

            requests = db.execute(
                """
                SELECT
                    lr.id,
                    lr.student_id,
                    lr.from_date,
                    lr.to_date,
                    lr.reason,
                    lr.status,
                    lr.qr_code,

                    u.name AS student_name,
                    u.username,
                    u.roll_no,
                    u.role

                FROM leave_requests lr

                LEFT JOIN users u
                    ON lr.student_id = u.id

                ORDER BY
                    CASE
                        WHEN LOWER(
                            COALESCE(lr.status, '')
                        ) = 'pending'
                        THEN 0
                        ELSE 1
                    END,
                    lr.id DESC
                """
            ).fetchall()


            return render_template(
                "leave.html",
                leave_requests=requests
            )


        # ====================================================
        # STUDENT / FACULTY
        # ====================================================

        if request.method == "POST":

            from_date = request.form.get(
                "from_date",
                ""
            ).strip()

            to_date = request.form.get(
                "to_date",
                ""
            ).strip()

            reason = request.form.get(
                "reason",
                ""
            ).strip()


            # ------------------------------------------------
            # VALIDATE FROM DATE
            # ------------------------------------------------

            if not from_date:

                flash(
                    "Please select the starting date.",
                    "error"
                )

                return redirect(
                    url_for("leave.leave_page")
                )


            # ------------------------------------------------
            # VALIDATE TO DATE
            # ------------------------------------------------

            if not to_date:

                flash(
                    "Please select the ending date.",
                    "error"
                )

                return redirect(
                    url_for("leave.leave_page")
                )


            # ------------------------------------------------
            # VALIDATE REASON
            # ------------------------------------------------

            if not reason:

                flash(
                    "Please enter the reason for leave.",
                    "error"
                )

                return redirect(
                    url_for("leave.leave_page")
                )


            # ------------------------------------------------
            # VALIDATE DATE RANGE
            # ------------------------------------------------

            if to_date < from_date:

                flash(
                    "Ending date cannot be before starting date.",
                    "error"
                )

                return redirect(
                    url_for("leave.leave_page")
                )


            # ------------------------------------------------
            # SAVE REQUEST
            # ------------------------------------------------

            db.execute(
                """
                INSERT INTO leave_requests
                (
                    student_id,
                    from_date,
                    to_date,
                    reason,
                    status,
                    qr_code
                )
                VALUES
                (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    from_date,
                    to_date,
                    reason,
                    "Pending",
                    None
                )
            )


            db.commit()


            flash(
                "Leave request submitted successfully.",
                "success"
            )


            return redirect(
                url_for("leave.leave_page")
            )


        # ====================================================
        # SHOW USER'S OWN REQUESTS
        # ====================================================

        requests = db.execute(
            """
            SELECT
                id,
                from_date,
                to_date,
                reason,
                status,
                qr_code

            FROM leave_requests

            WHERE student_id = ?

            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()


        return render_template(
            "leave.html",
            leave_requests=requests
        )


    except Exception as error:

        db.rollback()

        print(
            "================================================"
        )
        print(
            "LEAVE MODULE ERROR:"
        )
        print(
            error
        )
        print(
            "================================================"
        )


        flash(
            "Unable to process the leave request.",
            "error"
        )


        return redirect(
            url_for("leave.leave_page")
        )


    finally:

        db.close()


# ============================================================
# ADMIN APPROVE / REJECT / PENDING
# ============================================================

@leave.route(
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
    # DETERMINE NEW STATUS
    # --------------------------------------------------------

    if action == "approve":

        new_status = "Approved"


    elif action == "reject":

        new_status = "Rejected"


    elif action == "pending":

        new_status = "Pending"


    else:

        flash(
            "Invalid leave action.",
            "error"
        )

        return redirect(
            url_for("leave.leave_page")
        )


    db = get_db()


    try:

        # ====================================================
        # FIND REQUEST
        # ====================================================

        request_record = db.execute(
            """
            SELECT
                id,
                student_id,
                from_date,
                to_date,
                reason,
                status

            FROM leave_requests

            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()


        # ----------------------------------------------------
        # REQUEST NOT FOUND
        # ----------------------------------------------------

        if request_record is None:

            flash(
                "Leave request not found.",
                "error"
            )

            return redirect(
                url_for("leave.leave_page")
            )


        old_status = str(
            request_record["status"] or ""
        ).strip()


        # ====================================================
        # UPDATE STATUS
        # ====================================================

        db.execute(
            """
            UPDATE leave_requests

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

            FROM leave_requests

            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()


        if updated_record is None:

            flash(
                "Leave request update could not be verified.",
                "error"
            )

            return redirect(
                url_for("leave.leave_page")
            )


        updated_status = str(
            updated_record["status"] or ""
        ).strip()


        if updated_status.lower() != new_status.lower():

            flash(
                "Leave request status was not updated.",
                "error"
            )

            return redirect(
                url_for("leave.leave_page")
            )


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        if new_status == "Approved":

            flash(
                "Leave request approved successfully.",
                "success"
            )


        elif new_status == "Rejected":

            flash(
                "Leave request rejected successfully.",
                "success"
            )


        else:

            flash(
                "Leave request changed to pending.",
                "success"
            )


        # ----------------------------------------------------
        # DEBUG MESSAGE
        # ----------------------------------------------------

        print(
            "LEAVE STATUS:",
            "ID =", request_id,
            "|",
            old_status,
            "->",
            new_status
        )


        return redirect(
            url_for("leave.leave_page")
        )


    except Exception as error:

        db.rollback()

        print(
            "================================================"
        )
        print(
            "LEAVE ADMIN ACTION ERROR:"
        )
        print(
            error
        )
        print(
            "================================================"
        )


        flash(
            "Unable to update leave request.",
            "error"
        )


        return redirect(
            url_for("leave.leave_page")
        )


    finally:

        db.close()


# ============================================================
# DIRECT APPROVE ROUTE
# ============================================================

@leave.route(
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

@leave.route(
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

@leave.route(
    "/pending/<int:request_id>",
    methods=["GET", "POST"]
)
def pending(request_id):

    return admin_action(
        request_id,
        "pending"
    )


# ============================================================
# END OF LEAVE MODULE
# ============================================================
