import pandas as pd
import telebot
from telebot import types
import time

# 1. ቦቱን ማገናኘት
API_TOKEN = '7622239132:AAHlyRwTfYB4A4QUbX1xJWfqcHPGXLOPs5U'
ADMIN_ID = '8542308552' 
bot = telebot.TeleBot(API_TOKEN)

# ዳታውን የማንበቢያ ተግባር (Excel Error እንዳይመጣ ተስተካክሏል)
def load_data():
    try:
        df = pd.read_excel('customers.xlsx')
        df.columns = df.columns.str.strip()
        # ቁጥሮቹ ወደ ትክክለኛ ፎርማት እንዲቀየሩ ማድረግ
        df['Contract Account'] = pd.to_numeric(df['Contract Account'], errors='coerce')
        return df
    except Exception as e:
        print(f"Excel Error: {e}")
        return None

df = load_data()
user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    # የቆዩ ቻቶችን ለማጽዳት
    user_state[message.chat.id] = {}
    
    text = "እንኳን ደህና መጡ! / Baga nagaan dhuftan! / Welcome!\n\nእባክዎ ቋንቋ ይምረጡ / Maaloo afaan filadhaa / Please choose a language."
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='am'),
               types.InlineKeyboardButton("Afaan Oromoo 🌳", callback_data='or'),
               types.InlineKeyboardButton("English 🇬🇧", callback_data='en'))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def lang_set(call):
    user_state[call.message.chat.id] = {'l': call.data, 's': 'acc'}
    msg = {
        'am': "ክቡር ደንበኛችን፣ እባክዎ የኮንትራት አካውንት ቁጥርዎን ያስገቡ።",
        'or': "Kabajamaa maamil keenya, maaloo lakkoofsa herrega keessanii galchaa.",
        'en': "Our honored customer, please enter your contract account number."
    }
    bot.send_message(call.message.chat.id, msg[call.data])

@bot.message_handler(func=lambda m: m.text.isdigit())
def handle_digits(m):
    cid = m.chat.id
    if cid not in user_state or 'l' not in user_state[cid]:
        return

    st = user_state[cid]
    lang = st['l']
    global df
    if df is None: df = load_data()

    if st['s'] == 'acc':
        acc_num = int(m.text)
        cust = df[df['Contract Account'] == acc_num]
        
        if not cust.empty:
            row = cust.iloc[0]
            name = row['Customer Name']
            user_state[cid].update({'s': 'read', 'i': row})
            read_msg = {
                'am': f"ሰላም {name}! እባክዎ የአሁኑን የቆጣሪ ንባብ በቁጥር ብቻ ይላኩ። 📸",
                'or': f"Akkam {name}! Maaloo lakkoofsa miitaraa ammaa galchaa. 📸",
                'en': f"Hello {name}! Please send the current meter reading in numbers. 📸"
            }
            bot.send_message(cid, read_msg[lang])
        else:
            err = {'am': "❌ አካውንቱ አልተገኘም", 'or': "❌ Herregni hin argamne", 'en': "❌ Account not found"}
            bot.send_message(cid, err[lang])

    elif st['s'] == 'read':
        info = st['i']
        try:
            present = int(m.text)
            prev = info['Previous_Reading'] 
            kwh = present - prev
            bill = round((kwh * 2.92 + 131.7) * 1.15, 2)
            
            name = info['Customer Name']
            start_d = info['StartDay']
            end_d = info['EndDay']

            res_texts = {
                'am': (f"✅ **የኢትዮጵያ ኤሌክትሪክ አገልግሎት**\n\n"
                       f"ክቡር ደንበኛችን {name}፣ የወር ሂሳብዎ {bill} ETB ነው። "
                       f"እባክዎ ከቀን {start_d} እስከ ቀን {end_d} ባለው ጊዜ ውስጥ ክፍያዎን እንዲፈጽሙ በትህትና እናሳስባለን።"),
                'or': (f"✅ **Tajaajila Elektriika Itoophiyaa**\n\n"
                       f"Kabajamaa maamil keenya {name}, kaffaltiin keessan ETB {bill} dha."),
                'en': (f"✅ **Ethiopian Electric Utility**\n\n"
                       f"Our Honored Customer {name}, your monthly bill is {bill} ETB.")
            }
            
            bot.send_message(cid, res_texts[lang], parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"🔔 **ሪፖርት**\n👤 {name}\n💰 {bill} ETB")
            user_state[cid]['s'] = 'done'
        except:
            bot.send_message(cid, "⚠️ ስህተት ተፈጥሯል፣ እባክዎ ቁጥር ብቻ ያስገቡ።")

# 🔄 ዋናው ማስተካከያ፦ የቆዩ መልእክቶችን Skip እንዲያደርግና እንዳይጨናነቅ
print("Bot is starting...")
bot.infinity_polling(skip_pending=True)
