# ==============================================================
# Database Backup & Restore
# ==============================================================

import os
import subprocess
from datetime import datetime
from config import DB_CONFIG, REPORTS_DIR


def backup_database(output_dir=None):
    """Create a mysqldump backup of the database.

    Returns
    -------
    str : path to the backup .sql file, or error message on failure
    """
    if output_dir is None:
        output_dir = os.path.join(REPORTS_DIR, "backups")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{DB_CONFIG['database']}_{timestamp}.sql"
    filepath = os.path.join(output_dir, filename)

    cmd = [
        "mysqldump",
        f"--host={DB_CONFIG['host']}",
        f"--user={DB_CONFIG['user']}",
        f"--password={DB_CONFIG['password']}",
        "--single-transaction",
        "--routines",
        "--triggers",
        DB_CONFIG["database"],
    ]

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            result = subprocess.run(
                cmd, stdout=f, stderr=subprocess.PIPE,
                text=True, timeout=120,
            )
        if result.returncode != 0:
            return f"Backup failed: {result.stderr}"
        return filepath
    except FileNotFoundError:
        return "Error: mysqldump not found. Ensure MySQL client tools are installed and in PATH."
    except subprocess.TimeoutExpired:
        return "Error: Backup timed out after 120 seconds."
    except Exception as e:
        return f"Error: {e}"


def restore_database(filepath):
    """Restore a database from a .sql backup file.

    Returns
    -------
    tuple(bool, str) : (success, message)
    """
    if not os.path.isfile(filepath):
        return False, f"File not found: {filepath}"

    cmd = [
        "mysql",
        f"--host={DB_CONFIG['host']}",
        f"--user={DB_CONFIG['user']}",
        f"--password={DB_CONFIG['password']}",
        DB_CONFIG["database"],
    ]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            result = subprocess.run(
                cmd, stdin=f, stderr=subprocess.PIPE,
                text=True, timeout=120,
            )
        if result.returncode != 0:
            return False, f"Restore failed: {result.stderr}"
        return True, f"Database restored successfully from {filepath}"
    except FileNotFoundError:
        return False, "Error: mysql client not found. Ensure MySQL client tools are installed and in PATH."
    except subprocess.TimeoutExpired:
        return False, "Error: Restore timed out after 120 seconds."
    except Exception as e:
        return False, f"Error: {e}"
