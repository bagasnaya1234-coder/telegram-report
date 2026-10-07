import os
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from supabase import create_client


# =========================================================
# KONFIGURASI
# =========================================================

# Mendukung BOT_TOKEN dan TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_TOKEN = (
    os.getenv("BOT_TOKEN")
    or os.getenv("TELEGRAM_BOT_TOKEN")
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TIMEZONE = ZoneInfo("Asia/Jakarta")


def today():
    return datetime.now(TIMEZONE).date().isoformat()


def tanggal_indonesia():
    now = datetime.now(TIMEZONE)

    bulan = [
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

    return f"{now.day:02d} {bulan[now.month - 1]} {now.year}"


if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN belum diatur"
    )

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL belum diatur"
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY belum diatur"
    )


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# KATEGORI
# =========================================================

KATEGORI = {
    "ib_reguler": "IB REGULER",
    "ib_sameday": "IB SAMEDAY",
    "ib_h0": "IB H+0",
    "mt_reguler": "MT REGULER",
    "mt_h0": "MT H+0",
}


# =========================================================
# STATUS
# =========================================================

STATUS = {
    "done": ("DONE", "✅"),
    "pending": ("PENDING", "🅿️"),
    "cancel": ("CANCEL", "❌"),
}


# =========================================================
# DATABASE USER
# =========================================================

def get_user(user):

    user_id = user.id

    result = (
        supabase
        .table("bot_users")
        .select("*")
        .eq(
            "telegram_user_id",
            user_id
        )
        .limit(1)
        .execute()
    )

    if result.data:

        row = result.data[0]

        supabase.table(
            "bot_users"
        ).update({
            "username": user.username,
            "first_name": user.first_name,
            "updated_at": datetime.now(
                TIMEZONE
            ).isoformat(),
        }).eq(
            "telegram_user_id",
            user_id
        ).execute()

        return row

    result = (
        supabase
        .table("bot_users")
        .insert({
            "telegram_user_id": user_id,
            "username": user.username,
            "first_name": user.first_name,
            "team_name": "Belum diatur",
            "team_name_date": None,
        })
        .execute()
    )

    return result.data[0]


def update_team_name(
    user_id,
    team_name
):

    return (
        supabase
        .table("bot_users")
        .update({
            "team_name": team_name,
            "team_name_date": today(),
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


def is_new_day_for_user(user_id):

    result = (
        supabase
        .table("bot_users")
        .select("team_name_date")
        .eq(
            "telegram_user_id",
            user_id
        )
        .limit(1)
        .execute()
    )

    if not result.data:
        return True

    saved_date = result.data[0].get(
        "team_name_date"
    )

    return saved_date != today()


# =========================================================
# DATABASE REPORT
# =========================================================

def get_report_items(user_id):

    result = (
        supabase
        .table("report_items")
        .select("*")
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .order("id")
        .execute()
    )

    return result.data or []


def get_report_item(
    user_id,
    item_id
):

    result = (
        supabase
        .table("report_items")
        .select("*")
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .eq(
            "id",
            item_id
        )
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def add_report_item(
    user_id,
    number,
    category,
    status
):

    return (
        supabase
        .table("report_items")
        .insert({
            "telegram_user_id": user_id,
            "report_date": today(),
            "number": number,
            "category": category,
            "status": status,
        })
        .execute()
    )


def update_report_number(
    user_id,
    item_id,
    number
):

    return (
        supabase
        .table("report_items")
        .update({
            "number": number
        })
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .eq(
            "id",
            item_id
        )
        .execute()
    )


def update_report_category(
    user_id,
    item_id,
    category
):

    return (
        supabase
        .table("report_items")
        .update({
            "category": category
        })
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .eq(
            "id",
            item_id
        )
        .execute()
    )


def update_report_status(
    user_id,
    item_id,
    status
):

    return (
        supabase
        .table("report_items")
        .update({
            "status": status
        })
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .eq(
            "id",
            item_id
        )
        .execute()
    )


def delete_report_item(
    user_id,
    item_id
):

    return (
        supabase
        .table("report_items")
        .delete()
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .eq(
            "id",
            item_id
        )
        .execute()
    )


def delete_all_report_items(user_id):

    return (
        supabase
        .table("report_items")
        .delete()
        .eq(
            "telegram_user_id",
            user_id
        )
        .eq(
            "report_date",
            today()
        )
        .execute()
    )


# =========================================================
# KEYBOARD MENU
# =========================================================

def menu_keyboard():

    return ReplyKeyboardMarkup(
        [
            [
                "➕ Tambah Data",
                "📄 Buat Report",
            ],
            [
                "✏️ Edit Data",
                "🗑️ Hapus Data",
            ],
            [
                "👤 Ubah Nama Tim",
            ],
            [
                "📚 Tutorial",
            ],
        ],
        resize_keyboard=True
    )


def inline_menu_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Tambah Data",
                callback_data="cb_add"
            )
        ],
        [
            InlineKeyboardButton(
                "📄 Buat Report",
                callback_data="cb_report"
            )
        ],
        [
            InlineKeyboardButton(
                "✏️ Edit Data",
                callback_data="cb_editlist"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Hapus Data",
                callback_data="cb_deletelist"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Ubah Nama Tim",
                callback_data="cb_teamname"
            )
        ],
        [
            InlineKeyboardButton(
                "📚 Tutorial",
                callback_data="cb_tutor"
            )
        ]
    ])


