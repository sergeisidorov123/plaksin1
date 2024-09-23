import cmath
import telebot
import os
import wolframalpha
import re
from decimal import Decimal, getcontext


TOKEN = ''
APP_ID = ""
bot = telebot.TeleBot(TOKEN)

feedback_data = {}
user_language = {}
user_state = {}


def wolfram_calc(question):
    client = wolframalpha.Client(APP_ID)
    res = client.query(f"simplified square root of {question}")
    answer = next(res.results).text
    return answer


def load_language(language_code):
    lang_file_path = f'C:/Users/111/Documents/GitHub/plaksin1/lang/{language_code}.txt'
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        lang_dict = {}
        for line in lines:
            key, value = line.strip().split('=')
            lang_dict[key] = value
        return lang_dict
    else:
        return None


def get_translation(user_id, key):
    language_code = user_language.get(user_id, 'ru')
    translations = load_language(language_code)
    if translations and key in translations:
        return translations[key]
    return None


def create_back_markup(options, user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button_text = get_translation(user_id, 'back_button')
    markup.row(*options)
    markup.row(back_button_text)
    return markup


def create_back_only_markup(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button_text = get_translation(user_id, 'back_button')
    markup.row(back_button_text)
    return markup


def send_main_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Русский', 'English', 'Español')
    bot.send_message(message.chat.id, "Выберите язык:", reply_markup=markup)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_main_menu(message)


@bot.message_handler(func=lambda message: message.text in ['Русский', 'English', 'Español'])
def handle_language_choice(message):
    if message.text == 'Русский':
        user_language[message.chat.id] = 'ru'
    elif message.text == 'English':
        user_language[message.chat.id] = 'en'
    elif message.text == 'Español':
        user_language[message.chat.id] = 'es'

    user_state[message.chat.id] = 'main_menu'

    welcome_text = get_translation(message.chat.id, 'welcome')
    markup = create_back_markup([
        get_translation(message.chat.id, 'arithmetic'),
        get_translation(message.chat.id, 'complex'),
        get_translation(message.chat.id, 'analytic')
    ], message.chat.id)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'back_button'))
def handle_back(message):
    state = user_state.get(message.chat.id)

    if state in ['arithmetic', 'complex', 'analytic']:
        markup = create_back_markup([
            get_translation(message.chat.id, 'arithmetic'),
            get_translation(message.chat.id, 'complex'),
            get_translation(message.chat.id, 'analytic')
        ], message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "choose_expression_type"),
                         reply_markup=markup)

        user_state[message.chat.id] = 'main_menu'

    elif state == 'main_menu':
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "unexpected_error"))


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'arithmetic'))
def handle_arithmetic_command(message):
    user_state[message.chat.id] = 'arithmetic'
    markup = create_back_only_markup(message.chat.id)
    bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"), reply_markup=markup)
    bot.register_next_step_handler(message, process_arithmetic)


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'complex'))
def handle_complex_command(message):
    user_state[message.chat.id] = 'complex'
    markup = create_back_only_markup(message.chat.id)
    bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"), reply_markup=markup)
    bot.register_next_step_handler(message, process_complex)


@bot.message_handler(func=lambda message: message.text == get_translation(message.chat.id, 'analytic'))
def handle_analytic_command(message):
    user_state[message.chat.id] = 'analytic'
    markup = create_back_only_markup(message.chat.id)
    bot.send_message(message.chat.id, get_translation(message.chat.id, "enter_expression"), reply_markup=markup)
    bot.register_next_step_handler(message, process_analytical)


def process_arithmetic(message):
    if message.text == get_translation(message.chat.id, 'back_button'):
        handle_back(message)
        return

    try:
        num_str, accuracy_str = message.text.split(",")
        num = float(num_str)
        accuracy = float(accuracy_str)

        if '.' in accuracy_str:
            bot.send_message(message.chat.id, get_translation(message.chat.id, "error_fractional_accuracy"))
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return

        if accuracy < 0:
            error_message = get_translation(message.chat.id, "error_negative_accuracy").format(input_value=accuracy_str)
            bot.send_message(message.chat.id, error_message)
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return

        if num == 0:
            bot.send_message(message.chat.id, "Корень из 0: 0")
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return

        if num < 0:
            bot.send_message(message.chat.id, get_translation(message.chat.id, "error_negative_root"))
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"))
            bot.register_next_step_handler(message, process_arithmetic)
            return

        sqrt_result = sqrt_with_accuracy(num, int(accuracy))
        bot.send_message(message.chat.id, f"+{sqrt_result}, -{sqrt_result}")

        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_arithmetic)

    except ValueError:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_string_input"))
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_arithmetic)


