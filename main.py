import cmath
import telebot
import os
import wolframalpha
import re
from decimal import Decimal, getcontext, InvalidOperation


TOKEN = ""
APP_ID = ""
bot = telebot.TeleBot(TOKEN)

feedback_data = {}
user_language = {}
user_state = {}


def load_language(language_code):
    lang_file_path = f'./lang/{language_code}.txt'
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


def wolfram_calc(question, chat_id):
    client = wolframalpha.Client(APP_ID)
    try:
        res = client.query(f"simplified abs square root of {question}")

        result = next(res.results, None)

        if result is None:
            return get_translation(chat_id, "error_wolfram")

        answer = result.text

        if 'sqrt' in answer and 'abs' in answer:
            answer = answer.replace('abs', '1', 1)
            answer = answer.replace('sqrt', '2', 1)
            answer = answer.replace('1', 'sqrt', 1)
            answer = answer.replace('2', 'abs', 1)

        if 'abs' in answer:
            answer = answer.replace('abs', '+-', 1)

        return answer

    except Exception as e:
        return get_translation(chat_id, "error_wolfram")


def create_back_markup(options, user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button_text = get_translation(user_id, 'back_button')
    markup.row(*options)
    markup.row(back_button_text)
    return markup


def create_back_only_markup(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button_text = get_translation(user_id, 'only_back_button')
    markup.row(back_button_text)
    return markup


def send_main_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Русский', 'English', 'Español','汉语')
    bot.send_message(message.chat.id, "Выберите язык:", reply_markup=markup)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_main_menu(message)


@bot.message_handler(func=lambda message: message.text in ['Русский', 'English', 'Español','汉语'])
def handle_language_choice(message):
    if message.text == 'Русский':
        user_language[message.chat.id] = 'ru'
    elif message.text == 'English':
        user_language[message.chat.id] = 'en'
    elif message.text == 'Español':
        user_language[message.chat.id] = 'es'
    elif message.text == '汉语':
        user_language[message.chat.id] = 'ch'

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
    bot.send_message(message.chat.id, get_translation(message.chat.id, "analytic_instructions"), reply_markup=markup)
    bot.register_next_step_handler(message, process_analytical)


def process_arithmetic(message):
    if message.text == get_translation(message.chat.id, 'only_back_button'):
        handle_back(message)
        return

    try:
        input_data = message.text.split(",")

        if len(input_data) != 2:
            error_message = get_translation(message.chat.id, "arithmetic_input_format_error")
            bot.send_message(message.chat.id, error_message)
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return

        num_str, accuracy_str = map(str.strip, input_data)

        if num_str == "0":
            bot.send_message(message.chat.id, get_translation(message.chat.id, "zero_root_result"))
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return

        num = Decimal(num_str)
        accuracy = int(accuracy_str)

        if accuracy > 1000:
            accuracy = 1000
            bot.send_message(message.chat.id, get_translation(message.chat.id, "max_accuracy_warning"))

        if accuracy < 0 or not accuracy_str.isdigit():
            error_message = get_translation(message.chat.id, "error_negative_accuracy").format(input_value=accuracy_str)
            bot.send_message(message.chat.id, error_message)
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return


        if num < 0:
            error_message = get_translation(message.chat.id, "error_negative_root").format(input_value=num_str)
            bot.send_message(message.chat.id, error_message)
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_arithmetic)
            return

        sqrt_result = sqrt_with_accuracy(num, accuracy, message.chat.id)
        bot.send_message(message.chat.id,
                         get_translation(message.chat.id, "arithmetic_root_result").format(num=num, result=sqrt_result))

        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_arithmetic)

    except InvalidOperation:
        error_message = get_translation(message.chat.id, "error_string_input").format(input_value=message.text)
        bot.send_message(message.chat.id, error_message)
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_arithmetic)

    except ValueError as ve:
        error_message = get_translation(message.chat.id, "error_string_input").format(input_value=message.text)
        bot.send_message(message.chat.id, error_message)
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_arithmetic)

    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        bot.send_message(message.chat.id, error_message)
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "arithmetic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_arithmetic)


