import sqlite3

with sqlite3.connect('test_db') as conn:
    cursor = conn.cursor()
    cursor.execute('create table if not exists test(id int primary key, name varchar, phone varchar )')
    cursor.execute('create table if not exists test_2(id int primary key, user_id int, phone varchar, foreign key(user_id) references test(id))')

    # cursor.execute('insert into test(id,name, phone) values(1, "roman", 123)')
    # cursor.execute('insert into test(id,name, phone) values(2, "vlad", 544)')
    # cursor.execute('insert into test(id,name, phone) values(3, "alex", 555)')
    # cursor.execute('insert into test_2(id, user_id, phone) values(1, 1, 90)')
    # cursor.execute('insert into test_2(id, user_id, phone) values(2, 3, 100)')
    # cursor.execute('insert into test_2(id, user_id, phone) values(3, 2, 200)')
    conn.commit()

    # for i in conn.execute('select t.name, tt.phone from test t join test_2 tt on t.id=tt.user_id'):
    #     print(i)
    #
    # cursor.execute('update test_2 set phone=900 where id=3')
    # conn.commit()
    #
    # for i in conn.execute('select t.name, tt.phone from test t join test_2 tt on t.id=tt.user_id'):
    #     print(i)

    cursor.execute('delete from test_2 where id=1')
    conn.commit()
    for i in cursor.execute('select * from test t join test_2 tt'):
        print(i)