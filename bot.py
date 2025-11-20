import telebot
from telebot import types
import math
import time
import random 
import string 
import traceback 
import requests 
import json 
import os 

# --- 1. КОНСТАНТЫ И ИНИЦИАЛИЗАЦИЯ ---

# ВАШ API ТОКЕН
API_TOKEN = '8104015290:AAFXc5RilQo8NerxjYfopkR5S-yhTQLLwZw' 
# !!! УСТАНАВЛИВАЕМ parse_mode ПО УМОЛЧАНИЮ КАК 'HTML' !!!
bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')

# ВАЖНО: СПИСОК АДМИНИСТРАТОРСКИХ ID (Telegram ID)
ADMIN_IDS = [
    8305624267,  
    1242288682,  
    7907584687,  
    8262824885   
]

# Словарь для хранения состояний пользователей
user_data = {} 
# Словарь для хранения следующего шага администратора
admin_next_step = {}

# Файлы для постоянного хранения данных
REVIEWS_FILE = 'reviews_data.json' 
PRODUCTS_FILE = 'products_data.json' 

# --- 2. БАЗЫ ДАННЫХ И КУРСЫ ---

# ИСХОДНЫЕ ДАННЫЕ КУРСОВ (будут обновляться динамически)
EXCHANGE_RATES = {
    # Фиат (Установлены безопасные значения по умолчанию)
    "USD_TO_UAH": 40.0,  
    "USD_TO_RUB": 90.0,  
    "USD_TO_BYN": 3.20,  
    "USD_TO_KZT": 450.0, 
    # Криптовалюты (Установлены безопасные значения по умолчанию)
    "BTC_TO_USD": 65000.0, 
    "TON_TO_USD": 2.50, 
    "TG_STAR_TO_USD": 0.007, 
}

# АДРЕСА API (Используются стандартные бесплатные сервисы)
FIAT_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,the-open-network&vs_currencies=usd" 


LAST_RATE_UPDATE = 0
RATE_UPDATE_INTERVAL = 300 

WALLETS = {
    "BTC": "bc1qrynsflx2jylk3dm8dtlen2vmh80l6r35yy0k2s",
    "TON": "UQAo4BLxDYOi5iIAzrjl_kobeWK0v1ZDPOumUa2mzMPM2X", 
}

LINKS = {
    "SUPPORT": "aleksandr_0941", 
    "CHANNEL": "@akkaoaja", 
    "CHANNEL_URL": "https://t.me/akkaoaja", 
    "WORK_CHANNEL": "https://t.me/+RSqQG9g1XCc2ZGEy" 
}

# Дефолтные товары, если файл не найден
DEFAULT_PRODUCT_DB = {
    1: {"name": "Пакет 'Старт'", "price_usd": 10.00, "description": "Начальный набор услуг."},
    2: {"name": "Пакет 'Премиум'", "price_usd": 50.50, "description": "Максимальный набор услуг."},
    3: {"name": "Пакет 'VIP'", "price_usd": 100.00, "description": "Эксклюзивное предложение."},
}
# Добавляем еще дефолтных товаров
for i in range(len(DEFAULT_PRODUCT_DB) + 1, 34):
    DEFAULT_PRODUCT_DB[i] = {"name": f"Товар №{i}", "price_usd": i * 1.5, "description": f"Стандартный товар {i}"}

# Глобальный словарь товаров - будет загружен из файла
PRODUCT_DB = {}


COUNTRY_CURRENCY = {
    "Украина": {"code": "UAH", "rate_key": "USD_TO_UAH", "symbol": "₴"},
    "Россия": {"code": "RUB", "rate_key": "USD_TO_RUB", "symbol": "₽"},
    "Беларусь": {"code": "BYN", "rate_key": "USD_TO_BYN", "symbol": "Br"},
    "Казахстан": {"code": "KZT", "rate_key": "USD_TO_KZT", "symbol": "₸"},
}

CITY_DB = {
    "Беларусь": [
        "Минск", "Гомель", "Могилёв", "Витебск", "Гродно", "Брест", "Бобруйск", 
        "Барановичи", "Борисов", "Пинск", "Орша", "Мозырь", "Солигорск", 
        "Новополоцк", "Лида", "Молодечно", "Жлобин", "Светлогорск", "Речица", 
        "Слуцк", "Жодино", "Слоним", "Кобрин", "Волковыск", "Калинковичи", 
        "Сморгонь", "Рогачёв", "Осиповичи", "Горки", "Новогрудок", "Полоцк",
        "Берёза", "Лунинец", "Ивацевичи", "Пружаны", "Столбцы", "Поставы", 
        "Глубокое", "Лепель", "Быхов", "Климовичи", "Кричев", "Дятлово", 
        "Микашевичи", "Мядель", "Чаусы", "Чериков", "Шклов", "Дзержинск"
    ],
    "Россия": [
        "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", 
        "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону", 
        "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград", "Краснодар", 
        "Саратов", "Тюмень", "Тольятти", "Ижевск", "Барнаул", "Иркутск", 
        "Ульяновск", "Хабаровск", "Владивосток", "Ярославль", "Махачкала", 
        "Томск", "Оренбург", "Кемерово", "Новокузнецк", "Рязань", "Набережные Челны", 
        "Астрахань", "Пенза", "Липецк", "Киров", "Чебоксары", "Калининград", 
        "Тула", "Курск", "Ставрополь", "Севастополь", "Сочи", "Белгород", 
        "Владимир", "Архангельск", "Чита", "Смоленск", "Курган", "Брянск",
        "Орёл", "Иваново", "Тверь", "Симферополь", "Нижний Тагил", "Грозный", 
        "Волжский", "Сургут", "Череповец", "Саранск", "Мурманск", "Вологда", 
        "Якутск", "Тамбов", "Кострома", "Новороссийск", "Стерлитамак", "Петрозаводск",
        "Таганрог", "Дзержинск", "Комсомольск-на-Амуре", "Нальчик", "Улан-Удэ",
        "Магнитогорск", "Сыктывкар", "Нижневартовск", "Норильск", "Балашиха", 
        "Химки", "Подольск", "Королёв", "Салават", "Йошкар-Ола", "Калуга", 
        "Владикавказ", "Абакан", "Петропавловск-Камчатский", "Бийск", "Псков",
        "Шахты", "Энгельс", "Балаково", "Рыбинск", "Сызрань", "Гатчина"
    ],
    "Украина": [
        "Киев", "Харьков", "Одесса", "Днепр", "Запорожье", "Львов", "Кривой Рог", 
        "Николаев", "Винница", "Чернигов", "Черкассы", "Житомир", "Сумы", 
        "Хмельницкий", "Ровно", "Ивано-Франковск", "Тернополь", "Луцк", 
        "Белая Церковь", "Кременчуг", "Каменское", "Кропивницкий", "Полтава", 
        "Херсон", "Черновцы", "Ужгород", "Мукачево", "Бровары", "Конотоп", 
        "Умань", "Измаил", "Ковель", "Калуш", "Шостка", "Бердянск", "Мелитополь", 
        "Краматорск", "Славянск", "Лисичанск", "Павлоград", "Северодонецк", 
        "Каменец-Подольский", "Александрия", "Нежин", "Прилуки", "Энергодар",
        "Желтые Воды", "Миргород", "Обухов", "Донецк", "Луганск", "Мариуполь",
        "Горловка", "Макеевка", "Севастополь", "Симферополь", "Керчь" 
    ], 
    "Казахстан": [
        "Астана", "Алматы", "Шымкент", "Караганда", "Актобе", "Тараз", 
        "Павлодар", "Усть-Каменогорск", "Семей", "Атырау", "Костанай", 
        "Кызылорда", "Уральск", "Петропавловск", "Актау", "Темиртау", 
        "Туркестан", "Кокшетау", "Талдыкорган", "Экибастуз", "Рудный", 
        "Жезказган", "Сатпаев", "Балхаш", "Талгар", "Конаев", "Жанаозен", 
        "Каскелен", "Арыс", "Ушарал", "Кентау", "Кульсары", "Шардара", 
        "Аягоз", "Риддер", "Зайсан", "Аксу", "Степногорск", "Жетысай"
    ]
}


