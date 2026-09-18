# ============================================================
# GITAM CAMPUS LIFE
# NOTIFICATIONS MODULE
# STEP 49 - COMPLETE UPGRADED VERSION
# ============================================================

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request
)

from database import get_db
from datetime import datetime


# ============================================================
# BLUEPRINT
# ============================================================

notifications = Blueprint(
    "notifications",
    __name__,
    url_prefix="/notifications"
)


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user():

    if "user_id" not in session:
        return None

    db = get_db()

    try:

        return db.execute(
            """
            SELECT
                id,
                username,
                name,
                email,
                role,
                status
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()

    except Exception as e:

        print(
            "[NOTIFICATIONS USER ERROR]",
            str(e)
        )

        return None


# ============================================================
# ADMIN CHECK
# ============================================================

def admin_required():

    user = get_current_user()

    if not user:

        flash(
            "Please login first.",
            "warning"
        )

        return False

    if str(user["role"]).lower() != "admin":

        flash(
            "Administrator access required.",
            "error"
        )

        return False

    return True


# ============================================================
# DATABASE COLUMNS
# ============================================================

def get_notification_columns(db):

    rows = db.execute(
        "PRAGMA table_info(notifications)"
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


# ============================================================
# LOAD NOTIFICATIONS FOR USER
# ============================================================

def load_user_notifications(
    db,
    user_id
):

    columns = get_notification_columns(db)

    if "user_id" not in columns:

        return []

    select_columns = []

    if "id" in columns:
        select_columns.append("id")

    if "user_id" in columns:
        select_columns.append("user_id")

    if "title" in columns:
        select_columns.append("title")

    if "message" in columns:
        select_columns.append("message")

    if "notification_type" in columns:
        select_columns.append(
            "notification_type"
        )

    if "is_read" in columns:
        select_columns.append("is_read")

    if "created_at" in columns:
        select_columns.append("created_at")

    query = f"""
        SELECT {", ".join(select_columns)}
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
    """

    return db.execute(
        query,
        (user_id,)
    ).fetchall()


# ============================================================
# MAIN NOTIFICATIONS PAGE
#
# IMPORTANT:
# GET  -> display notifications
# POST -> mark all notifications as read
#
# This fixes:
# POST /notifications/ -> 405
# ============================================================

@notifications.route(
    "/",
    methods=["GET", "POST"]
)
def notifications_page():

    user = get_current_user()

    if not user:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        action = request.form.get(
            "action",
            ""
        ).strip().lower()

        # ----------------------------------------------------
        # MARK ALL READ
        # ----------------------------------------------------

        if action in (
            "",
            "read-all",
            "mark-all-read",
            "mark_all_read"
        ):

            try:

                columns = get_notification_columns(db)

                if (
                    "user_id" in columns
                    and "is_read" in columns
                ):

                    db.execute(
                        """
                        UPDATE notifications
                        SET is_read = 1
                        WHERE user_id = ?
                        """,
                        (user["id"],)
                    )

                    db.commit()

                    flash(
                        "All notifications marked as read.",
                        "success"
                    )

                else:

                    flash(
                        "Notification read status is not available.",
                        "warning"
                    )

            except Exception as e:

                try:
                    db.rollback()
                except Exception:
                    pass

                print(
                    "[NOTIFICATIONS POST ERROR]",
                    str(e)
                )

                flash(
                    "Unable to update notifications.",
                    "error"
                )

        # ----------------------------------------------------
        # UNKNOWN ACTION
        # ----------------------------------------------------

        else:

            flash(
                "Notification action completed.",
                "success"
            )

        return redirect(
            url_for(
                "notifications.notifications_page"
            )
        )

    # ========================================================
    # GET
    # ========================================================

    try:

        notification_records = load_user_notifications(
            db,
            user["id"]
        )

        # ----------------------------------------------------
        # UNREAD COUNT
        # ----------------------------------------------------

        unread_count = 0

        columns = get_notification_columns(db)

        if (
            "user_id" in columns
            and "is_read" in columns
        ):

            result = db.execute(
                """
                SELECT COUNT(*) AS total
                FROM notifications
                WHERE user_id = ?
                AND is_read = 0
                """,
                (user["id"],)
            ).fetchone()

            unread_count = result["total"]

    except Exception as e:

        print(
            "[NOTIFICATIONS LOAD ERROR]",
            str(e)
        )

        notification_records = []
        unread_count = 0

        flash(
            "Unable to load notifications.",
            "error"
        )

    return render_template(
        "notifications.html",
        notifications=notification_records,
        unread_count=unread_count,
        user=user
    )


# ============================================================
# MARK ONE NOTIFICATION AS READ
# ============================================================

@notifications.route(
    "/read/<int:notification_id>",
    methods=["GET", "POST"]
)
def mark_read(notification_id):

    user = get_current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        columns = get_notification_columns(db)

        if (
            "user_id" not in columns
            or "is_read" not in columns
        ):

            flash(
                "Read status is not available.",
                "warning"
            )

            return redirect(
                url_for(
                    "notifications.notifications_page"
                )
            )

        notification = db.execute(
            """
            SELECT id
            FROM notifications
            WHERE id = ?
            AND user_id = ?
            """,
            (
                notification_id,
                user["id"]
            )
        ).fetchone()

        if not notification:

            flash(
                "Notification not found.",
                "error"
            )

            return redirect(
                url_for(
                    "notifications.notifications_page"
                )
            )

        db.execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE id = ?
            AND user_id = ?
            """,
            (
                notification_id,
                user["id"]
            )
        )

        db.commit()

        flash(
            "Notification marked as read.",
            "success"
        )

    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass

        print(
            "[NOTIFICATION READ ERROR]",
            str(e)
        )

        flash(
            "Unable to mark notification as read.",
            "error"
        )

    return redirect(
        url_for(
            "notifications.notifications_page"
        )
    )


