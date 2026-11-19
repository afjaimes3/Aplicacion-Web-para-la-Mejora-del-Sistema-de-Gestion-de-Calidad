"""
Database connection module.
Provides SQLite database connections for the application.
"""
import sqlite3
import os

# SQLite configuration
DB_FILE = "database.db"


def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def get_connection():
    """
    Get database connection.
    Returns a SQLite connection object.
    """
    return get_db_connection()
