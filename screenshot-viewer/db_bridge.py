import sqlite3
import sys
import json
import os
import shutil

# Resolve DB path relative to this script (one level up)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "../screenshots.db")
# Destination root
SCREENSHOTS_DIR = '/sdcard/Pictures/Screenshots'

def get_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

def move_file(filename, new_category):
    conn = get_db()
    c = conn.cursor()
    
    # 1. Get current path
    c.execute("SELECT path, category FROM screenshots WHERE filename = ?", (filename,))
    row = c.fetchone()
    if not row:
        print(json.dumps({"error": "File not found in database"}))
        return

    old_path = row['path']
    old_category = row['category']
    
    if old_category == new_category:
        print(json.dumps({"success": True, "message": "Already in this category"}))
        return

    # 2. Construct new path
    dest_dir = os.path.join(SCREENSHOTS_DIR, new_category)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
    
    new_path = os.path.join(dest_dir, filename)
    
    # Handle collision
    if os.path.exists(new_path):
        import time
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_{int(time.time())}{ext}"
        new_path = os.path.join(dest_dir, new_filename)
        final_filename = new_filename
    else:
        final_filename = filename

    # 3. Move file
    try:
        if os.path.exists(old_path):
            shutil.move(old_path, new_path)
        else:
            # Maybe the path in DB is outdated but file exists in expected old location?
            # Or maybe it's already gone.
            print(json.dumps({"error": f"Physical file not found at {old_path}"}))
            return
            
    except Exception as e:
        print(json.dumps({"error": f"Move failed: {str(e)}"}))
        return

    # 4. Update DB
    try:
        c.execute("UPDATE screenshots SET path = ?, category = ?, filename = ? WHERE filename = ?", 
                  (new_path, new_category, final_filename, filename))
        conn.commit()
        print(json.dumps({"success": True, "new_path": new_path, "new_filename": final_filename}))
    except Exception as e:
        print(json.dumps({"error": f"DB update failed: {str(e)}"}))

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
            "amount": r['amount'],
            "created_at": r['created_at']
        })
    
    print(json.dumps(results))

def get_category_files(category, sort_by="date_desc"):
    conn = get_db()
    c = conn.cursor()
    
    order_clause = "created_at DESC"
    if sort_by == "date_asc":
        order_clause = "created_at ASC"
    elif sort_by == "name_asc":
        order_clause = "filename ASC"
    elif sort_by == "name_desc":
        order_clause = "filename DESC"
    elif sort_by == "amount_desc":
        order_clause = "amount DESC NULLS LAST"

    sql = f"SELECT * FROM screenshots WHERE category = ? ORDER BY {order_clause}"
    c.execute(sql, (category,))
    
    files = []
    for r in c.fetchall():
        files.append({
            "name": r['filename'],
            "path": r['path'].replace('/sdcard/Pictures/Screenshots', '/images'),
            "created_at": r['created_at'],
            "ai_summary": r['ai_summary'],
            "amount": r['amount']
        })
    
    print(json.dumps({"files": files}))

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
    elif command == "get_category_files":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing category"}))
        else:
            cat = sys.argv[2]
            sort = sys.argv[3] if len(sys.argv) > 3 else "date_desc"
            get_category_files(cat, sort)
    elif command == "move_file":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Missing filename or category"}))
        else:
            filename = sys.argv[2]
            new_cat = sys.argv[3]
            move_file(filename, new_cat)
    else:
        print(json.dumps({"error": "Unknown command"}))

if __name__ == "__main__":
    main()