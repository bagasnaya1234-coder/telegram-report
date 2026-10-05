print("=== BOT START TEST 0510 ===", flush=True)

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from supabase import create_client, Client

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


print("=== IMPORT SELESAI 0510 ===", flush=True)

# =========================================================
# KONFIGURASI
# =========================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN belum diatur.")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL belum diatur.")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY belum diatur.")

supabase: Client = create_client(
    SUPABASE_URL.rstrip("/"),
    SUPABASE_KEY
)

TIMEZONE = ZoneInfo("Asia/Jakarta")


# =========================================================
# DATA
# =========================================================

BULAN = [
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]

KATEGORI = {
    "ib_reguler": "IB Reguler",
    "ib_sameday": "IB Sameday",
    "mt_reguler": "MT Reguler",
    "mt_sameday": "MT Sameday",
}

STATUS = {
    "done": ("Done", "✅"),
    "pending": ("Pending", "⏳"),
    "cancel": ("Cancel", "❌"),
}


# =========================================================
# WAKTU
# =========================================================

def tanggal_sekarang():
    sekarang = datetime.now(TIMEZONE)

    return (
        f"{sekarang.day} "
        f"{BULAN[sekarang.month - 1]} "
        f"{sekarang.year}"
    )


# =========================================================
# USER
# =========================================================

def get_user(telegram_user):
    user_id = telegram_user.id

    try:
        response = (
            supabase
            .table("bot_users")
            .select(
                "telegram_user_id, username, first_name, team_name"
            )
            .eq("telegram_user_id", user_id)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        data = {
            "telegram_user_id": user_id,
            "username": telegram_user.username,
            "first_name": telegram_user.first_name or "",
            "team_name": "Belum diatur",
        }

        response = (
            supabase
            .table("bot_users")
            .insert(data)
            .execute()
        )

        return response.data[0]

    except Exception as e:
        print(f"Supabase get_user error: {e}")
        raise RuntimeError(
            "Gagal mengambil data user dari Supabase."
        )


def update_team_name(user_id, team_name):
    try:
        (
            supabase
            .table("bot_users")
            .update({
                "team_name": team_name,
                "updated_at": datetime.now(
                    TIMEZONE
                ).isoformat(),
            })
            .eq(
                "telegram_user_id",
                user_id
            )
            .execute()
        )

    except Exception as e:
        print(f"Supabase update name error: {e}")
        raise RuntimeError(
            "Gagal menyimpan nama tim."
        )


# =========================================================
# REPORT DATA
# =========================================================

def get_report_items(user_id):
    try:
        response = (
            supabase
            .table("report_items")
            .select(
                "id, number, category, status, created_at"
            )
            .eq(
                "telegram_user_id",
                user_id
            )
            .order("id")
            .execute()
        )

        return response.data or []

    except Exception as e:
        print(f"Supabase get items error: {e}")
        raise RuntimeError(
            "Gagal mengambil data report."
        )


def add_report_item(
    user_id,
    number,
    category,
    status
):
    try:
        (
            supabase
            .table("report_items")
            .insert({
                "telegram_user_id": user_id,
                "number": number,
                "category": category,
                "status": status,
            })
            .execute()
        )

    except Exception as e:
        print(f"Supabase add item error: {e}")
        raise RuntimeError(
            "Gagal menyimpan data report."
        )


def delete_all_report_items(user_id):
    try:
        (
            supabase
            .table("report_items")
            .delete()
            .eq(
                "telegram_user_id",
                user_id
            )
            .execute()
        )

    except Exception as e:
        print(f"Supabase delete items error: {e}")
        raise RuntimeError(
            "Gagal menghapus data report."
        )


# =========================================================
# MENU
# =========================================================

def menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Tambah Data",
                callback_data="tambah"
            )
        ],
        [
            InlineKeyboardButton(
                "📄 Buat Report",
                callback_data="report"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Ubah Nama",
                callback_data="nama"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Hapus Semua",
                callback_data="hapus"
            )
        ],
    ])


def kategori_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "IB Reguler",
                callback_data="cat_ib_reguler"
            ),
            InlineKeyboardButton(
                "IB Sameday",
                callback_data="cat_ib_sameday"
            ),
        ],
        [
            InlineKeyboardButton(
                "MT Reguler",
                callback_data="cat_mt_reguler"
            ),
            InlineKeyboardButton(
                "MT Sameday",
                callback_data="cat_mt_sameday"
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="menu"
            )
        ],
    ])


