import sqlite3
import os

DB = "/storage/emulated/0/Ai/campus.db"

print("=" * 60)
print("CHECKING GITAM CAMPUS LIFE DATABASE")
print("=" * 60)

print("Database:", DB)
print("Exists:", os.path.exists(DB))

if not os.path.exists(DB):
    print("\nERROR: campus.db was not found!")
    input("\nPress Enter to exit...")
    raise SystemExit


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ------------------------------------------------------------
# CHECK USERS TABLE
# ------------------------------------------------------------

try:

    columns = conn.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    print("\nUSERS TABLE COLUMNS:")
    for column in columns:
        print(
            column["name"],
            "| type:",
            column["type"]
        )


    # --------------------------------------------------------
    # SHOW ALL USERS
    # --------------------------------------------------------

    users = conn.execute(
        """
        SELECT
            id,
            username,
            name,
            email,
            role,
            status
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()


    print("\n" + "=" * 60)
    print("ALL USERS")
    print("=" * 60)


    if not users:

        print("NO USERS FOUND.")

    else:

        for user in users:

            print(
                f"ID={user['id']} | "
                f"Username={user['username']} | "
                f"Name={user['name']} | "
                f"Role={user['role']} | "
                f"Status={user['status']}"
            )


    # --------------------------------------------------------
    # PENDING STUDENTS
    # --------------------------------------------------------

    pending_students = conn.execute(
        """
        SELECT *
        FROM users
        WHERE LOWER(TRIM(COALESCE(status, ''))) = 'pending'
        AND LOWER(TRIM(COALESCE(role, ''))) = 'student'
        ORDER BY id DESC
        """
    ).fetchall()


    print("\n" + "=" * 60)
    print("PENDING STUDENTS")
    print("=" * 60)


    if not pending_students:

        print("NO PENDING STUDENTS FOUND.")

    else:

        for user in pending_students:

            print(
                f"ID={user['id']} | "
                f"Username={user['username']} | "
                f"Name={user['name']} | "
                f"Status={user['status']}"
            )


except Exception as e:

    print("\nDATABASE ERROR:")
    print(type(e).__name__)
    print(str(e))


finally:

    conn.close()


print("\n" + "=" * 60)
print("CHECK FINISHED")
print("=" * 60)

input("\nPress Enter to exit...")