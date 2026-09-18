# ============================================================
# GITAM CAMPUS LIFE
# NOTICE MANAGEMENT MODULE
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
from datetime import datetime


# ============================================================
# BLUEPRINT
# ============================================================

notices = Blueprint(
    "notices",
    __name__,
    url_prefix="/notices"
)


# ============================================================
# ADMIN CHECK
# ============================================================

def admin_required():
    """Check whether the current user is an administrator."""

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return False

    db = get_db()

    try:
        user = db.execute(
            """
            SELECT id, username, name, role, status
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        if not user:
            session.clear()
            flash("User account not found.", "error")
            return False

        if str(user["role"]).lower() != "admin":
            flash(
                "Administrator access required.",
                "error"
            )
            return False

        return True

    except Exception as e:

        print(
            "[NOTICE ADMIN CHECK ERROR]",
            str(e)
        )

        flash(
            "Unable to verify administrator access.",
            "error"
        )

        return False


# ============================================================
# GET NOTICE TABLE COLUMNS
# ============================================================

def get_notice_columns(db):
    """
    Detect the actual columns in the existing notices table.

    This makes the module work with different versions
    of the notices table without deleting campus.db.
    """

    rows = db.execute(
        "PRAGMA table_info(notices)"
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


# ============================================================
# LOAD CURRENT USER
# ============================================================

def get_current_user():
    """Return the currently logged-in user."""

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
            "[NOTICE USER ERROR]",
            str(e)
        )

        return None


# ============================================================
# BUILD NOTICE SELECT QUERY
# ============================================================

def load_notices(db):
    """
    Load notices using only columns that actually exist.
    """

    columns = get_notice_columns(db)

    select_columns = []

    # Required
    if "id" in columns:
        select_columns.append("id")

    if "title" in columns:
        select_columns.append("title")

    # Content
    if "content" in columns:
        select_columns.append("content")

    if "description" in columns:
        select_columns.append("description")

    # Optional
    if "category" in columns:
        select_columns.append("category")

    if "notice_date" in columns:
        select_columns.append("notice_date")

    if "created_at" in columns:
        select_columns.append("created_at")

    if not select_columns:
        return []

    query = f"""
        SELECT {", ".join(select_columns)}
        FROM notices
        ORDER BY id DESC
    """

    return db.execute(query).fetchall()


# ============================================================
# MAIN NOTICE PAGE
# GET + POST
# ============================================================

@notices.route(
    "/",
    methods=["GET", "POST"]
)
def notices_page():

    # --------------------------------------------------------
    # LOGIN CHECK
    # --------------------------------------------------------

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
    # ADMIN CREATE NOTICE
    # ========================================================

    if request.method == "POST":

        if str(user["role"]).lower() != "admin":

            flash(
                "Administrator access required.",
                "error"
            )

            return redirect(
                url_for("notices.notices_page")
            )

        title = request.form.get(
            "title",
            ""
        ).strip()

        # Current HTML uses description
        description = request.form.get(
            "description",
            ""
        ).strip()

        # Compatibility with content field
        if not description:

            description = request.form.get(
                "content",
                ""
            ).strip()

        category = request.form.get(
            "category",
            "General"
        ).strip()

        notice_date = request.form.get(
            "notice_date",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not title:

            flash(
                "Please enter the notice title.",
                "error"
            )

            return redirect(
                url_for("notices.notices_page")
            )

        if not description:

            flash(
                "Please enter the notice details.",
                "error"
            )

            return redirect(
                url_for("notices.notices_page")
            )

        try:

            columns = get_notice_columns(db)

            insert_columns = []
            values = []
            placeholders = []

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            if "title" in columns:

                insert_columns.append("title")
                values.append(title)
                placeholders.append("?")

            # ------------------------------------------------
            # DESCRIPTION / CONTENT
            # ------------------------------------------------

            if "content" in columns:

                insert_columns.append("content")
                values.append(description)
                placeholders.append("?")

            elif "description" in columns:

                insert_columns.append("description")
                values.append(description)
                placeholders.append("?")

            # ------------------------------------------------
            # CATEGORY
            # ------------------------------------------------

            if "category" in columns:

                insert_columns.append("category")
                values.append(
                    category or "General"
                )
                placeholders.append("?")

            # ------------------------------------------------
            # NOTICE DATE
            # ------------------------------------------------

            if "notice_date" in columns:

                insert_columns.append("notice_date")

                values.append(
                    notice_date or
                    datetime.now().strftime(
                        "%Y-%m-%d"
                    )
                )

                placeholders.append("?")

            # ------------------------------------------------
            # CREATED DATE
            # ------------------------------------------------

            if "created_at" in columns:

                insert_columns.append("created_at")

                values.append(
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                placeholders.append("?")

            # ------------------------------------------------
            # SAFETY CHECK
            # ------------------------------------------------

            if not insert_columns:

                raise Exception(
                    "No usable columns found in notices table."
                )

            query = f"""
                INSERT INTO notices
                ({", ".join(insert_columns)})
                VALUES ({", ".join(placeholders)})
            """

            db.execute(
                query,
                tuple(values)
            )

            db.commit()

            print(
                "[NOTICE] Created:",
                title
            )

            flash(
                "Notice published successfully.",
                "success"
            )

        except Exception as e:

            try:
                db.rollback()
            except Exception:
                pass

            print(
                "[NOTICE CREATE ERROR]",
                str(e)
            )

            flash(
                "Unable to publish notice: " + str(e),
                "error"
            )

        return redirect(
            url_for("notices.notices_page")
        )

    # ========================================================
    # LOAD NOTICE LIST
    # ========================================================

    try:

        notice_records = load_notices(db)

    except Exception as e:

        print(
            "[NOTICE LIST ERROR]",
            str(e)
        )

        notice_records = []

        flash(
            "Unable to load notices.",
            "error"
        )

    # IMPORTANT:
    # user IS now defined and safely passed to template.

    return render_template(
        "notices.html",
        notices=notice_records,
        user=user
    )


# ============================================================
# LIST COMPATIBILITY ROUTE
# /notices/list
# ============================================================

@notices.route("/list")
def list_notices():

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

    try:

        notice_records = load_notices(db)

    except Exception as e:

        print(
            "[NOTICE LIST ROUTE ERROR]",
            str(e)
        )

        notice_records = []

    return render_template(
        "notices.html",
        notices=notice_records,
        user=user
    )


# ============================================================
# ADMIN NOTICE PAGE
# ============================================================

@notices.route("/admin")
def admin_notices():

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        notice_records = load_notices(db)

    except Exception as e:

        print(
            "[NOTICE ADMIN LIST ERROR]",
            str(e)
        )

        notice_records = []

        flash(
            "Unable to load notices.",
            "error"
        )

    return render_template(
        "admin_notices.html",
        notices=notice_records
    )


# ============================================================
# CREATE NOTICE COMPATIBILITY ROUTE
# /notices/create
# ============================================================

@notices.route(
    "/create",
    methods=["GET", "POST"]
)
def create():

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return redirect(
            url_for("notices.notices_page")
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    if not description:

        description = request.form.get(
            "content",
            ""
        ).strip()

    category = request.form.get(
        "category",
        "General"
    ).strip()

    notice_date = request.form.get(
        "notice_date",
        ""
    ).strip()

    if not title:

        flash(
            "Please enter the notice title.",
            "error"
        )

        return redirect(
            url_for("notices.notices_page")
        )

    if not description:

        flash(
            "Please enter the notice details.",
            "error"
        )

        return redirect(
            url_for("notices.notices_page")
        )

    db = get_db()

    try:

        columns = get_notice_columns(db)

        insert_columns = []
        values = []
        placeholders = []

        if "title" in columns:

            insert_columns.append("title")
            values.append(title)
            placeholders.append("?")

        if "content" in columns:

            insert_columns.append("content")
            values.append(description)
            placeholders.append("?")

        elif "description" in columns:

            insert_columns.append("description")
            values.append(description)
            placeholders.append("?")

        if "category" in columns:

            insert_columns.append("category")
            values.append(
                category or "General"
            )
            placeholders.append("?")

        if "notice_date" in columns:

            insert_columns.append("notice_date")
            values.append(
                notice_date or
                datetime.now().strftime("%Y-%m-%d")
            )
            placeholders.append("?")

        if "created_at" in columns:

            insert_columns.append("created_at")
            values.append(
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            placeholders.append("?")

        query = f"""
            INSERT INTO notices
            ({", ".join(insert_columns)})
            VALUES ({", ".join(placeholders)})
        """

        db.execute(
            query,
            tuple(values)
        )

        db.commit()

        flash(
            "Notice created successfully.",
            "success"
        )

    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass

        print(
            "[NOTICE CREATE ROUTE ERROR]",
            str(e)
        )

        flash(
            "Unable to create notice: " + str(e),
            "error"
        )

    return redirect(
        url_for("notices.admin_notices")
    )


# ============================================================
# DELETE NOTICE
# ============================================================

@notices.route(
    "/delete/<int:notice_id>",
    methods=["GET", "POST"]
)
def delete(notice_id):

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        notice = db.execute(
            """
            SELECT id, title
            FROM notices
            WHERE id = ?
            """,
            (notice_id,)
        ).fetchone()

        if not notice:

            flash(
                "Notice not found.",
                "error"
            )

            return redirect(
                url_for("notices.admin_notices")
            )

        db.execute(
            """
            DELETE FROM notices
            WHERE id = ?
            """,
            (notice_id,)
        )

        db.commit()

        print(
            "[NOTICE] Deleted:",
            notice["title"]
        )

        flash(
            "Notice deleted successfully.",
            "success"
        )

    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass

        print(
            "[NOTICE DELETE ERROR]",
            str(e)
        )

        flash(
            "Unable to delete notice: " + str(e),
            "error"
        )

    return redirect(
        url_for("notices.admin_notices")
    )


# ============================================================
# UPDATE NOTICE
# ============================================================

@notices.route(
    "/<int:notice_id>/update",
    methods=["GET", "POST"]
)
def update(notice_id):

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        columns = get_notice_columns(db)

        notice = db.execute(
            """
            SELECT *
            FROM notices
            WHERE id = ?
            """,
            (notice_id,)
        ).fetchone()

        if not notice:

            flash(
                "Notice not found.",
                "error"
            )

            return redirect(
                url_for("notices.admin_notices")
            )

        # ----------------------------------------------------
        # GET EDIT PAGE
        # ----------------------------------------------------

        if request.method == "GET":

            return render_template(
                "edit_notice.html",
                notice=notice
            )

        # ----------------------------------------------------
        # POST UPDATE
        # ----------------------------------------------------

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not description:

            description = request.form.get(
                "content",
                ""
            ).strip()

        if not title:

            flash(
                "Notice title cannot be empty.",
                "error"
            )

            return redirect(
                url_for(
                    "notices.update",
                    notice_id=notice_id
                )
            )

        if not description:

            flash(
                "Notice details cannot be empty.",
                "error"
            )

            return redirect(
                url_for(
                    "notices.update",
                    notice_id=notice_id
                )
            )

        # ----------------------------------------------------
        # UPDATE TITLE
        # ----------------------------------------------------

        if "content" in columns:

            db.execute(
                """
                UPDATE notices
                SET
                    title = ?,
                    content = ?
                WHERE id = ?
                """,
                (
                    title,
                    description,
                    notice_id
                )
            )

        elif "description" in columns:

            db.execute(
                """
                UPDATE notices
                SET
                    title = ?,
                    description = ?
                WHERE id = ?
                """,
                (
                    title,
                    description,
                    notice_id
                )
            )

        else:

            db.execute(
                """
                UPDATE notices
                SET title = ?
                WHERE id = ?
                """,
                (
                    title,
                    notice_id
                )
            )

        # ----------------------------------------------------
        # OPTIONAL CATEGORY
        # ----------------------------------------------------

        if "category" in columns:

            db.execute(
                """
                UPDATE notices
                SET category = ?
                WHERE id = ?
                """,
                (
                    request.form.get(
                        "category",
                        "General"
                    ).strip() or "General",
                    notice_id
                )
            )

        # ----------------------------------------------------
        # OPTIONAL DATE
        # ----------------------------------------------------

        if "notice_date" in columns:

            notice_date = request.form.get(
                "notice_date",
                ""
            ).strip()

            if notice_date:

                db.execute(
                    """
                    UPDATE notices
                    SET notice_date = ?
                    WHERE id = ?
                    """,
                    (
                        notice_date,
                        notice_id
                    )
                )

        db.commit()

        flash(
            "Notice updated successfully.",
            "success"
        )

        return redirect(
            url_for("notices.admin_notices")
        )

    except Exception as e:

        try:
            db.rollback()
        except Exception:
            pass

        print(
            "[NOTICE UPDATE ERROR]",
            str(e)
        )

        flash(
            "Unable to update notice: " + str(e),
            "error"
        )

        return redirect(
            url_for("notices.admin_notices")
        )


# ============================================================
# PUBLISH NOTICE
# ============================================================

@notices.route(
    "/<int:notice_id>/publish",
    methods=["GET", "POST"]
)
def publish(notice_id):

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        notice = db.execute(
            """
            SELECT id, title
            FROM notices
            WHERE id = ?
            """,
            (notice_id,)
        ).fetchone()

        if not notice:

            flash(
                "Notice not found.",
                "error"
            )

            return redirect(
                url_for("notices.admin_notices")
            )

        # The current database does not require a separate
        # publication status. Existing notices are visible.

        flash(
            "Notice published successfully.",
            "success"
        )

    except Exception as e:

        print(
            "[NOTICE PUBLISH ERROR]",
            str(e)
        )

        flash(
            "Unable to publish notice.",
            "error"
        )

    return redirect(
        url_for("notices.admin_notices")
    )


# ============================================================
# ARCHIVE COMPATIBILITY ROUTE
# ============================================================

@notices.route(
    "/<int:notice_id>/archive",
    methods=["GET", "POST"]
)
def archive(notice_id):

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        notice = db.execute(
            """
            SELECT id
            FROM notices
            WHERE id = ?
            """,
            (notice_id,)
        ).fetchone()

        if not notice:

            flash(
                "Notice not found.",
                "error"
            )

            return redirect(
                url_for("notices.admin_notices")
            )

        flash(
            "Archive status is not available in the current database schema.",
            "warning"
        )

    except Exception as e:

        print(
            "[NOTICE ARCHIVE ERROR]",
            str(e)
        )

    return redirect(
        url_for("notices.admin_notices")
    )


# ============================================================
# SEARCH NOTICES
# ============================================================

@notices.route("/search")
def search():

    user = get_current_user()

    if not user:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    query_text = request.args.get(
        "q",
        ""
    ).strip()

    db = get_db()

    try:

        columns = get_notice_columns(db)

        select_columns = ["id"]

        if "title" in columns:
            select_columns.append("title")

        if "content" in columns:
            select_columns.append("content")

        if "description" in columns:
            select_columns.append("description")

        if "category" in columns:
            select_columns.append("category")

        if "notice_date" in columns:
            select_columns.append("notice_date")

        if "created_at" in columns:
            select_columns.append("created_at")

        conditions = []
        parameters = []

        if query_text:

            if "title" in columns:

                conditions.append(
                    "title LIKE ?"
                )

                parameters.append(
                    "%" + query_text + "%"
                )

            if "content" in columns:

                conditions.append(
                    "content LIKE ?"
                )

                parameters.append(
                    "%" + query_text + "%"
                )

            if "description" in columns:

                conditions.append(
                    "description LIKE ?"
                )

                parameters.append(
                    "%" + query_text + "%"
                )

        sql = f"""
            SELECT {", ".join(select_columns)}
            FROM notices
        """

        if conditions:

            sql += (
                " WHERE " +
                " OR ".join(conditions)
            )

        sql += " ORDER BY id DESC"

        notice_records = db.execute(
            sql,
            tuple(parameters)
        ).fetchall()

    except Exception as e:

        print(
            "[NOTICE SEARCH ERROR]",
            str(e)
        )

        notice_records = []

        flash(
            "Unable to search notices.",
            "error"
        )

    return render_template(
        "notices.html",
        notices=notice_records,
        user=user
    )


# ============================================================
# NOTICE HISTORY
# ============================================================

@notices.route("/history")
def history():

    if not admin_required():

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        notice_records = load_notices(db)

    except Exception as e:

        print(
            "[NOTICE HISTORY ERROR]",
            str(e)
        )

        notice_records = []

    return render_template(
        "admin_notices.html",
        notices=notice_records
    )


# ============================================================
# MODULE LOADED
# ============================================================

print("[OK] Notices module loaded.")
