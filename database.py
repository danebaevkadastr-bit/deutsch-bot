import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

from logger import get_logger

logger = get_logger(__name__)

DB_FILE = "bot_stats.db"


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                total_requests INTEGER DEFAULT 0,
                total_tasks_checked INTEGER DEFAULT 0,
                total_teacher_requests INTEGER DEFAULT 0,
                language TEXT DEFAULT 'uz'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_number INTEGER,
                text_length INTEGER,
                check_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_length INTEGER,
                response_time INTEGER,
                request_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_users INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                task_checks INTEGER DEFAULT 0,
                teacher_requests INTEGER DEFAULT 0
            )
        ''')
        
        logger.info("Database initialized")


def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Dict:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        now = datetime.now()
        
        if user:
            cursor.execute('''
                UPDATE users SET last_seen = ?, username = COALESCE(?, username)
                WHERE user_id = ?
            ''', (now, username, user_id))
            return dict(user)
        else:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen, total_requests)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, now, now, 0))
            logger.info(f"New user: {user_id} ({username})")
            return {'user_id': user_id, 'username': username}


def update_user_request(user_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET total_requests = total_requests + 1, last_seen = ?
            WHERE user_id = ?
        ''', (datetime.now(), user_id))


def log_task_check(user_id: int, task_number: int, text_length: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO task_checks (user_id, task_number, text_length, check_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, task_number, text_length, datetime.now()))
        cursor.execute('''
            UPDATE users SET total_tasks_checked = COALESCE(total_tasks_checked, 0) + 1
            WHERE user_id = ?
        ''', (user_id,))
        update_daily_stats('task_checks')


def log_teacher_request(user_id: int, question_length: int, response_time: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO teacher_requests (user_id, question_length, response_time, request_time)
            VALUES (?, ?, ?, ?)
        ''', (user_id, question_length, response_time, datetime.now()))
        cursor.execute('''
            UPDATE users SET total_teacher_requests = COALESCE(total_teacher_requests, 0) + 1
            WHERE user_id = ?
        ''', (user_id,))
        update_daily_stats('teacher_requests')


def update_daily_stats(request_type: str):
    today = date.today().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_stats WHERE date = ?", (today,))
        stats = cursor.fetchone()
        
        if stats:
            if request_type == 'task_checks':
                cursor.execute('''
                    UPDATE daily_stats SET task_checks = task_checks + 1, total_requests = total_requests + 1
                    WHERE date = ?
                ''', (today,))
            else:
                cursor.execute('''
                    UPDATE daily_stats SET teacher_requests = teacher_requests + 1, total_requests = total_requests + 1
                    WHERE date = ?
                ''', (today,))
        else:
            cursor.execute('''
                INSERT INTO daily_stats (date, total_users, total_requests, task_checks, teacher_requests)
                VALUES (?, ?, ?, ?, ?)
            ''', (today, 0, 1, 1 if request_type == 'task_checks' else 0, 1 if request_type == 'teacher_requests' else 0))
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        cursor.execute('UPDATE daily_stats SET total_users = ? WHERE date = ?', (total_users, today))


def get_user_statistics(user_id: int) -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {}
        
        cursor.execute("SELECT COUNT(*) as count FROM task_checks WHERE user_id = ?", (user_id,))
        task_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM teacher_requests WHERE user_id = ?", (user_id,))
        teacher_count = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT task_number, COUNT(*) as count FROM task_checks
            WHERE user_id = ? GROUP BY task_number ORDER BY count DESC LIMIT 5
        ''', (user_id,))
        top_tasks = [dict(row) for row in cursor.fetchall()]
        
        return {
            'user_id': user_id,
            'username': user['username'],
            'first_seen': user['first_seen'],
            'last_seen': user['last_seen'],
            'total_requests': user['total_requests'],
            'task_checks': task_count,
            'teacher_requests': teacher_count,
            'top_tasks': top_tasks
        }


def get_bot_statistics() -> Dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM task_checks")
        total_task_checks = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM teacher_requests")
        total_teacher_requests = cursor.fetchone()['count']
        
        cursor.execute('''
            SELECT task_number, COUNT(*) as count FROM task_checks
            GROUP BY task_number ORDER BY count DESC LIMIT 5
        ''')
        top_tasks = [dict(row) for row in cursor.fetchall()]
        
        return {
            'total_users': total_users,
            'total_task_checks': total_task_checks,
            'total_teacher_requests': total_teacher_requests,
            'top_tasks': top_tasks
        }


def get_admin_stats_text() -> str:
    stats = get_bot_statistics()
    text = (
        f"📊 **Bot Statistikasi**\n\n"
        f"👥 **Foydalanuvchilar:** {stats['total_users']}\n"
        f"📝 **Task tekshirishlar:** {stats['total_task_checks']}\n"
        f"👨‍🏫 **AI Ustoz so'rovlari:** {stats['total_teacher_requests']}\n\n"
        f"🔥 **Eng ko'p tekshirilgan Aufgabe:**\n"
    )
    for task in stats['top_tasks']:
        text += f"  • Aufgabe {task['task_number']}: {task['count']} marta\n"
    return text


def get_all_users():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username FROM users")
        return [dict(row) for row in cursor.fetchall()]


init_db()