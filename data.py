import sqlite3

db_path = 'flipp.db'

# Connect to DB and return Conn and Cur objects
def connect_db(db_path):
    conn = sqlite3.connect(db_path)
    #convert tuples to dictionaries
    conn.row_factory = sqlite3.Row
    return (conn, conn.cursor())


#delete announcement through announcement id
def process_deleting_announcement(announcement_id):
    conn, cur = connect_db(db_path)
    query = 'DELETE FROM Announcement WHERE id=?'
    cur.execute(query, announcement_id)
    conn.commit()
    conn.close()