# =========================================================
# KEYBOARD KATEGORI
# =========================================================

def kategori_keyboard(prefix="addcat"):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "IB REGULER",
                callback_data=f"{prefix}_ib_reguler"
            ),
            InlineKeyboardButton(
                "IB SAMEDAY",
                callback_data=f"{prefix}_ib_sameday"
            ),
        ],
        [
            InlineKeyboardButton(
                "IB H+0",
                callback_data=f"{prefix}_ib_h0"
            ),
        ],
        [
            InlineKeyboardButton(
                "MT REGULER",
                callback_data=f"{prefix}_mt_reguler"
            ),
            InlineKeyboardButton(
                "MT H+0",
                callback_data=f"{prefix}_mt_h0"
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ]
    ])


# =========================================================
# KEYBOARD STATUS
# =========================================================

def status_keyboard(prefix="addstatus"):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Done",
                callback_data=f"{prefix}_done"
            ),
            InlineKeyboardButton(
                "🅿️ Pending",
                callback_data=f"{prefix}_pending"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data=f"{prefix}_cancel"
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ]
    ])


# =========================================================
# MENU
# =========================================================

async def tampilkan_menu_callback(
    query,
    data
):

    await query.edit_message_text(
        "📋 <b>REPORT PROGRESS</b>\n\n"
        f"👥 Tim: <b>{escape(data.get('team_name', 'Belum diatur'))}</b>\n\n"
        "Silakan pilih menu:",
        parse_mode="HTML",
        reply_markup=inline_menu_keyboard()
    )


async def tampilkan_menu_message(
    message,
    data
):

    await message.reply_text(
        "📋 <b>REPORT PROGRESS</b>\n\n"
        f"👥 Tim: <b>{escape(data.get('team_name', 'Belum diatur'))}</b>\n\n"
        "Silakan pilih menu di bawah.",
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# MINTA NAMA TIM HARI INI
# =========================================================

async def minta_nama_hari_ini(
    message,
    context,
    first_name=None
):

    context.user_data.clear()

    context.user_data[
        "waiting_name"
    ] = True

    if first_name:

        await message.reply_text(
            f"👋 <b>Halo, {escape(first_name)}!</b>\n\n"
            "Selamat datang di "
            "<b>Report Progress Bot</b> 📋",
            parse_mode="HTML"
        )

    await message.reply_text(
        "📅 <b>HARI BARU</b>\n\n"
        f"Tanggal hari ini: <b>{tanggal_indonesia()}</b>\n\n"
        "Silakan isi nama tim anda hari ini.\n\n"
        "Contoh:\n"
        "<code>Bagas - Giver</code>",
        parse_mode="HTML"
    )


# =========================================================
# BUAT REPORT
# =========================================================

def buat_report_text(
    team_name,
    items
):

    grouped = {
        category: []
        for category in KATEGORI
    }

    for item in items:

        category = item.get(
            "category"
        )

        if category in grouped:
            grouped[category].append(item)

    lines = [
        "<b>REPORT PROGRESS</b>",
        "",
        f"TEAM: {escape(str(team_name))}",
        f"TANGGAL: {tanggal_indonesia()}",
        "",
    ]

    for category_key, category_name in KATEGORI.items():

        lines.append(
            f"<b>{escape(category_name)}</b>"
        )

        category_items = grouped[
            category_key
        ]

        # =================================================
        # KATEGORI KOSONG
        # =================================================

        if not category_items:

            lines.append("• -")

        else:

            for item in category_items:

                status_key = item.get(
                    "status"
                )

                status_name, emoji = STATUS.get(
                    status_key,
                    (
                        str(status_key or "UNKNOWN").upper(),
                        "❔"
                    )
                )

                lines.append(
                    f"• "
                    f"{escape(str(item.get('number', '')))} "
                    f"<b>{escape(status_name)}</b> "
                    f"{emoji}"
                )

        # Satu baris kosong antar kategori
        lines.append("")

    return "\n".join(lines).rstrip()


async def kirim_report_message(
    message,
    user_id,
    team_name
):

    items = get_report_items(
        user_id
    )

    report = buat_report_text(
        team_name,
        items
    )

    await message.reply_text(
        report,
        parse_mode="HTML"
    )


async def kirim_report_callback(
    query,
    user_id,
    team_name
):

    items = get_report_items(
        user_id
    )

    report = buat_report_text(
        team_name,
        items
    )

    await query.edit_message_text(
        report,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Kembali ke Menu",
                    callback_data="cb_menu"
                )
            ]
        ])
    )