def process_complex(message):
    if message.text == get_translation(message.chat.id, 'back_button'):
        handle_back(message)
        return

    try:
        real_part_str, imaginary_part_str, decimal_places_str = message.text.split(",")

        real_part_str = real_part_str.strip()
        imaginary_part_str = imaginary_part_str.strip()
        decimal_places_str = decimal_places_str.strip()

        if '.' in decimal_places_str:
            bot.send_message(message.chat.id, get_translation(message.chat.id, "error_fractional_accuracy"))
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_complex)
            return

        real_part = float(real_part_str)
        imaginary_part = float(imaginary_part_str)

        try:
            decimal_places = int(decimal_places_str)
        except ValueError:
            bot.send_message(message.chat.id, f"Ошибка. Точность НЕ записана. Ваш ввод: '{decimal_places_str}'. Введите целое, положительное число, чтобы ввести точность вычислений.")
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_complex)
            return

        if decimal_places < 0:
            bot.send_message(message.chat.id, f"Ошибка. Точность НЕ записана. Ваш ввод: {decimal_places}. Введите целое, положительное число, чтобы ввести точность вычислений.")
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_complex)
            return

        result = sqrt_of_complex(real_part, imaginary_part, decimal_places)

        bot.send_message(message.chat.id, f"{result}")

        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_complex)

    except ValueError:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_string_input"))
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_complex)



def process_analytical(message):
    if message.text == get_translation(message.chat.id, 'back_button'):
        handle_back(message)
        return

    try:
        question = message.text
        if ',' in question:
            question, decimal_places_str = question.split(',')
            if '.' in decimal_places_str:
                bot.send_message(message.chat.id, get_translation(message.chat.id, "error_fractional_accuracy"))
                markup = create_back_only_markup(message.chat.id)
                bot.send_message(message.chat.id, get_translation(message.chat.id, "enter_expression"),
                                 reply_markup=markup)
                bot.register_next_step_handler(message, process_analytical)
                return
            decimal_places = int(decimal_places_str)
            if decimal_places < 0:
                bot.send_message(message.chat.id, get_translation(message.chat.id, "error_negative_accuracy"))
                markup = create_back_only_markup(message.chat.id)
                bot.send_message(message.chat.id, get_translation(message.chat.id, "enter_expression"),
                                 reply_markup=markup)
                bot.register_next_step_handler(message, process_analytical)
                return

        result = wolfram_calc(question)
        bot.send_message(message.chat.id, f"{result}")

        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "enter_expression"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_analytical)

    except ValueError:
        bot.send_message(message.chat.id, get_translation(message.chat.id, "error_string_input"))
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "enter_expression"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_analytical)


def sqrt_with_accuracy(num: float, accuracy: int, chat_id: int) -> Decimal:
    if accuracy < 0:
        error_message = get_translation(chat_id, "error_negative_accuracy")
        if not error_message:
            error_message = "Точность не может быть отрицательной"
        raise ValueError(error_message)

    getcontext().prec = accuracy + 2

    num_decimal = Decimal(num)
    guess = num_decimal / 2
    tolerance = Decimal('1e-' + str(accuracy))

    while abs(guess * guess - num_decimal) > tolerance:
        guess = (guess + num_decimal / guess) / 2

    return guess.quantize(Decimal(10) ** -accuracy)



def sqrt_of_complex(real_part: Decimal, imaginary_part: Decimal, decimal_places: int) -> str:
    complex_number = complex(float(real_part), float(imaginary_part))

    sqrt_result = cmath.sqrt(complex_number)

    real_decimal = Decimal(sqrt_result.real).quantize(Decimal(10) ** -decimal_places)
    imaginary_decimal = Decimal(sqrt_result.imag).quantize(Decimal(10) ** -decimal_places)

    return f"{real_decimal} + {imaginary_decimal}i" if imaginary_decimal >= 0 else f"{real_decimal} - {abs(imaginary_decimal)}i"


def save_feedback_to_file(user_id):
    feedback = feedback_data.get(user_id)

    if feedback:
        file_path = 'feedback_data.txt'

        feedback_text = f"Имя: {feedback['name']}\nEmail: {feedback['email']}\nСообщение: {feedback['message']}\n{'-' * 40}\n"

        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(feedback_text)

        del feedback_data[user_id]


@bot.message_handler(commands=['feedback'])
def start_feedback(message):
    bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя:")
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    feedback_data[message.chat.id] = {'name': message.text}
    bot.send_message(message.chat.id, "Теперь введите ваш email:")
    bot.register_next_step_handler(message, get_email)


def get_email(message):
    email = message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        bot.send_message(message.chat.id, "Некорректный email. Пожалуйста, попробуйте снова.")
        bot.register_next_step_handler(message, get_email)
    else:
        feedback_data[message.chat.id]['email'] = email
        bot.send_message(message.chat.id, "Теперь введите ваше сообщение:")
        bot.register_next_step_handler(message, get_message)


def get_message(message):
    feedback_data[message.chat.id]['message'] = message.text
    bot.send_message(message.chat.id, "Спасибо за ваше сообщение! Мы скоро свяжемся с вами.")

    save_feedback_to_file(message.chat.id)


if __name__ == '__main__':
    bot.polling()