# БД для хранения пользовательских отзывов
REVIEWS_DATA = []

# 1 отзыв на страницу
REVIEWS_PER_PAGE = 1 
CITIES_PER_PAGE = 12
PRODUCTS_PER_PAGE = 9
ADMIN_PRODUCTS_PER_PAGE = 5 

# --- 3. ФУНКЦИИ-ПОМОЩНИКИ ---

def generate_random_hashtag(length=8):
    """Генерирует уникальный хэштег сделки."""
    characters = string.ascii_uppercase + string.digits
    return '#ID' + ''.join(random.choice(characters) for i in range(length))

def update_crypto_rates():
    """Обновляет глобальный словарь EXCHANGE_RATES, если прошло RATE_UPDATE_INTERVAL."""
    global LAST_RATE_UPDATE
    global EXCHANGE_RATES
    
    if time.time() - LAST_RATE_UPDATE < RATE_UPDATE_INTERVAL:
        return "Курсы актуальны."

    new_rates = {}
    success = False
    
    try:
        # 1. Запрос Fiat Rates (USD base)
        fiat_response = requests.get(FIAT_API_URL, timeout=5)
        fiat_response.raise_for_status() 
        fiat_data = fiat_response.json()
        
        rates = fiat_data.get('rates', {})
        if 'UAH' in rates: new_rates["USD_TO_UAH"] = rates['UAH']
        if 'RUB' in rates: new_rates["USD_TO_RUB"] = rates['RUB']
        if 'BYN' in rates: new_rates["USD_TO_BYN"] = rates['BYN']
        if 'KZT' in rates: new_rates["USD_TO_KZT"] = rates['KZT']

        # 2. Запрос Crypto Rates
        crypto_response = requests.get(CRYPTO_API_URL, timeout=5)
        crypto_response.raise_for_status()
        crypto_data = crypto_response.json()
        
        if 'bitcoin' in crypto_data and 'usd' in crypto_data['bitcoin']:
            new_rates["BTC_TO_USD"] = crypto_data['bitcoin']['usd']
        
        if 'the-open-network' in crypto_data and 'usd' in crypto_data['the-open-network']:
            new_rates["TON_TO_USD"] = crypto_data['the-open-network']['usd']

        EXCHANGE_RATES.update(new_rates)
        LAST_RATE_UPDATE = time.time()
        success = True
        return "Курсы успешно обновлены с внешних источников."

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе курсов (API не отвечает или таймаут): {e}")
        return "Ошибка обновления курсов. Используются старые данные."
    except Exception as e:
        print(f"❌ Неизвестная ошибка при обновлении курсов: {e}")
        return "Неизвестная ошибка обновления курсов. Используются старые данные."

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ (ОТЗЫВЫ) ---

def load_reviews():
    """Загружает отзывы из файла, если он существует, иначе возвращает дефолтные."""
    global REVIEWS_DATA
    # Дефолтные отзывы
    default_reviews = [
        {"rating": 5, "text": "Отличный сервис, все быстро и четко!", "author": "Анонимный пользователь"},
        {"rating": 4, "text": "Хорошо, но есть куда стремиться.", "author": "Анонимный пользователь"},
        {"rating": 5, "text": "Просто супер! Спасибо!", "author": "Анонимный пользователь"},
    ]
    
    if os.path.exists(REVIEWS_FILE):
        try:
            with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    REVIEWS_DATA = data
                    print(f"✅ Отзывы успешно загружены из {REVIEWS_FILE}. Всего {len(REVIEWS_DATA)}.")
                    return
                else:
                    print(f"❌ Файл {REVIEWS_FILE} содержит неверный формат данных (не список). Используются дефолтные.")
        except (IOError, json.JSONDecodeError) as e:
            print(f"❌ Ошибка чтения/декодирования файла {REVIEWS_FILE}: {e}. Используются дефолтные.")
            
    # Если загрузка не удалась или файла нет, используем дефолтные и сохраняем их
    REVIEWS_DATA = default_reviews
    print("ℹ️ Использованы дефолтные отзывы.")
    save_reviews() 

def save_reviews():
    """Сохраняет текущий список отзывов в файл."""
    try:
        with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(REVIEWS_DATA, f, ensure_ascii=False, indent=4) 
        return True
    except IOError as e:
        print(f"❌ Ошибка записи в файл {REVIEWS_FILE}: {e}")
        return False

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ (ТОВАРЫ) ---

def load_products():
    """Загружает товары из файла, если он существует, иначе возвращает дефолтные."""
    global PRODUCT_DB
    
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ключи JSON всегда строки, преобразуем их обратно в int
                if isinstance(data, dict):
                    PRODUCT_DB = {int(k): v for k, v in data.items()}
                    print(f"✅ Товары успешно загружены из {PRODUCTS_FILE}. Всего {len(PRODUCT_DB)}.")
                    return
                else:
                    print(f"❌ Файл {PRODUCTS_FILE} содержит неверный формат данных (не словарь). Используются дефолтные.")
        except (IOError, json.JSONDecodeError, ValueError) as e:
            print(f"❌ Ошибка чтения/декодирования файла {PRODUCTS_FILE}: {e}. Используются дефолтные.")
            
    # Если загрузка не удалась или файла нет, используем дефолтные и сохраняем их
    PRODUCT_DB = DEFAULT_PRODUCT_DB.copy()
    print("ℹ️ Использованы дефолтные товары по умолчанию.")
    save_products()

