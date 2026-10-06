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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TIMEZONE = ZoneInfo("Asia/Jakarta")


if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN belum diatur."
    )

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL belum diatur."
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY belum diatur."
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
    "pending": ("PENDING", "⏳"),
    "cancel": ("CANCEL", "❌"),
}


# =========================================================
# TANGGAL WIB
# =========================================================

def today():
    return datetime.now(
        TIMEZONE
    ).date().isoformat()


# =========================================================
# DATABASE USER
# =========================================================

def get_user(user):

    result = (
        supabase
        .table("bot_users")
        .select("*")
        .eq(
            "telegram_user_id",
            user.id
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
            user.id
        ).execute()

        return row

    result = (
        supabase
        .table("bot_users")
        .insert({
            "telegram_user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "team_name": "Belum diatur",
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


# =========================================================
# DATABASE REPORT HARIAN
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


def delete_all_report_items(
    user_id
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
        .execute()
    )


# =========================================================
# MENU
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
        ],
    ])


# =========================================================
# KATEGORI
# =========================================================

def kategori_keyboard(
    prefix="addcat"
):

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
            InlineKeyboardButton(
                "MT REGULER",
                callback_data=f"{prefix}_mt_reguler"
            ),
        ],
        [
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
# STATUS
# =========================================================

def status_keyboard(
    prefix="addstatus"
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ DONE",
                callback_data=f"{prefix}_done"
            )
        ],
        [
            InlineKeyboardButton(
                "⏳ PENDING",
                callback_data=f"{prefix}_pending"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ CANCEL",
                callback_data=f"{prefix}_cancel"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="cb_menu"
            )
        ]
    ])


# =========================================================
# FORMAT REPORT
# =========================================================

def format_report(
    team_name,
    items
):

    now = datetime.now(
        TIMEZONE
    )

    months = [
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
        "Desember"
    ]

    grouped = {
        key: []
        for key in KATEGORI
    }

    for item in items:

        category = item.get(
            "category"
        )

        if category in grouped:
            grouped[category].append(
                item
            )

    lines = [
        "<b>REPORT PROGRESS</b>",
        "",
        f"Tim: {escape(str(team_name))}",
        (
            f"Tanggal: "
            f"{now.day:02d} "
            f"{months[now.month - 1]} "
            f"{now.year}"
        ),
        "",
    ]

    for key, label in KATEGORI.items():

        # KATEGORI BOLD
        lines.append(
            f"<b>{label}</b>"
        )

        category_items = grouped[key]

        if not category_items:

            lines.append("• -")

        else:

            for item in category_items:

                status_name, emoji = STATUS.get(
                    item.get("status"),
                    (
                        str(
                            item.get(
                                "status",
                                "UNKNOWN"
                            )
                        ).upper(),
                        "❔"
                    )
                )

                # ID + STATUS BOLD
                lines.append(
                    f"• "
                    f"{escape(str(item.get('number', '')))} "
                    f"(<b>{status_name}</b>) "
                    f"{emoji}"
                )

                # BARIS KOSONG SETELAH SETIAP ID
                lines.append("")

        # BARIS KOSONG ANTAR KATEGORI
        lines.append("")

    return "\n".join(
        lines
    ).rstrip()


# =========================================================
# TAMPILKAN MENU
# =========================================================