def status_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Done",
                callback_data="status_done"
            ),
            InlineKeyboardButton(
                "⏳ Pending",
                callback_data="status_pending"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="status_cancel"
            ),
        ]
    ])


# =========================================================
# BUAT REPORT
# =========================================================

def buat_report(user_id, team_name):

    items = get_report_items(user_id)

    teks = (
        f"Report Progress {tanggal_sekarang()}\n\n"
        f"({team_name})\n\n"
    )

    for key, nama_kategori in KATEGORI.items():

        teks += f"{nama_kategori}\n\n"

        for item in items:

            if item["category"] == key:

                status_nama, emoji = STATUS[
                    item["status"]
                ]

                teks += (
                    f"• {item['number']} "
                    f"({status_nama}){emoji}\n\n"
                )

    return teks.strip()


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    data = get_user(user)

    if data["team_name"] == "Belum diatur":

        context.user_data[
            "waiting_name"
        ] = True

        await update.message.reply_text(
            "📋 *REPORT PROGRESS*\n\n"
            f"📅 Tanggal: {tanggal_sekarang()}\n\n"
            "👤 Kamu belum memiliki nama tim/report.\n\n"
            "Silakan kirim nama tim kamu.\n\n"
            "Contoh:\n"
            "`Bagas-Toni`",
            parse_mode="Markdown"
        )

        return

    await update.message.reply_text(
        "🟢 *VERSI BARU 0510*\n\n"
        "Kode terbaru berhasil dijalankan.\n\n"
        f"📋 *REPORT PROGRESS*\n\n"
        f"📅 {tanggal_sekarang()}\n"
        f"👤 Nama: {data['team_name']}\n\n"
        "Silakan pilih menu:",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )

# =========================================================
# MENU COMMAND
# =========================================================

