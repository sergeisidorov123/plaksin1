import cmath
import sympy
import telebot
import os

TOKEN = '7240415310:AAGOoQe_ln15vU2icX_w574-4uEm2XuxTXI'

bot = telebot.TeleBot(TOKEN)

user_language = {}


def load_language(language_code):
    lang_file_path = f'C:/Users/111/PycharmProjects/proektniiseminar1/lang/{language_code}.txt'
    print(f"Загрузка файла языка: {lang_file_path}")
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        lang_dict = {}
        for line in lines:
            key, value = line.strip().split('=')
            lang_dict[key] = value
        print(f"Загруженные строки: {lang_dict}")
        return lang_dict
    else:
        print(f"Файл языка не найден: {lang_file_path}")
        return None


def get_translation(user_id, key):
    language_code = user_language.get(user_id, 'ru')
    translations = load_language(language_code)
    if translations and key in translations:
        return translations[key]
    return None


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Русский', 'English', 'Español')
    bot.send_message(message.chat.id, "Выберите язык:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Русский', 'English', 'Español'])
def handle_language_choice(message):
    if message.text == 'Русский':
        user_language[message.chat.id] = 'ru'
    elif message.text == 'English':
        user_language[message.chat.id] = 'en'
    elif message.text == 'Español':
        user_language[message.chat.id] = 'es'

    welcome_text = get_translation(message.chat.id, 'welcome')
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(get_translation(message.chat.id, 'arithmetic'),
               get_translation(message.chat.id, 'complex'),
               get_translation(message.chat.id, 'analytic'))
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'arithmetic'))
def handle_arithmetic_command(message):
    bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"))
    bot.register_next_step_handler(message, process_arithmetic)


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'complex'))
def handle_complex_command(message):
    bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"))
    bot.register_next_step_handler(message, process_complex)


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'analytic'))
def handle_analytic_command(message):
    # Отправляем сообщение о вводе выражения для извлечения корня
    bot.send_message(message.chat.id, get_translation(message.chat.id, "enter_expression"))
    bot.register_next_step_handler(message, process_analytical)


def process_arithmetic(message):
    try:
        num, accuracy = map(float, message.text.split(","))
        if accuracy < 0:
            bot.send_message(message.chat.id, get_translation(message.chat.id, "error_accuracy"))
            return
        sqrt_result = sqrt_with_accuracy(num, int(accuracy))
        bot.send_message(message.chat.id, f"+{sqrt_result}, -{sqrt_result}")
    except ValueError:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_input"))
    except Exception as e:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_general") + str(e))


def process_complex(message):
    try:
        real_part, imaginary_part, decimal_places = map(float, message.text.split(","))
        complex_number = complex(real_part, imaginary_part)
        result = sqrt_of_complex(complex_number, int(decimal_places))
        bot.send_message(message.chat.id, f"{result}")
    except Exception as e:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_input") + str(e))


def process_analytical(message):
    try:
        result = sqrt_of_analitics(message.text)
        bot.send_message(message.chat.id, f"{result}")
    except Exception as e:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_analytical") + str(e))


def sqrt_with_accuracy(num, accuracy):
    if accuracy < 0:
        raise ValueError("Точность не может быть отрицательной")

    precision = 10 ** (-accuracy)
    low = 0
    high = num
    mid = (low + high) / 2

    while abs(mid ** 2 - num) > precision:
        if mid ** 2 < num:
            low = mid
        else:
            high = mid
        mid = (low + high) / 2

    return round(mid, accuracy)


def sqrt_of_complex(number, decimal_places):
    sqrt_result = cmath.sqrt(number)
    real_part = round(sqrt_result.real, decimal_places)
    imaginary_part = round(sqrt_result.imag, decimal_places)

    return complex(real_part, imaginary_part)


def sqrt_of_analitics(expression_str):
    expression = sympy.sympify(expression_str)
    sqrt_result = sympy.sqrt(expression)

    simplified_result = sympy.simplify(sqrt_result)

    return simplified_result


if __name__ == '__main__':
    bot.polling()