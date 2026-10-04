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


# =========================================================
# PENGATURAN
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

# Buat client Supabase menggunakan Secret API Key.
# Key ini HARUS disimpan sebagai Environment Variable di Render,
# jangan ditulis di dalam kode dan jangan di-upload ke GitHub.
supabase: Client = create_client(SUPABASE_URL.rstrip("/"), SUPABASE_KEY)

TIMEZONE = ZoneInfo("Asia/Jakarta")

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
# DATABASE SUPABASE
# =========================================================

def get_chat_data(chat_id):
    """Ambil data satu chat dari Supabase."""
    chat_id = str(chat_id)

    try:
        response = (
            supabase
            .table("bot_data")
            .select("id, name, data")
            .eq("id", chat_id)
            .limit(1)
            .execute()
        )

        if response.data:
            row = response.data[0]
            stored = row.get("data") or {}
            return {
                "name": row.get("name") or "Bagas-Toni",
                "items": stored.get("items", []),
            }

        # Data baru: buat record pertama.
        new_chat = {
            "name": "Bagas-Toni",
            "items": [],
        }

        supabase.table("bot_data").insert({
            "id": chat_id,
            "name": new_chat["name"],
            "data": new_chat,
        }).execute()

        return new_chat

    except Exception as e:
        print(f"Supabase get error: {e}")
        raise RuntimeError("Gagal mengambil data dari Supabase.")


def save_chat_data(chat_id, chat):
    """Simpan/perbarui data satu chat di Supabase."""
    chat_id = str(chat_id)

    try:
        supabase.table("bot_data").upsert({
            "id": chat_id,
            "name": chat["name"],
            "data": {
                "items": chat["items"],
            },
            "updated_at": datetime.now(TIMEZONE).isoformat(),
        }).execute()

    except Exception as e:
        print(f"Supabase save error: {e}")
        raise RuntimeError("Gagal menyimpan data ke Supabase.")


# =========================================================
# TANGGAL WIB
# =========================================================

def tanggal_sekarang():
    sekarang = datetime.now(TIMEZONE)

    return (
        f"{sekarang.day} "
        f"{BULAN[sekarang.month - 1]} "
        f"{sekarang.year}"
    )


# =========================================================
# MENU UTAMA
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
# FORMAT REPORT
# =========================================================

def buat_report(chat_id):
    chat = get_chat_data(chat_id)

    nama = chat["name"]

    teks = (
        f"Report Progress {tanggal_sekarang()}\n\n"
        f"({nama})\n\n"
    )

    for key, nama_kategori in KATEGORI.items():
        teks += f"{nama_kategori}\n\n"

        for item in chat["items"]:
            if item["category"] == key:
                status_nama, emoji = STATUS[item["status"]]

                teks += (
                    f"• {item['number']} "
                    f"({status_nama}){emoji}\n\n"
                )

    return teks.strip()


