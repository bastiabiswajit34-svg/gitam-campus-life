# ============================================================
# GITAM CAMPUS LIFE
# CERTIFICATE REQUEST MODULE
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

certificates = Blueprint(
    "certificates",
    __name__,
    url_prefix="/certificates"
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
# CERTIFICATE MAIN PAGE
# ============================================================

@certificates.route(
    "/",
    methods=["GET", "POST"]
)
def certificates_page():

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

            # Admin cannot submit certificate requests
            if request.method == "POST":

                flash(
                    "Administrator cannot submit a student/faculty certificate request.",
                    "error"
                )

                return redirect(
                    url_for("certificates.certificates_page")
                )


            # ------------------------------------------------
            # GET ALL CERTIFICATE REQUESTS
            # ------------------------------------------------

            requests = db.execute(
                """
                SELECT
                    cr.id,
                    cr.student_id,
                    cr.certificate_type,
                    cr.reason,
                    cr.status,

                    u.name AS student_name,
                    u.username,
                    u.roll_no,
                    u.role

                FROM certificate_requests cr

                LEFT JOIN users u
                    ON cr.student_id = u.id

                ORDER BY
                    CASE
                        WHEN LOWER(
                            COALESCE(cr.status, '')
                        ) = 'pending'
                        THEN 0
                        ELSE 1
                    END,
                    cr.id DESC
                """
            ).fetchall()


            return render_template(
                "certificates.html",
                certificate_requests=requests
            )


        # ====================================================
        # STUDENT / FACULTY SUBMISSION
        # ====================================================

        if request.method == "POST":

            certificate_type = request.form.get(
                "certificate_type",
                ""
            ).strip()

            reason = request.form.get(
                "reason",
                ""
            ).strip()


            # ------------------------------------------------
            # COMPATIBILITY WITH OLDER FORM
            # ------------------------------------------------

            if not reason:

                reason = request.form.get(
                    "purpose",
                    ""
                ).strip()


            # ------------------------------------------------
            # VALIDATE CERTIFICATE TYPE
            # ------------------------------------------------

            if not certificate_type:

                flash(
                    "Please select a certificate type.",
                    "error"
                )

                return redirect(
                    url_for("certificates.certificates_page")
                )


            # ------------------------------------------------
            # VALIDATE REASON
            # ------------------------------------------------

            if not reason:

                flash(
                    "Please enter the reason for your request.",
                    "error"
                )

                return redirect(
                    url_for("certificates.certificates_page")
                )


            # =================================================
            # SAVE CERTIFICATE REQUEST
            # =================================================

            db.execute(
                """
                INSERT INTO certificate_requests
                (
                    student_id,
                    certificate_type,
                    reason,
                    status
                )
                VALUES
                (?, ?, ?, ?)
                """,
                (
                    user_id,
                    certificate_type,
                    reason,
                    "Pending"
                )
            )


            db.commit()


            flash(
                "Certificate request submitted successfully.",
                "success"
            )


            return redirect(
                url_for("certificates.certificates_page")
            )


        # ====================================================
        # SHOW MY CERTIFICATE REQUESTS
        # ====================================================

        requests = db.execute(
            """
            SELECT
                id,
                certificate_type,
                reason,
                status

            FROM certificate_requests

            WHERE student_id = ?

            ORDER BY id DESC
            """,
            (user_id,)
        ).fetchall()


        return render_template(
            "certificates.html",
            certificate_requests=requests
        )


    except Exception as error:

        db.rollback()

        print(
            "================================================"
        )
        print(
            "CERTIFICATE MODULE ERROR:"
        )
        print(
            error
        )
        print(
            "================================================"
        )


        flash(
            "Unable to process the certificate request.",
            "error"
        )


        return redirect(
            url_for("certificates.certificates_page")
        )


    finally:

        db.close()


# ============================================================
# ADMIN APPROVE / REJECT / PENDING
# ============================================================

@certificates.route(
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
            "Invalid certificate action.",
            "error"
        )

        return redirect(
            url_for("certificates.certificates_page")
        )


    db = get_db()


    try:

        # ====================================================
        # FIND CERTIFICATE REQUEST
        # ====================================================

        record = db.execute(
            """
            SELECT
                id,
                student_id,
                certificate_type,
                reason,
                status

            FROM certificate_requests

            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()


        # ----------------------------------------------------
        # REQUEST NOT FOUND
        # ----------------------------------------------------

        if record is None:

            flash(
                "Certificate request not found.",
                "error"
            )

            return redirect(
                url_for("certificates.certificates_page")
            )


        old_status = str(
            record["status"] or ""
        ).strip()


        # ====================================================
        # UPDATE STATUS
        # ====================================================

        db.execute(
            """
            UPDATE certificate_requests

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

            FROM certificate_requests

            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()


        if updated_record is None:

            flash(
                "Certificate request update could not be verified.",
                "error"
            )

            return redirect(
                url_for("certificates.certificates_page")
            )


        updated_status = str(
            updated_record["status"] or ""
        ).strip()


        if updated_status.lower() != new_status.lower():

            flash(
                "Certificate request status was not updated.",
                "error"
            )

            return redirect(
                url_for("certificates.certificates_page")
            )


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        if new_status == "Approved":

            flash(
                "Certificate request approved successfully.",
                "success"
            )


        elif new_status == "Rejected":

            flash(
                "Certificate request rejected successfully.",
                "success"
            )


        else:

            flash(
                "Certificate request changed to pending.",
                "success"
            )


        # ----------------------------------------------------
        # DEBUG INFORMATION
        # ----------------------------------------------------

        print(
            "CERTIFICATE STATUS:",
            "ID =", request_id,
            "|",
            old_status,
            "->",
            new_status
        )


        return redirect(
            url_for("certificates.certificates_page")
        )


    except Exception as error:

        db.rollback()

        print(
            "================================================"
        )
        print(
            "CERTIFICATE ADMIN ACTION ERROR:"
        )
        print(
            error
        )
        print(
            "================================================"
        )


        flash(
            "Unable to update certificate request.",
            "error"
        )


        return redirect(
            url_for("certificates.certificates_page")
        )


    finally:

        db.close()


# ============================================================
# DIRECT APPROVE ROUTE
# ============================================================

@certificates.route(
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

@certificates.route(
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

@certificates.route(
    "/pending/<int:request_id>",
    methods=["GET", "POST"]
)
def pending(request_id):

    return admin_action(
        request_id,
        "pending"
    )


# ============================================================
# END OF CERTIFICATE MODULE
# ============================================================
