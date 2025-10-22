import telebot
from telebot import types
import random
from config import BOT_TOKEN, MESSAGES
from database import Database

# Инициализация бота и базы данных
bot = telebot.TeleBot(BOT_TOKEN)
db = Database()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Добавляем пользователя в базу
    db.add_user(user_id, username, first_name)

    # Отправляем приветственное сообщение
    bot.send_message(
        message.chat.id,
        MESSAGES['start'],
        reply_markup=create_main_keyboard()
    )


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        MESSAGES['help'],
        reply_markup=create_main_keyboard()
    )


# Обработчик команды /new_habit
# Опросник в виде кнопок, сколько денег
@bot.message_handler(commands=['new_habit'])
def new_habit_command(message):
    msg = bot.send_message(
        message.chat.id,
        "🎯 Какую вредную привычку ты хочешь победить?\n\nНапример: 'курение', 'грызть ногти', 'прокрастинация'"
    )
    bot.register_next_step_handler(msg, process_habit_name)


def process_habit_name(message):
    habit_name = message.text.strip()
    user_id = message.from_user.id

    if habit_name:
        # Создаем новую привычку
        if db.create_habit(user_id, habit_name):
            bot.send_message(
                message.chat.id,
                MESSAGES['habit_created'].format(habit_name),
                reply_markup=create_main_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при создании привычки. Попробуй еще раз."
            )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Название привычки не может быть пустым. Попробуй еще раз с помощью /new_habit"
        )


# Обработчик команды /success
@bot.message_handler(commands=['success'])
def success_command(message):
    user_id = message.from_user.id

    # Проверяем, есть ли у пользователя привычка
    habit = db.get_user_habit(user_id)
    if not habit:
        bot.send_message(message.chat.id, MESSAGES['no_habit'])
        return

    # Записываем успешный день
    new_streak = db.record_success(user_id)

    if new_streak:
        # Выбираем случайную мотивационную фразу
        motivation = random.choice(MESSAGES['motivation'])

        bot.send_message(
            message.chat.id,
            f"{MESSAGES['success'].format(new_streak)}\n\n{motivation}"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при записи результата."
        )


# Обработчик команды /break
@bot.message_handler(commands=['break'])
def break_command(message):
    user_id = message.from_user.id

    # Проверяем, есть ли у пользователя привычка
    habit = db.get_user_habit(user_id)
    if not habit:
        bot.send_message(message.chat.id, MESSAGES['no_habit'])
        return

    # Записываем срыв
    if db.record_break(user_id):
        bot.send_message(
            message.chat.id,
            MESSAGES['break']
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при записи результата."
        )


# Обработчик команды /stats
@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id

    # Получаем статистику
    stats = db.get_user_stats(user_id)
    if not stats:
        bot.send_message(message.chat.id, MESSAGES['no_habit'])
        return

    # Формируем сообщение со статистикой
    stats_message = f"""
📊 Твоя статистика по привычке: *{stats['habit_name']}*

✅ Текущая серия: *{stats['current_streak']} дней*
🏆 Самая длинная серия: *{stats['longest_streak']} дней*
📅 Всего успешных дней: *{stats['total_days']}*
😔 Дней со срывом: *{stats['break_days']}*
📈 Успешность: *{stats['success_rate']}%*

Продолжай в том же духе! 💫
    """

    bot.send_message(
        message.chat.id,
        stats_message,
        parse_mode='Markdown'
    )


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.lower() in ['привет', 'hello', 'start']:
        start_command(message)
    else:
        bot.send_message(
            message.chat.id,
            "🤔 Я не понял твое сообщение. Используй команды из меню или /help"
        )


def create_main_keyboard():
    """Создание основной клавиатуры"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('/success ✅'))
    keyboard.add(types.KeyboardButton('/break 😔'))
    keyboard.add(types.KeyboardButton('/stats 📊'))
    keyboard.add(types.KeyboardButton('/help ❓'))
    return keyboard


# Запуск бота
if __name__ == "__main__":
    print("Бот HabitBreaker AI запущен...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        db.close()