def save_products():
    """Сохраняет текущий словарь товаров в файл."""
    try:
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            # Ключи в JSON всегда строки, что нормально
            json.dump(PRODUCT_DB, f, ensure_ascii=False, indent=4) 
        return True
    except IOError as e:
        print(f"❌ Ошибка записи в файл {PRODUCTS_FILE}: {e}")
        return False

# ----------------------------------------------------

def escape_html(text: str) -> str:
    if text is None:
        return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def get_main_menu_text():
    return "Вы вернулись в <b>Главное меню</b>. Выберите интересующий раздел:"

def format_stars(rating: int) -> str:
    """Форматирует число в строку из звезд."""
    full_star = "⭐️"
    empty_star = "☆"
    return full_star * rating + empty_star * (5 - rating)

def get_localized_price(chat_id, price_usd):
    update_crypto_rates() 

    user_info = user_data.get(chat_id, {})
    country_name = user_info.get('country', 'Россия')
    
    currency_info = COUNTRY_CURRENCY.get(country_name)
    
    if not currency_info:
        return f"{price_usd:,.2f} $", 1.0, "$" 

    rate_key = currency_info['rate_key']
    rate = EXCHANGE_RATES.get(rate_key, 1.0) 
    symbol = currency_info['symbol']
    
    localized_price = price_usd * rate
    
    formatted_price = f"{localized_price:,.2f}".replace(',', 'TEMP_SEP').replace('.', ',').replace('TEMP_SEP', ' ')
    
    return f"{formatted_price} {symbol}", rate, symbol

def get_next_product_id():
    """Возвращает следующий доступный ID для нового товара."""
    if not PRODUCT_DB:
        return 1
    return max(PRODUCT_DB.keys()) + 1

# --- 4. ФУНКЦИИ-КЛАВИАТУРЫ --- 
def get_main_menu_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    item_country = types.InlineKeyboardButton("🌍 Выбрать страну/город", callback_data="menu_country")
    item_buy = types.InlineKeyboardButton("🛍️ Купить товар", callback_data="menu_buy")
    item_reviews = types.InlineKeyboardButton("⭐️ Отзывы", callback_data="menu_reviews")
    item_work = types.InlineKeyboardButton("💼 Работа", callback_data="menu_work") 
    item_support = types.InlineKeyboardButton("🆘 Поддержка", url=f"https://t.me/{LINKS['SUPPORT']}")
    item_info = types.InlineKeyboardButton("ℹ️ Информация", url=LINKS['CHANNEL_URL'])
    
    markup.add(item_country, item_buy, item_reviews) 
    markup.add(item_work, item_support, item_info)
    
    if chat_id in ADMIN_IDS:
        markup.add(types.InlineKeyboardButton("🛠️ Админ-панель", callback_data="menu_admin"))
        
    return markup
    
def get_reviews_keyboard(chat_id, page=1):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # Кнопка "Оставить отзыв" только для администраторов
    if chat_id in ADMIN_IDS:
        markup.add(types.InlineKeyboardButton("✍️ Оставить отзыв", callback_data="start_leave_review"))
    
    total_reviews = len(REVIEWS_DATA)
    total_pages = math.ceil(total_reviews / REVIEWS_PER_PAGE) 
    current_page = max(1, min(page, total_pages))

    if total_pages > 1:
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"reviews_page_{current_page-1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore")) 

        nav_buttons.append(types.InlineKeyboardButton(f"Стр. {current_page}/{total_pages}", callback_data="ignore"))

        if current_page < total_pages:
            nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"reviews_page_{current_page+1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore"))

        markup.add(*nav_buttons)
        
    markup.add(types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="back_main"))
    
    return markup
    
def get_rating_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=5)
    
    for i in range(1, 6):
        markup.add(types.InlineKeyboardButton(format_stars(i), callback_data=f"select_rating_{i}"))
        
    markup.add(types.InlineKeyboardButton("⬅️ Назад к отзывам", callback_data="menu_reviews"))
    return markup
    
def get_product_keyboard(page=1):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    if not PRODUCT_DB:
        markup.add(types.InlineKeyboardButton("Нет доступных товаров", callback_data="ignore"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="back_main"))
        return markup
        
    product_keys = sorted(PRODUCT_DB.keys())
    
    start_num = (page - 1) * PRODUCTS_PER_PAGE
    end_num = min(start_num + PRODUCTS_PER_PAGE, len(product_keys))
    
    product_buttons = [
        types.InlineKeyboardButton(f"{PRODUCT_DB[product_keys[i]]['name']}", callback_data=f"select_product_{product_keys[i]}")
        for i in range(start_num, end_num)
    ]
    
    for i in range(0, len(product_buttons), 3):
        markup.add(*product_buttons[i:i+3])

    total_pages = math.ceil(len(PRODUCT_DB) / PRODUCTS_PER_PAGE)
    nav_buttons = []
    
    if total_pages > 1:
        current_page = max(1, min(page, total_pages))
        if current_page > 1:
            nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"page_{current_page-1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore")) 

        nav_buttons.append(types.InlineKeyboardButton(f"Стр. {current_page}/{total_pages}", callback_data="ignore"))

        if current_page < total_pages:
            nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"page_{current_page+1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore"))

        markup.add(*nav_buttons)
        
    markup.add(types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="back_main"))
    
    return markup
    
def get_quantity_keyboard(product_id: int):
    markup = types.InlineKeyboardMarkup(row_width=5)
    
    quantity_buttons = [
        types.InlineKeyboardButton(f"{i} шт.", callback_data=f"qty_{product_id}_{i}") 
        for i in range(1, 6)
    ]
    markup.add(*quantity_buttons)
    markup.add(types.InlineKeyboardButton("⬅️ Сменить товар", callback_data="back_buy")) 
    
    return markup

def get_payment_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    markup.add(
        types.InlineKeyboardButton("💰 Bitcoin (BTC)", callback_data="pay_btc"),
        types.InlineKeyboardButton("💎 TON (The Open Network)", callback_data="pay_ton"), 
        types.InlineKeyboardButton("💳 Перевод на карту", callback_data="pay_card")
    )
    markup.add(types.InlineKeyboardButton("⬅️ Назад к выбору количества", callback_data="back_qty_select"))
    return markup

