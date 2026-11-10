from datetime import date
import sqlite3
from flask import Flask, render_template, request, redirect
from db import init_db, get_connection

app = Flask(__name__)
init_db()

@app.route("/")
def home():
    return render_template("home.html")

# EVENTS: add + view
@app.route("/events", methods=["GET", "POST"])
def events():
    conn = get_connection()
    if request.method == "POST":
        conn.execute(
            "INSERT INTO Events (evName, evDate, evVenue, evRFee) VALUES (?, ?, ?, ?)",
            (request.form["evName"], request.form["evDate"],
             request.form["evVenue"], request.form["evRFee"]))
        conn.commit()
        conn.close()
        return redirect("/events")
    rows = conn.execute("SELECT * FROM Events").fetchall()
    conn.close()
    return render_template("events.html", events=rows)

# EVENTS: search + update
@app.route("/events/update", methods=["GET", "POST"])
def events_update():
    conn = get_connection()
    if request.method == "POST":
        conn.execute(
            "UPDATE Events SET evName=?, evDate=?, evVenue=?, evRFee=? WHERE evCode=?",
            (request.form["evName"], request.form["evDate"],
             request.form["evVenue"], request.form["evRFee"],
             request.form["evCode"]))
        conn.commit()
        conn.close()
        return redirect("/events/update")
    search = request.args.get("search", "")
    rows = conn.execute("SELECT * FROM Events WHERE evName LIKE ?",
                        ("%" + search + "%",)).fetchall()
    conn.close()
    return render_template("events_update.html", events=rows, search=search)

# EVENTS: search + delete
@app.route("/events/delete", methods=["GET", "POST"])
def events_delete():
    conn = get_connection()
    error = ""
    if request.method == "POST":
        try:
            conn.execute("DELETE FROM Events WHERE evCode=?", (request.form["evCode"],))
            conn.commit()
        except sqlite3.IntegrityError:
            error = "Cannot delete: this event is still used by a participant."
    search = request.args.get("search", "")
    rows = conn.execute("SELECT * FROM Events WHERE evName LIKE ?",
                        ("%" + search + "%",)).fetchall()
    conn.close()
    return render_template("events_delete.html", events=rows, search=search, error=error)

# PARTICIPANTS: add + view 
@app.route("/participants", methods=["GET", "POST"])
def participants():
    conn = get_connection()
    if request.method == "POST":
        conn.execute(
            "INSERT INTO Participants (evCode, partFName, partLName, partDRate) VALUES (?, ?, ?, ?)",
            (request.form["evCode"], request.form["partFName"],
             request.form["partLName"], request.form["partDRate"]))
        conn.commit()
        conn.close()
        return redirect("/participants")
    events = conn.execute("SELECT * FROM Events").fetchall()
    rows = conn.execute("""
        SELECT p.*, e.evName FROM Participants p
        LEFT JOIN Events e ON p.evCode = e.evCode
    """).fetchall()
    conn.close()
    return render_template("participants.html", participants=rows, events=events)

# PARTICIPANTS: search + update 
@app.route("/participants/update", methods=["GET", "POST"])
def participants_update():
    conn = get_connection()
    if request.method == "POST":
        conn.execute(
            "UPDATE Participants SET evCode=?, partFName=?, partLName=?, partDRate=? WHERE partID=?",
            (request.form["evCode"], request.form["partFName"],
             request.form["partLName"], request.form["partDRate"],
             request.form["partID"]))
        conn.commit()
        conn.close()
        return redirect("/participants/update")
    search = request.args.get("search", "")
    events = conn.execute("SELECT * FROM Events").fetchall()
    rows = conn.execute(
        "SELECT * FROM Participants WHERE partFName LIKE ? OR partLName LIKE ?",
        ("%" + search + "%", "%" + search + "%")).fetchall()
    conn.close()
    return render_template("participants_update.html", participants=rows, events=events, search=search)

# PARTICIPANTS: search + delete 
@app.route("/participants/delete", methods=["GET", "POST"])
def participants_delete():
    conn = get_connection()
    error = ""
    if request.method == "POST":
        try:
            conn.execute("DELETE FROM Participants WHERE partID=?", (request.form["partID"],))
            conn.commit()
        except sqlite3.IntegrityError:
            error = "Cannot delete: this participant has registration records."
    search = request.args.get("search", "")
    rows = conn.execute("""
        SELECT p.*, e.evName FROM Participants p
        LEFT JOIN Events e ON p.evCode = e.evCode
        WHERE p.partFName LIKE ? OR p.partLName LIKE ?
    """, ("%" + search + "%", "%" + search + "%")).fetchall()
    conn.close()
    return render_template("participants_delete.html", participants=rows, search=search, error=error)

# REGISTRATION 
@app.route("/registration", methods=["GET", "POST"])
def registration():
    conn = get_connection()
    if request.method == "POST":
        part = conn.execute("""
            SELECT p.partDRate, e.evRFee FROM Participants p
            JOIN Events e ON p.evCode = e.evCode
            WHERE p.partID = ?
        """, (request.form["partID"],)).fetchone()
        fee = part["evRFee"] - (part["evRFee"] * part["partDRate"])
        conn.execute(
            "INSERT INTO Registration (partID, regDate, regFPaid, regPMode) VALUES (?, ?, ?, ?)",
            (request.form["partID"], request.form["regDate"], fee, request.form["regPMode"]))
        conn.commit()
        conn.close()
        return redirect("/registration")

    participants = conn.execute("""
        SELECT p.partID, p.partFName, p.partLName, p.partDRate,
               e.evName, e.evRFee
        FROM Participants p
        JOIN Events e ON p.evCode = e.evCode
    """).fetchall()
    records = conn.execute("""
        SELECT r.regCode, e.evName, p.partFName, p.partLName,
               r.regDate, r.regFPaid, r.regPMode
        FROM Registration r
        JOIN Participants p ON r.partID = p.partID
        JOIN Events e ON p.evCode = e.evCode
        ORDER BY r.regDate DESC, r.regCode DESC
    """).fetchall()
    conn.close()
    return render_template("registration.html", participants=participants,
                           records=records, today=date.today().isoformat())

# MONITORING 
@app.route("/monitoring")
def monitoring():
    conn = get_connection()
    events = conn.execute("SELECT * FROM Events").fetchall()
    evCode = request.args.get("evCode", "")
    event = None
    records = []
    count = 0
    total = 0
    discounts = 0

    if evCode:
        event = conn.execute("SELECT * FROM Events WHERE evCode = ?", (evCode,)).fetchone()
        records = conn.execute("""
            SELECT p.partFName, p.partLName, r.regDate, r.regFPaid
            FROM Registration r
            JOIN Participants p ON r.partID = p.partID
            WHERE p.evCode = ?
            ORDER BY r.regDate DESC, r.regCode DESC
        """, (evCode,)).fetchall()
        agg = conn.execute("""
            SELECT COUNT(r.regCode) AS cnt, COALESCE(SUM(r.regFPaid), 0) AS total
            FROM Registration r
            JOIN Participants p ON r.partID = p.partID
            WHERE p.evCode = ?
        """, (evCode,)).fetchone()
        count = agg["cnt"]
        total = agg["total"]
        discounts = (count * event["evRFee"]) - total

    conn.close()
    return render_template("monitoring.html", events=events, event=event,
                           records=records, count=count, total=total,
                           discounts=discounts, evCode=evCode)

if __name__ == "__main__":
    app.run(debug=True)