async def show_menu_message(
    message,
    data
):

    await message.reply_text(
        "📋 <b>REPORT PROGRESS</b>\n\n"
        f"👥 Tim: "
        f"<b>{escape(str(data['team_name']))}</b>\n\n"
        "Silakan pilih menu di bawah.",
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


async def show_menu_callback(
    query,
    data
):

    await query.edit_message_text(
        "📋 <b>REPORT PROGRESS</b>\n\n"
        f"👥 Tim: "
        f"<b>{escape(str(data['team_name']))}</b>\n\n"
        "Silakan pilih menu:",
        parse_mode="HTML",
        reply_markup=inline_menu_keyboard()
    )


# =========================================================
# KIRIM REPORT
# =========================================================

async def send_report_message(
    message,
    user_id,
    team_name
):

    items = get_report_items(
        user_id
    )

    report = format_report(
        team_name,
        items
    )

    await message.reply_text(
        report,
        parse_mode="HTML"
    )


async def send_report_callback(
    query,
    user_id,
    team_name
):

    items = get_report_items(
        user_id
    )

    report = format_report(
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
# TUTORIAL
# =========================================================

async def tutor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "<b>📚 TUTORIAL REPORT PROGRESS BOT</b>\n\n"

        "<b>1. Atur nama tim</b>\n"
        "Ketik /nama lalu masukkan nama tim.\n\n"

        "<b>2. Tambah data</b>\n"
        "Pilih ➕ Tambah Data.\n"
        "Masukkan nomor, pilih kategori, "
        "kemudian pilih status.\n\n"

        "<b>3. Buat report</b>\n"
        "Ketik /report atau pilih "
        "📄 Buat Report.\n\n"

        "<b>4. Pergantian hari otomatis</b>\n"
        "Pada pukul <b>00.00 WIB</b>, "
        "report otomatis menggunakan tanggal baru.\n"
        "Report hari baru otomatis kosong.\n"
        "Tidak perlu menggunakan /reset.\n\n"

        "<b>5. Data hari sebelumnya</b>\n"
        "Data lama tetap tersimpan di Supabase "
        "dan tidak ikut muncul pada report hari baru.\n\n"

        "<b>6. Reset manual</b>\n"
        "/reset hanya menghapus data "
        "report hari berjalan.\n\n"

        "<b>7. Zona waktu</b>\n"
        "Asia/Jakarta (WIB)"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
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

    data = get_user(
        user
    )

    first_name = (
        user.first_name
        or "Teman"
    )

    # SALAM PEMBUKA
    await update.message.reply_text(
        f"👋 <b>Halo, "
        f"{escape(first_name)}!</b>\n\n"
        "Selamat datang di "
        "<b>Report Progress Bot</b> 📋\n\n"
        "Bot ini membantu kamu mencatat "
        "dan membuat report progress "
        "dengan lebih mudah.\n\n"
        "🚀 Yuk, kita mulai!",
        parse_mode="HTML"
    )

    # USER BARU
    if (
        not data.get("team_name")
        or data["team_name"]
        == "Belum diatur"
    ):

        context.user_data[
            "waiting_name"
        ] = True

        await update.message.reply_text(
            "📋 <b>SETUP AWAL</b>\n\n"
            "Sebelum mulai, silakan isi "
            "nama tim kamu.\n\n"
            "Contoh:\n"
            "<code>Bagas-Toni</code>\n\n"
            "✏️ Silakan ketik nama tim kamu:",
            parse_mode="HTML"
        )

        return

    # USER LAMA
    await update.message.reply_text(
        f"👥 Tim: "
        f"<b>{escape(str(data['team_name']))}</b>\n\n"
        "Kamu sudah siap membuat report. 🚀\n\n"
        "Silakan pilih menu di bawah:",
        parse_mode="HTML",
        reply_markup=menu_keyboard()
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

    context.user_data.clear()

    data = get_user(
        user
    )

    await show_menu_message(
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

    context.user_data.clear()

    data = get_user(
        user
    )

    await send_report_message(
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
        f"<b>{escape(str(data['team_name']))}</b>\n\n"
        "Silakan kirim nama tim baru.\n\n"
        "Contoh:\n"
        "<code>Bagas-Toni</code>",
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

    # HANYA DATA HARI INI
    delete_all_report_items(
        user.id
    )

    context.user_data.clear()

    await update.message.reply_text(
        "🗑️ <b>REPORT HARI INI BERHASIL DIHAPUS</b>\n\n"
        "Data hari sebelumnya tetap tersimpan.",
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# DAFTAR DATA EDIT / HAPUS
# =========================================================

async def show_item_list(
    message,
    context,
    user_id,
    edit=True
):

    context.user_data.clear()

    items = get_report_items(
        user_id
    )

    if edit:

        action = "edititem"
        title = "✏️ <b>EDIT DATA</b>"

    else:

        action = "deleteitem"
        title = "🗑️ <b>HAPUS DATA</b>"

    if not items:

        await message.reply_text(
            f"{title}\n\n"
            "Belum ada data.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return

    keyboard = []

    for item in items:

        category = KATEGORI.get(
            item.get("category"),
            item.get("category", "")
        )

        status = STATUS.get(
            item.get("status"),
            ("Unknown", "❔")
        )[1]

        label = (
            f"{item.get('number')} • "
            f"{category} • "
            f"{status}"
        )

        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=(
                    f"{action}_{item.get('id')}"
                )
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Kembali",
            callback_data="cb_menu"
        )
    ])

    await message.reply_text(
        f"{title}\n\n"
        "Pilih data:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


async def show_item_list_callback(
    query,
    context,
    user_id,
    edit=True
):

    context.user_data.clear()

    items = get_report_items(
        user_id
    )

    if edit:

        action = "edititem"
        title = "✏️ <b>EDIT DATA</b>"

    else:

        action = "deleteitem"
        title = "🗑️ <b>HAPUS DATA</b>"

    if not items:

        await query.edit_message_text(
            f"{title}\n\n"
            "Belum ada data.",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    keyboard = []

    for item in items:

        category = KATEGORI.get(
            item.get("category"),
            item.get("category", "")
        )

        status = STATUS.get(
            item.get("status"),
            ("Unknown", "❔")
        )[1]

        label = (
            f"{item.get('number')} • "
            f"{category} • "
            f"{status}"
        )

        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=(
                    f"{action}_{item.get('id')}"
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
        f"{title}\n\n"
        "Pilih data:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# PESAN TEXT
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
    # NAMA TIM
    # =====================================================

    if context.user_data.get(
        "waiting_name"
    ):

        if len(text) < 2:

            await update.message.reply_text(
                "⚠️ Nama tim terlalu pendek."
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
            f"👥 Tim: <b>{escape(text)}</b>",
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

        if (
            not text.isdigit()
            or not 4 <= len(text) <= 20
        ):

            await update.message.reply_text(
                "⚠️ Nomor harus berupa "
                "4–20 digit angka."
            )

            return

        context.user_data[
            "number"
        ] = text

        context.user_data[
            "waiting_number"
        ] = False

        await update.message.reply_text(
            "📂 <b>PILIH KATEGORI</b>",
            parse_mode="HTML",
            reply_markup=kategori_keyboard()
        )

        return

    # =====================================================
    # NOMOR EDIT
    # =====================================================

    if context.user_data.get(
        "waiting_edit_number"
    ):

        if (
            not text.isdigit()
            or not 4 <= len(text) <= 20
        ):

            await update.message.reply_text(
                "⚠️ Nomor harus berupa "
                "4–20 digit angka."
            )

            return

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if (
            not item_id
            or not get_report_item(
                user_id,
                item_id
            )
        ):

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
            "✅ <b>NOMOR BERHASIL DIUBAH</b>",
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
            "Kirim nomor:\n"
            "<code>1234567</code>",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # REPORT
    # =====================================================

    if text == "📄 Buat Report":

        context.user_data.clear()

        data = get_user(
            user
        )

        await send_report_message(
            update.message,
            user_id,
            data["team_name"]
        )

        return

    # =====================================================
    # EDIT
    # =====================================================

    if text == "✏️ Edit Data":

        await show_item_list(
            update.message,
            context,
            user_id,
            edit=True
        )

        return

    # =====================================================
    # HAPUS
    # =====================================================

    if text == "🗑️ Hapus Data":

        await show_item_list(
            update.message,
            context,
            user_id,
            edit=False
        )

        return

    # =====================================================
    # NAMA
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

    if not query:
        return

    user = update.effective_user

    if not user:
        return

    await query.answer()

    user_id = user.id

    data = get_user(
        user
    )

    pilihan = (
        query.data
        or ""
    )

    # =====================================================
    # KEMBALI MENU
    # =====================================================

    if pilihan == "cb_menu":

        context.user_data.clear()

        await show_menu_callback(
            query,
            data
        )

        return

    # =====================================================
    # TUTOR
    # =====================================================

    if pilihan == "cb_tutor":

        await query.edit_message_text(
            "<b>📚 TUTORIAL</b>\n\n"
            "➕ Tambah Data untuk menambahkan report.\n\n"
            "📄 Buat Report untuk melihat report.\n\n"
            "Setiap <b>00.00 WIB</b>, "
            "report otomatis berganti tanggal "
            "dan mulai kosong.\n\n"
            "/reset hanya menghapus report hari ini.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ Kembali",
                        callback_data="cb_menu"
                    )
                ]
            ])
        )

        return

    # =====================================================
    # TAMBAH DATA
    # =====================================================

    if pilihan == "cb_add":

        context.user_data.clear()

        context.user_data[
            "waiting_number"
        ] = True

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            "Kirim nomor:\n"
            "<code>1234567</code>",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # REPORT
    # =====================================================

    if pilihan == "cb_report":

        context.user_data.clear()

        await send_report_callback(
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
            "Kirim nama tim baru:",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # DAFTAR EDIT
    # =====================================================

    if pilihan == "cb_editlist":

        await show_item_list_callback(
            query,
            context,
            user_id,
            edit=True
        )

        return

    # =====================================================
    # DAFTAR HAPUS
    # =====================================================

    if pilihan == "cb_deletelist":

        await show_item_list_callback(
            query,
            context,
            user_id,
            edit=False
        )

        return

    # =====================================================
    # PILIH KATEGORI TAMBAH
    # =====================================================

    if pilihan.startswith(
        "addcat_"
    ):

        category = pilihan[
            len("addcat_"):
        ]

        if category not in KATEGORI:
            return

        context.user_data[
            "category"
        ] = category

        await query.edit_message_text(
            "📊 <b>PILIH STATUS</b>",
            parse_mode="HTML",
            reply_markup=status_keyboard()
        )

        return

    # =====================================================
    # PILIH STATUS TAMBAH
    # =====================================================

    if pilihan.startswith(
        "addstatus_"
    ):

        status = pilihan[
            len("addstatus_"):
        ]

        number = context.user_data.get(
            "number"
        )

        category = context.user_data.get(
            "category"
        )

        if (
            status not in STATUS
            or not number
            or category not in KATEGORI
        ):

            context.user_data.clear()

            await query.edit_message_text(
                "⚠️ Data belum lengkap.",
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
            f"🔢 <code>{escape(number)}</code>\n"
            f"📂 <b>{KATEGORI[category]}</b>\n"
            f"📊 <b>{status_name}</b> {emoji}",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # PILIH DATA EDIT
    # =====================================================

    if pilihan.startswith(
        "edititem_"
    ):

        try:
            item_id = int(
                pilihan[
                    len("edititem_"):
                ]
            )
        except ValueError:
            return

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

        await query.edit_message_text(
            "✏️ <b>PILIH YANG INGIN DIUBAH</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔢 Nomor",
                        callback_data="edit_number"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📂 Kategori",
                        callback_data="edit_category"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Status",
                        callback_data="edit_status"
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

    if pilihan == "edit_number":

        context.user_data[
            "waiting_edit_number"
        ] = True

        await query.edit_message_text(
            "🔢 <b>UBAH NOMOR</b>\n\n"
            "Kirim nomor baru:",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # EDIT KATEGORI
    # =====================================================

    if pilihan == "edit_category":

        await query.edit_message_text(
            "📂 <b>UBAH KATEGORI</b>",
            parse_mode="HTML",
            reply_markup=kategori_keyboard(
                "editcat"
            )
        )

        return

    # =====================================================
    # PILIH KATEGORI EDIT
    # =====================================================

    if pilihan.startswith(
        "editcat_"
    ):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        category = pilihan[
            len("editcat_"):
        ]

        if (
            not item_id
            or category not in KATEGORI
        ):
            return

        if not get_report_item(
            user_id,
            item_id
        ):
            return

        update_report_category(
            user_id,
            item_id,
            category
        )

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>KATEGORI BERHASIL DIUBAH</b>",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # EDIT STATUS
    # =====================================================

    if pilihan == "edit_status":

        await query.edit_message_text(
            "📊 <b>UBAH STATUS</b>",
            parse_mode="HTML",
            reply_markup=status_keyboard(
                "editstat"
            )
        )

        return

    # =====================================================
    # PILIH STATUS EDIT
    # =====================================================

    if pilihan.startswith(
        "editstat_"
    ):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        status = pilihan[
            len("editstat_"):
        ]

        if (
            not item_id
            or status not in STATUS
        ):
            return

        if not get_report_item(
            user_id,
            item_id
        ):
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
            f"Status baru: "
            f"<b>{status_name}</b> {emoji}",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return

    # =====================================================
    # PILIH DATA HAPUS
    # =====================================================

    if pilihan.startswith(
        "deleteitem_"
    ):

        try:
            item_id = int(
                pilihan[
                    len("deleteitem_"):
                ]
            )
        except ValueError:
            return

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
            item.get("category"),
            item.get("category", "")
        )

        await query.edit_message_text(
            "⚠️ <b>KONFIRMASI HAPUS</b>\n\n"
            f"Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"Kategori: "
            f"<b>{escape(category_name)}</b>\n\n"
            "Apakah kamu yakin ingin menghapus data ini?",
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

    if pilihan.startswith(
        "confirmdelete_"
    ):

        try:
            item_id = int(
                pilihan[
                    len("confirmdelete_"):
                ]
            )
        except ValueError:
            return

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

        delete_report_item(
            user_id,
            item_id
        )

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>DATA BERHASIL DIHAPUS</b>",
            parse_mode="HTML",
            reply_markup=inline_menu_keyboard()
        )

        return


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

    # COMMAND
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

    # CALLBACK
    app.add_handler(
        CallbackQueryHandler(
            tombol
        )
    )

    # TEXT
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            pesan
        )
    )

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