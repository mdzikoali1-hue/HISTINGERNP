import os
import json
import time
import shutil
import subprocess
import threading
import zipfile
import telebot
from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ================= কনফিগারেশন =================
BOT_TOKEN = "9210454052:AAEiVPLc3AY6uPohSILfHZeT-1EA-HZNuco"
ADMIN_ID = 7471940190
PROJECTS_DIR = "hosted_projects"
DB_FILE = "hosting_db.json"

os.makedirs(PROJECTS_DIR, exist_ok=True)
bot = telebot.TeleBot(BOT_TOKEN)

# রানিং প্রসেস ট্র্যাক রাখার ডিকশনারি
running_processes = {}
user_states = {}


# ================= ডাটাবেজ ফাংশন =================
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "projects": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 0}
        save_db(db)
    return db["users"][uid]


# ================= মেইন কিবোর্ড মেনু =================
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("➕ New Project"),
        KeyboardButton("📁 My Projects"),
        KeyboardButton("💰 Balance"),
        KeyboardButton("💎 Premium Hosting Plan"),
        KeyboardButton("🛒 Buy Bot Code"),
        KeyboardButton("🆘 Support / Admin"),
    )
    return markup


# ================= স্টার্ট ও কমান্ড হ্যান্ডলার =================
@bot.message_handler(commands=["start"])
def start_cmd(message):
    get_user(message.from_user.id)
    user_states.pop(message.from_user.id, None)
    text = f"👋 স্বাগতম **{message.from_user.first_name}**!\n\nআমাদের টেলিগ্রাম বট ও ওয়েবসাইট হোস্টিং প্যানেলে আপনাকে স্বাগতম। নিচের মেনু থেকে আপনার প্রয়োজনীয় অপশন বেছে নিন:"
    bot.send_message(
        message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu()
    )


# অ্যাডমিন কমান্ড: ব্যালেন্স যোগ করার জন্য (/addbal user_id amount)
@bot.message_handler(commands=["addbal"])
def add_balance_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_id, amount = message.text.split()
        amount = float(amount)
        db = load_db()
        if target_id not in db["users"]:
            db["users"][target_id] = {"balance": 0}
        db["users"][target_id]["balance"] += amount
        save_db(db)
        bot.reply_to(
            message, f"✅ ইউজার `{target_id}` এর একাউন্টে `{amount} TK` যোগ করা হয়েছে!"
        )
        bot.send_message(
            int(target_id),
            f"🎉 অ্যাডমিন আপনার একাউন্টে **{amount} TK** যোগ করেছেন!",
            parse_mode="Markdown",
        )
    except Exception:
        bot.reply_to(message, "❌ সঠিক নিয়ম: `/addbal 123456789 30`", parse_mode="Markdown")


# ================= মেনু বাটন অ্যাকশন =================
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def check_balance(message):
    user = get_user(message.from_user.id)
    text = f"👤 **User ID:** `{message.from_user.id}`\n💳 **Current Balance:** `{user['balance']} TK`\n\nব্যালেন্স রিচার্জ করতে @Mahim55699 এর সাথে যোগাযোগ করুন।"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "💎 Premium Hosting Plan")
def hosting_plan(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🛒 Buy 7 Days Plan (30 TK)", callback_data="buy_plan_7d"
        )
    )
    text = f"💎 **Premium Hosting Plan**\n\n⏳ **মেয়াদ:** 7 Days (৭ দিন)\n💵 **মূল্য:** 30 TK (1 CPR)\n⚡ **রিসোর্স:** 1 Core CPU / 24/7 Uptime\n\nনিচের বাটনে ক্লিক করে আপনার ব্যালেন্স দিয়ে প্ল্যানটি কিনুন অথবা অ্যাডমিনের সাথে যোগাযোগ করুন।"
    bot.send_message(
        message.chat.id, text, parse_mode="Markdown", reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == "🛒 Buy Bot Code")
