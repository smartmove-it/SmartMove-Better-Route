from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = "smartmove-demo-secret"

DATABASE = "smartmove.db"


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- DATABASE SETUP ----------------

def init_db():

    conn = get_db()

    conn.executescript("""
    
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        area TEXT NOT NULL,
        crowd_level TEXT NOT NULL,
        crowd_count INTEGER NOT NULL,
        best_time TEXT NOT NULL,
        alternative TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id INTEGER NOT NULL,
        crowd_level TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(location_id) REFERENCES locations(id)
    );

    """)

    # Check if locations already exist
    count = conn.execute(
        "SELECT COUNT(*) FROM locations"
    ).fetchone()[0]

    # Add sample locations only once
    if count == 0:

        locations = [

            (
                "Palghar Railway Station",
                "Palghar",
                "High",
                85,
                "After 4:00 PM",
                "Tembhode Road"
            ),

            (
                "Palghar Market",
                "Palghar",
                "Moderate",
                55,
                "10:30 AM - 12:00 PM",
                "Tembhode Road"
            ),

            (
                "Palghar Bus Stand",
                "Palghar",
                "Low",
                25,
                "Anytime",
                "Palghar Railway Station"
            ),

            (
                "Boisar Railway Station",
                "Boisar",
                "High",
                90,
                "After 3:30 PM",
                "Umroli Railway Station"
            ),

            (
                "Boisar Market",
                "Boisar",
                "Moderate",
                60,
                "11:00 AM - 1:00 PM",
                "Palghar Market"
            ),

            (
                "Tembhode Road",
                "Palghar",
                "Low",
                20,
                "Anytime",
                "Palghar Main Road"
            )

        ]

        conn.executemany("""
            INSERT INTO locations
            (name, area, crowd_level, crowd_count, best_time, alternative)
            VALUES (?, ?, ?, ?, ?, ?)
        """, locations)

    conn.commit()
    conn.close()


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():

    conn = get_db()

    locations = conn.execute("""
        SELECT * FROM locations
        ORDER BY name
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        locations=locations
    )


# ---------------- DASHBOARD ----------------


@app.route("/dashboard")
def dashboard():

    conn = get_db()

    locations = conn.execute("""
        SELECT * FROM locations
        ORDER BY crowd_count DESC
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        locations=locations
    )
   
@app.route("/crowd_status")
def crowd_status():

    conn = get_db()

    locations = conn.execute("""
        SELECT * FROM locations
        ORDER BY crowd_count DESC
    """).fetchall()

    conn.close()

    return render_template(
        "crowd_status.html",
        locations=locations
    )
   


# ---------------- LOCATION DETAILS ----------------

@app.route("/location/<int:location_id>")
def location(location_id):

    conn = get_db()

    selected_location = conn.execute("""
        SELECT * FROM locations
        WHERE id = ?
    """, (location_id,)).fetchone()

    alternatives = conn.execute("""
        SELECT * FROM locations
        WHERE id != ?
        ORDER BY crowd_count ASC
        LIMIT 3
    """, (location_id,)).fetchall()

    conn.close()

    if selected_location is None:
        return "Location not found", 404

    return render_template(
        "location.html",
        location=selected_location,
        alternatives=alternatives
    )


# ---------------- CROWD REPORT ----------------

@app.route("/report", methods=["POST"])
def report():

    location_id = request.form.get("location_id")
    crowd_level = request.form.get("crowd_level")

    if crowd_level not in ["Low", "Moderate", "High"]:

        flash("Please select a valid crowd level.")

        return redirect(url_for("home"))

    conn = get_db()

    # Save user report
    conn.execute("""
        INSERT INTO reports
        (location_id, crowd_level, created_at)
        VALUES (?, ?, ?)
    """, (
        location_id,
        crowd_level,
        datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    ))

    # Convert crowd level into estimated percentage
    crowd_percentage = {

        "Low": 25,
        "Moderate": 55,
        "High": 85

    }

    percentage = crowd_percentage[crowd_level]

    # Update location
    conn.execute("""
        UPDATE locations
        SET crowd_level = ?,
            crowd_count = ?
        WHERE id = ?
    """, (
        crowd_level,
        percentage,
        location_id
    ))

    conn.commit()
    conn.close()

    flash("Crowd report submitted successfully.")

    return redirect(
        url_for(
            "location",
            location_id=location_id
        )
    )


# ---------------- ADMIN PAGE ----------------

@app.route("/admin")
def admin():

    conn = get_db()

    locations = conn.execute("""
        SELECT * FROM locations
        ORDER BY id
    """).fetchall()

    reports = conn.execute("""
        SELECT reports.*, locations.name
        FROM reports
        JOIN locations
        ON reports.location_id = locations.id
        ORDER BY reports.id DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        locations=locations,
        reports=reports
    )


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )
    
