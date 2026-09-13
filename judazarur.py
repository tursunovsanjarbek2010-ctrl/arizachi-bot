import logging
import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest


# ==================================================
# SOZLAMALAR
# ==================================================

BOT_TOKEN = "8805037450:AAHel4Xkdy0bLS5mycS1NciFldYvEhAIvB8"
ADMIN_ID = 8196582667


# ==================================================
# DATABASE
# ==================================================

db = sqlite3.connect("arizalar.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS arizalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    text TEXT NOT NULL,
    status TEXT DEFAULT 'Qabul qilindi'
)
""")
db.commit()


# ==================================================
# ARIZA BOSQICHLARI
# ==================================================

NAME, PHONE, ADDRESS, TEXT = range(4)


# ==================================================
# MENYU
# ==================================================

def main_menu(user_id):
    buttons = [
        [
            InlineKeyboardButton(
                "🟢 📝 Ariza yuborish",
                callback_data="new_application"
            ),
            InlineKeyboardButton(
                "🔵 🔎 Arizam holati",
                callback_data="check_status"
            ),
        ],
        [
            InlineKeyboardButton(
                "🟣 📚 Ma'lumot",
                callback_data="info"
            ),
            InlineKeyboardButton(
                "🟠 📞 Bog'lanish",
                callback_data="contact"
            ),
        ],
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                "🔴 👨‍💼 ADMIN PANEL",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(buttons)


def admin_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 📥 Yangi arizalar",
                callback_data="admin_new"
            )
        ],
        [
            InlineKeyboardButton(
                "🔵 📋 Barcha arizalar",
                callback_data="admin_all"
            )
        ],
        [
            InlineKeyboardButton(
                "🟣 📊 Statistika",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="back"
            )
        ],
    ])


def back_button():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏠 Bosh menyu",
                callback_data="back"
            )
        ]
    ])


def admin_application_buttons(app_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔵 Ko'rib chiqilmoqda",
                callback_data=f"review_{app_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🟢 Tasdiqlash",
                callback_data=f"approve_{app_id}"
            ),
            InlineKeyboardButton(
                "🔴 Rad etish",
                callback_data=f"reject_{app_id}"
            ),
        ],
    ])


# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    text = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "🤖 <b>ARIZACHI BOT</b>ga xush kelibsiz!\n\n"
        "📋 Ushbu bot orqali ariza va murojaat yuborishingiz mumkin.\n\n"
        "👇 Kerakli bo'limni tanlang:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(user_id),
    )


# ==================================================
# INLINE MENYU
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "new_application":

        await query.message.reply_text(
            "🟢 <b>ARIZA YUBORISH</b>\n\n"
            "1️⃣ F.I.Sh.ingizni kiriting:",
            parse_mode="HTML",
        )

        return NAME

    if data == "check_status":

        context.user_data["checking_status"] = True

        await query.message.reply_text(
            "🔵 <b>ARIZA HOLATINI TEKSHIRISH</b>\n\n"
            "🔢 Ariza raqamingizni yuboring.\n"
            "Masalan: <b>15</b>",
            parse_mode="HTML",
        )

        return ConversationHandler.END

    if data == "info":

        await query.message.reply_text(
            "🟣 <b>BOT HAQIDA</b>\n\n"
            "🤖 Arizachi Bot\n"
            "📝 Ariza yuborish\n"
            "🔎 Ariza holatini tekshirish\n"
            "📩 Murojaatlarni qabul qilish\n\n"
            "Ariza yuborganingizdan so'ng sizga maxsus raqam beriladi.",
            parse_mode="HTML",
            reply_markup=back_button(),
        )

        return ConversationHandler.END

    if data == "contact":

        await query.message.reply_text(
            "🟠 <b>BOG'LANISH</b>\n\n"
            "📞 Telefon: +998 XX XXX XX XX\n"
            "📩 Telegram: @username\n\n"
            "💬 Murojaat uchun admin bilan bog'lanishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=back_button(),
        )

        return ConversationHandler.END

    if data == "admin_panel":

        if query.from_user.id != ADMIN_ID:

            await query.message.reply_text(
                "⛔ Sizda admin huquqi yo'q."
            )

            return ConversationHandler.END

        await query.message.reply_text(
            "🔴 <b>ADMIN PANEL</b>\n\n"
            "Kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )

        return ConversationHandler.END

    if data == "admin_new":

        if query.from_user.id != ADMIN_ID:
            return ConversationHandler.END

        cursor.execute("""
            SELECT id, name, phone, address, text, status
            FROM arizalar
            WHERE status = 'Qabul qilindi'
            ORDER BY id DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()

        if not rows:

            await query.message.reply_text(
                "📭 <b>Yangi arizalar yo'q.</b>",
                parse_mode="HTML"
            )

            return ConversationHandler.END

        for app_id, name, phone, address, text, status in rows:

            message = (
                f"🚨 <b>YANGI ARIZA #{app_id}</b>\n\n"
                f"👤 <b>F.I.Sh:</b> {name}\n"
                f"📱 <b>Telefon:</b> {phone}\n"
                f"📍 <b>Manzil:</b> {address}\n\n"
                f"📝 <b>MUROJAAT:</b>\n{text}\n\n"
                f"📌 <b>Holat:</b> {status}"
            )

            await query.message.reply_text(
                message,
                parse_mode="HTML",
                reply_markup=admin_application_buttons(app_id),
            )

        return ConversationHandler.END

    if data == "admin_all":

        if query.from_user.id != ADMIN_ID:
            return ConversationHandler.END

        cursor.execute("""
            SELECT id, name, status
            FROM arizalar
            ORDER BY id DESC
            LIMIT 30
        """)

        rows = cursor.fetchall()

        if not rows:

            await query.message.reply_text(
                "📭 Arizalar mavjud emas."
            )

            return ConversationHandler.END

        message = "📋 <b>BARCHA ARIZALAR</b>\n\n"

        for app_id, name, status in rows:

            icon = {
                "Tasdiqlandi": "🟢",
                "Rad etildi": "🔴",
                "Ko'rib chiqilmoqda": "🔵",
                "Qabul qilindi": "🟠",
            }.get(status, "⚪")

            message += (
                f"{icon} <b>#{app_id}</b> — {name}\n"
                f"   📌 {status}\n\n"
            )

        await query.message.reply_text(
            message,
            parse_mode="HTML"
        )

        return ConversationHandler.END

    if data == "admin_stats":

        if query.from_user.id != ADMIN_ID:
            return ConversationHandler.END

        cursor.execute(
            "SELECT COUNT(*) FROM arizalar"
        )
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM arizalar
            WHERE status = 'Qabul qilindi'
        """)
        received = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM arizalar
            WHERE status = 'Ko'rib chiqilmoqda'
        """)
        review = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM arizalar
            WHERE status = 'Tasdiqlandi'
        """)
        approved = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM arizalar
            WHERE status = 'Rad etildi'
        """)
        rejected = cursor.fetchone()[0]

        await query.message.reply_text(
            "📊 <b>STATISTIKA</b>\n\n"
            f"📋 Jami: <b>{total}</b>\n"
            f"🟠 Qabul qilingan: <b>{received}</b>\n"
            f"🔵 Ko'rib chiqilmoqda: <b>{review}</b>\n"
            f"🟢 Tasdiqlangan: <b>{approved}</b>\n"
            f"🔴 Rad etilgan: <b>{rejected}</b>",
            parse_mode="HTML",
        )

        return ConversationHandler.END

    if data == "back":

        await query.message.reply_text(
            "🏠 <b>ASOSIY MENYU</b>\n\n"
            "Kerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=main_menu(query.from_user.id),
        )

        return ConversationHandler.END

    return ConversationHandler.END