def buy_code(message):
    text = f"🛒 **Buy Bot Code**\n\nযেকোনো কাস্টম টেলিগ্রাম বট বা সোর্স কোড কিনতে যোগাযোগ করুন:\n👉 @Mahim55699"
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: m.text == "🆘 Support / Admin")
def support_admin(message):
    text = f"🆘 **Support / Admin**\n\nযেকোনো সমস্যা বা পেমেন্টের জন্য মেসেজ দিন:\n👉 @Mahim55699"
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
    )


# ================= NEW PROJECT তৈরি =================
@bot.message_handler(func=lambda m: m.text == "➕ New Project")
def new_project_start(message):
    user = get_user(message.from_user.id)
    if user["balance"] < 30:
        bot.send_message(
            message.chat.id,
            "❌ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই!\nনতুন প্রজেক্ট তৈরি করতে কমপক্ষে **30 TK** (7 Days Plan) প্রয়োজন।\n\nযোগাযোগ: @Mahim55699",
            parse_mode="Markdown",
        )
        return

    user_states[message.from_user.id] = {"step": "awaiting_project_name"}
    bot.send_message(
        message.chat.id,
        "📝 আপনার নতুন প্রজেক্টের একটি **নাম** লিখুন (যেমন: `my_bot`):\n*(প্রজেক্ট তৈরি করলে একাউন্ট থেকে 30 TK কাটা হবে এবং ৭ দিনের মেয়াদ পাবেন)*",
        parse_mode="Markdown",
    )


# ================= MY PROJECTS লিস্ট =================
@bot.message_handler(func=lambda m: m.text == "📁 My Projects")
def my_projects(message):
    uid = str(message.from_user.id)
    db = load_db()
    user_projects = {
        k: v for k, v in db["projects"].items() if v["owner"] == uid
    }

    if not user_projects:
        bot.send_message(
            message.chat.id, "📭 আপনার কোনো প্রজেক্ট তৈরি করা নেই। `➕ New Project` থেকে তৈরি করুন."
        )
        return

    markup = InlineKeyboardMarkup(row_width=1)
    for proj_key, proj_data in user_projects.items():
        status_icon = "🟢" if proj_key in running_processes and running_processes[proj_key].poll() is None else "🔴"
        markup.add(
            InlineKeyboardButton(
                f"{status_icon} {proj_data['name']}",
                callback_data=f"manage|{proj_key}",
            )
        )

    bot.send_message(
        message.chat.id,
        "📁 **আপনার প্রজেক্টসমূহ:**\nম্যানেজ করতে যেকোনো একটিতে ক্লিক করুন:",
        parse_mode="Markdown",
        reply_markup=markup,
    )


# ================= প্রজেক্ট কন্ট্রোল প্যানেল ড্যাশবোর্ড =================
def send_project_panel(chat_id, proj_key, message_id=None):
    db = load_db()
    if proj_key not in db["projects"]:
        bot.send_message(chat_id, "❌ প্রজেক্টটি খুঁজে পাওয়া যায়নি।")
        return

    proj = db["projects"][proj_key]
    is_running = (
        proj_key in running_processes
        and running_processes[proj_key].poll() is None
    )
    status_text = "🟢 Running" if is_running else "🔴 Stopped"

    remaining_sec = proj["expires_at"] - time.time()
    days_left = max(0, round(remaining_sec / 86400, 1))

    text = f"⚙️ **Project Panel:** `{proj['name']}`\n📊 **Status:** {status_text}\n⏳ **Active Remaining:** `{days_left} Days`\n📄 **Main File:** `{proj.get('main_file', 'Not Set')}`\n\nনিচের বাটনগুলো দিয়ে প্রজেক্ট কন্ট্রোল করুন:"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📤 Upload File / Zip", callback_data=f"upload|{proj_key}"),
        InlineKeyboardButton("📂 Browse Files", callback_data=f"browse|{proj_key}"),
        InlineKeyboardButton(
            "📦 Install Package (req.txt)", callback_data=f"install|{proj_key}"
        ),
        InlineKeyboardButton("ℹ️ Project Info", callback_data=f"info|{proj_key}"),
        InlineKeyboardButton("▶️ Run All", callback_data=f"run|{proj_key}"),
        InlineKeyboardButton("⏹ Stop", callback_data=f"stop|{proj_key}"),
        InlineKeyboardButton("🖥 Live Console", callback_data=f"console|{proj_key}"),
        InlineKeyboardButton("🗑 Delete Project", callback_data=f"delete|{proj_key}"),
    )

    if message_id:
        try:
            bot.edit_message_text(
                text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup
            )
        except Exception:
            bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


