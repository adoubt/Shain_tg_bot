from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
import telebot
from telebot import types
from datetime import datetime
import re,requests
from telegram.constants import ParseMode

#________Подключение к API Google_______________________
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
credentials_FILE = os.path.join(BASE_DIR, 'credentials.json')
token_FILE = os.path.join(BASE_DIR, 'token.json')
creds = None
if os.path.exists(token_FILE):
    creds = Credentials.from_authorized_user_file(token_FILE, SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(token_FILE, 'w') as token:
        token.write(creds.to_json())
SAMPLE_SPREADSHEET_ID = 'SAMPLE_SPREADSHEET_ID'
SAMPLE_RANGE_NAME = 'Queue'
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets().values()
#_____________________________

TOKEN = 'tg_bot_token'
ADMIN_ID = 'admin_user_id_example_4579510886'
bot = telebot.TeleBot(TOKEN)

def convertdate(timestamp):

    current_date = datetime.fromtimestamp(timestamp-14400).strftime('%d.%m.%Y %H:%M:%S')
    return(current_date)


@bot.message_handler(commands=['start','menu','Отследить заказ','Калькулятор доставки','Инструкция','🚧О нас'])

def send_welcome(message):
    
    chat_id = message.chat.id
    tg_user = message.chat.username
    ids = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,range ='Customer!A:A').execute()
    id = [f'{chat_id}']
    if id not in ids['values']:
        cart_total = ''
        oauth_date= convertdate(message.date)
        last_seen_date = oauth_date
        array = {'values': [[chat_id, chat_id,'','','']]}
        sheet.append(spreadsheetId=SAMPLE_SPREADSHEET_ID,range ='Cart',valueInputOption='USER_ENTERED',body=array).execute()
        array = {'values': [[chat_id, tg_user,'','','',oauth_date,last_seen_date]]}
        result = sheet.append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range='Customer',
                                valueInputOption='USER_ENTERED',
                                body=array).execute()
    else: 
        cart_total = ''
        row=0
        for value in ids['values']:
            row+=1
            if id == value:
                last_seen_date = convertdate(message.date)
                array = {'values': [[last_seen_date]]}
                result = sheet.update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=f'Customer!G{row}',
                                        valueInputOption='USER_ENTERED',
                                        body=array).execute()
                break
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtnadd = types.KeyboardButton(text='📦Добавить товар')
    itembtncart = types.KeyboardButton(text=f'🛒Корзина{cart_total}')
    itembtnprofile = types.KeyboardButton(text='👤Профиль')
    itembtntrack = types.KeyboardButton(text='🚧Отследить заказ')
    itembtnclc = types.KeyboardButton(text='🚧Калькулятор доставки')
    itembtnfaq = types.KeyboardButton(text='🚧Инструкция')
    itembtnabout = types.KeyboardButton(text='🚧О нас')
    
    markup.row(itembtnadd)
    markup.row(itembtncart)
    markup.row(itembtnprofile)
    markup.row(itembtntrack)
    markup.row(itembtnclc)
    markup.row(itembtnfaq)
    markup.row(itembtnabout)

    bot.send_message(chat_id, 'ХЕлоу епта', reply_markup=markup)	
    
@bot.message_handler(content_types=['text'])
def func(message):
    chat_id= message.chat.id
    if 'Добавить' in message.text:
        bot.reply_to(message, "Перед копированием ссылки, выбери размер! жду тут")
        bot.register_next_step_handler(message, process_link_step)
    elif "Корзина" in message.text:
        ids = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,range ='Cart!B:B').execute()
        id = [f'{chat_id}']
        if id in ids['values']:
            row=0
            for value in ids['values']:
                row+=1
                if id == value:
                    result = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=f'Cart!A{row}:E{row}').execute()
                    break
            products = result['values'][0][2]
            products = products.split(sep=', ')
            if products == [] or products =='':
                bot.send_message(chat_id,'Пусто')
            else:
                for product in products:
                    ids = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,range ='Product!A:A').execute()
                    product = [product]
                    if product in ids['values']:
                        row=0
                        for value in ids['values']:
                            row+=1
                            if product == value:
                                product = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                    range=f'Product!A{row}:G{row}').execute()
                    product = product['values'][0]

                    delbtn = types.InlineKeyboardButton("🚧Удалить",callback_data='🚧Удалить')
                    delmarkup = types.InlineKeyboardMarkup()
                    delmarkup.add(delbtn)
