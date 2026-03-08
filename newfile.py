import telebot
import pandas as pd
from datetime import datetime

# ቦትህንና አንተን የሚያገናኝ መለያ
TOKEN = "7622239132:AAHlyRwTfYB4A4QUbX1xJWfqcHPGXLOPs5U"
ADMIN_ID = "8542308552"

bot = telebot.TeleBot(TOKEN)

def load_data():
    return pd.read_excel("data.xlsx")

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = {}
    text = "እንኳን ደህና መጡ! / Baga nagaan dhuftan! / Welcome!\n\nእባክዎ ቋንቋ ይምረጡ / Maaloo afaan filadhaa / Please choose a language."
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='am'),
               telebot.types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data='or'),
               telebot.types.InlineKeyboardButton("English 🇬🇧", callback_data='en'))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def lang_set(call):
    user_state[call.message.chat.id] = {'l': call.data, 's': 'acc'}
    msg = {
        'am': "ክቡር ደንበኛችን እባክዎ የኮንትራት አካውንት ቁጥርዎን ያስገቡ።",
        'or': "Kabajamaa maamil keenya, maaloo lakkoofsa herrega keessanii galchaa.",
        'en': "Our honored customer, please enter your contract account number."
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
                'am': f"ሰላም {row['Customer Name']}! እባክዎ አሁን በቆጣሪዎ ላይ የሚታየውን ንባብ በቁጥር ብቻ ይላኩ። 📸",
                'or': f"Akkam {row['Customer Name']}! Maaloo lakkoofsa miitaraa ammaa galchaa. 📸",
                'en': f"Hello {row['Customer Name']}! Please send the current meter reading in numbers. 📸"
            }
            bot.send_message(cid, read_msg[lang])
        else:
            err = {'am': "❌ አካውንቱ አልተገኘም", 'or': "❌ Herregni hin argamne", 'en': "❌ Account not found"}
            bot.send_message(cid, err[lang])

    elif st == 'read':
        info = user_state[cid]['i']
        try:
            present = int(m.text)
            # የድሮ ንባብ ከሌለ 0 ይውሰድ
            prev = info['Previous_Reading'] if pd.notna(info['Previous_Reading']) else 0
            
            # የቀን ቁጥጥር
            today = datetime.now().day
            if today < int(info['StartDay']):
                msg = {'am': "⚠️ የንባብ ጊዜ ገና አልደረሰም።", 'or': "⚠️ Yinnaan galmee hin geenye.", 'en': "⚠️ Not registration date."}
                bot.send_message(cid, msg[lang])
                return

            if present < prev:
                bot.send_message(cid, "⚠️ ስህተት፡ ንባቡ ከበፊቱ ያነሰ ሊሆን አይችልም!")
            else:
                kwh = present - prev
                bill = round((kwh * 0.4735), 2) # በታሪፍ መሰረት የተቀየረ
                res = {
                    'am': f"✅ ተመዝግቧል!\nስም: {info['Customer Name']}\nንባብ: {present}\nሂሳብ: {bill} ብር\n\nለወደኋላ መመለስ /start ይጫኑ",
                    'or': f"✅ Galmeeffameera!\nMaqaa: {info['Customer Name']}\nMiitara: {present}\nKaffaltii: {bill} ETB",
                    'en': f"✅ Recorded!\nName: {info['Customer Name']}\nReading: {present}\nBill: {bill} ETB"
                }
                bot.send_message(cid, res[lang])
                # ለአንተ (ለAdmin) መረጃውን ይልካል
                bot.send_message(ADMIN_ID, f"🔔 አዲስ ንባብ ገብቷል!\n👤 ደንበኛ: {info['Customer Name']}\n🔢 ንባብ: {present}\n💰 ብር: {bill} ETB")
                user_state[cid]['s'] = 'done'
        except:
            bot.send_message(cid, "⚠️ እባክዎ ቁጥር ብቻ ያስገቡ!")

bot.infinity_polling()