# ================= ইনলাইন বাটন কলব্যাক হ্যান্ডলার =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    data = call.data

    if data == "buy_plan_7d":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "💡 প্ল্যান অ্যাক্টিভ করতে সরাসরি `➕ New Project` বাটনে ক্লিক করুন (30 TK ব্যালেন্স থাকলে অটোমেটিক ৭ দিনের প্রজেক্ট তৈরি হবে)।",
            parse_mode="Markdown",
        )
        return

    if "|" not in data:
        return

    action, proj_key = data.split("|", 1)
    db = load_db()

    if proj_key not in db["projects"]:
        bot.answer_callback_query(call.id, "❌ প্রজেক্ট পাওয়া যায়নি!", show_alert=True)
        return

    proj = db["projects"][proj_key]
    proj_path = os.path.join(PROJECTS_DIR, proj_key)

    if time.time() > proj["expires_at"] and action not in ["delete", "info"]:
        bot.answer_callback_query(
            call.id, "⚠️ আপনার এই প্রজেক্টের মেয়াদ শেষ হয়ে গেছে!", show_alert=True
        )
        return

    if action == "manage":
        bot.answer_callback_query(call.id)
        send_project_panel(call.message.chat.id, proj_key, call.message.message_id)

    elif action == "upload":
        bot.answer_callback_query(call.id)
        user_states[uid] = {"step": "awaiting_file", "proj_key": proj_key}
        bot.send_message(
            call.message.chat.id,
            f"📤 **{proj['name']}** প্রজেক্টে আপলোড করার জন্য আপনার `.py`, `requirements.txt` অথবা পুরো প্রজেক্টের `.zip` ফাইলটি সেন্ড করুন:",
            parse_mode="Markdown",
        )

    elif action == "browse":
        bot.answer_callback_query(call.id)
        all_files = []
        for root, dirs, files in os.walk(proj_path):
            for file in files:
                if file != "console.log":
                    rel_path = os.path.relpath(os.path.join(root, file), proj_path)
                    all_files.append(rel_path)

        if not all_files:
            bot.send_message(call.message.chat.id, "📂 ফোল্ডারটি একদম খালি! কোনো ফাইল আপলোড করা হয়নি।")
        else:
            file_list = "\n".join([f"📄 `{f}`" for f in all_files[:30]])
            bot.send_message(
                call.message.chat.id,
                f"📂 **Files in {proj['name']}:**\n\n{file_list}",
                parse_mode="Markdown",
            )

    elif action == "install":
        req_path = os.path.join(proj_path, "requirements.txt")
        if not os.path.exists(req_path):
            bot.answer_callback_query(
                call.id,
                "❌ প্রজেক্টে requirements.txt ফাইল পাওয়া যায়নি!",
                show_alert=True,
            )
            return
        bot.answer_callback_query(call.id, "⏳ প্যাকেজ ইনস্টল শুরু হচ্ছে...")
        msg = bot.send_message(
            call.message.chat.id, "📦 `requirements.txt` থেকে প্যাকেজ ইনস্টল হচ্ছে, অপেক্ষা করুন..."
        )

        def install_packages():
            try:
                res = subprocess.run(
                    ["pip", "install", "-r", req_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                output = res.stdout[-1000:] if res.returncode == 0 else res.stderr[-1000:]
                status_txt = "✅ **ইনস্টল সম্পন্ন!**" if res.returncode == 0 else "❌ **ইনস্টল এরর!**"
                bot.edit_message_text(
                    f"{status_txt}\n\n```\n{output}\n```",
                    call.message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown",
                )
            except Exception as e:
                bot.edit_message_text(
                    f"❌ Error: `{str(e)}`",
                    call.message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown",
                )

        threading.Thread(target=install_packages).start()

    elif action == "info":
        bot.answer_callback_query(call.id)
        rem_sec = max(0, proj["expires_at"] - time.time())
        days = int(rem_sec // 86400)
        hours = int((rem_sec % 86400) // 3600)
        exp_date = time.strftime("%Y-%m-%d %H:%M", time.localtime(proj["expires_at"]))

        info_text = f"ℹ️ **Project Information**\n\n🏷 **Name:** `{proj['name']}`\n⚡ **Plan:** 7 Days (1 Core CPU)\n⏳ **Remaining Time:** `{days} দিন {hours} ঘণ্টা`\n📅 **Expire Date:** `{exp_date}`\n🐍 **Main File:** `{proj.get('main_file', 'None')}`"
        bot.send_message(call.message.chat.id, info_text, parse_mode="Markdown")

    elif action == "run":
        main_file = proj.get("main_file")
        full_main_path = os.path.join(proj_path, main_file) if main_file else ""

        if not main_file or not os.path.exists(full_main_path):
            bot.answer_callback_query(
                call.id, "❌ কোনো রান করার মতো .py ফাইল সেট করা নেই!", show_alert=True
            )
            return

        if proj_key in running_processes and running_processes[proj_key].poll() is None:
            bot.answer_callback_query(call.id, "⚠️ প্রজেক্ট ইতিমধ্যে চলছে!", show_alert=True)
            return

        log_path = os.path.join(proj_path, "console.log")
        log_file = open(log_path, "w", encoding="utf-8")
        
        file_dir = os.path.dirname(full_main_path)
        file_base = os.path.basename(full_main_path)
        
        proc = subprocess.Popen(
            ["python", "-u", file_base],
            cwd=file_dir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        running_processes[proj_key] = proc
        bot.answer_callback_query(call.id, "▶️ প্রজেক্ট সফলভাবে রান হয়েছে!")
        send_project_panel(call.message.chat.id, proj_key, call.message.message_id)

    elif action == "stop":
        if proj_key in running_processes and running_processes[proj_key].poll() is None:
            running_processes[proj_key].terminate()
            bot.answer_callback_query(call.id, "⏹ প্রজেক্ট বন্ধ করা হয়েছে!")
        else:
            bot.answer_callback_query(call.id, "ℹ️ প্রজেক্ট আগেই বন্ধ আছে।")
        send_project_panel(call.message.chat.id, proj_key, call.message.message_id)

    elif action == "console":
        bot.answer_callback_query(call.id)
        log_path = os.path.join(proj_path, "console.log")
        is_running = (
            proj_key in running_processes
            and running_processes[proj_key].poll() is None
        )
        state_str = "🟢 RUNNING" if is_running else "🔴 STOPPED / ERROR"

        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                logs = f.read()
            logs = logs[-2500:] if logs.strip() else "No console output yet..."
        else:
            logs = "Console log is empty. Click 'Run All' first."

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔄 Refresh", callback_data=f"console|{proj_key}"),
            InlineKeyboardButton("🔙 Back Panel", callback_data=f"manage|{proj_key}"),
        )

        console_msg = f"🖥 **Live Terminal Console ({proj['name']})**\nStatus: **{state_str}**\n\n```bash\n{logs}\n```"
        try:
            bot.edit_message_text(
                console_msg,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                console_msg,
                parse_mode="Markdown",
                reply_markup=markup,
            )

    elif action == "delete":
        if proj_key in running_processes and running_processes[proj_key].poll() is None:
            running_processes[proj_key].terminate()
            del running_processes[proj_key]

        if os.path.exists(proj_path):
            shutil.rmtree(proj_path)
        del db["projects"][proj_key]
        save_db(db)

        bot.answer_callback_query(call.id, "🗑 প্রজেক্ট সফলভাবে ডিলিট করা হয়েছে!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass


# ================= ইউজার ইনপুট ও ফাইল হ্যান্ডলার =================
@bot.message_handler(content_types=["text"])
def handle_text_inputs(message):
    uid = message.from_user.id
    if uid not in user_states:
        return

    state = user_states[uid]
    if state["step"] == "awaiting_project_name":
        proj_name = "".join(c for c in message.text if c.isalnum() or c in ("_", "-"))
        if not proj_name:
            bot.send_message(message.chat.id, "❌ সঠিক নাম দিন (শুধু ইংরেজি অক্ষর ও সংখ্যা ব্যবহার করুন):")
            return

        db = load_db()
        str_uid = str(uid)
        if db["users"][str_uid]["balance"] < 30:
            bot.send_message(message.chat.id, "❌ পর্যাপ্ত ব্যালেন্স নেই!")
            user_states.pop(uid, None)
            return

        db["users"][str_uid]["balance"] -= 30
        proj_key = f"{str_uid}_{int(time.time())}"
        os.makedirs(os.path.join(PROJECTS_DIR, proj_key), exist_ok=True)

        db["projects"][proj_key] = {
            "owner": str_uid,
            "name": proj_name,
            "created_at": time.time(),
            "expires_at": time.time() + (7 * 86400),
            "main_file": None,
        }
        save_db(db)
        user_states.pop(uid, None)

        bot.send_message(
            message.chat.id,
            f"✅ **{proj_name}** প্রজেক্ট তৈরি হয়েছে! (30 TK কাটা হয়েছে, মেয়াদ ৭ দিন)",
            parse_mode="Markdown",
        )
        send_project_panel(message.chat.id, proj_key)


@bot.message_handler(content_types=["document"])
def handle_file_upload(message: telebot.types.Message):
    uid = message.from_user.id
    if uid not in user_states or user_states[uid]["step"] != "awaiting_file":
        return

    proj_key = user_states[uid]["proj_key"]
    db = load_db()
    if proj_key not in db["projects"]:
        user_states.pop(uid, None)
        return

    file_name = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    proj_path = os.path.join(PROJECTS_DIR, proj_key)
    save_path = os.path.join(proj_path, file_name)

    with open(save_path, "wb") as f:
        f.write(downloaded_file)

    if file_name.endswith(".zip"):
        try:
            with zipfile.ZipFile(save_path, "r") as zip_ref:
                zip_ref.extractall(proj_path)
            os.remove(save_path)

            found_py = None
            for root, dirs, files in os.walk(proj_path):
                for f in files:
                    if f.endswith(".py") and f != "console.log":
                        found_py = os.path.relpath(os.path.join(root, f), proj_path)
                        break
                if found_py:
                    break

            if found_py:
                db["projects"][proj_key]["main_file"] = found_py
                save_db(db)

            bot.reply_to(
                message,
                f"📦 জিপ ফাইল সফলভাবে আনপ্যাক (Extract) হয়েছে!\nDetected Main File: `{found_py}`",
                parse_mode="Markdown",
            )
        except Exception as e:
            bot.reply_to(message, f"❌ জিপ এক্সট্রাক্ট করতে সমস্যা হয়েছে: `{str(e)}`")

    elif file_name.endswith(".py"):
        db["projects"][proj_key]["main_file"] = file_name
        save_db(db)
        bot.reply_to(message, f"✅ `{file_name}` সফলভাবে মেইন ফাইল হিসেবে আপলোড হয়েছে!", parse_mode="Markdown")

    user_states.pop(uid, None)
    send_project_panel(message.chat.id, proj_key)


# ================= অটো এক্সপায়ারি চেকার (ব্যাকগ্রাউন্ড) =================
def expiry_checker():
    while True:
        try:
            db = load_db()
            now = time.time()
            for proj_key, proj in list(db["projects"].items()):
                if now > proj["expires_at"]:
                    if proj_key in running_processes and running_processes[proj_key].poll() is None:
                        running_processes[proj_key].terminate()
                        del running_processes[proj_key]
        except Exception:
            pass
        time.sleep(60)


threading.Thread(target=expiry_checker, daemon=True).start()

print("🤖 Hosting Bot is Running...")
bot.infinity_polling()
