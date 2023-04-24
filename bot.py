import logging
import aiohttp
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.utils import executor


API_TOKEN = 'bot_token'
OPENWEATHER_API_KEY = 'openweather_token'
EXCHANGERATE_API_KEY = 'exchangerate_token'

#Настраиваем логгер, чтобы выводить сообщения с уровнем INFO
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def get_weather(city: str) -> str:
    '''
    Функция принимает название города и возвращает строку с информацией о температуре воздуха в этом городе. 
    Она использует модуль aiohttp для асинхронных HTTP запросов к API погоды. 
    Если запрос успешен и получен JSON объект, функция возвращает строку с температурой.
    Если город не найден, функция вернет сообщение об ошибке, а если что-то пошло не так, она вернет общее сообщение об ошибке.
    '''
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                temp = data['main']['temp']
                return f'Температура воздуха в городе {city} сейчас {temp}°C)'
            elif resp.status == 404:
                return f'Я не могу найти город {city}(\nПожалуйста, отправь мне город еще раз'
            else:
                return f'Ой... что-то пошло не так(\nПожалуйста, отправь мне город еще раз'
            

@dp.message_handler(lambda message: message.text == 'Узнать погоду')
async def get_city(message: types.Message):
    '''
    Функция @dp.message_handler обрабатывает сообщения от пользователя, которые содержат текст "Узнать погоду". 
    Она отправляет сообщение пользователю с просьбой ввести название города 
    и регистрирует следующий обработчик сообщений для сообщений от этого пользователя, который будет вызываться только для сообщений с названием города.
    '''
    await message.answer('Конечно!)\nВ каком городе ты хочешь узнать погоду?)')
    dp.register_message_handler(process_city, lambda message: message.chat.id == message.chat.id)


async def process_city(message: types.Message):
    '''
    Функция process_city получает название города от пользователя, 
    вызывает функцию get_weather для получения температуры в этом городе 
    и отправляет сообщение пользователю с температурой и вспомогательной клавиатурой. 
    '''
    city = message.text
    weather = await get_weather(city)
    await message.reply(weather, reply_markup=keyboard_markup)


async def convert_currency(from_currency: str, to_currency: str, amount: float) -> str:
    '''
    Данная функция конвертирует валюту. 
    Она принимает три аргумента: исходную валюту, конечную валюту и сумму для конвертации. 
    Внутри функции выполняется запрос на сайт, который предоставляет данные о курсах валют, 
    и если запрос успешен, то происходит поиск курса конечной валюты и вычисление результата. 
    Если конвертация не поддерживается или запрос не успешен, то возвращается соответствующее сообщение.
    '''
    async with aiohttp.ClientSession() as session:
        url = f'https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{from_currency}'
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if to_currency not in data['conversion_rates'].keys():
                    return f'Мне очень жаль, но конвертация из {from_currency} в {to_currency} не поддерживается('
            elif response.status == 404:
                return f'Мне очень жаль, но я не могу найти валюту {from_currency}(\nПожалуйста, попробуй ещё раз\nСписок валют, с которыми я могу провести операцию:\nRUB - рубли\nUSD - доллары\nKZT - тенге\nAED - дирхам'
            else:
                return f'Ой... что-то пошло не так(\nПожалуйста, попробуй ещё раз\nСписок валют, с которыми я могу провести операцию:\nRUB - рубли\nUSD - доллары\nKZT - тенге\nAED - дирхам'
            for currency, rate in data['conversion_rates'].items():
                if currency == to_currency:
                    result = amount * rate
                    break
            return f'{amount} {from_currency} это {round(result, 1)} {to_currency})'


@dp.message_handler(lambda message: message.text == 'Конвертировать валюту')
async def get_currency(message: types.Message):
    '''
    Функция отвечает за обработку сообщения с запросом на конвертацию валюты. 
    Она отправляет пользователю сообщение с инструкцией о том, как правильно отправить запрос, 
    а также вызывает функцию process_currency, которая будет обрабатывать следующее сообщение от пользователя.
    '''
    await message.reply('С радостью!)\nПришли мне, пожалуйста, код валюты, которую нужно конвертировать, и код валюты, в которую ты хочешь конвертировать, через пробел, а затем сумму для конвертации)\n\
В формате: <код валюты 1> <код валюты 2> <сумма>\nВот список валют, с которыми я могу провести операцию:\nRUB - рубли\nUSD - доллары\nKZT - тенге\nAED - дирхам')
    dp.register_message_handler(process_currency, lambda message: message.chat.id == message.chat.id)
 

async def process_currency(message: types.Message):
    '''
    Функция process_currency отвечает за обработку сообщения пользователя с запросом на конвертацию валюты. 
    Она получает коды валют и сумму, проверяет, что сообщение было отправлено в корректном формате и обрабатывает возможные ошибки, 
    такие как некорректная сумма для конвертации или неподдерживаемые коды валют. 
    Далее функция вызывает функцию convert_currency, которая получает курсы обмена валюты с помощью API, 
    конвертирует введенную сумму в соответствующую валюту и возвращает результат в сообщении пользователю.
    '''
    response = message.text
    values = response.split()
    if len(values) != 3:
        await message.reply('Ты отправил мне сообщение не в том формате(\nПожалуйста, отправь в формате: <код валюты 1> <код валюты 2> <сумма>, чтобы я тебя поняла)\nСписок валют, с которыми я могу провести операцию:\nRUB - рубли\nUSD - доллары\nKZT - тенге\nAED - дирхам')
        return
    from_currency = values[0].upper()
    to_currency = values[1].upper()
    amount = values[2]
    try:
        amount = float(amount)
    except ValueError:
        await message.reply('Упс, видимо ты некорректно ввёл сумму для конвертации)\nПожалуйста, попробуй ещё раз\nСписок валют, с которыми я могу провести операцию:\nRUB - рубли\nUSD - доллары\nKZT - тенге\nAED - дирхам')
        return
    convert = await convert_currency(from_currency, to_currency, amount)
    await message.reply(convert, reply_markup=keyboard_markup)


