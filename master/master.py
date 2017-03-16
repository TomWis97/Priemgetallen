#!flask/bin/python
from flask import Flask, jsonify, request, abort
import configparser
import sqlite3
import time


###############################################################################
# Load config                                                                 #
###############################################################################
config = configparser.ConfigParser()
config.read('/data/config.ini')


###############################################################################
# Database and logic                                                          #
###############################################################################


def init_db():
    # Database layout:
    # Tasks
    #   id         = int
    #   startNum   = int
    #   startTime  = int (unix time)
    #   state      = int
    #                  1 = waiting for slave
    #                  2 = complete
    # Results
    #   id         = int
    #   result     = int
    conn = sqlite3.connect(config['master']['databasefile'])
    c = conn.cursor()
    # Attempt to clean up.
    c.execute('''DROP TABLE IF EXISTS tasks''')
    c.execute('''DROP TABLE IF EXISTS results''')
    c.execute('''CREATE TABLE tasks
                 (id int, startnum int, starttime int, state int)''')
    c.execute('''CREATE TABLE results (id int, result int)''')
    conn.commit()
    conn.close()


def get_work():
    conn = sqlite3.connect(config['master']['databasefile'])
    c = conn.cursor()
    # Check if there's any work waiting too long.
    # Define "too long" (300 sec = 5 min)
    tooLongTime = int(time.time()) - 300
    c.execute('''SELECT * FROM tasks WHERE state = 1 AND starttime < ?''',
              (tooLongTime, ))
    failedTasks = c.fetchall()
    if len(failedTasks) > 0:
        selectedTask = failedTasks[0]
        print("Failed task found. (#{}) Re-assigning id {}.".format(
            len(failedTasks), selectedTask[0]))
        c.execute('''UPDATE tasks SET starttime = ? WHERE id = ?''',
                  (int(time.time()), selectedTask[0]))
        conn.commit()
        return {
            'id': selectedTask[0],
            'startnum': selectedTask[0],
            'steps': int(config['master']['steps'])
        }
    else:
        # Create new task
        # Check if this is the first task.
        c.execute('''SELECT COUNT(id) FROM tasks''')
        if c.fetchone()[0] == 0:
            newStart = 0
            newId = 1
        else:
            c.execute('''SELECT MAX(startnum) FROM tasks''')
            newStart = c.fetchone()[0] + int(config['master']['steps'])
            c.execute('''SELECT MAX(id) FROM tasks''')
            newId = c.fetchone()[0] + 1
        c.execute('''INSERT INTO tasks (id, startnum, starttime, state) VALUES
                     (?, ?, ?, ?)''', (newId, newStart, int(time.time()), 1))
        conn.commit()
        return {
            'id': newId,
            'startnum': newStart,
            'steps': int(config['master']['steps'])
        }


def add_results(id, results):
    conn = sqlite3.connect(config['master']['databasefile'])
    c = conn.cursor()
    # Construct result list
    resultList = []
    for i in results:
        resultList.append((int(id), int(i)))
    # Insert all results in result table.
    c.executemany('''INSERT INTO results (id, result) VALUES (?, ?)''',
                  resultList)
    c.execute('''UPDATE tasks SET state = 2 WHERE id = ?''', (int(id), ))
    conn.commit()


def get_all_results():
    conn = sqlite3.connect(config['master']['databasefile'])
    c = conn.cursor()
    c.execute('''SELECT result FROM results''')
    resultList = []
    for i in c.fetchall():
        resultList.append(i[0])
    return resultList


def get_stats():
    conn = sqlite3.connect(config['master']['databasefile'])
    c = conn.cursor()
    c.execute('''SELECT * FROM tasks ORDER BY id DESC LIMIT 1''')
    lastjobdata = c.fetchone()
    lastjob = {'id': lastjobdata[0], 'startnum': lastjobdata[1]}
    return {'lastjob': lastjob, 'results': get_all_results()}

###############################################################################
# User Interface                                                              #
###############################################################################
def build_index():
    baseHtml = '''<!DOCTYPE html>
<html>
    <head>
        <title>Priemgetallen</title>
        <meta charset='UTF-8'>
    </head>
    <body>
        <h1>Priemgetallen</h1>
        <table>
            <tr><th>Last job</th><td>{lastjob}</td></tr>
            <tr><th>Amount of prime numbers found</th><td>{amount}</td></tr>
            <tr><th>All prime numbers found</th><td>{primetable}</td></tr>
        </table>
    </body>
</html>
    '''
    stats = get_stats()
    if config['master'].getboolean('disableprimelisttable'):
        primetable = '<i>Disabled in settings</i>'
    else:
        primetable = '<table><tr>'
        for i in stats['results']:
            primetable = primetable + '<td>{}</td>'.format(i)
            if i % 10 == 0:
                primetable = primetable + '</tr><tr>'
        primetable = primetable + '</tr></table>'
    return baseHtml.format(
        lastjob='ID: {id}, Start number: {startnum}'.format(
            id=stats['lastjob']['id'],
            startnum=stats['lastjob']['startnum']
            ),
        amount=len(stats['results']),
        primetable=primetable
    )

###############################################################################
# Flask                                                                       #
###############################################################################
app = Flask(__name__)


@app.route('/')
def index():
    return build_index()


@app.route('/api/init', methods=['GET'])
def init():
    init_db()
    return jsonify({'dbstate': 'ok'})


@app.route('/api/getjob', methods=['GET'])
def get_job():
    return jsonify(get_work())


@app.route('/api/results', methods=['POST'])
def post_results():
    if not request.json or 'id' not in request.json or 'data' not in request.json:
        print("Invalid request:", request.json)
        abort(400)
    try:
        add_results(request.json['id'], request.json['data'])
        return jsonify({'status': 'Ok', 'amount': len(request.json['data'])})
    except:
        return jsonify({'status': 'Error while saving results.'})


@app.route('/api/results', methods=['GET'])
def get_results():
    return jsonify(get_all_results())

###############################################################################
# Init code                                                                   #
###############################################################################
if __name__ == '__main__':
    app.run(debug=True)