# =========================================================
# /START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat_data(chat_id)

    teks = (
        "📋 *REPORT PROGRESS*\n\n"
        f"📅 Tanggal: {tanggal_sekarang()}\n"
        f"👤 Nama: {chat['name']}\n\n"
        "Silakan pilih menu:"
    )

    await update.message.reply_text(
        teks,
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


# =========================================================
# /MENU
# =========================================================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat_data(chat_id)

    teks = (
        "📋 *REPORT PROGRESS*\n\n"
        f"📅 {tanggal_sekarang()}\n"
        f"👤 {chat['name']}\n\n"
        "Pilih menu:"
    )

    await update.message.reply_text(
        teks,
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


# =========================================================
# TOMBOL
# =========================================================

async def tombol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    chat = get_chat_data(chat_id)

    pilihan = query.data

    # -------------------------
    # MENU
    # -------------------------

    if pilihan == "menu":
        await query.edit_message_text(
            "📋 *REPORT PROGRESS*\n\n"
            f"📅 {tanggal_sekarang()}\n"
            f"👤 {chat['name']}\n\n"
            "Pilih menu:",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )
        return

    # -------------------------
    # TAMBAH
    # -------------------------

    if pilihan == "tambah":
        await query.edit_message_text(
            "📂 Pilih kategori:",
            reply_markup=kategori_keyboard()
        )
        return

    # -------------------------
    # PILIH KATEGORI
    # -------------------------

    if pilihan.startswith("cat_"):
        kategori = pilihan.replace("cat_", "")

        context.user_data["category"] = kategori
        context.user_data["waiting_number"] = True

        await query.edit_message_text(
            f"📂 *{KATEGORI[kategori]}*\n\n"
            "Silakan kirim nomor yang ingin ditambahkan.\n\n"
            "Contoh:\n"
            "`6277046`",
            parse_mode="Markdown"
        )
        return

    # -------------------------
    # STATUS
    # -------------------------

    if pilihan.startswith("status_"):
        status = pilihan.replace("status_", "")

        category = context.user_data.get("category")
        number = context.user_data.get("number")

        if not category or not number:
            await query.edit_message_text(
                "Data tidak ditemukan. Silakan mulai lagi dari menu.",
                reply_markup=menu_keyboard()
            )
            return

        chat["items"].append({
            "number": number,
            "category": category,
            "status": status
        })

        save_chat_data(chat_id, chat)

        context.user_data.pop("category", None)
        context.user_data.pop("number", None)
        context.user_data.pop("waiting_number", None)

        status_nama, emoji = STATUS[status]

        await query.edit_message_text(
            f"✅ Data berhasil ditambahkan!\n\n"
            f"Nomor: {number}\n"
            f"Kategori: {KATEGORI[category]}\n"
            f"Status: {status_nama} {emoji}\n\n"
            "Mau tambah data lagi?",
            reply_markup=menu_keyboard()
        )
        return

    # -------------------------
    # REPORT
    # -------------------------

    if pilihan == "report":
        teks = buat_report(chat_id)

        await query.edit_message_text(
            f"```text\n{teks}\n```",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )
        return

    # -------------------------
    # UBAH NAMA
    # -------------------------

    if pilihan == "nama":
        context.user_data["waiting_name"] = True

        await query.edit_message_text(
            "👤 *Ubah Nama Report*\n\n"
            f"Nama sekarang: `{chat['name']}`\n\n"
            "Kirim nama baru.\n\n"
            "Contoh:\n"
            "`Bagas-Toni`",
            parse_mode="Markdown"
        )
        return

    # -------------------------
    # HAPUS
    # -------------------------

    if pilihan == "hapus":
        chat["items"] = []

        save_chat_data(chat_id, chat)

        await query.edit_message_text(
            "🗑️ Semua data nomor berhasil dihapus.\n\n"
            "Nama dan pengaturan tetap tersimpan.",
            reply_markup=menu_keyboard()
        )
        return


# =========================================================
# PESAN TEKS
# =========================================================

async def pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat_data(chat_id)

    teks = update.message.text.strip()

    # -------------------------
    # MENUNGGU NAMA
    # -------------------------

    if context.user_data.get("waiting_name"):
        chat["name"] = teks

        save_chat_data(chat_id, chat)

        context.user_data.pop("waiting_name", None)

        await update.message.reply_text(
            f"✅ Nama berhasil diubah menjadi:\n\n"
            f"*{teks}*",
            parse_mode="Markdown",
            reply_markup=menu_keyboard()
        )

        return

    # -------------------------
    # MENUNGGU NOMOR
    # -------------------------

    if context.user_data.get("waiting_number"):
        # Hanya menerima angka
        if not teks.isdigit():
            await update.message.reply_text(
                "⚠️ Nomor harus berupa angka.\n\n"
                "Contoh: `6277046`",
                parse_mode="Markdown"
            )
            return

        context.user_data["number"] = teks
        context.user_data.pop("waiting_number", None)

        await update.message.reply_text(
            f"🔢 Nomor: *{teks}*\n\n"
            "Pilih status:",
            parse_mode="Markdown",
            reply_markup=status_keyboard()
        )

        return

    # -------------------------
    # PESAN BIASA
    # -------------------------

    await update.message.reply_text(
        "Gunakan menu di bawah:",
        reply_markup=menu_keyboard()
    )


# =========================================================
# /REPORT
# =========================================================

async def command_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    teks = buat_report(chat_id)

    await update.message.reply_text(
        f"```text\n{teks}\n```",
        parse_mode="Markdown",
        reply_markup=menu_keyboard()
    )


# =========================================================
# /NAMA
# =========================================================

async def command_nama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_name"] = True

    await update.message.reply_text(
        "👤 Kirim nama baru untuk report.\n\n"
        "Contoh:\n"
        "`Bagas-Toni`",
        parse_mode="Markdown"
    )


# =========================================================
# /RESET
# =========================================================

async def command_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat = get_chat_data(chat_id)

    chat["items"] = []

    save_chat_data(chat_id, chat)

    await update.message.reply_text(
        "🗑️ Semua nomor dan status telah dihapus.\n\n"
        "Nama tetap tersimpan.",
        reply_markup=menu_keyboard()
    )


# =========================================================
# JALANKAN BOT
# =========================================================

def main():
    print("====================================")
    print("REPORT PROGRESS BOT")
    print("Bot sedang berjalan...")
    print("Zona waktu: Asia/Jakarta")
    print("Penyimpanan: Supabase")
    print("====================================")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("report", command_report))
    app.add_handler(CommandHandler("nama", command_nama))
    app.add_handler(CommandHandler("reset", command_reset))

    app.add_handler(CallbackQueryHandler(tombol))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pesan
        )
    )

    print("Mode: polling")
    app.run_polling()


if __name__ == "__main__":
    main()
