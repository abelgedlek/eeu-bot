import os
import time
from datetime import datetime
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import openpyxl
from openpyxl.utils import get_column_letter

# 🔑 የተሰጡ ትክክለኛ መረጃዎች
API_TOKEN = '9053511509:AAHGpqDMiUFBvC2NHOQBMSn04egn0Vam9mo'
ADMIN_IDS = [6428627869]  # አድሚን ID
GROUP_CHAT_ID = -1003890530195  # የግሩፕ ID

bot = telebot.TeleBot(API_TOKEN)

MEMBERS = {
    1111111: {
        "full_name": "አበበ ከበደ",
        "employer_id": "1640445",
        "username": "@abebe12",
        "phone": "0911223344",
        "account": "1000223344556"
    }
}

paid_members = set()
contribution_amount = 500  

emergency_campaigns = {
    "active": False,
    "amount": 0,
    "deadline_day": 0,
    "reason": "",
    "paid_members": set()
}

@bot.message_handler(commands=['addmember'])
def add_new_member(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split(maxsplit=6)
        if len(parts) < 7:
            bot.reply_to(message, "⚠️ አጠቃቀም: `/addmember [ID] [ሙሉ ስም] [EEU_ID] [Username] [Phone] [Account]`", parse_mode="Markdown")
            return
        target_id = int(parts[1])
        MEMBERS[target_id] = {
            "full_name": parts[2], "employer_id": parts[3],
            "username": parts[4], "phone": parts[5], "account": parts[6]
        }
        bot.reply_to(message, f"✅ ተመዝግቧል: **{parts[2]}** (EEU ID: `{parts[3]}`)", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ ስህተት: {e}")

@bot.message_handler(commands=['delmember'])
def delete_member(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        target_id = int(message.text.split()[1])
        if target_id in MEMBERS:
            name = MEMBERS[target_id]['full_name']
            del MEMBERS[target_id]
            bot.reply_to(message, f"🗑 **{name}** ከዝርዝር ተሰርዟል።", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ ID አልተገኘምም።")
    except:
        bot.reply_to(message, "⚠️ አጠቃቀም: `/delmember [Telegram_ID]`", parse_mode="Markdown")

@bot.message_handler(commands=['listmembers'])
def list_members(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not MEMBERS:
        bot.reply_to(message, "⚠️ እስካሁን የተመዘገበ አባል የለም።")
        return
    text = f"📋 **የአባላት ዝርዝር ({len(MEMBERS)} አባላት):**\n\n"
    for i, (uid, info) in enumerate(MEMBERS.items(), 1):
        text += f"{i}. `{info['full_name']}` | EEU: `{info['employer_id']}`\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['setamount'])
def set_contribution_amount(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    global contribution_amount
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, f"⚠️ አሁን ያለው መጠን: `{contribution_amount} ብር`\nለመቀየር: `/setamount [መጠን]`", parse_mode="Markdown")
            return
        contribution_amount = float(parts[1])
        bot.reply_to(message, f"✅ አዲሱ ወርሃዊ መዋጮ መጠን: `✨ {contribution_amount} ብር ✨` ሆኗል።", parse_mode="Markdown")
        bot.send_message(GROUP_CHAT_ID, f"📢 **ማስታወሻ:** የዚህ ወር መዋጮ መጠን ወደ **{contribution_amount} ብር** ተስተካክሏል።", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ ስህተት: {e}")

@bot.message_handler(commands=['addemergency'])
def create_emergency_campaign(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    global emergency_campaigns
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            bot.reply_to(message, "⚠️ አጠቃቀም: `/addemergency [መጠን] [የቀን_ገደብ] [ምክንያት]`", parse_mode="Markdown")
            return
        amount = float(parts[1])
        deadline = int(parts[2])
        reason = parts[3]
        emergency_campaigns = {
            "active": True, "amount": amount,
            "deadline_day": deadline, "reason": reason, "paid_members": set()
        }
        bot.reply_to(message, f"✅ ድንገተኛ መዋጮ ተከፈተ!\n💰 መጠን: `{amount} ብር`\n📌 ምክንያት: `{reason}`", parse_mode="Markdown")
        bot.send_message(GROUP_CHAT_ID, f"🚨 **አስቸኳይ መዋጮ ማስታወሻ**\n📌 ምክንያት: {reason}\n💰 መጠን: `{amount} ብር`\n⏳ እስከ ቀን `{deadline}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ ስህተት: {e}")

@bot.message_handler(commands=['stopemergency'])
def stop_emergency_campaign(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    global emergency_campaigns
    emergency_campaigns["active"] = False
    bot.reply_to(message, "🛑 የድንገተኛ መዋጮ ፕሮግራም ተዘግቷል።", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    user_id = message.from_user.id
    if user_id not in MEMBERS:
        return

    current_day = datetime.now().day
    if not (1 <= current_day <= 5) and not emergency_campaigns["active"]:
        bot.reply_to(message, "⚠️ **ማሳሰቢያ:** የመዋጮ ጊዜው ከቀን 1 እስከ 5 ብቻ ነው።")
        return

    if user_id in paid_members:
        bot.reply_to(message, "✨ የእርስዎ ወርሃዊ መዋጮ ቀድሞ ተረጋግጧል።")
        return

    member_info = MEMBERS[user_id]
    file_id = message.photo[-1].file_id
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 (አረጋግጥ)", callback_data=f"app_{user_id}"),
        InlineKeyboardButton("❌ 𝙍𝙚𝙟𝙚𝙘𝙩 (ውድቅ አድርግ)", callback_data=f"rej_{user_id}")
    )
    
    caption = (
        f"╔══════════════════════════╗\n"
        f"   🔍 **NEW PAYMENT SUBMISSION** 🔍\n"
        f"╚══════════════════════════╝\n\n"
        f"👤 **ሙሉ ስም:** `{member_info['full_name']}`\n"
        f"🆔 **EEU ID:** `{member_info['employer_id']}`\n"
        f"📱 **ስልክ:** `{member_info['phone']}`\n"
        f"🏦 **አካውንት:** `{member_info['account']}`"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(admin_id, file_id, caption=caption, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            print(f"Could not send to admin {admin_id}: {e}")

    bot.reply_to(message, f"✨ ደረሰኝዎ ለአድሚኖች ተልኳል። ሲረጋገጥ እናሳውቅዎታለን። 🙏")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    data = call.data
    if call.from_user.id not in ADMIN_IDS:
        return

    action, user_id_str = data.split('_')
    user_id = int(user_id_str)
    member_info = MEMBERS.get(user_id, {})
    user_name = member_info.get("full_name", "አባል")

    if action == 'app':
        paid_members.add(user_id)
        bot.answer_callback_query(call.id, "ክፍያው ጸድቋል!")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                 caption=f"✅ **APPROVED** by Admin\n\n👤 {user_name}", parse_mode="Markdown")
        
        bot.send_message(user_id, f"🎉 የ{datetime.now().strftime('%B')} ወር መዋጮ ክፍያዎ ጸድቋል! እናመሰግናለን። 🌺", parse_mode="Markdown")
        bot.send_message(GROUP_CHAT_ID, f"✨ **{user_name}** (`{member_info.get('employer_id')}`) የዚህን ወር መዋጮ አጠናቋል! 🙏", parse_mode="Markdown")

    elif action == 'rej':
        bot.answer_callback_query(call.id, "ክፍያው ውድቅ ተደርጓል!")
        bot.send_message(user_id, "❌ የላኩት ስሊፕ ውድቅ ተደርጓል፤ እባክዎ እንደገና ይላኩ።")

def generate_excel_report():
    file_name = f"EEU_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"
    
    headers = ["ተ.ቁ", "ሙሉ ስም", "EEU ID", "ስልክ", "ሁኔታ", "መጠን"]
    for col_idx, h in enumerate(headers, start=1):
        ws.cell(row=1, column=col_idx, value=h)

    row = 2
    for idx, (uid, info) in enumerate(MEMBERS.items(), start=1):
        status = "Paid" if uid in paid_members else "Pending"
        ws.cell(row=row, column=1, value=idx)
        ws.cell(row=row, column=2, value=info["full_name"])
        ws.cell(row=row, column=3, value=info["employer_id"])
        ws.cell(row=row, column=4, value=info["phone"])
        ws.cell(row=row, column=5, value=status)
        ws.cell(row=row, column=6, value=contribution_amount if status=="Paid" else 0)
        row += 1

    wb.save(file_name)
    return file_name

def background_scheduler():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                path = generate_excel_report()
                with open(path, 'rb') as doc:
                    for admin_id in ADMIN_IDS:
                        bot.send_document(admin_id, doc, caption="📊 **የዕለቱ አውቶማቲክ Excel ሪፖርት**")
                os.remove(path)
            except Exception as e:
                print(e)
            time.sleep(60)
        time.sleep(30)

Thread(target=background_scheduler, daemon=True).start()

print("EEU Bot with your exact credentials is running 24/7...")
bot.infinity_polling()