def get_admin_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✍️ Анонимный отзыв (В канал)", callback_data="admin_review_start"),
        types.InlineKeyboardButton("📦 Управление товарами", callback_data="admin_products_1"), 
        types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="back_main")
    )
    return markup

def get_admin_product_main_keyboard(page=1):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Добавить новый товар", callback_data="admin_add_product")
    )
    
    product_keys = sorted(PRODUCT_DB.keys())
    
    if product_keys:
        markup.add(types.InlineKeyboardButton("--- Редактировать / Удалить ---", callback_data="ignore"))
        
        start_num = (page - 1) * ADMIN_PRODUCTS_PER_PAGE
        end_num = min(start_num + ADMIN_PRODUCTS_PER_PAGE, len(product_keys))
        
        for i in range(start_num, end_num):
            product_id = product_keys[i]
            product = PRODUCT_DB[product_id]
            markup.add(types.InlineKeyboardButton(
                f"📝 ID {product_id}: {product['name']}", 
                callback_data=f"admin_edit_select_{product_id}")
            )

        total_pages = math.ceil(len(PRODUCT_DB) / ADMIN_PRODUCTS_PER_PAGE)
        if total_pages > 1:
            nav_buttons = []
            current_page = max(1, min(page, total_pages))
            if current_page > 1:
                nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"admin_products_{current_page-1}"))
            else:
                nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore")) 

            nav_buttons.append(types.InlineKeyboardButton(f"Стр. {current_page}/{total_pages}", callback_data="ignore"))

            if current_page < total_pages:
                nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"admin_products_{current_page+1}"))
            else:
                nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore"))

            markup.add(*nav_buttons)


    markup.add(types.InlineKeyboardButton("⬅️ Назад в Админ-панель", callback_data="menu_admin"))
    return markup

def get_admin_product_edit_keyboard(product_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Название", callback_data=f"admin_edit_field_{product_id}_name"),
        types.InlineKeyboardButton("💰 Цена (USD)", callback_data=f"admin_edit_field_{product_id}_price"),
        types.InlineKeyboardButton("📜 Описание", callback_data=f"admin_edit_field_{product_id}_description"),
        types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"admin_delete_product_{product_id}"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_products_1")
    )
    return markup

def get_country_keyboard(page=1):
    markup = types.InlineKeyboardMarkup(row_width=2)
    countries = list(COUNTRY_CURRENCY.keys())
    
    for country in countries:
        markup.add(types.InlineKeyboardButton(country, callback_data=f"select_country_{country}"))

    markup.add(types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="back_main"))
    return markup

def get_city_keyboard(country, page=1):
    markup = types.InlineKeyboardMarkup(row_width=3)
    cities = CITY_DB.get(country, [])
    
    start_index = (page - 1) * CITIES_PER_PAGE
    end_index = min(start_index + CITIES_PER_PAGE, len(cities))
    
    city_buttons = [
        types.InlineKeyboardButton(city, callback_data=f"select_city_{country}_{city}")
        for city in cities[start_index:end_index]
    ]
    
    for i in range(0, len(city_buttons), 3):
        markup.add(*city_buttons[i:i+3])

    total_pages = math.ceil(len(cities) / CITIES_PER_PAGE)
    nav_buttons = []
    
    if total_pages > 1:
        current_page = max(1, min(page, total_pages))
        if current_page > 1:
            nav_buttons.append(types.InlineKeyboardButton("◀️", callback_data=f"city_page_{country}_{current_page-1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore")) 

        nav_buttons.append(types.InlineKeyboardButton(f"Стр. {current_page}/{total_pages}", callback_data="ignore"))

        if current_page < total_pages:
            nav_buttons.append(types.InlineKeyboardButton("▶️", callback_data=f"city_page_{country}_{current_page+1}"))
        else:
            nav_buttons.append(types.InlineKeyboardButton(" ", callback_data="ignore"))

        markup.add(*nav_buttons)

    markup.add(types.InlineKeyboardButton("⬅️ Сменить страну", callback_data="menu_country"))
    return markup
# --- 5. ОБРАБОТЧИКИ МЕНЮ И ПОКУПКИ ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
    
    update_crypto_rates() 
    
    welcome_text = (
        "👋 Добро пожаловать в развлекательный мир <b>дяди Александра!</b>\n\n"
        "Здесь вы всегда получите то, что вам нужно:\n\n"
        "• Молниеносные ответы\n"
        "• Высокое качество услуг\n"
        "• Работа опытных специалистов\n"
        "• Решение любых проблем в кратчайшие сроки\n\n"
        "Выберите интересующий раздел:"
    )
    bot.send_message(
        chat_id, 
        welcome_text, 
        reply_markup=get_main_menu_keyboard(chat_id)
    )

@bot.callback_query_handler(func=lambda call: call.data in ['back_main', 'menu_buy', 'menu_country'])
def callback_menu_handler(call):
    chat_id = call.message.chat.id
    
    # FIX: Безопасная инициализация данных при нажатии старой кнопки
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    try:
        if call.data == 'back_main':
            if 'temp_data' in user_data[chat_id]:
                user_data[chat_id]['temp_data'] = {} 
                
            bot.edit_message_text(
                chat_id=chat_id, 
                message_id=call.message.message_id, 
                text=get_main_menu_text(),
                reply_markup=get_main_menu_keyboard(chat_id)
            )
        elif call.data == 'menu_buy':
            callback_back_buy(call)
        elif call.data == 'menu_country':
            user_info = user_data.get(chat_id, {})
            current_country = user_info.get('country', 'Не выбрана')
            current_city = user_info.get('city', 'Не выбран')
            
            text = f"🌍 Выберите вашу <b>страну</b> (Текущая локация: {current_country}, {current_city}):"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_country_keyboard())

        bot.answer_callback_query(call.id)
        
    # FIX: Игнорируем ошибку "message is not modified"
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            bot.answer_callback_query(call.id, "Действие уже выполнено.")
        else:
            # Если это другая, критическая ошибка, выводим ее в консоль
            print(f"Ошибка в callback_menu_handler: {e}")
            bot.answer_callback_query(call.id, "Произошла ошибка, попробуйте снова.", show_alert=True)
            


