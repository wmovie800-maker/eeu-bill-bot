import telebot
import pandas as pd
from datetime import datetime
from telebot import types

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

# ዳታውን መጫን
def load_data():
    try:
        return pd.read_excel('customers.xlsx')
    except:
        return None

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = {}
    text = "እንኳን ደህና መጡ! / Baga nagaan dhuftan! / Welcome!\nእባክዎ ቋንቋ ይምረጡ / Maaloo afaan filadhaa / Please choose a language."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='an'),
               types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data='or'),
               types.InlineKeyboardButton("English 🇬🇧", callback_data='en'))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def lang_set(call):
    user_state[call.message.chat.id] = {'l': call.data, 's': 'acc'}
    msg = {
        'an': "የኮንትራት አካውንት ቁጥርዎን ያስገቡ።",
        'or': "Maaloo lakkoofsa herrega keessanii galchaa.",
        'en': "Please enter your contract account number."
    }
    bot.send_message(call.message.chat.id, msg[call.data])

@bot.message_handler(func=lambda m: m.text.isdigit())
def handle_digits(m):
    cid = m.chat.id
    if cid not in user_state or 'l' not in user_state[cid]: return
    
    lang = user_state[cid]['l']
    st = user_state[cid]['s']
    df = load_data()
    
    if st == 'acc':
        acc_num = int(m.text)
        cust = df[df['Contract Account'] == acc_num]
        
        if not cust.empty:
            row = cust.iloc[0]
            user_state[cid].update({'s': 'read', 'i': row})
            read_msg = {
                'an': f"ጤና ይስጥልኝ {row['Customer Name']}! አሁን በቆጣሪዎ ላይ የሚታየውን ንባብ ብቻ ይላኩ። 📸",
                'or': f"Akkam {row['Customer Name']}! Maaloo lakkoofsa miitaraa ammaa galchaa. 📸",
                'en': f"Hello {row['Customer Name']}! Please send the current meter reading. 📸"
            }
            bot.send_message(cid, read_msg[lang])
        else:
            err = {'an': "❌ አካውንቱ አልተገኘም", 'or': "❌ Herregni hin argamne", 'en': "❌ Account not found"}
            bot.send_message(cid, err[lang])

    elif st == 'read':
        info = user_state[cid]['i']
        try:
            present = int(m.text)
            # የድሮ ንባብ ከሌለ እንደ 0 ይቆጠራል
            prev = info['Previous_Reading'] if pd.notna(info['Previous_Reading']) else 0
            
            # 1. የቀን ምርመራ
            today = datetime.now().day
            if today < int(info['StartDay']):
                msg = {'an': "📅 የመመዝገቢያ ጊዜ አልደረሰም።", 'or': "📅 Yinnaan galmee hin geenye.", 'en': "📅 Not registration time."}
                bot.send_message(cid, msg[lang])
                return

            # 2. የንባብ ምርመራ
            if present < prev:
                err = {'an': "⚠️ ስህተት፡ ንባቡ ካለፈው ያንሳል።", 'or': "⚠️ Dogoggora: Lakkoofsi kan duraa gadi.", 'en': "⚠️ Error: Reading is lower."}
                bot.send_message(cid, err[lang])
            else:
                kwh = present - prev
                bill = round((kwh * 0.4735), 2) # ታሪፉን እዚህ ያስተካክሉ
                res = {
                    'an': f"✅ የክፍያ መረጃ\nስም: {info['Customer Name']}\nየአሁኑ ንባብ: {present}\nክፍያ: {bill} ብር\nየመጨረሻ ቀን: {info['Due Date']}\n\n🔄 ሌላ ለመፈለግ /start ይጫኑ",
                    'or': f"✅ Odeeffannoo Kaffaltii\nMaqaa: {info['Customer Name']}\nMiitara Ammaa: {present}\nKaffaltii: {bill} ETB\nGuyyaa Dhumaa: {info['Due Date']}\n\n🔄 Nama biraa barbaaduuf /start tuqaa",
                    'en': f"✅ Bill Info\nName: {info['Customer Name']}\nReading: {present}\nBill: {bill} ETB\nDue Date: {info['Due Date']}\n\n🔄 To search again /start"
                }
                bot.send_message(cid, res[lang])
                user_state[cid]['s'] = 'done'
        except Exception as e:
            bot.send_message(cid, "⚠️ Error!")

bot.infinity_polling()
