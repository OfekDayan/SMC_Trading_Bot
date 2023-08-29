import os
import sqlite3
import pandas as pd

from tools.order_block import OrderBlock, OrderBlockStatus
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
                status INTEGER,
                userDecision INTEGER,
                pollId INTEGER,
                nintyPercentFiboPrice FLOAT,
                symbol TEXT,
                FOREIGN KEY (buttonLeftPointId) REFERENCES Point(id),
                FOREIGN KEY (topRightPointId) REFERENCES Point(id)
            )
        '''
        cursor.execute(create_orderblock_table_query)
        conn.commit()

    def insert_order_block(self, order_block: OrderBlock, poll_id):
        cursor = self.connection.cursor()

        cursor.execute('SELECT id FROM OrderBlock WHERE id = ?', (order_block.id,))
        existing_order_block = cursor.fetchone()

        if existing_order_block:
            return

        cursor.execute('INSERT INTO Point (x, y) VALUES (?, ?)',
                       (order_block.bottom_left.datetime.to_pydatetime(), order_block.bottom_left.price))
        bottom_left_point_id = cursor.lastrowid

        # if order_block.is_failed or order_block.is_touched:
        cursor.execute('INSERT INTO Point (x, y) VALUES (?, ?)',
                       (order_block.top_right.datetime.to_pydatetime(), order_block.top_right.price))
        top_right_point_id = cursor.lastrowid

        order_block_type = "bullish" if order_block.is_bullish else "bearish"

        cursor.execute('''
            INSERT INTO OrderBlock (id, buttonLeftPointId, topRightPointId, type, status, userDecision, pollId, nintyPercentFiboPrice, symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_block.id,
            bottom_left_point_id,
            top_right_point_id,
            order_block_type,
            order_block.order_block_status.value,
            0, # userDecision
            poll_id,
            order_block.ninty_percent_fibo_price,
            order_block.symbol
        ))

        self.connection.commit()


    def convert_orderblocks_results_to_list(self, db_results):
        order_blocks = []

        for row in db_results:
            # Convert bottom_left_x
            bottom_left_x_as_timestamp = pd.Timestamp(row[6])
            bottom_left = Point(date_time=bottom_left_x_as_timestamp, price=row[7])

            # Convert bottom_left_x
            top_right_x_as_timestamp = pd.Timestamp(row[8])
            top_right = Point(date_time=top_right_x_as_timestamp, price=row[9])

            symbol = row[5]

            order_block = OrderBlock(bottom_left, top_right, symbol, row[1] == 'bullish')
            order_block.order_block_status = row[2]
            order_block.user_decision = row[3]
            order_block.ninty_percent_fibo_price = row[4]
            order_blocks.append(order_block)

        return order_blocks

    def get_all_order_blocks(self, symbol: str):
        cursor = self.connection.cursor()

        query = f'''
            SELECT ob.id, 
                   ob.type, 
                   ob.status, 
                   ob.userDecision, 
                   ob.nintyPercentFiboPrice,
                   ob.symbol,
                   p1.x AS bottom_left_x, 
                   p1.y AS bottom_left_y, 
                   p2.x AS top_right_x, 
                   p2.y AS top_right_y
            FROM OrderBlock AS ob
            JOIN Point AS p1 ON ob.buttonLeftPointId = p1.id
            JOIN Point AS p2 ON ob.topRightPointId = p2.id
            WHERE ob.symbol = {symbol}
        '''

        cursor.execute(query)
        db_results = cursor.fetchall()
        return self.convert_orderblocks_results_to_list(db_results)

    def get_active_order_blocks(self, symbol: str):
        cursor = self.connection.cursor()

        query = f''' 
            SELECT ob.id, 
            ob.type, 
            ob.status, 
            ob.userDecision, 
            ob.nintyPercentFiboPrice,
            ob.symbol,
            p1.x AS bottom_left_x, 
            p1.y AS bottom_left_y, 
            p2.x AS top_right_x, 
            p2.y AS top_right_y
            FROM OrderBlock AS ob
            JOIN Point AS p1 ON ob.buttonLeftPointId = p1.id
            JOIN Point AS p2 ON ob.topRightPointId = p2.id
            WHERE ob.symbol = "{symbol}" AND ob.status = {OrderBlockStatus.UNKNOWN.value} AND
            (ob.userDecision = {UserOption.NOTIFY_PRICE_HIT_ODB.value} OR ob.userDecision = {UserOption.NOTIFY_REVERSAL_CANDLE_FOUND.value})
        '''

        cursor.execute(query)
        db_results = cursor.fetchall()
        return self.convert_orderblocks_results_to_list(db_results)

    def get_order_block_by_poll_id(self, poll_id):
        cursor = self.connection.cursor()

        query = f'''
            SELECT ob.id, 
                   ob.type, 
                   ob.status, 
                   ob.userDecision, 
                   ob.nintyPercentFiboPrice,
                   ob.symbol,
                   p1.x AS bottom_left_x, 
                   p1.y AS bottom_left_y, 
                   p2.x AS top_right_x, 
                   p2.y AS top_right_y
            FROM OrderBlock AS ob
            JOIN Point AS p1 ON ob.buttonLeftPointId = p1.id
            JOIN Point AS p2 ON ob.topRightPointId = p2.id
            WHERE ob.pollId = {poll_id}
        '''

        cursor.execute(query)
        db_results = cursor.fetchall()
        return self.convert_orderblocks_results_to_list(db_results)[0]

    def update_status(self, order_block_id, status: OrderBlockStatus):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE OrderBlock SET status = ? WHERE id = ?", (status.value, order_block_id))
        self.connection.commit()

    def update_user_decision(self, order_block_id, user_option: UserOption):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE OrderBlock SET userDecision = ? WHERE id = ?", (user_option.value, order_block_id))
        self.connection.commit()

    def update_poll_id(self, order_block_id, poll_id):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE OrderBlock SET pollId = ? WHERE id = ?", (poll_id, order_block_id))
        self.connection.commit()

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