# --- 6. ОБРАБОТЧИК РАЗДЕЛА "РАБОТА" --- 
@bot.callback_query_handler(func=lambda call: call.data == 'menu_work')
def callback_menu_work(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    text = (
        "💼 <b>Работа у дяди Александра</b>\n\n"
        "Работа заключается в продвижении нашего тега в Тик Токе.\n"
        "После короткого инструктажа вы заходите в приложение и размещаете комментарии либо по готовому шаблону, либо в свободной форме.\n\n"
        "У вас будет установленный период времени, в течение которого необходимо выполнить минимальный объём работы, чтобы получить выплату.\n"
        "После выполнения — подаёте заявку и получаете своё вознаграждение."
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➡️ Канал по работе", url=LINKS['WORK_CHANNEL']),
        types.InlineKeyboardButton("⬅️ Назад в Главное меню", callback_data="back_main")
    )
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)


# --- 7. ОБРАБОТЧИК РАЗДЕЛА "ОТЗЫВЫ" --- 

def render_reviews(page):
    """Генерирует текст с отзывами для текущей страницы (1 отзыв на страницу)."""
    
    if not REVIEWS_DATA:
        return "⭐️ <b>Отзывы наших клиентов</b>\n\nПока нет ни одного отзыва. Будьте первым!"

    total_reviews = len(REVIEWS_DATA)
    total_pages = math.ceil(total_reviews / REVIEWS_PER_PAGE) 
    page = max(1, min(page, total_pages)) 
    current_page = page
    
    start_index = (page - 1) * REVIEWS_PER_PAGE
    end_index = min(start_index + REVIEWS_PER_PAGE, len(REVIEWS_DATA))
    
    reviews_text = "⭐️ <b>Отзывы наших клиентов</b>\n"
    
    for i in range(start_index, end_index):
        review = REVIEWS_DATA[i]
        stars = format_stars(review['rating'])
        reviews_text += f"\n--- Отзыв {i + 1} ---\n"
        reviews_text += f"Оценка: <b>{stars}</b>\n"
        reviews_text += f"Текст: <i>{escape_html(review['text'])}</i>\n"
        reviews_text += f"Автор: <b>Анонимный пользователь</b>\n" 
    
    reviews_text += f"\n----------------------------------------\n"
    reviews_text += f"Всего отзывов: {len(REVIEWS_DATA)}. Страница {current_page}/{total_pages}."
    
    return reviews_text


@bot.callback_query_handler(func=lambda call: call.data == 'menu_reviews')
def callback_menu_reviews(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    page = 1 if REVIEWS_DATA else 1
    
    text = render_reviews(page)
    
    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=call.message.message_id, 
            text=text,
            reply_markup=get_reviews_keyboard(chat_id, page=page)
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reviews_page_'))
def callback_reviews_page(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    page = int(call.data.split('_')[2])
    
    text = render_reviews(page)
    
    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=call.message.message_id, 
            text=text,
            reply_markup=get_reviews_keyboard(chat_id, page=page)
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'start_leave_review')
def callback_start_leave_review(call):
    chat_id = call.message.chat.id
    
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    # ПРОВЕРКА НА АДМИНИСТРАТОРА
    if chat_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Только администраторы могут оставлять отзывы.", show_alert=True)
        return
        
    user_data[chat_id]['temp_data'] = {'review_step': 'select_rating'}
    
    text = "✍️ <b>Оставить отзыв</b>\n\nШаг 1/2: Выберите оценку от 1 до 5 звезд."
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_rating_keyboard())
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id, "Вы выбрали оставить отзыв. Выберите оценку.")
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('select_rating_'))
def callback_select_rating(call):
    chat_id = call.message.chat.id
    
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    # ПРОВЕРКА НА АДМИНИСТРАТОРА
    if chat_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Только администраторы могут оставлять отзывы.", show_alert=True)
        return
        
    rating = int(call.data.split('_')[2])
    
    user_data[chat_id]['temp_data']['review_rating'] = rating
    user_data[chat_id]['temp_data']['review_step'] = 'enter_text'
    
    stars = format_stars(rating)
    text = (
        f"✍️ <b>Оставить отзыв</b>\n\n"
        f"Шаг 2/2: Вы выбрали оценку: <b>{stars}</b>.\n"
        f"Теперь, пожалуйста, <b>введите текст</b> вашего отзыва (минимум 10 символов).\n\n"
        f"<i>(Ваш отзыв будет опубликован анонимно)</i>"
    )
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text)
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id, text=f"Выбрана оценка {rating}. Введите текст.")
    
    bot.register_next_step_handler(call.message, process_review_text)

def process_review_text(message):
    chat_id = message.chat.id
    
    # ПРОВЕРКА НА АДМИНИСТРАТОРА
    if chat_id not in ADMIN_IDS:
        try:
            bot.send_message(chat_id, "❌ Только администраторы могут оставлять отзывы.", reply_markup=get_main_menu_keyboard(chat_id))
        except:
             pass 
        return

    state = user_data.get(chat_id, {}).get('temp_data', {})
    
    if state.get('review_step') != 'enter_text' or 'review_rating' not in state:
        try:
            bot.send_message(chat_id, "❌ Ошибка сессии. Начните оставление отзыва сначала.", reply_markup=get_reviews_keyboard(chat_id, 1))
        except:
             pass 
        return

    review_text = message.text.strip()
    rating = state['review_rating']
    
    if len(review_text) < 10:
        bot.send_message(chat_id, "❌ Текст отзыва слишком короткий. Пожалуйста, введите более 10 символов.")
        bot.register_next_step_handler(message, process_review_text)
        return

    # Сохраняем отзыв
    new_review = {
        "rating": rating, 
        "text": review_text, 
        "author": "Анонимный пользователь" 
    }
    REVIEWS_DATA.insert(0, new_review) 
    
    # Сохранение отзывов в файл после добавления нового
    save_reviews()
    
    # Очистка временных данных
    user_data[chat_id]['temp_data'] = {}
    
    stars = format_stars(rating)
    final_text = (
        f"🎉 <b>Ваш отзыв успешно добавлен!</b>\n\n"
        f"Оценка: <b>{stars}</b>\n"
        f"Текст: <i>{escape_html(review_text)}</i>\n\n"
        f"Спасибо за вашу обратную связь."
    )
    
    bot.send_message(
        chat_id, 
        final_text, 
        reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⭐️ Посмотреть отзывы", callback_data="menu_reviews"), 
                                                     types.InlineKeyboardButton("⬅️ Главное меню", callback_data="back_main"))
    )

