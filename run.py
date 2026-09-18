# ============================================================
# GITAM CAMPUS LIFE
# RUN FILE
# ============================================================

from app import app


if __name__ == "__main__":
    print("=" * 60)
    print("        GITAM CAMPUS LIFE")
    print("        MADE BY TEAM INNOVATORS HUB")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )