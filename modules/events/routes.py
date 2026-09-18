# ============================================================
# GITAM CAMPUS LIFE
# EVENTS MODULE
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

events = Blueprint(
    "events",
    __name__,
    url_prefix="/events"
)


# ============================================================
# ADMIN CHECK
# ============================================================

def admin_required():
    """
    Check whether the current user is logged in
    and has admin role.
    """

    if "user_id" not in session:
        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    if str(
        session.get("role", "")
    ).lower() != "admin":

        flash(
            "Administrator access required.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    return None


# ============================================================
# EVENTS LIST
# ============================================================

@events.route(
    "/",
    methods=["GET"]
)
def events_page():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        event_records = db.execute(
            """
            SELECT
                id,
                title,
                description,
                event_date,
                event_time,
                venue,
                organizer,
                image
            FROM events
            ORDER BY event_date ASC, event_time ASC
            """
        ).fetchall()

    finally:

        db.close()

    return render_template(
        "events.html",
        events=event_records
    )


# ============================================================
# EVENT DETAILS
# ============================================================

@events.route(
    "/<int:event_id>",
    methods=["GET"]
)
def event_details(event_id):

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    db = get_db()

    try:

        event = db.execute(
            """
            SELECT
                id,
                title,
                description,
                event_date,
                event_time,
                venue,
                organizer,
                image
            FROM events
            WHERE id = ?
            """,
            (event_id,)
        ).fetchone()

        if not event:

            flash(
                "Event not found.",
                "error"
            )

            return redirect(
                url_for("events.events_page")
            )

        registration = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM event_registrations
            WHERE event_id = ?
            """,
            (event_id,)
        ).fetchone()

        registration_count = registration["total"]

    finally:

        db.close()

    return render_template(
        "event_details.html",
        event=event,
        registration_count=registration_count
    )


# ============================================================
# EVENT REGISTRATION
# ============================================================

@events.route(
    "/<int:event_id>/register",
    methods=["GET", "POST"]
)
def event_register(event_id):

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------

    role = str(
        session.get("role", "")
    ).lower()

    # Faculty can view events but cannot register.
    if role == "faculty":

        flash(
            "Faculty members can view events but cannot register.",
            "warning"
        )

        return redirect(
            url_for(
                "events.event_details",
                event_id=event_id
            )
        )

    # Admin does not register for events.
    if role == "admin":

        flash(
            "Administrators cannot register for events.",
            "warning"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    user_id = session["user_id"]

    db = get_db()

    try:

        event = db.execute(
            """
            SELECT
                id,
                title,
                description,
                event_date,
                event_time,
                venue,
                organizer,
                image
            FROM events
            WHERE id = ?
            """,
            (event_id,)
        ).fetchone()

        if not event:

            flash(
                "Event not found.",
                "error"
            )

            return redirect(
                url_for("events.events_page")
            )

        # ----------------------------------------------------
        # POST REGISTRATION
        # ----------------------------------------------------

        if request.method == "POST":

            confirmation = request.form.get(
                "confirmation",
                ""
            ).strip()

            # Support checkbox or hidden confirmation.
            if not confirmation:

                confirmation = request.form.get(
                    "confirm",
                    ""
                ).strip()

            if not confirmation:

                flash(
                    "Please confirm your registration.",
                    "error"
                )

                return redirect(
                    url_for(
                        "events.event_register",
                        event_id=event_id
                    )
                )

            existing = db.execute(
                """
                SELECT id
                FROM event_registrations
                WHERE event_id = ?
                  AND user_id = ?
                """,
                (
                    event_id,
                    user_id
                )
            ).fetchone()

            if existing:

                flash(
                    "You are already registered for this event.",
                    "warning"
                )

                return redirect(
                    url_for(
                        "events.event_details",
                        event_id=event_id
                    )
                )

            db.execute(
                """
                INSERT INTO event_registrations
                (
                    event_id,
                    user_id
                )
                VALUES (?, ?)
                """,
                (
                    event_id,
                    user_id
                )
            )

            db.commit()

            flash(
                "You have successfully registered for the event.",
                "success"
            )

            return redirect(
                url_for(
                    "events.event_details",
                    event_id=event_id
                )
            )

    finally:

        db.close()

    return render_template(
        "event_register.html",
        event=event
    )


# ============================================================
# ADMIN EVENT MANAGEMENT
#
# IMPORTANT:
# GET  /events/admin
# POST /events/admin
#
# POST is intentionally accepted here so an older template
# submitting directly to /events/admin will NOT give 405.
# ============================================================

@events.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin_events():

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    check = admin_required()

    if check:
        return check

    # --------------------------------------------------------
    # IMPORTANT COMPATIBILITY FIX
    #
    # If an old admin event form submits:
    #
    # POST /events/admin
    #
    # process it as event creation.
    # --------------------------------------------------------

    if request.method == "POST":

        return create_event_from_form()

    # --------------------------------------------------------
    # SHOW ADMIN EVENT PAGE
    # --------------------------------------------------------

    db = get_db()

    try:

        event_records = db.execute(
            """
            SELECT
                e.id,
                e.title,
                e.description,
                e.event_date,
                e.event_time,
                e.venue,
                e.organizer,
                e.image,
                COUNT(er.id) AS registration_count
            FROM events e
            LEFT JOIN event_registrations er
                ON e.id = er.event_id
            GROUP BY e.id
            ORDER BY
                e.event_date ASC,
                e.event_time ASC
            """
        ).fetchall()

        total_events = len(
            event_records
        )

        from datetime import date

        today = date.today().isoformat()

        upcoming_events = sum(
            1
            for event in event_records
            if event["event_date"]
            and event["event_date"] >= today
        )

        completed_events = sum(
            1
            for event in event_records
            if event["event_date"]
            and event["event_date"] < today
        )

        registrations = sum(
            (
                event["registration_count"]
                or 0
            )
            for event in event_records
        )

    finally:

        db.close()

    return render_template(
        "admin_events.html",
        events=event_records,
        total_events=total_events,
        upcoming_events=upcoming_events,
        registrations=registrations,
        completed_events=completed_events
    )


# ============================================================
# CREATE EVENT HELPER
# ============================================================

def create_event_from_form():

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    check = admin_required()

    if check:
        return check

    # --------------------------------------------------------
    # FORM VALUES
    # --------------------------------------------------------

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    event_date = request.form.get(
        "event_date",
        ""
    ).strip()

    event_time = request.form.get(
        "event_time",
        ""
    ).strip()

    venue = request.form.get(
        "venue",
        ""
    ).strip()

    organizer = request.form.get(
        "organizer",
        ""
    ).strip()

    image = request.form.get(
        "image",
        ""
    ).strip()

    # --------------------------------------------------------
    # COMPATIBILITY FOR OPTIONAL FIELDS
    # --------------------------------------------------------

    if not event_time:

        event_time = request.form.get(
            "time",
            ""
        ).strip()

    if not venue:

        venue = request.form.get(
            "location",
            ""
        ).strip()

    if not organizer:

        organizer = request.form.get(
            "created_by",
            ""
        ).strip()

    # --------------------------------------------------------
    # IMAGE FILE SUPPORT
    # --------------------------------------------------------

    uploaded_image = request.files.get(
        "image"
    )

    if uploaded_image:

        filename = (
            uploaded_image.filename
            or ""
        ).strip()

        if filename:

            image = filename

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not title:

        flash(
            "Please enter event title.",
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    if not description:

        flash(
            "Please enter event description.",
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    if not event_date:

        flash(
            "Please select event date.",
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    if not event_time:

        flash(
            "Please select event time.",
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    if not venue:

        flash(
            "Please enter event venue.",
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    if not organizer:

        flash(
            "Please enter event organizer.",
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    # --------------------------------------------------------
    # DATABASE INSERT
    # --------------------------------------------------------

    db = get_db()

    try:

        db.execute(
            """
            INSERT INTO events
            (
                title,
                description,
                event_date,
                event_time,
                venue,
                organizer,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                event_date,
                event_time,
                venue,
                organizer,
                image or None
            )
        )

        db.commit()

    except Exception as error:

        db.rollback()

        print(
            "[ERROR] Event creation failed:",
            error
        )

        flash(
            "Unable to create event: "
            + str(error),
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    finally:

        db.close()

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    flash(
        "Event created successfully.",
        "success"
    )

    return redirect(
        url_for(
            "events.admin_events"
        )
    )


# ============================================================
# ADMIN CREATE EVENT
#
# Correct URL:
# POST /events/admin/create
# ============================================================

@events.route(
    "/admin/create",
    methods=["POST"]
)
def admin_create_event():

    return create_event_from_form()


# ============================================================
# ADMIN DELETE EVENT
# ============================================================

@events.route(
    "/admin/delete/<int:event_id>",
    methods=["POST", "GET"]
)
def admin_delete_event(event_id):

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    check = admin_required()

    if check:
        return check

    db = get_db()

    try:

        event = db.execute(
            """
            SELECT id
            FROM events
            WHERE id = ?
            """,
            (event_id,)
        ).fetchone()

        if not event:

            flash(
                "Event not found.",
                "error"
            )

            return redirect(
                url_for(
                    "events.admin_events"
                )
            )

        # ----------------------------------------------------
        # DELETE REGISTRATIONS FIRST
        # ----------------------------------------------------

        db.execute(
            """
            DELETE FROM event_registrations
            WHERE event_id = ?
            """,
            (event_id,)
        )

        # ----------------------------------------------------
        # DELETE EVENT
        # ----------------------------------------------------

        db.execute(
            """
            DELETE FROM events
            WHERE id = ?
            """,
            (event_id,)
        )

        db.commit()

    except Exception as error:

        db.rollback()

        print(
            "[ERROR] Event deletion failed:",
            error
        )

        flash(
            "Unable to delete event: "
            + str(error),
            "error"
        )

        return redirect(
            url_for(
                "events.admin_events"
            )
        )

    finally:

        db.close()

    flash(
        "Event deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "events.admin_events"
        )
    )


# ============================================================
# COMPATIBILITY ENDPOINT
#
# Supports:
# events.admin_delete
#
# Some older templates may use:
# url_for('events.admin_delete', event_id=...)
# ============================================================

@events.route(
    "/admin/delete/<int:event_id>",
    methods=["POST"],
    endpoint="admin_delete"
)
def admin_delete(event_id):

    return admin_delete_event(
        event_id
    )


# ============================================================
# COMPATIBILITY ENDPOINT
#
# Some older templates may use:
# events.events
# ============================================================

@events.route(
    "/all",
    methods=["GET"],
    endpoint="events"
)
def events_compatibility():

    return events_page()


# ============================================================
# END OF EVENTS MODULE
# ============================================================

print(
    "[OK] Events module loaded."
)