# =========================================================
# /START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    user = update.effective_user

    if not user:
        return

    get_user(user)

    first_name = (
        user.first_name
        or "Teman"
    )

    await update.message.reply_text(
        f"👋 <b>Halo, {escape(first_name)}!</b>\n\n"
        "Selamat datang di "
        "<b>Report Progress Bot</b> 📋\n\n"
        "Bot ini membantu kamu mencatat "
        "dan membuat report progress "
        "dengan lebih mudah.",
        parse_mode="HTML"
    )

    # /start selalu memulai setup nama
    context.user_data[
        "waiting_name"
    ] = True

    await update.message.reply_text(
        "📋 <b>SETUP NAMA TIM</b>\n\n"
        f"Tanggal: <b>{tanggal_indonesia()}</b>\n\n"
        "Silakan isi nama tim anda hari ini.\n\n"
        "Contoh:\n"
        "<code>Bagas - Giver</code>",
        parse_mode="HTML"
    )


# =========================================================
# /MENU
# =========================================================

async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    data = get_user(user)

    # Cek pergantian hari
    if is_new_day_for_user(user.id):

        await minta_nama_hari_ini(
            update.message,
            context,
            user.first_name
        )

        return

    context.user_data.clear()

    await tampilkan_menu_message(
        update.message,
        data
    )


# =========================================================
# /REPORT
# =========================================================

async def command_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    data = get_user(user)

    # Jika hari baru, minta nama tim dulu
    if is_new_day_for_user(user.id):

        await minta_nama_hari_ini(
            update.message,
            context,
            user.first_name
        )

        return

    context.user_data.clear()

    await kirim_report_message(
        update.message,
        user.id,
        data["team_name"]
    )


# =========================================================
# /NAMA
# =========================================================