def process_complex(message):
    if message.text == get_translation(message.chat.id, 'only_back_button'):
        handle_back(message)
        return

    try:
        if ',' not in message.text or message.text.count(',') != 2:
            error_message = get_translation(message.chat.id, "complex_input_format_error")
            bot.send_message(message.chat.id, error_message)
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_complex)
            return

        real_str, imaginary_str, decimal_places_str = map(str.strip, message.text.split(","))

        real_part = float(real_str)
        imaginary_part = float(imaginary_str)
        decimal_places = int(decimal_places_str)

        if decimal_places > 1000:
            decimal_places = 1000
            bot.send_message(message.chat.id, get_translation(message.chat.id, "max_accuracy_warning"))

        if decimal_places < 0 or not decimal_places_str.isdigit():
            error_message = get_translation(message.chat.id, "error_negative_accuracy").format(input_value=decimal_places_str)
            bot.send_message(message.chat.id, error_message)
            markup = create_back_only_markup(message.chat.id)
            bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                             reply_markup=markup)
            bot.register_next_step_handler(message, process_complex)
            return

        complex_number = complex(real_part, imaginary_part)
        result = sqrt_of_complex(real_part, imaginary_part, decimal_places)
        bot.send_message(message.chat.id,
                         get_translation(message.chat.id, "complex_root_result").format(complex_number=complex_number, result=result))

        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_complex)

    except ValueError:
        error_message = get_translation(message.chat.id, "error_string_input").format(input_value=message.text)
        bot.send_message(message.chat.id, error_message)
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_complex)

    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        bot.send_message(message.chat.id, error_message)
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "complex_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_complex)


def process_analytical(message):
    if message.text == get_translation(message.chat.id, 'only_back_button'):
        handle_back(message)
        return

    try:
        question = message.text
        if ',' in question:
            question, decimal_places_str = question.split(',')
            if '.' in decimal_places_str:
                bot.send_message(message.chat.id, get_translation(message.chat.id, "error_fractional_accuracy"))
                markup = create_back_only_markup(message.chat.id)
                bot.send_message(message.chat.id, get_translation(message.chat.id, "analytic_instructions"),
                                 reply_markup=markup)
                bot.register_next_step_handler(message, process_analytical)
                return
            decimal_places = int(decimal_places_str)
            if decimal_places < 0:
                bot.send_message(message.chat.id, get_translation(message.chat.id, "error_negative_accuracy"))
                markup = create_back_only_markup(message.chat.id)
                bot.send_message(message.chat.id, get_translation(message.chat.id, "analytic_instructions"),
                                 reply_markup=markup)
                bot.register_next_step_handler(message, process_analytical)
                return

        result = wolfram_calc(question, message.chat.id)

        if "пожалуйста, введите корректное выражение" in result.lower():
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное выражение.")
        else:
            bot.send_message(message.chat.id,
                             get_translation(message.chat.id, "analytic_root_result").format(number=question,
                                                                                            result=result))

        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "analytic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_analytical)

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное выражение.")
        markup = create_back_only_markup(message.chat.id)
        bot.send_message(message.chat.id, get_translation(message.chat.id, "analytic_instructions"),
                         reply_markup=markup)
        bot.register_next_step_handler(message, process_analytical)




def sqrt_with_accuracy(num: float, accuracy: int, chat_id: int) -> Decimal:
    if accuracy < 0:
        error_message = get_translation(chat_id, "error_negative_accuracy")
        raise ValueError(error_message)

    getcontext().prec = max(accuracy + 2, 1000)

    num_decimal = Decimal(num)
    guess = num_decimal / 2
    tolerance = Decimal('1e-' + str(accuracy))

    while abs(guess * guess - num_decimal) > tolerance:
        guess = (guess + num_decimal / guess) / 2

    if guess == 0:
        raise ValueError("")

    return guess.quantize(Decimal(10) ** -accuracy)


def sqrt_of_complex(real_part: Decimal, imaginary_part: Decimal, decimal_places: int) -> str:
    if decimal_places > 1000:
        decimal_places = 1000

    getcontext().prec = decimal_places + 5

    real_part_decimal = Decimal(real_part)
    imaginary_part_decimal = Decimal(imaginary_part)

    complex_number = complex(real_part_decimal, imaginary_part_decimal)

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