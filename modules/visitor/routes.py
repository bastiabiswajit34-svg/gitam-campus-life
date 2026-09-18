# ============================================================
# GITAM CAMPUS LIFE
# VISITOR PASS MODULE
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

from database import get_db

import secrets
from datetime import datetime


# ============================================================
# BLUEPRINT
# ============================================================

visitor = Blueprint(
    "visitor",
    __name__,
    url_prefix="/visitor"
)


# ============================================================
# HELPER
# ============================================================

def get_visitor_by_code(code):

    db = get_db()

    try:
        visitor_record = db.execute(
            """
            SELECT
                id,
                student_id,
                visitor_name,
                visitor_phone,
                visitor_email,
                relationship,
                person_to_meet,
                visit_date,
                arrival_time,
                visitor_count,
                purpose,
                id_proof_type,
                id_proof_number,
                status,
                qr_code,
                created_at
            FROM visitors
            WHERE qr_code = ?
            LIMIT 1
            """,
            (code,)
        ).fetchone()

        return visitor_record

    finally:
        db.close()


# ============================================================
# ADMIN CHECK
# ============================================================

def admin_required():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    if session.get("role") != "admin":

        flash(
            "Administrator access required.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    return None


# ============================================================
# PUBLIC VISITOR PASS APPLICATION
# ============================================================

@visitor.route(
    "/apply",
    methods=["GET", "POST"]
)
def visitor_apply():

    if request.method == "POST":

        # ----------------------------------------------------
        # READ FORM DATA
        # ----------------------------------------------------

        visitor_name = request.form.get(
            "visitor_name",
            ""
        ).strip()

        # IMPORTANT:
        # visitor_apply.html uses name="phone"
        # Therefore backend must read "phone".
        visitor_phone = request.form.get(
            "phone",
            ""
        ).strip()

        visitor_email = request.form.get(
            "email",
            ""
        ).strip()

        visit_date = request.form.get(
            "visit_date",
            ""
        ).strip()

        visit_time = request.form.get(
            "visit_time",
            ""
        ).strip()

        purpose = request.form.get(
            "purpose",
            ""
        ).strip()

        student_id = request.form.get(
            "student_id",
            ""
        ).strip()

        student_name = request.form.get(
            "student_name",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not visitor_name:

            flash(
                "Please enter visitor name.",
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        if not visitor_phone:

            flash(
                "Please enter visitor phone number.",
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        if not visit_date:

            flash(
                "Please select visit date.",
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        if not purpose:

            flash(
                "Please enter purpose of visit.",
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        # ----------------------------------------------------
        # PHONE VALIDATION
        # ----------------------------------------------------

        cleaned_phone = (
            visitor_phone
            .replace(" ", "")
            .replace("-", "")
        )

        if not cleaned_phone.isdigit():

            flash(
                "Please enter a valid visitor phone number.",
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        if len(cleaned_phone) < 10:

            flash(
                "Please enter a valid visitor phone number.",
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        visitor_phone = cleaned_phone


        # ----------------------------------------------------
        # GENERATE UNIQUE VISITOR PASS CODE
        # ----------------------------------------------------

        pass_code = (
            "VST-"
            + datetime.now().strftime("%Y%m%d")
            + "-"
            + secrets.token_hex(4).upper()
        )


        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        db = get_db()

        try:

            # ------------------------------------------------
            # LOGGED-IN USER
            # ------------------------------------------------

            logged_user_id = session.get(
                "user_id"
            )


            # ------------------------------------------------
            # IMPORTANT DATABASE MAPPING
            #
            # The visitors table uses:
            # visitor_phone
            # visitor_email
            # arrival_time
            #
            # The current HTML uses:
            # phone
            # email
            # visit_time
            #
            # We already converted them above.
            # ------------------------------------------------

            db.execute(
                """
                INSERT INTO visitors
                (
                    student_id,
                    visitor_name,
                    visitor_phone,
                    visitor_email,
                    relationship,
                    person_to_meet,
                    visit_date,
                    arrival_time,
                    visitor_count,
                    purpose,
                    id_proof_type,
                    id_proof_number,
                    status,
                    qr_code,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    logged_user_id,

                    visitor_name,

                    visitor_phone,

                    visitor_email,

                    # Compatibility fields.
                    # These are optional in the new form.
                    "Visitor",

                    student_name,

                    visit_date,

                    visit_time,

                    1,

                    purpose,

                    "Other",

                    address,

                    "Pending",

                    pass_code,

                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )


            db.commit()


        except Exception as e:

            db.rollback()

            flash(
                "Unable to submit visitor application: "
                + str(e),
                "error"
            )

            return render_template(
                "visitor_apply.html"
            )


        finally:

            db.close()


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        flash(
            "Visitor Pass application submitted successfully. "
            "Please wait for admin approval.",
            "success"
        )


        return redirect(
            url_for(
                "visitor.visitor_status",
                code=pass_code
            )
        )


    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "visitor_apply.html"
    )


# ============================================================
# VISITOR STATUS
# ============================================================

@visitor.route(
    "/status"
)
def visitor_status():

    code = request.args.get(
        "code",
        ""
    ).strip().upper()


    if not code:

        return render_template(
            "visitor_status.html",
            visitor=None,
            search_code=""
        )


    visitor_record = get_visitor_by_code(
        code
    )


    if not visitor_record:

        flash(
            "Visitor Pass not found. Please check your pass code.",
            "error"
        )


    return render_template(
        "visitor_status.html",
        visitor=visitor_record,
        search_code=code
    )


# ============================================================
# VISITOR PASS
# ONLY APPROVED PASSES
# ============================================================

@visitor.route(
    "/pass/<int:visitor_id>"
)
def visitor_pass(visitor_id):

    db = get_db()

    try:

        visitor_record = db.execute(
            """
            SELECT
                id,
                student_id,
                visitor_name,
                visitor_phone,
                visitor_email,
                relationship,
                person_to_meet,
                visit_date,
                arrival_time,
                visitor_count,
                purpose,
                id_proof_type,
                id_proof_number,
                status,
                qr_code,
                created_at
            FROM visitors
            WHERE id = ?
            LIMIT 1
            """,
            (visitor_id,)
        ).fetchone()

    finally:

        db.close()


    if not visitor_record:

        flash(
            "Visitor Pass not found.",
            "error"
        )

        return redirect(
            url_for(
                "visitor.visitor_apply"
            )
        )


    # --------------------------------------------------------
    # ONLY APPROVED
    # --------------------------------------------------------

    if visitor_record["status"] != "Approved":

        if visitor_record["status"] == "Pending":

            flash(
                "Your visitor application is still waiting "
                "for admin approval.",
                "warning"
            )

        elif visitor_record["status"] == "Rejected":

            flash(
                "Your visitor application was rejected "
                "by the administrator.",
                "error"
            )

        else:

            flash(
                "Visitor pass is not approved.",
                "error"
            )


        return redirect(
            url_for(
                "visitor.visitor_status",
                code=visitor_record["qr_code"]
            )
        )


    return render_template(
        "visitor_pass.html",
        visitor=visitor_record
    )


# ============================================================
# VISITOR PASS VERIFICATION
# ============================================================

@visitor.route(
    "/verify",
    methods=["GET", "POST"]
)
def visitor_verify():

    verification_result = None

    verification_code = ""


    if request.method == "POST":

        verification_code = request.form.get(
            "verification_code",
            ""
        ).strip().upper()


        if not verification_code:

            verification_result = {
                "valid": False,
                "message": "Please enter a visitor pass code."
            }


        else:

            visitor_record = get_visitor_by_code(
                verification_code
            )


            if not visitor_record:

                verification_result = {
                    "valid": False,
                    "message": "Invalid visitor pass code."
                }


            elif visitor_record["status"] == "Pending":

                verification_result = {
                    "valid": False,
                    "status": "Pending",
                    "visitor": visitor_record,
                    "message": (
                        "This visitor application is still "
                        "waiting for admin approval."
                    )
                }


            elif visitor_record["status"] == "Rejected":

                verification_result = {
                    "valid": False,
                    "status": "Rejected",
                    "visitor": visitor_record,
                    "message": (
                        "This visitor application was "
                        "rejected by the administrator."
                    )
                }


            elif visitor_record["status"] == "Approved":

                verification_result = {
                    "valid": True,
                    "status": "Approved",
                    "visitor": visitor_record,
                    "message": (
                        "Valid approved visitor pass."
                    )
                }


            else:

                verification_result = {
                    "valid": False,
                    "status": visitor_record["status"],
                    "visitor": visitor_record,
                    "message": (
                        "This visitor pass is not valid."
                    )
                }


    return render_template(
        "visitor_verify.html",
        verification_result=verification_result,
        verification_code=verification_code
    )


# ============================================================
# ADMIN VISITOR MANAGEMENT
# ============================================================

@visitor.route(
    "/admin"
)
def admin_visitors():

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    check = admin_required()

    if check:

        return check


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    db = get_db()

    try:

        visitor_records = db.execute(
            """
            SELECT
                v.id,
                v.student_id,
                v.visitor_name,
                v.visitor_phone,
                v.visitor_email,
                v.relationship,
                v.person_to_meet,
                v.visit_date,
                v.arrival_time,
                v.visitor_count,
                v.purpose,
                v.id_proof_type,
                v.id_proof_number,
                v.status,
                v.qr_code,
                v.created_at,

                u.name AS student_name,
                u.roll_no

            FROM visitors v

            LEFT JOIN users u
                ON v.student_id = u.id

            ORDER BY v.id DESC
            """
        ).fetchall()


        total = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM visitors
            """
        ).fetchone()["total"]


        pending = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE status = 'Pending'
            """
        ).fetchone()["total"]


        approved = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE status = 'Approved'
            """
        ).fetchone()["total"]


        rejected = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM visitors
            WHERE status = 'Rejected'
            """
        ).fetchone()["total"]


    finally:

        db.close()


    return render_template(
        "admin_visitors.html",
        visitors=visitor_records,
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected
    )


# ============================================================
# ADMIN APPROVE / REJECT
# ============================================================

@visitor.route(
    "/admin/action/<int:visitor_id>/<action>",
    methods=["POST"]
)
def admin_visitor_action(
    visitor_id,
    action
):

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    check = admin_required()

    if check:

        return check


    action = action.lower().strip()


    # --------------------------------------------------------
    # VALID ACTIONS
    # --------------------------------------------------------

    if action not in (
        "approve",
        "reject"
    ):

        flash(
            "Invalid visitor action.",
            "error"
        )

        return redirect(
            url_for(
                "visitor.admin_visitors"
            )
        )


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    db = get_db()

    try:

        visitor_record = db.execute(
            """
            SELECT
                id,
                status,
                visitor_name,
                qr_code
            FROM visitors
            WHERE id = ?
            LIMIT 1
            """,
            (visitor_id,)
        ).fetchone()


        if not visitor_record:

            flash(
                "Visitor application not found.",
                "error"
            )

            return redirect(
                url_for(
                    "visitor.admin_visitors"
                )
            )


        # ----------------------------------------------------
        # ALREADY APPROVED
        # ----------------------------------------------------

        if (
            action == "approve"
            and visitor_record["status"] == "Approved"
        ):

            flash(
                "This visitor pass is already approved.",
                "warning"
            )

            return redirect(
                url_for(
                    "visitor.admin_visitors"
                )
            )


        # ----------------------------------------------------
        # ALREADY REJECTED
        # ----------------------------------------------------

        if (
            action == "reject"
            and visitor_record["status"] == "Rejected"
        ):

            flash(
                "This visitor application is already rejected.",
                "warning"
            )

            return redirect(
                url_for(
                    "visitor.admin_visitors"
                )
            )


        # ----------------------------------------------------
        # NEW STATUS
        # ----------------------------------------------------

        if action == "approve":

            new_status = "Approved"

        else:

            new_status = "Rejected"


        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        db.execute(
            """
            UPDATE visitors
            SET status = ?
            WHERE id = ?
            """,
            (
                new_status,
                visitor_id
            )
        )


        db.commit()


    except Exception as e:

        db.rollback()

        flash(
            "Unable to update visitor pass: "
            + str(e),
            "error"
        )

        return redirect(
            url_for(
                "visitor.admin_visitors"
            )
        )


    finally:

        db.close()


    # --------------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------------

    if new_status == "Approved":

        flash(
            "Visitor Pass approved successfully. "
            "The visitor can now use the pass and QR verification.",
            "success"
        )

    else:

        flash(
            "Visitor Pass rejected successfully.",
            "success"
        )


    return redirect(
        url_for(
            "visitor.admin_visitors"
        )
    )


# ============================================================
# COMPATIBILITY ROUTE
# ============================================================

@visitor.route(
    "/admin/action/<int:visitor_id>/<action>",
    methods=["POST"],
    endpoint="admin_action"
)
def admin_action(
    visitor_id,
    action
):

    return admin_visitor_action(
        visitor_id,
        action
    )


# ============================================================
# END OF VISITOR MODULE
# ============================================================