#  deleteProduct(product[0])
                    bot.send_message(chat_id,text=
                                    f'{product[1]}\n{product[3]} | ${product[5]} | Кол-во: {product[4]} | {telebot.formatting.hlink(content="link",url=product[2],escape=True)}',
                                    reply_markup=delmarkup,parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True,
                                    disable_notification=True)
                

        else: 
            array = {'values': [[chat_id, chat_id,'','','']]}
            sheet.append(spreadsheetId=SAMPLE_SPREADSHEET_ID,range ='Cart',valueInputOption='USER_ENTERED',body=array).execute()
            bot.send_message(chat_id,'Пусто')

def deleteProduct(id):
    # result = sheet.update()
    return

def process_link_step(message):
    chat_id=message.chat.id
    link = message.text
    r = requests.get(url = link)
    if r.status_code !=200:
        print('gg')
        bot.reply_to(message, 'А это точно ссылка?🤨еще разок давай',process_link_step)
        return
    musor = str(r.content).split(sep= 'window.goodsDetailV3SsrData = ')
    musor = musor[1].split(sep='\\n    //\\xe7\\x89\\xa9\\xe6\\xb5\\x81\\xe8\\xbf\\x90\\xe8\\xb4\\xb9\\xe5\\xb1\\x95\\xe7\\xa4\\xba')
    name = musor[0].split(sep='pageKeywords')
    name = name[0][14:-3].split(sep='|')
    name = name[0]
    usprice = musor[0].split(sep='retailPrice')
    usprice = usprice[1][13:19].replace('\"','').replace(',','')
    goods_id = musor[0].split(sep='goods_id')
    goods_id = goods_id[1][2:15]
    goods_id = re.sub(r'[^0-9]', '', goods_id)
    sizes = musor[0].split(sep='attr_value_list')
    try:
        sizes=sizes[1].split(sep='attr_std_value')
        all_sizes = []
        for size in sizes[0:-1]:
            size=size[-8:-1]
            size = re.sub(r'[^a-zA-Z0-9\-]', '', size)
            if size =='-size':
                size='one-size'
            elif size[0] == 'n':
                size = size.replace('n','')
            all_sizes.append(size)
    except:
        all_sizes=['one-size']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for size in all_sizes:
        sizebtn = types.KeyboardButton(text=f'{size}')
        markup.row(sizebtn)
    qty='1'
    product = [goods_id,name,link,all_sizes,qty,usprice,chat_id]
    bot.send_message(chat_id, f"Нашел вот:\n{name}\nкакой размер?", reply_markup=markup)
    bot.register_next_step_handler(message, process_size_step,product=product)
    

def process_size_step(message,product):
    size = message.text
    product[3] = size
    bot.send_message(message.chat.id, "Количество?",reply_markup=telebot.types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_order_step,product=product)

def process_order_step(message,product):

    product[4] = message.text
    array = {'values': [product]}
    result = sheet.append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range='Product',
                            valueInputOption='USER_ENTERED',
                            body=array).execute()
    
    ids = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,range='Cart!B:B').execute()
    id = [f'{message.chat.id}']
    if id in ids['values']:
        row=0
        for value in ids['values']:
            row+=1
            if id == value:
                product_id = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=f'Cart!C{row}').execute()

                if 'values' not in product_id:
                    array = {'values': [[product[0]]]}
                    result = sheet.update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=f'Cart!C{row}',
                                        valueInputOption='USER_ENTERED',
                                        body=array).execute()
                else:
                    product_id = product_id['values'][0]
                    array = {'values': [[f'{product_id[0]}, {product[0]}']]}
                    result = sheet.update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                            range=f'Cart!C{row}',
                                            valueInputOption='USER_ENTERED',
                                            body=array).execute()
                break

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtnadd = types.KeyboardButton(text='📦Добавить товар')
    btnmenu = types.KeyboardButton(text='/menu')
    markup.row(itembtnadd)
    markup.row(btnmenu)
    bot.send_message(message.chat.id, "Уже в корзине, добавим еще?",reply_markup=markup)
def notify_admin(product):

    admin_message = f"Новая заявка:\nCu"

    bot.send_message(ADMIN_ID, admin_message)


# Панель администратора

@bot.message_handler(commands=['admin'])

def handle_admin(message):

    if str(message.chat.id) == ADMIN_ID:

        if len(requests) > 0:

            for request in requests:

                request_message = f"Заявка от пользователя {request['name']}:\n{request['message']}"

                bot.send_message(ADMIN_ID, request_message)

        else:

            bot.send_message(ADMIN_ID, "Нет новых заявок.")



    else:

        bot.reply_to(message, f"У вас нет доступа к админ-панели.u-{message.chat.id}")



bot.polling()
