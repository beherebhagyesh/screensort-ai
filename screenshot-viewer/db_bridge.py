import sqlite3
import sys
import json
import os

# Resolve DB path relative to this script (one level up)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../screenshots.db")

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

def get_stats():
    conn = get_db()
    c = conn.cursor()
    
    # Total Files
    c.execute("SELECT count(*) as count, sum(length(text)) as size_est FROM screenshots")
    row = c.fetchone()
    total_files = row['count']
    
    # Categories
    c.execute("SELECT category, count(*) as count FROM screenshots GROUP BY category ORDER BY count DESC")
    categories = []
    for r in c.fetchall():
        categories.append({
            "name": r['category'],
            "count": r['count']
        })
    
    # Recent Insights (just 2 newest)
    c.execute("SELECT * FROM screenshots ORDER BY created_at DESC LIMIT 2")
    insights = []
    for r in c.fetchall():
        insights.append({
            "title": f"New {r['category']} Screenshot",
            "category": r['category'],
            "detail": r['text'][:50] + "..." if r['text'] else "No text detected",
            "time": r['created_at'], # Timestamp
            "image": r['path'].replace('/sdcard/Pictures/Screenshots', '/images'),
            "amount": r['amount']
        })
        
    print(json.dumps({
        "total_photos": total_files,
        "storage_usage": "Calculating...",
        "categories": categories,
        "insights": insights
    }))

def get_dashboard_data():
    conn = get_db()
    c = conn.cursor()
    
    # 1. Activity (Last 14 Days)
    # created_at is in milliseconds
    sql_activity = """
        SELECT strftime('%Y-%m-%d', datetime(created_at/1000, 'unixepoch', 'localtime')) as date, count(*) as count
        FROM screenshots 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 14
    """
    c.execute(sql_activity)
    activity_data = [{"date": r['date'], "count": r['count']} for r in c.fetchall()]
    # Reverse to show chronological order in graphs
    activity_data.reverse()

    # 2. Finance/Spending (Last 30 Days)
    sql_finance = """
        SELECT strftime('%Y-%m-%d', datetime(created_at/1000, 'unixepoch', 'localtime')) as date, sum(amount) as total
        FROM screenshots 
        WHERE amount IS NOT NULL AND amount > 0
        GROUP BY date
        ORDER BY date DESC 
        LIMIT 30
    """
    c.execute(sql_finance)
    finance_data = [{"date": r['date'], "total": r['total']} for r in c.fetchall()]
    finance_data.reverse()

    # 3. Category Breakdown (All time)
    c.execute("SELECT category, count(*) as count FROM screenshots GROUP BY category ORDER BY count DESC")
    categories = [{"name": r['category'], "count": r['count']} for r in c.fetchall()]

    # 4. Language Distribution
    c.execute("SELECT detected_language, count(*) as count FROM screenshots WHERE detected_language IS NOT NULL GROUP BY detected_language")
    languages = [{"lang": r['detected_language'], "count": r['count']} for r in c.fetchall()]

    # 5. Recent Files (Extended)
    c.execute("SELECT * FROM screenshots ORDER BY created_at DESC LIMIT 6")
    recent = []
    for r in c.fetchall():
        recent.append({
            "id": r['id'],
            "filename": r['filename'],
            "category": r['category'],
            "text_preview": r['text'][:60] + "..." if r['text'] else "",
            "amount": r['amount'],
            "created_at": r['created_at'],
            "ai_summary": r['ai_summary'],
            "is_video": r['is_video'],
            "path": r['path'].replace('/sdcard/Pictures/Screenshots', '/images')
        })

    print(json.dumps({
        "activity": activity_data,
        "finance": finance_data,
        "categories": categories,
        "languages": languages,
        "recent": recent
    }))

def search(query):
    conn = get_db()
    c = conn.cursor()
    
    # Full text search (simple LIKE for now)
    sql = "SELECT * FROM screenshots WHERE text LIKE ? OR category LIKE ? ORDER BY created_at DESC LIMIT 50"
    term = f"%{query}%"
    c.execute(sql, (term, term))
    
    results = []
    for r in c.fetchall():
        results.append({
            "filename": r['filename'],
            "category": r['category'],
            "path": r['path'].replace('/sdcard/Pictures/Screenshots', '/images'),
            "text_snippet": r['text'][:100] if r['text'] else "",
            "amount": r['amount']
        })
    
    print(json.dumps(results))

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        return

    command = sys.argv[1]
    
    if command == "stats":
        get_stats()
    elif command == "dashboard_data":
        get_dashboard_data()
    elif command == "search":
        if len(sys.argv) < 3:
            print(json.dumps([]))
        else:
            search(sys.argv[2])
    else:
        print(json.dumps({"error": "Unknown command"}))

if __name__ == "__main__":
    main()