@dp.message_handler(lambda message: message.text == 'Милое животное')
async def send_random_animal(message: types.Message):
    '''
    Эта функция обрабатывает сообщение "Милое животное" и отправляет случайное фото красной панды из API some-random-api.ml. 
    Функция делает запрос на этот API, получает ссылку на фотографию красной панды и отправляет ее пользователю в качестве ответа на его сообщение. 
    Если возникает ошибка при отправке сообщения, функция логирует эту ошибку и отправляет пользователю сообщение о том, что возникла проблема, 
    и предлагает попробовать позже.
    '''
    try:
        response = requests.get('https://some-random-api.ml/img/red_panda', verify=False)
        response.raise_for_status()
        image_url = response.json()['link']
        await bot.send_photo(message.chat.id, image_url)
    except Exception as e:
        logging.error(f'Error while sending random animal: {e}')
        await message.reply('Ой... возникла кое-какая проблема(\nПопробуй, пожалуйста чуть позже', reply_markup=keyboard_markup)


@dp.message_handler(lambda message: message.text == 'Создать опрос')
async def get_data(message: types.Message):
    '''
    Функция обрабатывает сообщение от пользователя и запрашивает у пользователя вопрос с вариантами ответа для создания опроса. 
    После того, как пользователь отправит вопрос с ответами, функция переходит к обработке второй функции - process_poll.
    '''
    await message.reply('Конечно!)\nПришли мне, пожалуйста, вопрос с вариантами ответа через запятую\nВ формате: <вопрос>:<ответ1>,<ответ2>,<ответ3>...')
    dp.register_message_handler(process_poll, lambda message: message.chat.id == message.chat.id)


async def process_poll(message: types.Message):
    '''
    Функция обрабатывает вопрос с вариантами ответа, который отправил пользователь, и разбивает его на вопрос и варианты ответа. 
    Затем функция отправляет вопрос с вариантами ответа в виде опроса в чат и ожидает ответа пользователя.
    '''
    response = message.text
    values = response.split(':')
    if len(values) != 2:
        await message.reply('Ты отправил мне сообщение не в том формате(\nПожалуйста, отправь в формате: <вопрос> <ответ1>,<ответ2>,<ответ3>..., чтобы я тебя поняла)')
        return
    question = values[0]
    answers = values[1].split(',')
    await message.answer_poll(question=question,
                              options=answers,
                              type='quiz',
                              correct_option_id=1,
                              is_anonymous=False)


@dp.message_handler(lambda message: message.text == 'Отправь опрос в чат')
async def send_poll_to_channel_command_handler(message: types.Message):
    '''
    Функция обрабатывает сообщение от пользователя и запрашивает у пользователя логин канала, в который необходимо отправить опрос. 
    После того, как пользователь отправит логин канала, функция переходит к обработке второй функции - send_poll_to_channel_handler.
    '''
    await message.answer('Да, хорошо)\nВ какой канал ты хочешь отправить опрос?)\nПришли мне, пожалуйста, логин канала)')
    dp.register_message_handler(send_poll_to_channel_handler, lambda message: message.from_user.id == message.from_user.id)


async def send_poll_to_channel_handler(message: types.Message):
    '''
    Функция обрабатывает логин канала, в который необходимо отправить опрос. 
    Функция получает ID чата по логину канала и пересылает опрос в этот чат. 
    Если возникает ошибка, функция отправляет сообщение пользователю с информацией об ошибке.
    '''
    channel_name = message.text
    try:
        chat_id = await bot.get_chat(channel_name)
        await bot.forward_message(chat_id, message.chat.id, message.message_id)
    except Exception as e:
        await message.answer(f'Упс, произошла ошибка при отправке сообщения :c\n{e}')


@dp.poll_answer_handler()
async def poll_answer(poll_answer: types.PollAnswer):
    '''
    Функция обрабатывает ответы на опрос, который пользователи отправляют. 
    Функция получает ID пользователя, который отправил ответ, и ID опроса.
    '''
    answer_ids = poll_answer.option_ids
    user_id = poll_answer.user.id
    poll_id = poll_answer.poll_id


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    '''
    Данная функция является обработчиком команды /start. 
    При вызове данной команды пользователю отправляется приветственное сообщение с кнопками, 
    которые можно нажимать для получения определенных действий от бота. 
    Для создания кнопок используется объект ReplyKeyboardMarkup.
    '''
    global keyboard_markup
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_weather = types.KeyboardButton('Узнать погоду')
    button_currency = types.KeyboardButton('Конвертировать валюту')
    button_animal = types.KeyboardButton('Милое животное')
    button_polls = types.KeyboardButton('Создать опрос')
    keyboard_markup.add(button_weather, button_currency, button_animal, button_polls)
    await message.reply('Привет!)\nВыбери нужную тебе команду и я тебе помогу)', reply_markup=keyboard_markup)


if __name__ == '__main__':
    '''
    Запускаем цикл обработки входящих сообщений с помощью переданного объекта Dispatcher dp с параметром skip_updates=True, 
    который указывает, что нужно пропустить все сохраненные обновления, если были какие-либо проблемы при запуске бота
    '''
    executor.start_polling(dp, skip_updates=True)