async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    data = get_user(user)

    await update.message.reply_text(
        "📋 *REPORT PROGRESS*\n\n"
        f"📅 {tanggal_sekarang()}\n"
        f"👤 Nama: {data['team_name']}\n\n"
        "Pilih menu:",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


# =========================================================
# TOMBOL
# =========================================================

async def tombol(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = update.effective_user

    if not user:
        return

    user_id = user.id

    data = get_user(user)

    pilihan = query.data

    # KEMBALI
    if pilihan == "menu":

        await query.edit_message_text(
            "📋 *REPORT PROGRESS*\n\n"
            f"📅 {tanggal_sekarang()}\n"
            f"👤 Nama: {data['team_name']}\n\n"
            "Pilih menu:",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

        return

    # TAMBAH DATA
    if pilihan == "tambah":

        await query.edit_message_text(
            "📂 Pilih kategori:",
            reply_markup=kategori_keyboard()
        )

        return

    # KATEGORI
    if pilihan.startswith("cat_"):

        kategori = pilihan.replace(
            "cat_",
            ""
        )

        context.user_data[
            "category"
        ] = kategori

        context.user_data[
            "waiting_number"
        ] = True

        await query.edit_message_text(
            f"📂 *{KATEGORI[kategori]}*\n\n"
            "Silakan kirim nomor yang ingin "
            "ditambahkan.\n\n"
            "Contoh:\n"
            "`6277046`",
            parse_mode="Markdown"
        )

        return

    # STATUS
    if pilihan.startswith("status_"):

        status = pilihan.replace(
            "status_",
            ""
        )

        category = context.user_data.get(
            "category"
        )

        number = context.user_data.get(
            "number"
        )

        if not category or not number:

            await query.edit_message_text(
                "⚠️ Data sesi tidak ditemukan.\n\n"
                "Silakan mulai lagi dari menu.",
                reply_markup=menu_keyboard()
            )

            return

        add_report_item(
            user_id,
            number,
            category,
            status
        )

        context.user_data.pop(
            "category",
            None
        )

        context.user_data.pop(
            "number",
            None
        )

        context.user_data.pop(
            "waiting_number",
            None
        )

        status_nama, emoji = STATUS[
            status
        ]

        await query.edit_message_text(
            "✅ *Data berhasil ditambahkan!*\n\n"
            f"Nomor: `{number}`\n"
            f"Kategori: {KATEGORI[category]}\n"
            f"Status: {status_nama} {emoji}\n\n"
            "Kamu bisa menambahkan data lagi.",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

        return

    # REPORT
    if pilihan == "report":

        teks = buat_report(
            user_id,
            data["team_name"]
        )

        await query.edit_message_text(
            f"```text\n{teks}\n```",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

        return

    # UBAH NAMA
    if pilihan == "nama":

        context.user_data[
            "waiting_name"
        ] = True

        await query.edit_message_text(
            "👤 *Ubah Nama Report*\n\n"
            f"Nama sekarang: `{data['team_name']}`\n\n"
            "Kirim nama baru.\n\n"
            "Contoh:\n"
            "`Bagas-Toni`",
            parse_mode="Markdown"
        )

        return

    # HAPUS SEMUA
    if pilihan == "hapus":

        delete_all_report_items(
            user_id
        )

        await query.edit_message_text(
            "🗑️ *Semua data nomor berhasil "
            "dihapus.*\n\n"
            "Nama tim tetap tersimpan.",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

        return


# =========================================================
# PESAN TEXT
# =========================================================

async def pesan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    user_id = user.id

    teks = update.message.text.strip()

    # NAMA
    if context.user_data.get(
        "waiting_name"
    ):

        if len(teks) < 2:

            await update.message.reply_text(
                "⚠️ Nama terlalu pendek.\n\n"
                "Silakan kirim nama tim yang benar."
            )

            return

        if len(teks) > 50:

            await update.message.reply_text(
                "⚠️ Nama maksimal 50 karakter."
            )

            return

        update_team_name(
            user_id,
            teks
        )

        context.user_data.pop(
            "waiting_name",
            None
        )

        await update.message.reply_text(
            "✅ *Nama berhasil disimpan!*\n\n"
            f"Nama: *{teks}*",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

        return

    # NOMOR
    if context.user_data.get(
        "waiting_number"
    ):

        if not teks.isdigit():

            await update.message.reply_text(
                "⚠️ Nomor harus berupa angka.\n\n"
                "Contoh:\n"
                "`6277046`",
                parse_mode="Markdown"
            )

            return

        if len(teks) < 4 or len(teks) > 20:

            await update.message.reply_text(
                "⚠️ Nomor harus terdiri dari "
                "4 sampai 20 digit."
            )

            return

        context.user_data[
            "number"
        ] = teks

        context.user_data.pop(
            "waiting_number",
            None
        )

        await update.message.reply_text(
            f"🔢 Nomor: *{teks}*\n\n"
            "Pilih status:",
            parse_mode="Markdown",
            reply_markup=status_keyboard()
        )

        return

    # PESAN BIASA
    await update.message.reply_text(
        "Gunakan menu di bawah:",
        reply_markup=menu_keyboard()
    )


# =========================================================
# COMMAND REPORT
# =========================================================

async def command_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    data = get_user(user)

    teks = buat_report(
        user.id,
        data["team_name"]
    )

    await update.message.reply_text(
        f"```text\n{teks}\n```",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


# =========================================================
# COMMAND NAMA
# =========================================================

async def command_nama(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data[
        "waiting_name"
    ] = True

    await update.message.reply_text(
        "👤 *Ubah Nama Report*\n\n"
        "Kirim nama baru.\n\n"
        "Contoh:\n"
        "`Bagas-Toni`",
        parse_mode="Markdown"
    )


# =========================================================
# COMMAND RESET
# =========================================================

async def command_reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    delete_all_report_items(
        user.id
    )

    await update.message.reply_text(
        "🗑️ *Semua nomor dan status kamu "
        "telah dihapus.*\n\n"
        "Nama tim tetap tersimpan.",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "ERROR:",
        repr(context.error)
    )


# =========================================================
# MAIN
# =========================================================

def main():
    print("=== MASUK MAIN 0510 ===", flush=True)

    print("====================================")
    print("REPORT PROGRESS BOT")
    print("Bot sedang berjalan...")
    print("Zona waktu: Asia/Jakarta")
    print("Penyimpanan: Supabase")
    print("MODE BARU 0510")
    print("====================================")

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
        
    )


    print("=== APP TELEGRAM BERHASIL 0510 ===", flush=True)
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "menu",
            menu
        )
    )

    app.add_handler(
        CommandHandler(
            "report",
            command_report
        )
    )

    app.add_handler(
        CommandHandler(
            "nama",
            command_nama
        )
    )

    app.add_handler(
        CommandHandler(
            "reset",
            command_reset
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            tombol
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pesan
        )
    )

    app.add_error_handler(
        error_handler
    )
    

    app.run_polling()


if __name__ == "__main__":
    main()