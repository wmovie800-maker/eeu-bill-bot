import telebot
import pandas as pd
from datetime import datetime
from telebot import types

# ቦት ቶክንህን እዚህ አስገባ
bot = telebot.TeleBot("YOUR_BOT_TOKEN_HERE")

def load_data():
    try:
        # የፋይሉ ስም ከ GitHub ጋር አንድ መሆኑን አረጋግጥ
        return pd.read_excel('customers.xlsx')
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return None

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state[message.chat.id] = {}
    text = "እንኳን ደህና መጡ! / Baga nagaan dhuftan! / Welcome!\nእባክዎ ቋንቋ ይምረጡ / Maaloo afaan filadhaa."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='an'),
               types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data='or'),
               types.InlineKeyboardButton("English 🇬🇧", callback_data='en'))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def lang_set(call):
    # ቋንቋውን እና ቀጣዩን ደረጃ (acc) መመዝገብ
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
    if cid not in user_state or 'l' not in user_state[cid]:
        return
    
    lang = user_state[cid]['l']
    st = user_state[cid]['s']
    df = load_data()
    
    if df is None:
        bot.send_message(cid, "Excel file error!")
        return

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
            
            # 1. የቀን ምርመራ (StartDay ን ማረጋገጥ)
            today = datetime.now().day
            if today < int(info['StartDay']):
                msg = {
                    'an': f"📅 የመመዝገቢያ ጊዜ አልደረሰም። ቀኑ ገና {info['StartDay']} ነው።",
                    'or': f"📅 Yinnaan galmee hin geenye. Guyyaan isaa {info['StartDay']} dha.",
                    'en': f"📅 Not registration time. It starts on day {info['StartDay']}."
                }
                bot.send_message(cid, msg[lang])
                return

            # 2. የንባብ ምርመራ (ከድሮው መብለጥ አለበት)
            if present < prev:
                err = {
                    'an': f"⚠️ ስህተት፡ ንባቡ ካለፈው ({prev}) ያንሳል።",
                    'or': f"⚠️ Dogoggora: Lakkoofsi kan duraa ({prev}) gadi.",
                    'en': f"⚠️ Error: Reading is lower than previous ({prev})."
                }
                bot.send_message(cid, err[lang])
            else:
                kwh = present - prev
                bill = round((kwh * 0.4735), 2) # የታሪፍ ስሌት
                res = {
                    'an': f"✅ የክፍያ መረጃ\nስም: {info['Customer Name']}\nንባብ: {present}\nክፍያ: {bill} ብር\nመክፈያ ቀን: {info['Due Date']}\n\n🔄 ሌላ ለመፈለግ /start ይጫኑ",
                    'or': f"✅ Odeeffannoo Kaffaltii\nMaqaa: {info['Customer Name']}\nMiitara: {present}\nKaffaltii: {bill} ETB\nGuyyaa: {info['Due Date']}\n\n🔄 Deebitee barbaaduuf /start tuqaa",
                    'en': f"✅ Bill Info\nName: {info['Customer Name']}\nReading: {present}\nBill: {bill} ETB\nDue Date: {info['Due Date']}\n\n🔄 Search again /start"
                }
                bot.send_message(cid, res[lang])
                user_state[cid]['s'] = 'done' # ስራው ተጠናቀቀ
        except Exception:
            bot.send_message(cid, "⚠️ Error!")

bot.infinity_polling()