async def command_nama(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data[
        "waiting_name"
    ] = True

    data = get_user(
        update.effective_user
    )

    await update.message.reply_text(
        "👤 <b>UBAH NAMA TIM</b>\n\n"
        f"Nama sekarang:\n"
        f"<b>{escape(data.get('team_name', 'Belum diatur'))}</b>\n\n"
        "Silakan kirim nama tim baru.\n\n"
        "Contoh:\n"
        "<code>Bagas - Giver</code>",
        parse_mode="HTML"
    )


# =========================================================
# /RESET
# =========================================================

async def command_reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    # Hanya menghapus report HARI INI
    delete_all_report_items(
        user.id
    )

    context.user_data.clear()

    await update.message.reply_text(
        "🗑️ <b>DATA HARI INI BERHASIL DIHAPUS</b>\n\n"
        "Semua nomor dan status report hari ini "
        "sudah dihapus.\n\n"
        "Nama tim tetap tersimpan.",
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# /TUTORIAL
# =========================================================

async def tutor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📚 <b>TUTORIAL REPORT PROGRESS</b>\n\n"

        "<b>1. Nama Tim</b>\n"
        "Gunakan /nama untuk mengubah nama tim.\n\n"

        "<b>2. Tambah Data</b>\n"
        "Pilih ➕ Tambah Data, masukkan nomor, "
        "pilih kategori, lalu status.\n\n"

        "<b>3. Kategori</b>\n"
        "• IB REGULER\n"
        "• IB SAMEDAY\n"
        "• IB H+0\n"
        "• MT REGULER\n"
        "• MT H+0\n\n"

        "<b>4. Status</b>\n"
        "• <b>DONE</b> ✅\n"
        "• <b>PENDING</b> 🅿️\n"
        "• <b>CANCEL</b> ❌\n\n"

        "<b>5. Report</b>\n"
        "Pilih 📄 Buat Report untuk melihat "
        "report hari ini.\n\n"

        "<b>6. Hari Baru</b>\n"
        "Report otomatis berganti berdasarkan "
        "tanggal WIB. Pada hari baru, bot akan "
        "meminta nama tim hari itu.\n\n"

        "<b>7. Reset</b>\n"
        "/reset hanya menghapus data report "
        "hari ini. Data tanggal sebelumnya tetap "
        "tersimpan di Supabase.\n\n"

        "⏰ Zona waktu: <b>Asia/Jakarta (WIB)</b>",

        parse_mode="HTML"
    )


# =========================================================
# PESAN TEKS
# =========================================================

async def pesan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user = update.effective_user

    if not user:
        return

    text = (
        update.message.text
        or ""
    ).strip()

    user_id = user.id

    # =====================================================
    # TUTORIAL
    # =====================================================

    if text == "📚 Tutorial":

        await tutor(
            update,
            context
        )

        return

    # =====================================================
    # CEK HARI BARU
    # =====================================================

    # Jangan ganggu proses pengisian nama
    if not context.user_data.get(
        "waiting_name"
    ):

        if is_new_day_for_user(user_id):

            await minta_nama_hari_ini(
                update.message,
                context,
                user.first_name
            )

            return

    # =====================================================
    # NAMA TIM
    # =====================================================

    if context.user_data.get(
        "waiting_name"
    ):

        if len(text) < 2:

            await update.message.reply_text(
                "⚠️ Nama tim terlalu pendek.\n\n"
                "Silakan masukkan nama tim lagi."
            )

            return

        if len(text) > 50:

            await update.message.reply_text(
                "⚠️ Nama tim maksimal 50 karakter."
            )

            return

        update_team_name(
            user_id,
            text
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ <b>NAMA TIM BERHASIL DISIMPAN</b>\n\n"
            f"👥 Tim: <b>{escape(text)}</b>\n"
            f"📅 Tanggal: <b>{tanggal_indonesia()}</b>\n\n"
            "Sekarang kamu bisa mulai membuat report.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return

    # =====================================================
    # NOMOR TAMBAH DATA
    # =====================================================

    if context.user_data.get(
        "waiting_number"
    ):

        if not text.isdigit():

            await update.message.reply_text(
                "⚠️ Nomor harus berupa angka saja.\n\n"
                "Contoh:\n"
                "<code>6345483</code>",
                parse_mode="HTML"
            )

            return

        if len(text) < 4 or len(text) > 20:

            await update.message.reply_text(
                "⚠️ Nomor harus 4–20 digit."
            )

            return

        context.user_data[
            "number"
        ] = text

        context.user_data[
            "waiting_number"
        ] = False

        category = context.user_data.get(
            "category"
        )

        if not category:

            await update.message.reply_text(
                "📂 <b>PILIH KATEGORI</b>\n\n"
                f"🔢 Nomor: <code>{escape(text)}</code>\n\n"
                "Pilih kategori:",
                parse_mode="HTML",
                reply_markup=kategori_keyboard()
            )

            return

        await update.message.reply_text(
            "📊 <b>PILIH STATUS</b>\n\n"
            f"🔢 Nomor: <code>{escape(text)}</code>\n"
            f"📂 Kategori: "
            f"<b>{escape(KATEGORI[category])}</b>\n\n"
            "Pilih status:",
            parse_mode="HTML",
            reply_markup=status_keyboard()
        )

        return

    # =====================================================
    # NOMOR EDIT
    # =====================================================

    if context.user_data.get(
        "waiting_edit_number"
    ):

        if not text.isdigit():

            await update.message.reply_text(
                "⚠️ Nomor harus berupa angka saja."
            )

            return

        if len(text) < 4 or len(text) > 20:

            await update.message.reply_text(
                "⚠️ Nomor harus 4–20 digit."
            )

            return

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:

            context.user_data.clear()

            await update.message.reply_text(
                "⚠️ Data edit tidak ditemukan.",
                reply_markup=menu_keyboard()
            )

            return

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            context.user_data.clear()

            await update.message.reply_text(
                "⚠️ Data tidak ditemukan.",
                reply_markup=menu_keyboard()
            )

            return

        update_report_number(
            user_id,
            item_id,
            text
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ <b>NOMOR BERHASIL DIUBAH</b>\n\n"
            f"Nomor baru: <code>{escape(text)}</code>",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return

    # =====================================================
    # TAMBAH DATA
    # =====================================================

    if text == "➕ Tambah Data":

        context.user_data.clear()

        context.user_data[
            "waiting_number"
        ] = True

        await update.message.reply_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            "Silakan kirim nomor terlebih dahulu.\n\n"
            "Contoh:\n"
            "<code>6345483</code>",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # REPORT
    # =====================================================

    if text == "📄 Buat Report":

        data = get_user(user)

        if is_new_day_for_user(user_id):

            await minta_nama_hari_ini(
                update.message,
                context,
                user.first_name
            )

            return

        context.user_data.clear()

        await kirim_report_message(
            update.message,
            user_id,
            data["team_name"]
        )

        return

    # =====================================================
    # EDIT DATA
    # =====================================================

    if text == "✏️ Edit Data":

        context.user_data.clear()

        items = get_report_items(
            user_id
        )

        if not items:

            await update.message.reply_text(
                "✏️ <b>EDIT DATA</b>\n\n"
                "Belum ada data yang bisa diedit.",
                parse_mode="HTML",
                reply_markup=menu_keyboard()
            )

            return

        keyboard = []

        for item in items:

            category_name = KATEGORI.get(
                item["category"],
                item["category"]
            )

            status_data = STATUS.get(
                item["status"],
                ("UNKNOWN", "❔")
            )

            label = (
                f"{item['number']} • "
                f"{category_name} • "
                f"{status_data[1]}"
            )

            if len(label) > 55:
                label = label[:52] + "..."

            keyboard.append([
                InlineKeyboardButton(
                    label,
                    callback_data=(
                        f"edititem_{item['id']}"
                    )
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ])

        await update.message.reply_text(
            "✏️ <b>EDIT DATA</b>\n\n"
            "Pilih data yang ingin diedit:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # =====================================================
    # HAPUS DATA
    # =====================================================

    if text == "🗑️ Hapus Data":

        context.user_data.clear()

        items = get_report_items(
            user_id
        )

        if not items:

            await update.message.reply_text(
                "🗑️ <b>HAPUS DATA</b>\n\n"
                "Belum ada data yang bisa dihapus.",
                parse_mode="HTML",
                reply_markup=menu_keyboard()
            )

            return

        keyboard = []

        for item in items:

            category_name = KATEGORI.get(
                item["category"],
                item["category"]
            )

            status_data = STATUS.get(
                item["status"],
                ("UNKNOWN", "❔")
            )

            label = (
                f"{item['number']} • "
                f"{category_name} • "
                f"{status_data[1]}"
            )

            if len(label) > 55:
                label = label[:52] + "..."

            keyboard.append([
                InlineKeyboardButton(
                    label,
                    callback_data=(
                        f"deleteitem_{item['id']}"
                    )
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ])

        await update.message.reply_text(
            "🗑️ <b>HAPUS DATA</b>\n\n"
            "Pilih data yang ingin dihapus:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # =====================================================
    # UBAH NAMA TIM
    # =====================================================

    if text == "👤 Ubah Nama Tim":

        await command_nama(
            update,
            context
        )

        return

    # =====================================================
    # PESAN TIDAK DIKENAL
    # =====================================================

    await update.message.reply_text(
        "Silakan gunakan tombol menu di bawah.",
        reply_markup=menu_keyboard()
    )


# =========================================================
# CALLBACK BUTTON
# =========================================================

async def tombol(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    user = update.effective_user

    if not user:
        return

    user_id = user.id

    pilihan = query.data or ""

    # =====================================================
    # CEK HARI BARU
    # =====================================================

    if pilihan != "cb_tutor":

        if not context.user_data.get(
            "waiting_name"
        ):

            if is_new_day_for_user(user_id):

                await minta_nama_hari_ini(
                    query.message,
                    context,
                    user.first_name
                )

                return

    # =====================================================
    # TUTOR
    # =====================================================

    if pilihan == "cb_tutor":

        await query.message.reply_text(
            "📚 <b>TUTORIAL REPORT PROGRESS</b>\n\n"
            "Gunakan /tutor untuk melihat "
            "panduan lengkap.",
            parse_mode="HTML"
        )

        return

    data = get_user(user)

    # =====================================================
    # MENU
    # =====================================================

    if pilihan == "cb_menu":

        context.user_data.clear()

        await tampilkan_menu_callback(
            query,
            data
        )

        return

    # =====================================================
    # TAMBAH
    # =====================================================

    if pilihan == "cb_add":

        context.user_data.clear()

        context.user_data[
            "waiting_number"
        ] = True

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            "Silakan kirim nomor terlebih dahulu.\n\n"
            "Contoh:\n"
            "<code>6345483</code>",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # KATEGORI TAMBAH
    # =====================================================

    if pilihan.startswith("addcat_"):

        category = pilihan[
            len("addcat_"):
        ]

        if category not in KATEGORI:

            await query.edit_message_text(
                "⚠️ Kategori tidak valid.",
                reply_markup=inline_menu_keyboard()
            )

            return

        context.user_data[
            "category"
        ] = category

        number = context.user_data.get(
            "number"
        )

        if number:

            await query.edit_message_text(
                "📊 <b>PILIH STATUS</b>\n\n"
                f"🔢 Nomor: "
                f"<code>{escape(number)}</code>\n"
                f"📂 Kategori: "
                f"<b>{escape(KATEGORI[category])}</b>\n\n"
                "Pilih status:",
                parse_mode="HTML",
                reply_markup=status_keyboard()
            )

            return

        context.user_data[
            "waiting_number"
        ] = True

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            f"📂 Kategori: "
            f"<b>{escape(KATEGORI[category])}</b>\n\n"
            "Silakan kirim nomor.",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # STATUS TAMBAH
    # =====================================================

    if pilihan.startswith("addstatus_"):

        status = pilihan[
            len("addstatus_"):
        ]

        if status not in STATUS:

            await query.edit_message_text(
                "⚠️ Status tidak valid.",
                reply_markup=inline_menu_keyboard()
            )

            return

        category = context.user_data.get(
            "category"
        )

        number = context.user_data.get(
            "number"
        )

        if not category or not number:

            await query.edit_message_text(
                "⚠️ Data sementara tidak ditemukan.\n\n"
                "Silakan mulai lagi.",
                reply_markup=inline_menu_keyboard()
            )

            return

        add_report_item(
            user_id,
            number,
            category,
            status
        )

        status_name, emoji = STATUS[
            status
        ]

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>DATA BERHASIL DITAMBAHKAN</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(number)}</code>\n"
            f"📂 Kategori: "
            f"<b>{escape(KATEGORI[category])}</b>\n"
            f"📊 Status: "
            f"<b>{escape(status_name)}</b> {emoji}\n\n"
            "Data sudah tersimpan.",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # REPORT
    # =====================================================

    if pilihan == "cb_report":

        context.user_data.clear()

        await kirim_report_callback(
            query,
            user_id,
            data["team_name"]
        )

        return

    # =====================================================
    # NAMA TIM
    # =====================================================

    if pilihan == "cb_teamname":

        context.user_data.clear()

        context.user_data[
            "waiting_name"
        ] = True

        await query.edit_message_text(
            "👤 <b>UBAH NAMA TIM</b>\n\n"
            f"Nama sekarang:\n"
            f"<b>{escape(data.get('team_name', 'Belum diatur'))}</b>\n\n"
            "Silakan kirim nama tim baru.",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # DAFTAR EDIT
    # =====================================================

    if pilihan == "cb_editlist":

        items = get_report_items(
            user_id
        )

        if not items:

            await query.edit_message_text(
                "✏️ <b>EDIT DATA</b>\n\n"
                "Belum ada data yang bisa diedit.",
                parse_mode="HTML",
                reply_markup=inline_menu_keyboard()
            )

            return

        keyboard = []

        for item in items:

            category_name = KATEGORI.get(
                item["category"],
                item["category"]
            )

            status_data = STATUS.get(
                item["status"],
                ("UNKNOWN", "❔")
            )

            label = (
                f"{item['number']} • "
                f"{category_name} • "
                f"{status_data[1]}"
            )

            if len(label) > 55:
                label = label[:52] + "..."

            keyboard.append([
                InlineKeyboardButton(
                    label,
                    callback_data=(
                        f"edititem_{item['id']}"
                    )
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ])

        await query.edit_message_text(
            "✏️ <b>EDIT DATA</b>\n\n"
            "Pilih data yang ingin diedit:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # =====================================================
    # PILIH DATA EDIT
    # =====================================================

    if pilihan.startswith("edititem_"):

        item_id_text = pilihan[
            len("edititem_"):
        ]

        if not item_id_text.isdigit():
            return

        item_id = int(
            item_id_text
        )

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            await query.edit_message_text(
                "⚠️ Data tidak ditemukan.",
                reply_markup=inline_menu_keyboard()
            )

            return

        context.user_data[
            "edit_item_id"
        ] = item_id

        category_name = KATEGORI.get(
            item["category"],
            item["category"]
        )

        status_data = STATUS.get(
            item["status"],
            ("UNKNOWN", "❔")
        )

        await query.edit_message_text(
            "✏️ <b>EDIT DATA</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"📂 Kategori: "
            f"<b>{escape(category_name)}</b>\n"
            f"📊 Status: "
            f"<b>{escape(status_data[0])}</b> "
            f"{status_data[1]}\n\n"
            "Apa yang ingin diubah?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔢 Nomor",
                        callback_data="editnum"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📂 Kategori",
                        callback_data="editcategory"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Status",
                        callback_data="editstatus"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Kembali",
                        callback_data="cb_editlist"
                    )
                ]
            ])
        )

        return

    # =====================================================
    # EDIT NOMOR
    # =====================================================

    if pilihan == "editnum":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:

            await query.edit_message_text(
                "⚠️ Data edit tidak ditemukan.",
                reply_markup=inline_menu_keyboard()
            )

            return

        context.user_data[
            "waiting_edit_number"
        ] = True

        await query.edit_message_text(
            "🔢 <b>UBAH NOMOR</b>\n\n"
            "Silakan kirim nomor baru.\n\n"
            "Contoh:\n"
            "<code>6345483</code>",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # EDIT KATEGORI
    # =====================================================

    if pilihan == "editcategory":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        await query.edit_message_text(
            "📂 <b>UBAH KATEGORI</b>\n\n"
            "Pilih kategori baru:",
            parse_mode="HTML",
            reply_markup=kategori_keyboard(
                prefix="editcat"
            )
        )

        return

    # =====================================================
    # PILIH KATEGORI EDIT
    # =====================================================

    if pilihan.startswith("editcat_"):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        category = pilihan[
            len("editcat_"):
        ]

        if not item_id:
            return

        if category not in KATEGORI:
            return

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:
            return

        update_report_category(
            user_id,
            item_id,
            category
        )

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>KATEGORI BERHASIL DIUBAH</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"📂 Kategori baru: "
            f"<b>{escape(KATEGORI[category])}</b>",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # EDIT STATUS
    # =====================================================

    if pilihan == "editstatus":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        await query.edit_message_text(
            "📊 <b>UBAH STATUS</b>\n\n"
            "Pilih status baru:",
            parse_mode="HTML",
            reply_markup=status_keyboard(
                prefix="editstat"
            )
        )

        return

    # =====================================================
    # PILIH STATUS EDIT
    # =====================================================

    if pilihan.startswith("editstat_"):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        status = pilihan[
            len("editstat_"):
        ]

        if not item_id:
            return

        if status not in STATUS:
            return

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:
            return

        update_report_status(
            user_id,
            item_id,
            status
        )

        status_name, emoji = STATUS[
            status
        ]

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>STATUS BERHASIL DIUBAH</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"📊 Status baru: "
            f"<b>{escape(status_name)}</b> {emoji}",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # DAFTAR HAPUS
    # =====================================================

    if pilihan == "cb_deletelist":

        context.user_data.clear()

        items = get_report_items(
            user_id
        )

        if not items:

            await query.edit_message_text(
                "🗑️ <b>HAPUS DATA</b>\n\n"
                "Belum ada data yang bisa dihapus.",
                parse_mode="HTML",
                reply_markup=inline_menu_keyboard()
            )

            return

        keyboard = []

        for item in items:

            category_name = KATEGORI.get(
                item["category"],
                item["category"]
            )

            status_data = STATUS.get(
                item["status"],
                ("UNKNOWN", "❔")
            )

            label = (
                f"{item['number']} • "
                f"{category_name} • "
                f"{status_data[1]}"
            )

            if len(label) > 55:
                label = label[:52] + "..."

            keyboard.append([
                InlineKeyboardButton(
                    label,
                    callback_data=(
                        f"deleteitem_{item['id']}"
                    )
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ])

        await query.edit_message_text(
            "🗑️ <b>HAPUS DATA</b>\n\n"
            "Pilih data yang ingin dihapus:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

        return

    # =====================================================
    # PILIH DATA HAPUS
    # =====================================================

    if pilihan.startswith("deleteitem_"):

        item_id_text = pilihan[
            len("deleteitem_"):
        ]

        if not item_id_text.isdigit():
            return

        item_id = int(
            item_id_text
        )

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            await query.edit_message_text(
                "⚠️ Data tidak ditemukan.",
                reply_markup=inline_menu_keyboard()
            )

            return

        category_name = KATEGORI.get(
            item["category"],
            item["category"]
        )

        await query.edit_message_text(
            "⚠️ <b>KONFIRMASI HAPUS</b>\n\n"
            "Apakah kamu yakin ingin menghapus:\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"📂 Kategori: "
            f"<b>{escape(category_name)}</b>\n\n"
            "Data yang dihapus tidak dapat dikembalikan.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ Ya, Hapus",
                        callback_data=(
                            f"confirmdelete_{item_id}"
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Batal",
                        callback_data="cb_deletelist"
                    )
                ]
            ])
        )

        return

    # =====================================================
    # KONFIRMASI HAPUS
    # =====================================================

    if pilihan.startswith("confirmdelete_"):

        item_id_text = pilihan[
            len("confirmdelete_"):
        ]

        if not item_id_text.isdigit():
            return

        item_id = int(
            item_id_text
        )

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            await query.edit_message_text(
                "⚠️ Data sudah tidak ditemukan.",
                reply_markup=inline_menu_keyboard()
            )

            return

        delete_report_item(
            user_id,
            item_id
        )

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>DATA BERHASIL DIHAPUS</b>\n\n"
            f"Nomor <code>{escape(str(item['number']))}</code> "
            "telah dihapus.",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # CALLBACK TIDAK DIKENAL
    # =====================================================

    print(
        f"Callback tidak dikenal: {pilihan}",
        flush=True
    )

    await query.edit_message_text(
        "⚠️ Tombol sudah tidak berlaku.\n\n"
        "Silakan kembali ke menu.",
        reply_markup=inline_menu_keyboard()
    )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        f"ERROR: {context.error!r}",
        flush=True
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "====================================",
        flush=True
    )

    print(
        "REPORT PROGRESS BOT",
        flush=True
    )

    print(
        "Zona waktu: Asia/Jakarta",
        flush=True
    )

    print(
        "Penyimpanan: Supabase",
        flush=True
    )

    print(
        "Mode: REPORT HARIAN OTOMATIS",
        flush=True
    )

    print(
        "====================================",
        flush=True
    )

    app = (
        Application
        .builder()
        .token(
            TELEGRAM_BOT_TOKEN
        )
        .build()
    )

    # =====================================================
    # COMMAND
    # =====================================================

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
        CommandHandler(
            "tutor",
            tutor
        )
    )

    # =====================================================
    # CALLBACK
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            tombol
        )
    )

    # =====================================================
    # PESAN TEXT
    # =====================================================

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            pesan
        )
    )

    # =====================================================
    # ERROR
    # =====================================================

    app.add_error_handler(
        error_handler
    )

    print(
        "Bot siap menerima pesan Telegram.",
        flush=True
    )

    app.run_polling()


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()