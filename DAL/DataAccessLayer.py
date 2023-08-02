import sqlite3


def create_database(db_name):
    # Create a connection to the database
    conn = sqlite3.connect(db_name)
    print(f"Connected to database: {db_name}")
    return conn


def create_table(conn):
    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # SQL query to create a new table
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS sample_table (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER
    )
    '''

    # Execute the SQL query to create the table
    cursor.execute(create_table_query)
    print("Table 'sample_table' created successfully")

    # Commit the changes to the database
    conn.commit()


def insert_row(conn, name, age):
    cursor = conn.cursor()

    insert_row_query = '''
    INSERT INTO sample_table (name, age) VALUES (?, ?)
    '''
    cursor.execute(insert_row_query, (name, age))
    conn.commit()


if __name__ == "__main__":
    db_name = "sample.db"

    # Create a new SQLite database
    connection = create_database(db_name)

    # Create a new table in the database
    create_table(connection)

    # Insert a new row into the table
    name = "John Doe"
    age = 30
    insert_row(connection, name, age)

    # Close the database connection
    connection.close()
