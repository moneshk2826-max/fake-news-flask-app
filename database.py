import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fakenews.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS news_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            keyword TEXT,
            added_by TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS attack_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            keyword TEXT,
            added_by TEXT DEFAULT 'attacker',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS malware_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urls TEXT,
            keywords TEXT,
            ips TEXT,
            user_agent TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS malware_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            result TEXT,
            confidence REAL,
            ip_address TEXT,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    default_indicators = [
        'shocking', 'breaking', 'exclusive', 'unbelievable', 'scandal',
        'crisis', 'emergency', 'outrageous', 'bombshell', 'revolutionary',
        'miracle', 'secret', 'conspiracy', 'exposed', 'truth',
        'lies', 'deception', 'hoax', 'fake', 'fraud'
    ]
    for word in default_indicators:
        try:
            cursor.execute("INSERT INTO indicators (word) VALUES (?)", (word,))
        except sqlite3.IntegrityError:
            pass

    default_malware = [
        'http://malicious-phishing.com/login',
        'http://fake-bank-secure.xyz/verify',
        'http://win-free-prize.biz/claim',
        'http://download-virus.tk/free',
        'http://crypto-scam-invest.online/pay',
        'http://fake-news-generator.net/breaking',
        'http://suspicious-redirect.info/click',
        'http://phishing-attempt.co/reset',
    ]
    for site in default_malware:
        try:
            cursor.execute("INSERT INTO malware_sites (site) VALUES (?)", (site,))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


def get_all_indicators():
    conn = get_db()
    rows = conn.execute("SELECT * FROM indicators ORDER BY word").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_indicator_words():
    conn = get_db()
    rows = conn.execute("SELECT word FROM indicators ORDER BY word").fetchall()
    conn.close()
    return [r['word'] for r in rows]


def add_indicator(word):
    conn = get_db()
    try:
        conn.execute("INSERT INTO indicators (word) VALUES (?)", (word.strip().lower(),))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def remove_indicator(word):
    conn = get_db()
    conn.execute("DELETE FROM indicators WHERE word = ?", (word,))
    conn.commit()
    conn.close()


def add_news_url(url, keyword):
    conn = get_db()
    conn.execute("INSERT INTO news_urls (url, keyword) VALUES (?, ?)", (url, keyword))
    conn.commit()
    conn.close()


def get_all_news_urls():
    conn = get_db()
    rows = conn.execute("SELECT * FROM news_urls ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_attack_url(url, keyword):
    conn = get_db()
    conn.execute("INSERT INTO attack_urls (url, keyword) VALUES (?, ?)", (url, keyword))
    conn.commit()
    conn.close()


def get_all_attack_urls():
    conn = get_db()
    rows = conn.execute("SELECT * FROM attack_urls ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_malware(urls, keywords, ips, user_agent=''):
    conn = get_db()
    conn.execute(
        "INSERT INTO malware_logs (urls, keywords, ips, user_agent) VALUES (?, ?, ?, ?)",
        (urls, keywords, ips, user_agent)
    )
    conn.commit()
    conn.close()


def get_malware_logs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM malware_logs ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_malware_sites():
    conn = get_db()
    rows = conn.execute("SELECT * FROM malware_sites ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_malware_site(site):
    conn = get_db()
    try:
        conn.execute("INSERT INTO malware_sites (site) VALUES (?)", (site,))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def check_url_malicious(url):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM attack_urls WHERE url = ? LIMIT 1", (url,)
    ).fetchone()
    if not row:
        row = conn.execute(
            "SELECT * FROM malware_sites WHERE site = ? LIMIT 1", (url,)
        ).fetchone()
    conn.close()
    return dict(row) if row else None


def log_search(query, result, confidence, ip_address):
    conn = get_db()
    conn.execute(
        "INSERT INTO search_history (query, result, confidence, ip_address) VALUES (?, ?, ?, ?)",
        (query, result, confidence, ip_address)
    )
    conn.commit()
    conn.close()


def get_search_history(limit=50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM search_history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_stats():
    conn = get_db()
    stats = {
        'total_indicators': conn.execute("SELECT COUNT(*) FROM indicators").fetchone()[0],
        'total_news_urls': conn.execute("SELECT COUNT(*) FROM news_urls").fetchone()[0],
        'total_attack_urls': conn.execute("SELECT COUNT(*) FROM attack_urls").fetchone()[0],
        'total_malware_logs': conn.execute("SELECT COUNT(*) FROM malware_logs").fetchone()[0],
        'total_malware_sites': conn.execute("SELECT COUNT(*) FROM malware_sites").fetchone()[0],
        'total_searches': conn.execute("SELECT COUNT(*) FROM search_history").fetchone()[0],
        'fake_detections': conn.execute(
            "SELECT COUNT(*) FROM search_history WHERE result = 'Fake News'"
        ).fetchone()[0],
        'recent_searches': [dict(r) for r in conn.execute(
            "SELECT * FROM search_history ORDER BY id DESC LIMIT 5"
        ).fetchall()],
    }
    conn.close()
    return stats