# --- 8. ОБРАБОТЧИКИ ПОКУПКИ (СХЕМА ПЛАТЕЖА И ПРОДУКТОВ) --- 
@bot.callback_query_handler(func=lambda call: call.data == 'back_buy')
def callback_back_buy(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    text = "📦 <b>Каталог товаров</b> (Цены отображаются после выбора).\nВыберите товар:"
    
    if 'temp_data' in user_data[chat_id]:
        user_data[chat_id]['temp_data'] = {}
        
    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=call.message.message_id, 
            text=text,
            reply_markup=get_product_keyboard(page=1)
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def callback_product_page(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    page = int(call.data.split('_')[1])
    
    text = "📦 <b>Каталог товаров</b> (Цены отображаются после выбора).\nВыберите товар:"
    
    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=call.message.message_id, 
            text=text,
            reply_markup=get_product_keyboard(page=page)
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_country_') or call.data.startswith('select_city_') or call.data.startswith('city_page_'))
def callback_location_handler(call):
    chat_id = call.message.chat.id
    
    # FIX: Безопасная инициализация данных (ИСПРАВЛЕНИЕ KeyError)
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
    
    try:
        if call.data.startswith('select_country_'):
            country = call.data.split('_')[2]
            user_data[chat_id]['country'] = country
            default_city = CITY_DB.get(country, [''])[0] if CITY_DB.get(country) else 'Не выбран'
            user_data[chat_id]['city'] = default_city
            text = f"🌍 Выбрана страна: <b>{country}</b>. Теперь выберите <b>город</b> (цены будут конвертированы в {COUNTRY_CURRENCY[country]['code']}):"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_city_keyboard(country, page=1))
            
        elif call.data.startswith('select_city_'):
            parts = call.data.split('_')
            country = parts[2]
            city = parts[3] 
            if len(parts) > 4:
                city = '_'.join(parts[3:]) 
            
            user_data[chat_id]['country'] = country
            user_data[chat_id]['city'] = city
            text = f"✅ Ваша локация сохранена: <b>{country}, {city}</b>.\nТеперь выберите интересующий раздел:"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_main_menu_keyboard(chat_id))
            
        elif call.data.startswith('city_page_'):
            _, _, country, page_str = call.data.split('_')
            page = int(page_str)
            text = f"🌍 Выбрана страна: <b>{country}</b>. Теперь выберите <b>город</b> (цены будут конвертированы в {COUNTRY_CURRENCY[country]['code']}):"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_city_keyboard(country, page=page))

        bot.answer_callback_query(call.id)
    except telebot.apihelper.ApiTelegramException:
        bot.answer_callback_query(call.id, "Действие уже выполнено или произошла ошибка редактирования.")
        pass # Игнорируем "message is not modified" и прочие ошибки редактирования.


@bot.callback_query_handler(func=lambda call: call.data == 'back_qty_select')
def callback_back_qty_select(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    user_info = user_data.get(chat_id, {})
    temp_data = user_info.get('temp_data', {})
    product_id = temp_data.get('product_id')
    
    if not product_id:
        bot.answer_callback_query(call.id, "Ошибка сессии. Начните покупку снова.", show_alert=True)
        callback_back_buy(call)
        return
        
    product = PRODUCT_DB.get(product_id)
    localized_price_text, _, _ = get_localized_price(chat_id, product['price_usd'])
    
    product_info = (
        f"🛍️ Вы выбрали: <b>{escape_html(product['name'])}</b>\n"
        f"💵 <b>Цена за 1 ед.:</b> <b>{localized_price_text}</b>\n"
        f"📝 Описание: <i>{escape_html(product['description'])}</i>\n\n"
        f"Выберите <b>количество</b> (1-5 шт.)."
    )

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=product_info,
            reply_markup=get_quantity_keyboard(product_id)
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('select_product_'))
def callback_select_product(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    try:
        product_id = int(call.data.split('_')[2])
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "Ошибка: Неверный ID товара.", show_alert=True)
        return
    
    product = PRODUCT_DB.get(product_id)
    if not product:
        bot.answer_callback_query(call.id, "Товар не найден.", show_alert=True)
        return
        
    localized_price_text, _, _ = get_localized_price(chat_id, product['price_usd'])

    user_data[chat_id]['temp_data'] = {
        'product_id': product_id,
        'unit_price_usd': product['price_usd']
    }
    
    product_info = (
        f"🛍️ Вы выбрали: <b>{escape_html(product['name'])}</b>\n"
        f"💵 <b>Цена за 1 ед.:</b> <b>{localized_price_text}</b>\n"
        f"📝 Описание: <i>{escape_html(product['description'])}</i>\n\n"
        f"Выберите <b>количество</b> (1-5 шт.)."
    )
    
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=product_info,
            reply_markup=get_quantity_keyboard(product_id)
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('qty_'))
def callback_select_quantity(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    try:
        parts = call.data.split('_')
        product_id = int(parts[1])
        quantity = int(parts[2])
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "Ошибка: Неверные данные количества.", show_alert=True)
        return
        
    user_info = user_data.get(chat_id, {})
    product_data = user_info.get('temp_data')
    product = PRODUCT_DB.get(product_id)

    if not product_data or product_data.get('product_id') != product_id or not product:
        bot.answer_callback_query(call.id, "Ошибка сессии. Начните покупку сначала.", show_alert=True)
        return

    unit_price_usd = product['price_usd']
    total_price_usd = unit_price_usd * quantity
    
    order_hashtag = generate_random_hashtag()
    user_data[chat_id]['temp_data'].update({
        'quantity': quantity,
        'total_price_usd': total_price_usd,
        'order_hashtag': order_hashtag,
        'product_name': product['name'] 
    })

    localized_total_price, _, _ = get_localized_price(chat_id, total_price_usd)
    
    country = user_info.get('country', 'Россия')
    city = user_info.get('city', 'Москва')
    
    payment_info = (
        f"✅ <b>Заказ {order_hashtag} создан</b>\n\n"
        f"🛒 Товар: <b>{escape_html(product['name'])}</b>\n"
        f"🔢 Количество: <b>{quantity} шт.</b>\n"
        f"🌍 Страна / Город: <b>{country} / {city}</b>\n"
        f"💰 <b>ИТОГО К ОПЛАТЕ:</b> <b>{localized_total_price}</b>\n"
        f"----------------------------------------\n"
        f"Пожалуйста, выберите удобный способ оплаты."
    )
    
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=payment_info,
            reply_markup=get_payment_keyboard()
        )
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def callback_payment_handler(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    payment_method = call.data.split('_')[1]
    
    user_info = user_data.get(chat_id, {})
    temp_data = user_info.get('temp_data')

    if not temp_data or 'order_hashtag' not in temp_data:
        bot.answer_callback_query(call.id, "Ошибка: Данные заказа не найдены.", show_alert=True)
        return
        
    hashtag = temp_data['order_hashtag']
    total_price_usd = temp_data['total_price_usd']
    product_name = temp_data.get('product_name', 'Товар')
    quantity = temp_data['quantity']
    country = user_info.get('country', 'Не указано')
    city = user_info.get('city', 'Не указано')
    
    update_crypto_rates()
    localized_price_text, _, _ = get_localized_price(chat_id, total_price_usd)

    # Базовый блок информации о заказе (СВОДКА ДЛЯ КОПИРОВАНИЯ)
    order_summary_text = (
        f"✅ Заказ: {hashtag}\n"
        f"🌍 Локация: {country}, {city}\n"
        f"🛒 Товар: {escape_html(product_name)}\n"
        f"🔢 Количество: {quantity} шт.\n"
        f"💰 К оплате (В USD): {total_price_usd:.2f} $\n"
    )

    reply_markup = types.InlineKeyboardMarkup(row_width=1)
    
    if payment_method == 'card':
        
        text = (
            f"<b>💳 Перевод на карту</b>\n\n"
            f"{order_summary_text}"
            f"----------------------------------------\n"
            f"Для получения реквизитов, <b>скопируйте следующие данные</b> и отправьте их оператору:\n"
            f"<code>{order_summary_text}</code>\n"
            f"👉 @{LINKS['SUPPORT']}"
        )
        
        reply_markup.add(types.InlineKeyboardButton("⬅️ Сменить способ оплаты", callback_data="back_qty_select"))
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=reply_markup)
        except telebot.apihelper.ApiTelegramException:
            pass # Игнорируем "message is not modified"
        
    elif payment_method in ['btc', 'ton']:
        
        crypto_key = 'BTC' if payment_method == 'btc' else 'TON'
        crypto_to_usd_rate = EXCHANGE_RATES.get(f"{crypto_key}_TO_USD", 1.0)
        
        if crypto_to_usd_rate == 0:
             crypto_to_usd_rate = 1.0 
        
        amount_crypto = total_price_usd / crypto_to_usd_rate
        wallet_address = WALLETS.get(crypto_key, "АДРЕС НЕ НАЙДЕН")
        
        crypto_price_text = f"<code>{amount_crypto:.6f} {crypto_key}</code>"
        
        text = (
            f"<b>💰 Оплата {crypto_key}</b>\n\n"
            f"{order_summary_text}"
            f"💰 К оплате (В Вашей валюте): <b>{localized_price_text}</b>\n"
            f"💰 К оплате в <b>{crypto_key}</b>: {crypto_price_text}\n"
            f"Адрес для оплаты:\n<code>{wallet_address}</code>\n"
            f"----------------------------------------\n"
            f"⚠️ <b>Важно:</b> После перевода средств, <b>скопируйте сообщение с хештегом заказа</b> и <b>скриншот перевода</b> и перешлите их оператору @{LINKS['SUPPORT']}."
        )

        reply_markup.add(types.InlineKeyboardButton("⬅️ Сменить способ оплаты", callback_data="back_qty_select"))

        try:
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=reply_markup)
        except telebot.apihelper.ApiTelegramException:
            pass # Игнорируем "message is not modified"

    bot.answer_callback_query(call.id)


