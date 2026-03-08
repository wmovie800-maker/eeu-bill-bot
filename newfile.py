import telebot
import pandas as pd
from datetime import datetime
from telebot import types

# የአንተ ትክክለኛ መረጃዎች እዚህ ተሞልተዋል
TOKEN = "7622239132:AAHlyRwTfYB4A4QUbX1xJWfqcHPGXLOPs5U"
ADMIN_ID = "8542308552"

bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        # የኤክሴል ፋይሉ ስም 'customers.xlsx' መሆኑን አረጋግጥ
        return pd.read_excel('customers.xlsx')
    except:
        return None

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = {}
    text = "እንኳን ደህና መጡ! / Baga nagaan dhuftan! / Welcome!\nእባክዎ ቋንቋ ይምረጡ / Maaloo afaan filadhaa."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='am'),
               types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data='or'),
               types.InlineKeyboardButton("English 🇬🇧", callback_data='en'))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def lang_set(call):
    user_state[call.message.chat.id] = {'l': call.data, 's': 'acc'}
    msg = {'am': "የኮንትራት አካውንት ቁጥርዎን ያስገቡ።", 'or': "Lakkoofsa herrega keessanii galchaa.", 'en': "Enter contract account."}
    bot.send_message(call.message.chat.id, msg[call.data])

@bot.message_handler(func=lambda m: m.text.isdigit())
def handle_digits(m):
    cid = m.chat.id
    if cid not in user_state or 'l' not in user_state[cid]: return
    lang, st, df = user_state[cid]['l'], user_state[cid]['s'], load_data()
    if df is None: return

    if st == 'acc':
        acc_num = int(m.text)
        cust = df[df['Contract Account'] == acc_num]
        if not cust.empty:
            row = cust.iloc[0]
            user_state[cid].update({'s': 'read', 'i': row})
            bot.send_message(cid, f"ሰላም {row['Customer Name']}! ንባቡን ይላኩ።")
        else:
            bot.send_message(cid, "❌ አካውንቱ አልተገኘም")

    elif st == 'read':
        info = user_state[cid]['i']
        try:
            present = int(m.text)
            prev = info['Previous_Reading'] if pd.notna(info['Previous_Reading']) else 0
            
            # የቀን ምርመራ
            if datetime.now().day < int(info['StartDay']):
                bot.send_message(cid, f"📅 ንባብ የሚመዘገበው ከቀን {info['StartDay']} ጀምሮ ነው።")
                return

            if present < prev:
                bot.send_message(cid, f"⚠️ ስህተት፡ ንባቡ ከበፊቱ ({prev}) ያንሳል።")
            else:
                bill = round(((present - prev) * 0.4735), 2)
                bot.send_message(cid, f"✅ ተመዝግቧል!\nሂሳብ: {bill} ብር\n\nለወደኋላ /start")
                # መረጃውን ለአንተ መላክ
                bot.send_message(ADMIN_ID, f"🔔 አዲስ ንባብ፡ {info['Customer Name']}\n🔢 ንባብ፡ {present}\n💰 ሂሳብ፡ {bill} ETB")
                user_state[cid]['s'] = 'done'
        except:
            bot.send_message(cid, "⚠️ ቁጥር ብቻ!")

bot.infinity_polling()
