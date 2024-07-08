import sqlite3

conn = sqlite3.connect('../blackList.db')
cursor = conn.cursor()


cursor.execute("SELECT * FROM users")
result = cursor.fetchall()

for i in result:
    print(i)

conn.close()