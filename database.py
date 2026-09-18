# ============================================================
# GITAM CAMPUS LIFE
# DATABASE
# COMPLETE UPGRADED VERSION
# ============================================================

import sqlite3
from datetime import datetime
from config import DATABASE_PATH


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    db = sqlite3.connect(DATABASE_PATH)

    db.row_factory = sqlite3.Row

    db.execute("PRAGMA foreign_keys = ON")

    return db


# ============================================================
# CHECK COLUMN
# ============================================================

def get_table_columns(cursor, table_name):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    return cursor.fetchall()


# ============================================================
# VISITOR TABLE MIGRATION
# ============================================================

def migrate_visitors_table(db):

    cursor = db.cursor()

    # --------------------------------------------------------
    # Check whether visitors table exists
    # --------------------------------------------------------

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'visitors'
    """)

    table_exists = cursor.fetchone()

    if not table_exists:
        return


    # --------------------------------------------------------
    # Check student_id constraint
    # --------------------------------------------------------

    columns = get_table_columns(
        cursor,
        "visitors"
    )

    student_id_not_null = False

    for column in columns:

        # PRAGMA table_info:
        # name = index 1
        # notnull = index 3

        if column["name"] == "student_id":

            if column["notnull"] == 1:
                student_id_not_null = True

            break


    # --------------------------------------------------------
    # Already correct
    # --------------------------------------------------------

    if not student_id_not_null:
        return


    print(
        "[INFO] Old visitors table detected."
    )

    print(
        "[INFO] Updating student_id to allow public visitors..."
    )


    # --------------------------------------------------------
    # Disable foreign keys temporarily
    # --------------------------------------------------------

    db.execute(
        "PRAGMA foreign_keys = OFF"
    )


    # --------------------------------------------------------
    # Rename old table
    # --------------------------------------------------------

    cursor.execute("""
        ALTER TABLE visitors
        RENAME TO visitors_old
    """)


    # --------------------------------------------------------
    # Create corrected visitors table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE visitors (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER,

            visitor_name TEXT NOT NULL,

            visitor_phone TEXT NOT NULL,

            relationship TEXT,

            visit_date TEXT NOT NULL,

            purpose TEXT NOT NULL,

            status TEXT DEFAULT 'Pending',

            qr_code TEXT,

            visitor_email TEXT,

            person_to_meet TEXT,

            arrival_time TEXT,

            visitor_count INTEGER DEFAULT 1,

            id_proof_type TEXT,

            id_proof_number TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(student_id)
                REFERENCES users(id)

        )
    """)


    # --------------------------------------------------------
    # Copy old records
    # --------------------------------------------------------

    old_columns = get_table_columns(
        cursor,
        "visitors_old"
    )

    old_column_names = {
        column["name"]
        for column in old_columns
    }


    # --------------------------------------------------------
    # Build safe copy query
    # --------------------------------------------------------

    fields = [
        "id",
        "student_id",
        "visitor_name",
        "visitor_phone",
        "relationship",
        "visit_date",
        "purpose",
        "status",
        "qr_code",
        "visitor_email",
        "person_to_meet",
        "arrival_time",
        "visitor_count",
        "id_proof_type",
        "id_proof_number",
        "created_at"
    ]


    available_fields = [
        field
        for field in fields
        if field in old_column_names
    ]


    if available_fields:

        field_list = ", ".join(
            available_fields
        )

        cursor.execute(
            f"""
            INSERT INTO visitors
            ({field_list})
            SELECT
            {field_list}
            FROM visitors_old
            """
        )


    # --------------------------------------------------------
    # Remove old table
    # --------------------------------------------------------

    cursor.execute("""
        DROP TABLE visitors_old
    """)


    # --------------------------------------------------------
    # Restore foreign keys
    # --------------------------------------------------------

    db.execute(
        "PRAGMA foreign_keys = ON"
    )


    print(
        "[OK] Visitor database upgraded successfully."
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    db = get_db()

    cursor = db.cursor()


    # ========================================================
    # USERS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            name TEXT NOT NULL,

            email TEXT,

            role TEXT DEFAULT 'student',

            roll_no TEXT,

            branch TEXT,

            year TEXT,

            designation TEXT,

            phone TEXT,

            profile_image TEXT,

            status TEXT DEFAULT 'active',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # ========================================================
    # ATTENDANCE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            subject TEXT NOT NULL,

            attendance_date TEXT NOT NULL,

            status TEXT DEFAULT 'Present',

            qr_code TEXT,

            FOREIGN KEY(student_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # LEAVE REQUESTS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            from_date TEXT NOT NULL,

            to_date TEXT NOT NULL,

            reason TEXT NOT NULL,

            status TEXT DEFAULT 'Pending',

            qr_code TEXT,

            FOREIGN KEY(student_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # GATE PASSES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gate_passes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            purpose TEXT NOT NULL,

            exit_date TEXT NOT NULL,

            return_date TEXT NOT NULL,

            status TEXT DEFAULT 'Pending',

            qr_code TEXT,

            FOREIGN KEY(student_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # CERTIFICATE REQUESTS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificate_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            certificate_type TEXT NOT NULL,

            reason TEXT,

            status TEXT DEFAULT 'Pending',

            FOREIGN KEY(student_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # COMPLAINTS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            category TEXT NOT NULL,

            subject TEXT NOT NULL,

            description TEXT NOT NULL,

            status TEXT DEFAULT 'Pending',

            response TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # NOTICES
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            content TEXT NOT NULL,

            target_role TEXT DEFAULT 'all',

            created_by INTEGER,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(created_by)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            message TEXT NOT NULL,

            is_read INTEGER DEFAULT 0,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # DIGITAL ID
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS digital_ids (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER UNIQUE NOT NULL,

            qr_code TEXT,

            FOREIGN KEY(user_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # VISITORS
    #
    # IMPORTANT:
    # student_id IS OPTIONAL.
    #
    # This allows a public visitor to apply without
    # having a student account.
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER,

            visitor_name TEXT NOT NULL,

            visitor_phone TEXT NOT NULL,

            relationship TEXT,

            visit_date TEXT NOT NULL,

            purpose TEXT NOT NULL,

            status TEXT DEFAULT 'Pending',

            qr_code TEXT,

            visitor_email TEXT,

            person_to_meet TEXT,

            arrival_time TEXT,

            visitor_count INTEGER DEFAULT 1,

            id_proof_type TEXT,

            id_proof_number TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(student_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # FIX OLD VISITOR DATABASE
    # ========================================================

    migrate_visitors_table(db)


    # ========================================================
    # VISITOR COLUMN MIGRATION
    # ========================================================

    cursor.execute(
        "PRAGMA table_info(visitors)"
    )

    existing_columns = {
        row["name"]
        for row in cursor.fetchall()
    }


    visitor_columns = {

        "visitor_email": "TEXT",

        "person_to_meet": "TEXT",

        "arrival_time": "TEXT",

        "visitor_count": "INTEGER DEFAULT 1",

        "id_proof_type": "TEXT",

        "id_proof_number": "TEXT",

        "created_at": "TEXT"

    }


    for column_name, column_type in visitor_columns.items():

        if column_name not in existing_columns:

            try:

                cursor.execute(
                    f"""
                    ALTER TABLE visitors
                    ADD COLUMN {column_name}
                    {column_type}
                    """
                )

            except Exception:

                pass


    # ========================================================
    # EVENTS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            description TEXT,

            event_date TEXT NOT NULL,

            event_time TEXT,

            venue TEXT,

            organizer TEXT,

            image TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # ========================================================
    # EVENT REGISTRATIONS
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_registrations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            event_id INTEGER NOT NULL,

            user_id INTEGER NOT NULL,

            registered_at TEXT DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(event_id, user_id),

            FOREIGN KEY(event_id)
                REFERENCES events(id),

            FOREIGN KEY(user_id)
                REFERENCES users(id)

        )
    """)


    # ========================================================
    # UPDATE OLD VISITOR RECORDS
    # ========================================================

    try:

        cursor.execute("""
            UPDATE visitors

            SET created_at =
                COALESCE(
                    created_at,
                    ?
                )

            WHERE created_at IS NULL

        """, (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        ))

    except Exception:

        pass


    # ========================================================
    # SAVE
    # ========================================================

    db.commit()

    db.close()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    init_db()

    print(
        "Database initialized successfully."
    )