# --- 9. АДМИН-ПАНЕЛЬ --- 

@bot.callback_query_handler(func=lambda call: call.data == 'menu_admin')
def callback_menu_admin(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: return
    text = "🛠️ <b>Админ-панель</b>\n\nВыберите действие:"
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_admin_main_keyboard())
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

# ОБРАБОТЧИК ДЛЯ НАЧАЛА ОСТАВЛЕНИЯ АНОНИМНОГО ОТЗЫВА (ТОЛЬКО АДМИНЫ, В КАНАЛ)
@bot.callback_query_handler(func=lambda call: call.data == 'admin_review_start')
def callback_admin_review_start(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: 
        bot.answer_callback_query(call.id, "У вас нет прав администратора.", show_alert=True)
        return
    
    admin_next_step[chat_id] = {'action': 'post_review'}
    
    text = "✍️ <b>Оставить анонимный отзыв</b> (В канал)\n\nВведите текст отзыва, который будет <b>анонимно</b> опубликован в канале."
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text)
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id, "Ожидаю текст отзыва...")
    
    bot.register_next_step_handler(call.message, process_admin_review_text)

def process_admin_review_text(message):
    chat_id = message.chat.id
    state = admin_next_step.get(chat_id)
    if not state or state.get('action') != 'post_review': return
    
    review_text = message.text
    
    if len(review_text.strip()) < 10:
        bot.send_message(chat_id, "❌ Отзыв слишком короткий. Пожалуйста, введите более подробный текст.")
        bot.register_next_step_handler(message, process_admin_review_text)
        return
        
    try:
        # Форматирование отзыва для анонимной публикации
        final_review = (
            "⭐️⭐️⭐️⭐️⭐️\n"
            "<b>Новый анонимный отзыв!</b>\n\n"
            f"{escape_html(review_text)}\n\n"
            "<i>(Отзыв размещен администратором)</i>"
        )
        
        # Публикация в канал
        bot.send_message(
            chat_id=LINKS['CHANNEL'], 
            text=final_review, 
            parse_mode='HTML'
        )
        
        final_text = "✅ Отзыв успешно опубликован анонимно в канале!"
        
    except Exception as e:
        final_text = f"❌ Ошибка публикации. Убедитесь, что бот является администратором канала **{LINKS['CHANNEL']}**.\nОшибка: {e}"
        print(f"Ошибка при публикации отзыва: {e}")
        
    finally:
        if chat_id in admin_next_step:
            del admin_next_step[chat_id]
        bot.send_message(chat_id, final_text, reply_markup=get_admin_main_keyboard())


@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_products'))
def callback_admin_products(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: return
    try:
        page = int(call.data.split('_')[-1])
    except:
        page = 1 

    text = "📦 <b>Управление товарами</b>\n\nВыберите товар для редактирования или нажмите 'Добавить новый товар'."

    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_admin_product_main_keyboard(page=page))
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_edit_select_'))
def callback_admin_edit_select(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: return
    product_id = int(call.data.split('_')[-1])
    product = PRODUCT_DB.get(product_id)

    if not product:
        bot.answer_callback_query(call.id, "Товар не найден.", show_alert=True)
        return
        
    text = (
        f"📝 <b>Редактирование товара ID: {product_id}</b>\n\n"
        f"<b>Название:</b> {product['name']}\n"
        f"<b>Цена:</b> {product['price_usd']:.2f} USD\n"
        f"<b>Описание:</b> {product['description']}\n\n"
        f"Выберите поле для изменения:"
    )
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=get_admin_product_edit_keyboard(product_id))
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_edit_field_'))
def callback_admin_edit_field(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: return
    _, _, _, product_id_str, field = call.data.split('_')
    product_id = int(product_id_str)
    
    admin_next_step[chat_id] = {'action': 'edit_product', 'product_id': product_id, 'field': field}
    
    field_names = {'name': 'название', 'price': 'цену в USD', 'description': 'описание'}
    text = f"Введите новое <b>{field_names.get(field)}</b> для товара ID {product_id}."
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text)
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id)
    
    bot.register_next_step_handler(call.message, process_edited_product_value)