# ==================================================
# F.I.SH
# ==================================================

async def get_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["name"] = update.message.text

    button = KeyboardButton(
        "📱 Telefon raqamni yuborish",
        request_contact=True,
    )

    await update.message.reply_text(
        "📱 <b>Telefon raqamingizni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [[button]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )

    return PHONE


# ==================================================
# TELEFON
# ==================================================

async def get_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    context.user_data["phone"] = phone

    await update.message.reply_text(
        "📍 <b>Yashash manzilingizni kiriting:</b>",
        parse_mode="HTML",
    )

    return ADDRESS


# ==================================================
# MANZIL
# ==================================================

async def get_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data["address"] = update.message.text

    await update.message.reply_text(
        "✍️ <b>Arizangiz mazmunini to'liq yozing:</b>\n\n"
        "Murojaatingizni imkon qadar batafsil yozing.",
        parse_mode="HTML",
    )

    return TEXT


# ==================================================
# ARIZA MATNI
# ==================================================

async def get_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    name = context.user_data["name"]
    phone = context.user_data["phone"]
    address = context.user_data["address"]
    text = update.message.text
    user_id = update.effective_user.id

    cursor.execute("""
        INSERT INTO arizalar
        (user_id, name, phone, address, text)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        phone,
        address,
        text,
    ))

    db.commit()

    app_id = cursor.lastrowid

    await update.message.reply_text(
        f"🟢 <b>ARIZANGIZ QABUL QILINDI!</b>\n\n"
        f"🔢 Ariza raqami: <b>#{app_id}</b>\n"
        f"📌 Holati: <b>Qabul qilindi</b>\n\n"
        f"💾 Ariza raqamingizni saqlab qo'ying.",
        parse_mode="HTML",
        reply_markup=back_button(),
    )

    admin_text = (
        f"🚨 <b>YANGI ARIZA!</b>\n\n"
        f"🔢 <b>Ariza:</b> #{app_id}\n"
        f"👤 <b>F.I.Sh:</b> {name}\n"
        f"📱 <b>Telefon:</b> {phone}\n"
        f"📍 <b>Manzil:</b> {address}\n\n"
        f"📝 <b>MUROJAAT:</b>\n{text}"
    )

    try:

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="HTML",
            reply_markup=admin_application_buttons(app_id),
        )

    except Exception as e:

        logging.error(
            "Admin xabari yuborilmadi: %s",
            e
        )

    context.user_data.clear()

    return ConversationHandler.END


# ==================================================
# ARIZA RAQAMINI TEKSHIRISH
# ==================================================

async def receive_status_number(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get("checking_status"):
        return

    try:

        app_id = int(
            update.message.text.strip()
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Ariza raqamini faqat raqam ko'rinishida yuboring."
        )

        return

    cursor.execute("""
        SELECT user_id, name, status
        FROM arizalar
        WHERE id = ?
    """, (app_id,))

    result = cursor.fetchone()

    if not result:

        await update.message.reply_text(
            "❌ Bunday raqamli ariza topilmadi."
        )

    else:

        user_id, name, status = result

        if user_id != update.effective_user.id:

            await update.message.reply_text(
                "⛔ Bu ariza sizga tegishli emas."
            )

        else:

            icon = {
                "Tasdiqlandi": "🟢",
                "Rad etildi": "🔴",
                "Ko'rib chiqilmoqda": "🔵",
                "Qabul qilindi": "🟠",
            }.get(status, "⚪")

            await update.message.reply_text(
                f"🔎 <b>ARIZA MA'LUMOTI</b>\n\n"
                f"🔢 Raqam: <b>#{app_id}</b>\n"
                f"👤 F.I.Sh: {name}\n"
                f"{icon} Holati: <b>{status}</b>",
                parse_mode="HTML",
                reply_markup=back_button(),
            )

    context.user_data["checking_status"] = False


# ==================================================
# ADMIN STATUSINI O'ZGARTIRISH
# ==================================================

async def change_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.message.reply_text(
            "⛔ Sizda admin huquqi yo'q."
        )
        return

    action, app_id_text = query.data.split("_", 1)

    try:
        app_id = int(app_id_text)
    except ValueError:
        return

    status_map = {
        "review": "Ko'rib chiqilmoqda",
        "approve": "Tasdiqlandi",
        "reject": "Rad etildi",
    }

    status = status_map.get(action)

    if status is None:
        return

    cursor.execute("""
        UPDATE arizalar
        SET status = ?
        WHERE id = ?
    """, (
        status,
        app_id,
    ))

    db.commit()

    cursor.execute("""
        SELECT user_id
        FROM arizalar
        WHERE id = ?
    """, (app_id,))

    result = cursor.fetchone()

    if result:

        user_id = result[0]

        icon = {
            "Tasdiqlandi": "🟢",
            "Rad etildi": "🔴",
            "Ko'rib chiqilmoqda": "🔵",
        }[status]

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"📢 <b>ARIZA HOLATI YANGILANDI</b>\n\n"
                    f"🔢 Ariza: <b>#{app_id}</b>\n"
                    f"{icon} Yangi holat: <b>{status}</b>"
                ),
                parse_mode="HTML",
            )

        except Exception as e:

            logging.error(
                "Foydalanuvchiga xabar yuborilmadi: %s",
                e
            )

    await query.edit_message_reply_markup(
        reply_markup=None
    )

    await query.message.reply_text(
        f"✅ <b>#{app_id}</b> ariza holati o'zgartirildi.\n\n"
        f"📌 Yangi holat: <b>{status}</b>",
        parse_mode="HTML",
    )


# ==================================================
# BEKOR QILISH
# ==================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Ariza yuborish bekor qilindi.",
        reply_markup=main_menu(
            update.effective_user.id
        ),
    )

    return ConversationHandler.END


# ==================================================
# MAIN
# ==================================================

def main():

    logging.basicConfig(
        format=(
            "%(asctime)s - "
            "%(name)s - "
            "%(levelname)s - "
            "%(message)s"
        ),
        level=logging.INFO,
    )

    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30,
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .build()
    )

    # ==============================================
    # ARIZA CONVERSATION
    # ==============================================

    conversation = ConversationHandler(

        entry_points=[
            CallbackQueryHandler(
                button_handler,
                pattern=r"^new_application$",
            )
        ],

        states={

            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],

            PHONE: [
                MessageHandler(
                    filters.CONTACT,
                    get_phone,
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_phone,
                ),
            ],

            ADDRESS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_address,
                )
            ],

            TEXT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_text,
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel,
            )
        ],
    )

    # Start
    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # Ariza
    application.add_handler(
        conversation
    )
    # Admin status tugmalari
    application.add_handler(
        CallbackQueryHandler(
            change_status,
            pattern=r"^(review|approve|reject)_\d+$"
        )
    )

    # Asosiy inline tugmalar
    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # Ariza raqamini tekshirish
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_status_number
        )
    )

    print("🤖 ARIZACHI BOT ISHLADI!")

    application.run_polling()


if __name__ == "__main__":
    main()