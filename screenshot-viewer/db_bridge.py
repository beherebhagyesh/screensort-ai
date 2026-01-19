import sqlite3
import sys
import json
import os

DB_PATH = "../screenshots.db"

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
        "storage_usage": "Calculating...", # We don't track file size in DB yet, maybe add later
        "categories": categories,
        "insights": insights
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
    elif command == "search":
        if len(sys.argv) < 3:
            print(json.dumps([]))
        else:
            search(sys.argv[2])
    else:
        print(json.dumps({"error": "Unknown command"}))

if __name__ == "__main__":
    main()