# ============================================================
# MARK ALL READ
# ============================================================

@notifications.route(
    "/mark-all-read",
    methods=["GET", "POST"]
)
def mark_all_read():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        columns = get_notification_columns(db)

        if (
            "user_id" not in columns
            or "is_read" not in columns
        ):

            flash(
                "Read status is not available.",
                "warning"
            )

            return redirect(
                url_for(
                    "notifications.notifications_page"
                )
            )

        db.execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE user_id = ?
            """,
            (user["id"],)
        )

        db.commit()

        flash(
            "All notifications marked as read.",
            "success"
        )

    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass

        print(
            "[NOTIFICATIONS MARK ALL ERROR]",
            str(e)
        )

        flash(
            "Unable to mark notifications as read.",
            "error"
        )

    return redirect(
        url_for(
            "notifications.notifications_page"
        )
    )


# ============================================================
# UNREAD COUNT
# ============================================================

@notifications.route(
    "/unread-count"
)
def unread_count():

    user = get_current_user()

    if not user:

        return {
            "success": False,
            "count": 0
        }

    db = get_db()

    try:

        columns = get_notification_columns(db)

        if (
            "user_id" not in columns
            or "is_read" not in columns
        ):

            return {
                "success": True,
                "count": 0
            }

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM notifications
            WHERE user_id = ?
            AND is_read = 0
            """,
            (user["id"],)
        ).fetchone()

        return {
            "success": True,
            "count": result["total"]
        }

    except Exception as e:

        print(
            "[NOTIFICATIONS COUNT ERROR]",
            str(e)
        )

        return {
            "success": False,
            "count": 0
        }


# ============================================================
# ADMIN CREATE NOTIFICATION
# ============================================================

