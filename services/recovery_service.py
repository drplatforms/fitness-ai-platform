from datetime import datetime

from database import get_connection

# =====================================
# Get Recent Recovery Metrics
# =====================================


def get_recent_recovery_metrics(limit=7):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM daily_checkins
    ORDER BY created_at DESC
    LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    avg_sleep = sum(row["sleep_hours"] for row in rows) / len(rows)
    avg_energy = sum(row["energy_level"] for row in rows) / len(rows)
    avg_soreness = sum(row["soreness_level"] for row in rows) / len(rows)

    latest_weight = rows[0]["body_weight"]
    oldest_weight = rows[-1]["body_weight"]

    return {
        "entries_analyzed": len(rows),
        "avg_sleep": round(avg_sleep, 1),
        "avg_energy": round(avg_energy, 1),
        "avg_soreness": round(avg_soreness, 1),
        "latest_weight": latest_weight,
        "weight_change": round(latest_weight - oldest_weight, 1),
        "recent_notes": [row["notes"] for row in rows if row["notes"]],
    }


# =====================================
# Save Recovery Reports
# =====================================


def save_recovery_report(metrics, recommendation):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO recovery_reports (
        report_date,
        entries_analyzed,
        avg_sleep,
        avg_energy,
        avg_soreness,
        weight_change,
        recommendation
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            datetime.now().strftime("%Y-%m-%d"),
            metrics["entries_analyzed"],
            metrics["avg_sleep"],
            metrics["avg_energy"],
            metrics["avg_soreness"],
            metrics["weight_change"],
            recommendation,
        ),
    )

    conn.commit()
    conn.close()


# =====================================
# Get Recent Recovery Reports
# =====================================


def get_recent_recovery_reports(limit=5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT *
    FROM recovery_reports
    ORDER BY created_at DESC
    LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================
# Save Recovery Check-In
# =====================================


def save_recovery_checkin(
    user_id: int,
    body_weight: float,
    sleep_hours: float,
    energy_level: int,
    soreness_level: int,
    mood: str,
    notes: str,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO daily_checkins (
            user_id,
            checkin_date,
            body_weight,
            sleep_hours,
            energy_level,
            soreness_level,
            mood,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            datetime.now().strftime("%Y-%m-%d"),
            body_weight,
            sleep_hours,
            energy_level,
            soreness_level,
            mood,
            notes,
        ),
    )

    checkin_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return checkin_id
