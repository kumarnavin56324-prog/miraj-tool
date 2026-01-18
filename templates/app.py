from flask import Flask, render_template, request, redirect, Response
import datetime
import uuid
import sqlite3
import csv
import io

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('miraj.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links 
                 (id TEXT, title TEXT, original_url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tracks 
                 (title TEXT, platform TEXT, dt TEXT, browser TEXT, device TEXT, ip TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def dashboard():
    conn = sqlite3.connect('miraj.db')
    conn.row_factory = sqlite3.Row
    links = conn.execute('SELECT * FROM links').fetchall()
    tracks = conn.execute('SELECT * FROM tracks ORDER BY dt DESC').fetchall()
    conn.close()
    return render_template('index.html', links=links, tracks=tracks)

@app.route('/generate', methods=['POST'])
def generate():
    titles = request.form.getlist('title[]')
    urls = request.form.getlist('url[]')
    conn = sqlite3.connect('miraj.db')
    for t, u in zip(titles, urls):
        if t and u:
            project_id = str(uuid.uuid4())[:8]
            conn.execute('INSERT INTO links VALUES (?, ?, ?)', (project_id, t, u))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/t/<id>/<platform>')
def track(id, platform):
    conn = sqlite3.connect('miraj.db')
    link = conn.execute('SELECT * FROM links WHERE id = ?', (id,)).fetchone()
    if link:
        ua = request.headers.get('User-Agent', 'Unknown')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        conn.execute('INSERT INTO tracks VALUES (?, ?, ?, ?, ?, ?)', 
                     (link[1], platform, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                      ua[:30], "Mobile" if "Mobile" in ua else "Desktop", ip))
        conn.commit()
        conn.close()
        return redirect(link[2])
    return "Link Expired", 404

@app.route('/export')
def export():
    conn = sqlite3.connect('miraj.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks")
    rows = cursor.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Platform', 'Date&Time', 'Browser', 'Device', 'IP Address'])
    writer.writerows(rows)
    return Response(output.getvalue(), mimetype='text/csv', 
                    headers={"Content-disposition": "attachment; filename=miraj_report.csv"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
