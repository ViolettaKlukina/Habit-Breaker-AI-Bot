import sqlite3
import datetime
from config import DATABASE_NAME


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица привычек
        # Сделать опросник (), сколько денег уходит,
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                habit_name TEXT,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                total_days INTEGER DEFAULT 0,
                break_days INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица ежедневных отчетов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT, -- 'success' или 'break'
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        self.conn.commit()

    def add_user(self, user_id, username, first_name):
        """Добавление нового пользователя"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def create_habit(self, user_id, habit_name):
        """Создание новой привычки"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO habits (user_id, habit_name)
                VALUES (?, ?)
            ''', (user_id, habit_name))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating habit: {e}")
            return False

    def get_user_habit(self, user_id):
        """Получение привычки пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM habits WHERE user_id = ? ORDER BY id DESC LIMIT 1
        ''', (user_id,))
        return cursor.fetchone()

    def record_success(self, user_id):
        """Запись успешного дня"""
        cursor = self.conn.cursor()
        try:
            # Получаем текущую привычку
            habit = self.get_user_habit(user_id)
            if not habit:
                return False

            habit_id = habit[0]
            current_streak = habit[4]
            longest_streak = habit[5]
            total_days = habit[6]

            # Обновляем статистику
            new_streak = current_streak + 1
            new_longest_streak = max(longest_streak, new_streak)
            new_total_days = total_days + 1

            cursor.execute('''
                UPDATE habits 
                SET current_streak = ?, longest_streak = ?, total_days = ?
                WHERE id = ?
            ''', (new_streak, new_longest_streak, new_total_days, habit_id))

            # Записываем в ежедневные отчеты
            cursor.execute('''
                INSERT INTO daily_reports (user_id, date, status)
                VALUES (?, CURRENT_TIMESTAMP, 'success')
            ''', (user_id,))

            self.conn.commit()
            return new_streak
        except Exception as e:
            print(f"Error recording success: {e}")
            return False

    def record_break(self, user_id):
        """Запись срыва"""
        cursor = self.conn.cursor()
        try:
            # Получаем текущую привычку
            habit = self.get_user_habit(user_id)
            if not habit:
                return False

            habit_id = habit[0]
            break_days = habit[7]

            # Обновляем статистику
            cursor.execute('''
                UPDATE habits 
                SET current_streak = 0, break_days = ?
                WHERE id = ?
            ''', (break_days + 1, habit_id))

            # Записываем в ежедневные отчеты
            cursor.execute('''
                INSERT INTO daily_reports (user_id, date, status)
                VALUES (?, CURRENT_TIMESTAMP, 'break')
            ''', (user_id,))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording break: {e}")
            return False

    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        habit = self.get_user_habit(user_id)
        if not habit:
            return None

        return {
            'habit_name': habit[2],
            'current_streak': habit[4],
            'longest_streak': habit[5],
            'total_days': habit[6],
            'break_days': habit[7],
            'success_rate': round((habit[6] / (habit[6] + habit[7])) * 100, 1) if (habit[6] + habit[7]) > 0 else 0
        }

    def close(self):
        """Закрытие соединения с базой данных"""
        self.conn.close()