def process_edited_product_value(message):
    chat_id = message.chat.id
    if chat_id not in ADMIN_IDS: return
    state = admin_next_step.get(chat_id)
    if not state or state.get('action') != 'edit_product': return

    product_id = state['product_id']
    field = state['field']
    new_value = message.text.strip()
    
    try:
        if field == 'price':
            value = float(new_value)
            if value <= 0: raise ValueError
            PRODUCT_DB[product_id]['price_usd'] = value
            final_text = f"✅ Цена товара ID {product_id} успешно изменена на <b>{value:.2f} USD</b>."
        elif field == 'name':
            PRODUCT_DB[product_id]['name'] = new_value
            final_text = f"✅ Название товара ID {product_id} успешно изменено на <b>{new_value}</b>."
        elif field == 'description':
            PRODUCT_DB[product_id]['description'] = new_value
            final_text = f"✅ Описание товара ID {product_id} успешно изменено."
        else:
            final_text = "❌ Неизвестное поле для редактирования."
            
        # Сохранение товаров после редактирования
        save_products()
            
    except ValueError:
        final_text = "❌ Неверный формат данных. Для цены введите число (например, 15.50). Попробуйте снова."
        bot.send_message(chat_id, final_text)
        bot.register_next_step_handler(message, process_edited_product_value) 
        return
    
    del admin_next_step[chat_id]
    bot.send_message(chat_id, final_text, reply_markup=get_admin_product_main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_delete_product_'))
def callback_admin_delete_product(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: return
    product_id = int(call.data.split('_')[-1])
    
    if product_id in PRODUCT_DB:
        product_name = PRODUCT_DB[product_id]['name']
        del PRODUCT_DB[product_id]
        
        # Сохранение товаров после удаления
        save_products()
        
        final_text = f"🗑️ Товар <b>{product_name}</b> (ID {product_id}) успешно <b>удален</b>."
    else:
        final_text = "❌ Ошибка: Товар не найден."
        
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=final_text, reply_markup=get_admin_product_main_keyboard())
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id, text="Товар удален.")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_product')
def callback_admin_add_product(call):
    chat_id = call.message.chat.id
    # FIX: Безопасная инициализация данных
    if chat_id not in user_data:
        user_data[chat_id] = {'country': 'Россия', 'city': 'Москва', 'temp_data': {}}
        
    if chat_id not in ADMIN_IDS: return
    
    admin_next_step[chat_id] = {'action': 'add_product', 'data': {}}
    text = "➕ <b>Добавление товара</b>\n\nШаг 1/3: Введите <b>название</b> нового товара."
    
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text)
    except telebot.apihelper.ApiTelegramException:
        pass # Игнорируем "message is not modified"
        
    bot.answer_callback_query(call.id, "Ожидаю название товара...")
    
    bot.register_next_step_handler(call.message, process_new_product_name)

def process_new_product_name(message):
    chat_id = message.chat.id
    if chat_id not in ADMIN_IDS or admin_next_step.get(chat_id, {}).get('action') != 'add_product': return

    name = message.text.strip()
    if len(name) < 3:
        bot.send_message(chat_id, "❌ Название слишком короткое. Попробуйте снова.")
        bot.register_next_step_handler(message, process_new_product_name)
        return

    admin_next_step[chat_id]['data']['name'] = name
    text = "Шаг 2/3: Введите <b>цену</b> в долларах (USD). Используйте точку как разделитель (например, 15.50)."
    bot.send_message(chat_id, text)
    bot.register_next_step_handler(message, process_new_product_price)

def process_new_product_price(message):
    chat_id = message.chat.id
    if chat_id not in ADMIN_IDS or admin_next_step.get(chat_id, {}).get('action') != 'add_product': return

    try:
        price = float(message.text.strip())
        if price <= 0: raise ValueError
    except ValueError:
        bot.send_message(chat_id, "❌ Неверный формат цены. Введите число (например, 15.50).")
        bot.register_next_step_handler(message, process_new_product_price)
        return

    admin_next_step[chat_id]['data']['price_usd'] = price
    text = "Шаг 3/3: Введите <b>описание</b> товара."
    bot.send_message(chat_id, text)
    bot.register_next_step_handler(message, process_new_product_description)

def process_new_product_description(message):
    chat_id = message.chat.id
    if chat_id not in ADMIN_IDS or admin_next_step.get(chat_id, {}).get('action') != 'add_product': return

    description = message.text.strip()
    if len(description) < 5:
        bot.send_message(chat_id, "❌ Описание слишком короткое. Попробуйте снова.")
        bot.register_next_step_handler(message, process_new_product_description)
        return
        
    admin_next_step[chat_id]['data']['description'] = description
    
    new_product_id = get_next_product_id()
    new_product_data = admin_next_step[chat_id]['data']
    
    PRODUCT_DB[new_product_id] = new_product_data
    
    # Сохранение товаров после добавления
    save_products()
    
    final_text = (
        f"✅ <b>Товар успешно добавлен!</b>\n\n"
        f"ID: <code>{new_product_id}</code>\n"
        f"Название: {new_product_data['name']}\n"
        f"Цена: {new_product_data['price_usd']:.2f} USD"
    )
    
    del admin_next_step[chat_id]
    
    bot.send_message(chat_id, final_text, reply_markup=get_admin_product_main_keyboard())


# --- 10. ЗАПУСК БОТА С ЗАЩИТОЙ ---

if __name__ == '__main__':
    print(f"Бот запущен. Текущее время: {time.ctime()}")
    
    # Сначала загружаем товары
    load_products()
    # Загружаем отзывы
    load_reviews()

    try:
        # ПЕРВОЕ ОБНОВЛЕНИЕ КУРСОВ ПРИ ЗАПУСКЕ
        print(update_crypto_rates()) 
    except Exception as e:
        print(f"❌ Критическая ошибка при первом обновлении курсов: {e}.")

    try:
        print("Начинается процесс опроса Telegram API...")
        # Теперь бот более устойчив к старым кнопкам после перезапуска
        bot.infinity_polling(skip_pending=True, timeout=30) 
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ РАБОТЕ БОТА. БОТ ОСТАНОВИЛСЯ: {e}")
        traceback.print_exc()

        input()
