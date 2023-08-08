import os
import sqlite3
from datetime import datetime
from tools.order_block import OrderBlock
from tools.point import Point
from user_options import UserOption


class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = self.create_database()

    def create_database(self):
        is_exist = os.path.exists(self.db_name)
        connection = sqlite3.connect(self.db_name)

        if not is_exist:
            self.create_tables(connection)

        return connection

    def create_tables(self, conn):
        cursor = conn.cursor()

        create_point_table_query = '''
            CREATE TABLE IF NOT EXISTS Point (
                id INTEGER PRIMARY KEY,
                x DATETIME,
                y FLOAT
            )
        '''
        cursor.execute(create_point_table_query)

        create_orderblock_table_query = '''
            CREATE TABLE IF NOT EXISTS OrderBlock (
                id INTEGER PRIMARY KEY,
                buttonLeftPointId INTEGER,
                topRightPointId INTEGER,
                type TEXT,
                isTouched INTEGER,
                isFailed INTEGER,
                userDecision INTEGER,
                isValid INTEGER,
                FOREIGN KEY (buttonLeftPointId) REFERENCES Point(id),
                FOREIGN KEY (topRightPointId) REFERENCES Point(id)
            )
        '''
        cursor.execute(create_orderblock_table_query)
        conn.commit()

    def insert_order_block(self, order_block):
        cursor = self.connection.cursor()

        cursor.execute('SELECT id FROM OrderBlock WHERE id = ?', (order_block.id,))
        existing_order_block = cursor.fetchone()

        if existing_order_block:
            print("Order block with the same ID already exists in the database.")
            return

        cursor.execute('INSERT INTO Point (x, y) VALUES (?, ?)',
                       (order_block.bottom_left.datetime, order_block.bottom_left.price))
        bottom_left_point_id = cursor.lastrowid

        cursor.execute('INSERT INTO Point (x, y) VALUES (?, ?)',
                       (order_block.top_right.datetime, order_block.top_right.price))
        top_right_point_id = cursor.lastrowid

        order_block_type = "bullish" if order_block.is_bullish else "bearish"

        cursor.execute('''
            INSERT INTO OrderBlock (id, buttonLeftPointId, topRightPointId, type, isTouched, isFailed, userDecision, isValid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_block.id,
            bottom_left_point_id,
            top_right_point_id,
            order_block_type,
            int(order_block.is_touched),
            int(order_block.is_failed),
            0,
            1
        ))

        self.connection.commit()

    def convert_orderblocks_results_to_list(self, db_results):
        format_string = "%Y-%m-%d %H:%M:%S.%f"
        order_blocks = []

        for row in db_results:
            bottom_left = Point(date_time=datetime.strptime(row[6], format_string), price=row[7])
            top_right = Point(date_time=datetime.strptime(row[8], format_string), price=row[9])
            is_bullish = row[1] == 'bullish'
            is_touched = bool(row[2])
            is_failed = bool(row[3])
            user_decision = row[4]
            is_valid = bool(row[5])

            order_block = OrderBlock(bottom_left, top_right, is_bullish)
            order_block.is_touched = is_touched
            order_block.is_failed = is_failed
            order_block.user_decision = user_decision
            order_block.is_valid = is_valid
            order_blocks.append(order_block)

        return order_blocks

    def get_all_order_blocks(self):
        cursor = self.connection.cursor()

        query = '''
            SELECT ob.id, 
                   ob.type, 
                   ob.isTouched, 
                   ob.isFailed, 
                   ob.userDecision, 
                   ob.isValid, 
                   p1.x AS bottom_left_x, 
                   p1.y AS bottom_left_y, 
                   p2.x AS top_right_x, 
                   p2.y AS top_right_y
            FROM OrderBlock AS ob
            JOIN Point AS p1 ON ob.buttonLeftPointId = p1.id
            JOIN Point AS p2 ON ob.topRightPointId = p2.id
        '''

        cursor.execute(query)
        db_results = cursor.fetchall()
        return self.convert_orderblocks_results_to_list(db_results)

    def get_all_valid_order_blocks(self):
        cursor = self.connection.cursor()

        query = '''
            SELECT ob.id, 
                   ob.type, 
                   ob.isTouched, 
                   ob.isFailed, 
                   ob.userDecision, 
                   ob.isValid, 
                   p1.x AS bottom_left_x, 
                   p1.y AS bottom_left_y, 
                   p2.x AS top_right_x, 
                   p2.y AS top_right_y
            FROM OrderBlock AS ob
            JOIN Point AS p1 ON ob.buttonLeftPointId = p1.id
            JOIN Point AS p2 ON ob.topRightPointId = p2.id
            WHERE ob.isValid = 1
        '''

        cursor.execute(query)
        db_results = cursor.fetchall()
        return self.convert_orderblocks_results_to_list(db_results)

    def get_all_order_blocks_by_user_decision(self, user_option):
        cursor = self.connection.cursor()

        query = f'''
            SELECT ob.id, 
                   ob.type, 
                   ob.isTouched, 
                   ob.isFailed, 
                   ob.userDecision, 
                   ob.isValid, 
                   p1.x AS bottom_left_x, 
                   p1.y AS bottom_left_y, 
                   p2.x AS top_right_x, 
                   p2.y AS top_right_y
            FROM OrderBlock AS ob
            JOIN Point AS p1 ON ob.buttonLeftPointId = p1.id
            JOIN Point AS p2 ON ob.topRightPointId = p2.id
            WHERE ob.userDecision = {user_option.value}
        '''

        cursor.execute(query)
        db_results = cursor.fetchall()
        return self.convert_orderblocks_results_to_list(db_results)

    def close_connection(self):
        self.connection.close()


# if __name__ == "__main__":
#     db_manager = DatabaseManager("my_database.db")
#
#     # Create OrderBlock instance and insert into database
#     date_string = "8.8.2023 12:42:01.956"
#     format_string = "%d.%m.%Y %H:%M:%S.%f"
#     dt_object = datetime.strptime(date_string, format_string)
#
#     bottom_left = Point(dt_object, 5)
#     top_right = Point(dt_object, 7)
#     order_block = OrderBlock(bottom_left, top_right, True)
#
#     db_manager.insert_order_block(order_block)
#
#     # Retrieve order blocks from the database
#     order_blocks = db_manager.get_all_order_blocks()
#     valid_order_blocks = db_manager.get_all_valid_order_blocks()
#     user_option = UserOption.NONE
#     user_decision_order_blocks = db_manager.get_all_order_blocks_by_user_decision(user_option)
#
#     # Close the database connection when done
#     db_manager.close_connection()