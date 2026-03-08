import telebot
import pandas as pd
from telebot import types
import os

# የቦትህ መለያ ቁጥር (Token)
TOKEN = "7622239132:AAHlyRwTfYB4A4QUbX1xJWfqcHPGXLOPs5U"
# ያንተ የቴሌግራም መለያ ቁጥር (Admin ID)
ADMIN_ID = "8542308552"

bot = telebot.TeleBot(TOKEN)

def load_data():
    # በፎልደሩ ውስጥ ያለን ማንኛውንም የኤክሴል ፋይል ይፈልጋል
    files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not files:
        print("❌ ኤክሴል ፋይል አልተገኘም!")
        return None
    try:
        # የመጀመሪያውን ያገኘውን የኤክሴል ፋይል ያነባል
        df = pd.read_excel(files[0])
        # በኮለም ስሞች ዙሪያ ያሉ ባዶ ቦታዎችን ያጠፋል
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"❌ ስህተት፡ {e}")
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
    msg = {
        'am': "እባክዎ የኮንትራት አካውንት ቁጥርዎን ያስገቡ፡",
        'or': "Maaloo lakkoofsa herregaa keessanii galchaa:",
        'en': "Please enter your contract account number:"
    }
    bot.send_message(call.message.chat.id, msg[call.data])

@bot.message_handler(func=lambda m: m.text.isdigit())
def handle_digits(m):
    cid = m.chat.id
    if cid not in user_state or 'l' not in user_state[cid]:
        return

    lang = user_state[cid]['l']
    state = user_state[cid]['s']
    df = load_data()

    if df is None:
        bot.send_message(cid, "❌ የደንበኞች መረጃ ፋይል አልተገኘም! እባክዎ አስተዳዳሪውን ያነጋግሩ።")
        return

    # 1. የአካውንት ቁጥር ፍለጋ ደረጃ
    if state == 'acc':
        acc_num = int(m.text)
        # በምስል 5692 ላይ ባለው ስም 'Contract Account' ተብሎ ይፈለጋል
        try:
            cust = df[df['Contract Account'] == acc_num]
            if not cust.empty:
                row = cust.iloc[0]
                user_state[cid].update({'s': 'read', 'i': row})
                
                name = row['Customer Name']
                msg = {
                    'am': f"ሰላም {name}! አሁን በቆጣሪዎ ላይ የሚታየውን የአሁኑን ንባብ ቁጥር ብቻ ይላኩ።",
                    'or': f"Akkam {name}! Amma lakkoofsa herregaa qofaa ergaa.",
                    'en': f"Hello {name}! Please send only your current meter reading."
                }
                bot.send_message(cid, msg[lang])
            else:
                msg = {'am': "❌ ያስገቡት አካውንት አልተገኘም!", 'or': "❌ Lakkoofsi galchitan hin jiru!", 'en': "❌ Account not found!"}
                bot.send_message(cid, msg[lang])
        except Exception as e:
            bot.send_message(cid, "⚠️ በኤክሴል ፋይሉ ላይ 'Contract Account' የሚል ኮለም አልተገኘም!")

    # 2. ንባብ መቀበልና ሂሳብ ማሳየት
    elif state == 'read':
        info = user_state[cid]['i']
        try:
            present = int(m.text)
            # የድሮውን ንባብ ከ 'Previous_Reading' ኮለም ያነባል
            prev = float(info['Previous_Reading']) if pd.notna(info['Previous_Reading']) else 0
            
            diff = present - prev
            if diff < 0:
                msg = {'am': "⚠️ ስህተት፡ የአሁኑ ንባብ ከበፊቱ ሊያንስ አይችልም!", 'or': "⚠️ Dogoggora!", 'en': "⚠️ Current reading cannot be less than previous!"}
                bot.send_message(cid, msg[lang])
                return
            
            # የታሪፍ ስሌት (ልዩነት * 0.4735)
            bill = round((diff * 0.4735), 2)
            
            res_msg = {
                'am': f"✅ መረጃው ተመዝግቧል!\n🔢 የበፊቱ ንባብ: {prev}\n🔢 የአሁኑ ንባብ: {present}\n💰 የወር ሂሳብ: {bill} ብር",
                'or': f"✅ Galmeeffameera!\n🔢 Dubbisa duraa: {prev}\n🔢 Dubbisa ammaa: {present}\n💰 Kafaltii: {bill} ETB",
                'en': f"✅ Recorded!\n🔢 Previous: {prev}\n🔢 Current: {present}\n💰 Monthly Bill: {bill} ETB"
            }
            bot.send_message(cid, res_msg[lang])
            
            # ለአስተዳዳሪው መረጃ መላክ
            bot.send_message(ADMIN_ID, f"🔔 አዲስ ንባብ ተልኳል\n👤 ደንበኛ: {info['Customer Name']}\n🆔 አካውንት: {info['Contract Account']}\n🔢 ንባብ: {present}\n💰 ብር: {bill} ETB")
            user_state[cid]['s'] = 'done'
        except:
            bot.send_message(cid, "⚠️ እባክዎ ቁጥር ብቻ ያስገቡ!")

bot.infinity_polling()
