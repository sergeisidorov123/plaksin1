import cmath
import sympy
import telebot


TOKEN = '7240415310:AAGOoQe_ln15vU2icX_w574-4uEm2XuxTXI'

bot = telebot.TeleBot(TOKEN)


def sqrt_with_accuracy(num, accuracy):
    precision = 10**(-accuracy)
    low = 0
    high = num
    mid = (low + high) / 2

    while abs(mid**2 - num) > precision:
        if mid**2 < num:
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
    x = sympy.symbols('x')
    expression = sympy.sympify(expression_str)
    sqrt_result = sympy.sqrt(expression)
    simplified_result = sympy.simplify(sqrt_result)
    return simplified_result


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Арифметический корень', 'Комплексный корень', 'Аналитический корень')
    bot.send_message(message.chat.id, ".", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Арифметический корень', 'Комплексный корень', 'Аналитический корень'])
def handle_choice(message):
    if message.text == 'Арифметический корень':
        bot.send_message(message.chat.id, "Введите число и точность (через запятую, например 16, 4):")
        bot.register_next_step_handler(message, handle_arithmetic)
    elif message.text == 'Комплексный корень':
        bot.send_message(message.chat.id, "Введите действительную и мнимую части числа и количество знаков (например: 3, 4, 2):")
        bot.register_next_step_handler(message, handle_complex)
    elif message.text == 'Аналитический корень':
        bot.send_message(message.chat.id, "Введите аналитическое выражение (например: x**2 + 4*x + 4):")
        bot.register_next_step_handler(message, handle_analytical)


def handle_arithmetic(message):
    try:
        num, accuracy = map(float, message.text.split(","))
        result = sqrt_with_accuracy(num, int(accuracy))
        bot.send_message(message.chat.id, f"Арифметический квадратный корень: {result}")
    except:
        bot.send_message(message.chat.id, "Ошибка ввода. Пожалуйста, введите два числа через запятую.")


def handle_complex(message):
    try:
        real_part, imaginary_part, decimal_places = map(float, message.text.split(","))
        complex_number = complex(real_part, imaginary_part)
        result = sqrt_of_complex(complex_number, int(decimal_places))
        bot.send_message(message.chat.id, f"Комплексный квадратный корень: {result}")
    except:
        bot.send_message(message.chat.id, "Ошибка ввода. Пожалуйста, введите три числа через запятую.")


def handle_analytical(message):
    try:
        result = sqrt_of_analitics(message.text)
        bot.send_message(message.chat.id, f"Аналитический квадратный корень: {result}")
    except:
        bot.send_message(message.chat.id, "Ошибка при обработке аналитического выражения.")


if __name__ == '__main__':
    bot.polling()