@notifications.route(
    "/admin/create",
    methods=["GET", "POST"]
)
def admin_create():

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "admin_notifications.html"
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    title = request.form.get(
        "title",
        ""
    ).strip()

    message = request.form.get(
        "message",
        ""
    ).strip()

    notification_type = request.form.get(
        "notification_type",
        "General"
    ).strip()

    target_user_id = request.form.get(
        "user_id",
        ""
    ).strip()

    if not title:

        flash(
            "Notification title is required.",
            "error"
        )

        return redirect(
            url_for(
                "notifications.admin_create"
            )
        )

    if not message:

        flash(
            "Notification message is required.",
            "error"
        )

        return redirect(
            url_for(
                "notifications.admin_create"
            )
        )

    try:

        columns = get_notification_columns(db)

        if "user_id" not in columns:

            raise Exception(
                "notifications table does not contain user_id."
            )

        if "title" not in columns:

            raise Exception(
                "notifications table does not contain title."
            )

        if "message" not in columns:

            raise Exception(
                "notifications table does not contain message."
            )

        # ----------------------------------------------------
        # TARGET USER
        # ----------------------------------------------------

        if target_user_id:

            target_users = db.execute(
                """
                SELECT id
                FROM users
                WHERE id = ?
                """,
                (target_user_id,)
            ).fetchall()

        else:

            target_users = db.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(role)
                IN ('student', 'faculty')
                """
            ).fetchall()

        if not target_users:

            flash(
                "No target users found.",
                "warning"
            )

            return redirect(
                url_for(
                    "notifications.admin_create"
                )
            )

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        for target in target_users:

            insert_columns = [
                "user_id",
                "title",
                "message"
            ]

            values = [
                target["id"],
                title,
                message
            ]

            placeholders = [
                "?",
                "?",
                "?"
            ]

            if "notification_type" in columns:

                insert_columns.append(
                    "notification_type"
                )

                values.append(
                    notification_type or "General"
                )

                placeholders.append("?")

            if "is_read" in columns:

                insert_columns.append(
                    "is_read"
                )

                values.append(0)

                placeholders.append("?")

            if "created_at" in columns:

                insert_columns.append(
                    "created_at"
                )

                values.append(
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                placeholders.append("?")

            query = f"""
                INSERT INTO notifications
                ({", ".join(insert_columns)})
                VALUES ({", ".join(placeholders)})
            """

            db.execute(
                query,
                tuple(values)
            )

        db.commit()

        flash(
            "Notification sent successfully.",
            "success"
        )

    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass

        print(
            "[NOTIFICATION CREATE ERROR]",
            str(e)
        )

        flash(
            "Unable to send notification: " +
            str(e),
            "error"
        )

    return redirect(
        url_for(
            "notifications.admin_create"
        )
    )


# ============================================================
# ADMIN NOTIFICATION HISTORY
# ============================================================

@notifications.route(
    "/admin"
)
def admin_notifications():

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        columns = get_notification_columns(db)

        select_columns = [
            "notifications.id",
            "notifications.title",
            "notifications.message"
        ]

        if "notification_type" in columns:

            select_columns.append(
                "notifications.notification_type"
            )

        if "is_read" in columns:

            select_columns.append(
                "notifications.is_read"
            )

        if "created_at" in columns:

            select_columns.append(
                "notifications.created_at"
            )

        if "user_id" in columns:

            select_columns.extend([
                "notifications.user_id",
                "users.name AS user_name",
                "users.username AS user_username"
            ])

            query = f"""
                SELECT
                    {", ".join(select_columns)}
                FROM notifications
                LEFT JOIN users
                    ON users.id =
                       notifications.user_id
                ORDER BY notifications.id DESC
            """

        else:

            query = f"""
                SELECT
                    {", ".join(select_columns)}
                FROM notifications
                ORDER BY notifications.id DESC
            """

        records = db.execute(
            query
        ).fetchall()

    except Exception as e:

        print(
            "[NOTIFICATION ADMIN ERROR]",
            str(e)
        )

        records = []

        flash(
            "Unable to load notification history.",
            "error"
        )

    return render_template(
        "admin_notifications.html",
        notifications=records
    )


# ============================================================
# COMPATIBILITY ROUTES
# ============================================================

@notifications.route(
    "/read-all",
    methods=["GET", "POST"]
)
def read_all_compatibility():

    return redirect(
        url_for(
            "notifications.mark_all_read"
        )
    )


@notifications.route(
    "/mark-read/<int:notification_id>",
    methods=["GET", "POST"]
)
def mark_read_compatibility(
    notification_id
):

    return redirect(
        url_for(
            "notifications.mark_read",
            notification_id=notification_id
        )
    )


# ============================================================
# MODULE LOADED
# ============================================================

print("[OK] Notifications module loaded.")
