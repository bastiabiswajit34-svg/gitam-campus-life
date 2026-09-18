# ============================================================
# GITAM CAMPUS LIFE
# DIGITAL ID MODULE
# QR-BASED DIGITAL ID
# PYDROID-FRIENDLY - NO qrcode PACKAGE REQUIRED
# ============================================================

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session
)

from database import get_db

import urllib.parse


# ============================================================
# BLUEPRINT
# ============================================================

digital_id = Blueprint(
    "digital_id",
    __name__,
    url_prefix="/digital-id"
)


# ============================================================
# DIGITAL ID PAGE
# ============================================================

@digital_id.route("/")
def digital_id_page():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    db = get_db()

    # --------------------------------------------------------
    # GET CURRENT USER
    # --------------------------------------------------------

    user = db.execute(
        """
        SELECT
            id,
            username,
            name,
            email,
            role,
            roll_no,
            branch,
            year,
            phone,
            profile_image
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:
        session.clear()
        flash("User account not found.", "error")
        return redirect(url_for("auth.login"))

    # --------------------------------------------------------
    # GET DIGITAL ID RECORD
    # --------------------------------------------------------

    digital_id_record = db.execute(
        """
        SELECT
            id,
            user_id,
            qr_code
        FROM digital_ids
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    # --------------------------------------------------------
    # CREATE DIGITAL ID RECORD IF NOT EXISTS
    # --------------------------------------------------------

    if not digital_id_record:

        db.execute(
            """
            INSERT INTO digital_ids
            (
                user_id,
                qr_code
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                None
            )
        )

        db.commit()

        digital_id_record = db.execute(
            """
            SELECT
                id,
                user_id,
                qr_code
            FROM digital_ids
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

    # --------------------------------------------------------
    # DIGITAL ID VERIFICATION URL
    #
    # This URL contains only the user's Digital ID record.
    # It does NOT send personal information to QRServer.
    # --------------------------------------------------------

    verify_url = (
        request_host_url()
        + url_for(
            "digital_id.verify_digital_id",
            digital_id=digital_id_record["id"]
        )
    )

    # --------------------------------------------------------
    # GENERATE QR IMAGE USING THE SAME METHOD AS
    # YOUR WORKING ATTENDANCE SYSTEM
    #
    # NO qrcode PACKAGE
    # NO Pillow
    # --------------------------------------------------------

    qr_url = (
        "https://api.qrserver.com/v1/create-qr-code/"
        "?size=400x400&data="
        + urllib.parse.quote(
            verify_url,
            safe=""
        )
    )

    # --------------------------------------------------------
    # SAVE QR URL IN DATABASE
    # --------------------------------------------------------

    current_qr = digital_id_record["qr_code"]

    if current_qr != qr_url:

        db.execute(
            """
            UPDATE digital_ids
            SET qr_code = ?
            WHERE id = ?
            """,
            (
                qr_url,
                digital_id_record["id"]
            )
        )

        db.commit()

        digital_id_record = db.execute(
            """
            SELECT
                id,
                user_id,
                qr_code
            FROM digital_ids
            WHERE id = ?
            """,
            (
                digital_id_record["id"],
            )
        ).fetchone()

    # --------------------------------------------------------
    # RENDER DIGITAL ID
    # --------------------------------------------------------

    return render_template(
        "digital_id.html",
        user=user,
        digital_id=digital_id_record,
        qr_url=qr_url
    )


# ============================================================
# CREATE CURRENT HOST URL
# ============================================================

def request_host_url():
    """
    Gets the current Flask server URL without requiring
    request to be imported globally.
    """

    from flask import request

    return request.host_url.rstrip("/")


# ============================================================
# DIGITAL ID VERIFICATION
# ============================================================

@digital_id.route("/verify/<int:digital_id>")
def verify_digital_id(digital_id):

    db = get_db()

    # --------------------------------------------------------
    # GET DIGITAL ID + USER INFORMATION
    # --------------------------------------------------------

    record = db.execute(
        """
        SELECT
            digital_ids.id AS digital_id,
            digital_ids.user_id,
            users.name,
            users.username,
            users.email,
            users.role,
            users.roll_no,
            users.branch,
            users.year,
            users.phone,
            users.profile_image
        FROM digital_ids
        JOIN users
            ON users.id = digital_ids.user_id
        WHERE digital_ids.id = ?
        """,
        (digital_id,)
    ).fetchone()

    # --------------------------------------------------------
    # INVALID DIGITAL ID
    # --------------------------------------------------------

    if not record:

        return render_template(
            "digital_id.html",
            user=None,
            digital_id=None,
            qr_url=None,
            verification_error=True
        )

    # --------------------------------------------------------
    # VERIFIED DIGITAL ID
    # --------------------------------------------------------

    return render_template(
        "digital_id.html",
        user=record,
        digital_id=record,
        qr_url=None,
        verification_mode=True
    )


# ============================================================
# END OF DIGITAL ID MODULE
# ============================================================
