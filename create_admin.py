# ============================================================
# GITAM CAMPUS LIFE
# CREATE ADMIN ACCOUNT
# ============================================================

from werkzeug.security import generate_password_hash
from database import get_db, init_db


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_db()


# ============================================================
# ADMIN DETAILS
# ============================================================

USERNAME = "admin"
PASSWORD = "Admin@123"
NAME = "Campus Administrator"
EMAIL = "admin@gitamcampus.local"


# ============================================================
# CREATE / UPDATE ADMIN
# ============================================================

conn = get_db()

existing = conn.execute(
    """
    SELECT id
    FROM users
    WHERE username = ?
    """,
    (USERNAME,)
).fetchone()


if existing:

    # Existing admin username found.
    # Reset password and make account active.

    conn.execute(
        """
        UPDATE users
        SET
            password = ?,
            name = ?,
            email = ?,
            role = 'admin',
            status = 'Active'
        WHERE username = ?
        """,
        (
            generate_password_hash(PASSWORD),
            NAME,
            EMAIL,
            USERNAME
        )
    )

    conn.commit()

    print()
    print("=" * 60)
    print("ADMIN ACCOUNT UPDATED")
    print("=" * 60)

else:

    # Create new admin account.

    conn.execute(
        """
        INSERT INTO users
        (
            username,
            password,
            name,
            email,
            role,
            roll_no,
            branch,
            year,
            designation,
            phone,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            USERNAME,
            generate_password_hash(PASSWORD),
            NAME,
            EMAIL,
            "admin",
            "",
            "",
            "",
            "Administrator",
            "",
            "Active"
        )
    )

    conn.commit()

    print()
    print("=" * 60)
    print("ADMIN ACCOUNT CREATED")
    print("=" * 60)


conn.close()


# ============================================================
# SHOW LOGIN DETAILS
# ============================================================

print()
print("Username : admin")
print("Password : Admin@123")
print("Role     : admin")
print("Status   : Active")
print()
print("You can now login from:")
print("http://127.0.0.1:5000/login")
print()
print("=" * 60)