import telebot
import pandas as pd
from datetime import datetime
from telebot import types
import os

# የቦትህ መለያ ቁጥር (Token)
TOKEN = "7622239132:AAHlyRwTfYB4A4QUbX1xJWfqcHPGXLOPs5U"
# ያንተ የቴሌግራም መለያ ቁጥር (Admin ID)
ADMIN_ID = "8542308552"

bot = telebot.TeleBot(TOKEN)

def load_data():
    # በ GitHub ፎልደር ውስጥ ያለን የኤክሴል ፋይል ይፈልጋል
    files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not files:
        return None
    try:
        df = pd.read_excel(files[0])
        # በኤክሴል ኮለም ስሞች ላይ ያሉ አላስፈላጊ ክፍተቶችን ያስተካክላል
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='am'),
               types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data='or'),
               types.InlineKeyboardButton("English 🇬🇧", callback_data='en'))
    bot.send_message(message.chat.id, "እንኳን ደህና መጡ! / Baga nagaan dhuftan!\nእባክዎ ቋንቋ ይምረጡ / Maaloo afaan filadhaa.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def lang_set(call):
    user_state[call.message.chat.id] = {'l': call.data, 's': 'acc'}
    msg = {'am': "የኮንትራት አካውንት ቁጥር ያስገቡ", 
           'or': "Lakkoofsa herregaa keessanii galchaa", 
           'en': "Enter contract account number"}
    bot.send_message(call.message.chat.id, msg[call.data])

@bot.message_handler(func=lambda m: m.text.isdigit())
def handle_digits(m):
    cid = m.chat.id
    if cid not in user_state or 'l' not in user_state[cid]: return
    lang, st, df = user_state[cid]['l'], user_state[cid]['s'], load_data()
    
    if df is None:
        bot.send_message(cid, "❌ የደንበኞች መረጃ ፋይል አልተገኘም!")
        return

    if st == 'acc':
        acc_num = int(m.text)
        # 'Contract Account' የሚለው ስም ከኤክሴልህ ጋር መመሳሰሉን ያረጋግጣል
        cust = df[df['Contract Account'] == acc_num]
        if not cust.empty:
            row = cust.iloc[0]
            user_state[cid].update({'s': 'read', 'i': row})
            bot.send_message(cid, f"ሰላም {row['Customer Name']}! አሁን በቆጣሪዎ ላይ ያለውን ንባብ ቁጥር ብቻ ይላኩ።")
        else:
            bot.send_message(cid, "❌ ይቅርታ፣ ያስገቡት አካውንት አልተገኘም!")

    elif st == 'read':
        info = user_state[cid]['i']
        try:
            present = int(m.text)
            # የድሮውን ንባብ ከኤክሴል ያነባል
            prev = float(info['Previous_Reading']) if pd.notna(info['Previous_Reading']) else 0
            
            diff = present - prev
            if diff < 0:
                bot.send_message(cid, "⚠️ ስህተት፡ የአሁኑ ንባብ ከበፊቱ ሊያንስ አይችልም!")
                return
                
            # የሂሳብ ቀመር (ልዩነት * ታሪፍ)
            bill = round((diff * 0.4735), 2)
            bot.send_message(cid, f"✅ ተመዝግቧል!\nየበፊቱ ንባብ: {prev}\nየአሁኑ ንባብ: {present}\nየወር ሂሳብ: {bill} ብር")
            
            # ለአስተዳዳሪው መረጃ ይልካል
            bot.send_message(ADMIN_ID, f"🔔 አዲስ ንባብ ተልኳል\n👤 ደንበኛ፡ {info['Customer Name']}\n🔢 ንባብ፡ {present}\n💰 ሂሳብ፡ {bill} ETB")
            user_state[cid]['s'] = 'done'
        except Exception as e:
            bot.send_message(cid, "⚠️ ስህተት ተፈጥሯል! እባክዎ ቁጥር ብቻ ያስገቡ።")

bot.infinity_polling()
