import os
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape

from supabase import create_client
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN belum diatur")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL belum diatur")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY belum diatur")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)

TIMEZONE = ZoneInfo("Asia/Jakarta")


# =========================================================
# KATEGORI & STATUS
# =========================================================

KATEGORI = {
    "ib_reguler": "IB REGULER",
    "ib_sameday": "IB SAMEDAY",
    "ib_h0": "IB H+0",
    "mt_reguler": "MT REGULER",
    "mt_h0": "MT H+0",
}

STATUS = {
    "done": ("DONE", "✅"),
    "pending": ("PENDING", "🅿️"),
    "cancel": ("CANCEL", "❌"),
}


# =========================================================
# WAKTU
# =========================================================

def sekarang():
    return datetime.now(TIMEZONE)


def today():
    return sekarang().date().isoformat()


def tanggal_indonesia():
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

    dt = sekarang()

    return f"{dt.day:02d} {bulan[dt.month - 1]} {dt.year}"


# =========================================================
# USER
# =========================================================

def get_user(user_id):
    result = (
        supabase
        .table("bot_users")
        .select("*")
        .eq("telegram_user_id", user_id)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    result = (
        supabase
        .table("bot_users")
        .insert({
            "telegram_user_id": user_id,
            "team_name": "Belum diatur",
            "team_name_date": None,
        })
        .execute()
    )

    return result.data[0] if result.data else None


def update_user_info(user):
    user_id = user.id

    data = {
        "username": user.username,
        "first_name": user.first_name,
        "updated_at": sekarang().isoformat(),
    }

    (
        supabase
        .table("bot_users")
        .update(data)
        .eq("telegram_user_id", user_id)
        .execute()
    )


def update_team_name(user_id, team_name):
    (
        supabase
        .table("bot_users")
        .update({
            "team_name": team_name,
            "team_name_date": today(),
            "updated_at": sekarang().isoformat(),
        })
        .eq("telegram_user_id", user_id)
        .execute()
    )


def is_new_day_for_user(user_id):
    result = (
        supabase
        .table("bot_users")
        .select("team_name_date")
        .eq("telegram_user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return True

    saved_date = result.data[0].get("team_name_date")

    return saved_date != today()


# =========================================================
# REPORT DATABASE
# =========================================================

def get_report_items(user_id):
    result = (
        supabase
        .table("report_items")
        .select("*")
        .eq("telegram_user_id", user_id)
        .eq("report_date", today())
        .order("id")
        .execute()
    )

    return result.data or []


def get_report_item(user_id, item_id):
    result = (
        supabase
        .table("report_items")
        .select("*")
        .eq("telegram_user_id", user_id)
        .eq("id", item_id)
        .eq("report_date", today())
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def add_report_item(user_id, number, category, status):
    (
        supabase
        .table("report_items")
        .insert({
            "telegram_user_id": user_id,
            "number": number,
            "category": category,
            "status": status,
            "report_date": today(),
        })
        .execute()
    )


def update_report_number(user_id, item_id, number):
    (
        supabase
        .table("report_items")
        .update({
            "number": number,
        })
        .eq("telegram_user_id", user_id)
        .eq("id", item_id)
        .eq("report_date", today())
        .execute()
    )


def update_report_category(user_id, item_id, category):
    (
        supabase
        .table("report_items")
        .update({
            "category": category,
        })
        .eq("telegram_user_id", user_id)
        .eq("id", item_id)
        .eq("report_date", today())
        .execute()
    )


def update_report_status(user_id, item_id, status):
    (
        supabase
        .table("report_items")
        .update({
            "status": status,
        })
        .eq("telegram_user_id", user_id)
        .eq("id", item_id)
        .eq("report_date", today())
        .execute()
    )


def delete_report_item(user_id, item_id):
    (
        supabase
        .table("report_items")
        .delete()
        .eq("telegram_user_id", user_id)
        .eq("id", item_id)
        .eq("report_date", today())
        .execute()
    )


def reset_today(user_id):
    (
        supabase
        .table("report_items")
        .delete()
        .eq("telegram_user_id", user_id)
        .eq("report_date", today())
        .execute()
    )


# =========================================================
# FORMAT REPORT
# =========================================================

def buat_report_html(team_name, items):

    header = (
        "REPORT PROGRESS\n\n"
        f"TEAM: {escape(team_name)}\n"
        f"TANGGAL: {tanggal_indonesia()}"
    )

    blocks = [header]

    for category_key, category_name in KATEGORI.items():

        category_items = [
            item
            for item in items
            if item.get("category") == category_key
        ]

        category_lines = [
            f"<b>{escape(category_name)}</b>"
        ]

        item_lines = []

        for item in category_items:

            status_key = item.get("status")

            status_info = STATUS.get(
                status_key,
                ("UNKNOWN", "")
            )

            status_name = status_info[0]
            emoji = status_info[1]

            item_lines.append(
                f"• {escape(str(item.get('number', '')))} "
                f"<b>{escape(status_name)}</b> {emoji}"
            )

        if item_lines:
            category_lines.append(
                "\n".join(item_lines)
            )

        blocks.append(
            "\n".join(category_lines)
        )

    return "\n\n".join(blocks)


# =========================================================
# KEYBOARD MENU
# =========================================================

def menu_keyboard():

    keyboard = [
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
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
    )


# =========================================================
# INLINE KEYBOARDS
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
    ])


def status_keyboard(prefix="addstatus"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "DONE ✅",
                callback_data=f"{prefix}_done"
            ),
            InlineKeyboardButton(
                "PENDING 🅿️",
                callback_data=f"{prefix}_pending"
            ),
        ],
        [
            InlineKeyboardButton(
                "CANCEL ❌",
                callback_data=f"{prefix}_cancel"
            ),
        ],
    ])


# =========================================================
# DAILY SETUP
# =========================================================

async def minta_nama_hari_ini(target, context, user):

    context.user_data.clear()
    context.user_data["waiting_name"] = True

    nama = user.first_name or "Teman"

    pesan = (
        f"👋 Halo <b>{escape(nama)}</b>!\n\n"
        "Selamat datang di Report Progress Bot.\n\n"
        "📅 Hari ini sudah masuk tanggal baru.\n"
        "Silakan isi <b>nama tim anda hari ini</b>."
    )

    await target.reply_text(
        pesan,
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    get_user(user.id)
    update_user_info(user)

    context.user_data.clear()

    context.user_data["waiting_name"] = True

    nama = user.first_name or "Teman"

    pesan = (
        f"👋 Halo <b>{escape(nama)}</b>!\n\n"
        "Selamat datang di <b>Report Progress Bot</b>.\n\n"
        "Silakan isi <b>nama tim anda hari ini</b>."
    )

    await update.message.reply_text(
        pesan,
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# MENU
# =========================================================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    get_user(user.id)
    update_user_info(user)

    if context.user_data.get("waiting_name"):
        await update.message.reply_text(
            "Silakan isi nama tim anda hari ini."
        )
        return

    if is_new_day_for_user(user.id):
        await minta_nama_hari_ini(
            update.message,
            context,
            user,
        )
        return

    data = get_user(user.id)

    team_name = data.get("team_name") or "Belum diatur"

    await update.message.reply_text(
        f"📋 Menu Report Progress\n\n"
        f"TEAM: {team_name}",
        reply_markup=menu_keyboard(),
    )


# =========================================================
# COMMAND REPORT
# =========================================================

async def command_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    get_user(user.id)
    update_user_info(user)

    if context.user_data.get("waiting_name"):
        await update.message.reply_text(
            "Silakan isi nama tim anda hari ini terlebih dahulu."
        )
        return

    if is_new_day_for_user(user.id):
        await minta_nama_hari_ini(
            update.message,
            context,
            user,
        )
        return

    data = get_user(user.id)

    team_name = data.get("team_name") or "Belum diatur"

    items = get_report_items(user.id)

    report = buat_report_html(
        team_name,
        items,
    )

    await update.message.reply_text(
        report,
        parse_mode=ParseMode.HTML,
    )


# =========================================================
# COMMAND NAMA
# =========================================================

async def command_nama(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data["waiting_name"] = True

    await update.message.reply_text(
        "👤 Silakan masukkan nama tim anda hari ini."
    )


# =========================================================
# COMMAND RESET
# =========================================================

async def command_reset(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    get_user(user.id)
    update_user_info(user)

    if is_new_day_for_user(user.id):

        await minta_nama_hari_ini(
            update.message,
            context,
            user,
        )

        return

    reset_today(user.id)

    await update.message.reply_text(
        "♻️ Data report hari ini berhasil direset.\n\n"
        "Riwayat tanggal sebelumnya tetap aman."
    )


# =========================================================
# PESAN TEXT
# =========================================================

async def pesan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    text = update.message.text.strip()

    get_user(user.id)
    update_user_info(user)

    # -----------------------------------------------------
    # ISI NAMA TIM
    # -----------------------------------------------------

    if context.user_data.get("waiting_name"):

        team_name = text.strip()

        if not team_name:
            await update.message.reply_text(
                "Nama tim tidak boleh kosong.\n"
                "Silakan masukkan nama tim."
            )
            return

        update_team_name(
            user.id,
            team_name,
        )

        context.user_data.clear()

        await update.message.reply_text(
            f"✅ Nama tim berhasil disimpan.\n\n"
            f"TEAM: {team_name}\n"
            f"TANGGAL: {tanggal_indonesia()}\n\n"
            "Silakan pilih menu di bawah.",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # CEK HARI BARU
    # -----------------------------------------------------

    if is_new_day_for_user(user.id):

        await minta_nama_hari_ini(
            update.message,
            context,
            user,
        )

        return

    # -----------------------------------------------------
    # INPUT NOMOR UNTUK TAMBAH DATA
    # -----------------------------------------------------

    if context.user_data.get("waiting_number"):

        number = text.strip()

        if not number.isdigit():
            await update.message.reply_text(
                "❌ Nomor harus berupa angka.\n\n"
                "Silakan masukkan nomor kembali."
            )
            return

        context.user_data["number"] = number
        context.user_data.pop("waiting_number", None)

        await update.message.reply_text(
            "Pilih kategori:",
            reply_markup=kategori_keyboard("addcat"),
        )

        return

    # -----------------------------------------------------
    # INPUT NOMOR UNTUK EDIT
    # -----------------------------------------------------

    if context.user_data.get("waiting_edit_number"):

        number = text.strip()

        if not number.isdigit():
            await update.message.reply_text(
                "❌ Nomor harus berupa angka."
            )
            return

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            context.user_data.clear()

            await update.message.reply_text(
                "Data edit sudah tidak berlaku."
            )

            return

        update_report_number(
            user.id,
            item_id,
            number,
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ Nomor berhasil diubah.",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # TAMBAH DATA
    # -----------------------------------------------------

    if text == "➕ Tambah Data":

        context.user_data.clear()
        context.user_data["waiting_number"] = True

        await update.message.reply_text(
            "➕ <b>Tambah Data</b>\n\n"
            "Silakan masukkan nomor:",
            parse_mode=ParseMode.HTML,
        )

        return

    # -----------------------------------------------------
    # BUAT REPORT
    # -----------------------------------------------------

    if text == "📄 Buat Report":

        data = get_user(user.id)

        team_name = data.get(
            "team_name"
        ) or "Belum diatur"

        items = get_report_items(user.id)

        report = buat_report_html(
            team_name,
            items,
        )

        await update.message.reply_text(
            report,
            parse_mode=ParseMode.HTML,
        )

        return

    # -----------------------------------------------------
    # EDIT DATA
    # -----------------------------------------------------

    if text == "✏️ Edit Data":

        items = get_report_items(user.id)

        if not items:

            await update.message.reply_text(
                "Belum ada data untuk diedit.",
                reply_markup=menu_keyboard(),
            )

            return

        buttons = []

        for item in items:

            status_name = STATUS.get(
                item.get("status"),
                ("UNKNOWN", "")
            )[0]

            label = (
                f"{item.get('number')} "
                f"- {KATEGORI.get(item.get('category'), item.get('category'))} "
                f"- {status_name}"
            )

            buttons.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"edititem_{item['id']}",
                )
            ])

        await update.message.reply_text(
            "✏️ Pilih data yang ingin diedit:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        return

    # -----------------------------------------------------
    # HAPUS DATA
    # -----------------------------------------------------

    if text == "🗑️ Hapus Data":

        items = get_report_items(user.id)

        if not items:

            await update.message.reply_text(
                "Belum ada data untuk dihapus.",
                reply_markup=menu_keyboard(),
            )

            return

        buttons = []

        for item in items:

            label = (
                f"{item.get('number')} - "
                f"{KATEGORI.get(item.get('category'), item.get('category'))}"
            )

            buttons.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"deleteitem_{item['id']}",
                )
            ])

        await update.message.reply_text(
            "🗑️ Pilih data yang ingin dihapus:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        return

    # -----------------------------------------------------
    # UBAH NAMA TIM
    # -----------------------------------------------------

    if text == "👤 Ubah Nama Tim":

        context.user_data.clear()
        context.user_data["waiting_name"] = True

        await update.message.reply_text(
            "👤 Silakan masukkan nama tim yang baru."
        )

        return

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    await update.message.reply_text(
        "Silakan gunakan tombol menu di bawah.",
        reply_markup=menu_keyboard(),
    )


# =========================================================
# CALLBACK
# =========================================================

async def tombol(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = update.effective_user
    data = query.data

    get_user(user.id)
    update_user_info(user)

    # -----------------------------------------------------
    # CEK HARI BARU
    # -----------------------------------------------------

    if (
        not context.user_data.get("waiting_name")
        and is_new_day_for_user(user.id)
    ):

        context.user_data.clear()
        context.user_data["waiting_name"] = True

        await query.message.reply_text(
            "👋 Halo!\n\n"
            "Hari baru sudah dimulai.\n"
            "Silakan isi <b>nama tim anda hari ini</b>.",
            parse_mode=ParseMode.HTML,
        )

        return

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    if data == "cb_menu":

        await query.message.reply_text(
            "📋 Silakan pilih menu:",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # TAMBAH DATA
    # -----------------------------------------------------

    if data == "cb_add":

        context.user_data.clear()
        context.user_data["waiting_number"] = True

        await query.message.reply_text(
            "Silakan masukkan nomor:"
        )

        return

    # -----------------------------------------------------
    # PILIH KATEGORI TAMBAH
    # -----------------------------------------------------

    if data.startswith("addcat_"):

        category = data.replace(
            "addcat_",
            "",
            1,
        )

        if category not in KATEGORI:
            await query.message.reply_text(
                "Kategori tidak valid."
            )
            return

        context.user_data["category"] = category

        await query.message.reply_text(
            "Pilih status:",
            reply_markup=status_keyboard("addstatus"),
        )

        return

    # -----------------------------------------------------
    # PILIH STATUS TAMBAH
    # -----------------------------------------------------

    if data.startswith("addstatus_"):

        status = data.replace(
            "addstatus_",
            "",
            1,
        )

        if status not in STATUS:
            await query.message.reply_text(
                "Status tidak valid."
            )
            return

        number = context.user_data.get("number")
        category = context.user_data.get("category")

        if not number or not category:
            context.user_data.clear()

            await query.message.reply_text(
                "Sesi tambah data sudah berakhir.",
                reply_markup=menu_keyboard(),
            )

            return

        add_report_item(
            user.id,
            number,
            category,
            status,
        )

        context.user_data.clear()

        status_name, emoji = STATUS[status]

        await query.message.reply_text(
            f"✅ Data berhasil ditambahkan.\n\n"
            f"• {number} {status_name} {emoji}\n"
            f"Kategori: {KATEGORI[category]}",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    if data == "cb_report":

        user_data = get_user(user.id)

        team_name = (
            user_data.get("team_name")
            or "Belum diatur"
        )

        items = get_report_items(user.id)

        report = buat_report_html(
            team_name,
            items,
        )

        await query.message.reply_text(
            report,
            parse_mode=ParseMode.HTML,
        )

        return

    # -----------------------------------------------------
    # TEAM NAME
    # -----------------------------------------------------

    if data == "cb_teamname":

        context.user_data.clear()
        context.user_data["waiting_name"] = True

        await query.message.reply_text(
            "Silakan masukkan nama tim:"
        )

        return

    # -----------------------------------------------------
    # LIST EDIT
    # -----------------------------------------------------

    if data == "cb_editlist":

        items = get_report_items(user.id)

        if not items:

            await query.message.reply_text(
                "Belum ada data."
            )

            return

        buttons = []

        for item in items:

            status_name = STATUS.get(
                item.get("status"),
                ("UNKNOWN", "")
            )[0]

            label = (
                f"{item.get('number')} - "
                f"{KATEGORI.get(item.get('category'), item.get('category'))} - "
                f"{status_name}"
            )

            buttons.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"edititem_{item['id']}",
                )
            ])

        await query.message.reply_text(
            "Pilih data:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        return

    # -----------------------------------------------------
    # PILIH ITEM EDIT
    # -----------------------------------------------------

    if data.startswith("edititem_"):

        item_id = int(
            data.replace(
                "edititem_",
                "",
                1,
            )
        )

        item = get_report_item(
            user.id,
            item_id,
        )

        if not item:

            await query.message.reply_text(
                "Data tidak ditemukan."
            )

            return

        context.user_data["edit_item_id"] = item_id

        buttons = [
            [
                InlineKeyboardButton(
                    "🔢 Ubah Nomor",
                    callback_data="editnum",
                )
            ],
            [
                InlineKeyboardButton(
                    "📂 Ubah Kategori",
                    callback_data="editcategory",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Ubah Status",
                    callback_data="editstatus",
                )
            ],
        ]

        await query.message.reply_text(
            f"✏️ Edit data:\n\n"
            f"Nomor: {item.get('number')}\n"
            f"Kategori: {KATEGORI.get(item.get('category'))}\n"
            f"Status: {STATUS.get(item.get('status'), ('UNKNOWN', ''))[0]}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        return

    # -----------------------------------------------------
    # EDIT NOMOR
    # -----------------------------------------------------

    if data == "editnum":

        if not context.user_data.get("edit_item_id"):

            await query.message.reply_text(
                "Sesi edit sudah berakhir."
            )

            return

        context.user_data["waiting_edit_number"] = True

        await query.message.reply_text(
            "Masukkan nomor yang baru:"
        )

        return

    # -----------------------------------------------------
    # EDIT KATEGORI
    # -----------------------------------------------------

    if data == "editcategory":

        await query.message.reply_text(
            "Pilih kategori baru:",
            reply_markup=kategori_keyboard("editcat"),
        )

        return

    # -----------------------------------------------------
    # PILIH KATEGORI BARU
    # -----------------------------------------------------

    if data.startswith("editcat_"):

        category = data.replace(
            "editcat_",
            "",
            1,
        )

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            await query.message.reply_text(
                "Sesi edit sudah berakhir."
            )
            return

        update_report_category(
            user.id,
            item_id,
            category,
        )

        context.user_data.clear()

        await query.message.reply_text(
            "✅ Kategori berhasil diubah.",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # EDIT STATUS
    # -----------------------------------------------------

    if data == "editstatus":

        await query.message.reply_text(
            "Pilih status baru:",
            reply_markup=status_keyboard("editstat"),
        )

        return

    # -----------------------------------------------------
    # PILIH STATUS BARU
    # -----------------------------------------------------

    if data.startswith("editstat_"):

        status = data.replace(
            "editstat_",
            "",
            1,
        )

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            await query.message.reply_text(
                "Sesi edit sudah berakhir."
            )
            return

        update_report_status(
            user.id,
            item_id,
            status,
        )

        context.user_data.clear()

        await query.message.reply_text(
            "✅ Status berhasil diubah.",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # LIST HAPUS
    # -----------------------------------------------------

    if data == "cb_deletelist":

        items = get_report_items(user.id)

        if not items:

            await query.message.reply_text(
                "Belum ada data."
            )

            return

        buttons = []

        for item in items:

            label = (
                f"{item.get('number')} - "
                f"{KATEGORI.get(item.get('category'), item.get('category'))}"
            )

            buttons.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"deleteitem_{item['id']}",
                )
            ])

        await query.message.reply_text(
            "Pilih data yang ingin dihapus:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        return

    # -----------------------------------------------------
    # PILIH ITEM HAPUS
    # -----------------------------------------------------

    if data.startswith("deleteitem_"):

        item_id = int(
            data.replace(
                "deleteitem_",
                "",
                1,
            )
        )

        item = get_report_item(
            user.id,
            item_id,
        )

        if not item:

            await query.message.reply_text(
                "Data tidak ditemukan."
            )

            return

        buttons = [
            [
                InlineKeyboardButton(
                    "✅ Ya, Hapus",
                    callback_data=f"confirmdelete_{item_id}",
                ),
                InlineKeyboardButton(
                    "❌ Batal",
                    callback_data="cb_menu",
                ),
            ]
        ]

        await query.message.reply_text(
            f"Yakin ingin menghapus?\n\n"
            f"• {item.get('number')}\n"
            f"{KATEGORI.get(item.get('category'))}\n"
            f"{STATUS.get(item.get('status'), ('UNKNOWN', ''))[0]}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        return

    # -----------------------------------------------------
    # KONFIRMASI HAPUS
    # -----------------------------------------------------

    if data.startswith("confirmdelete_"):

        item_id = int(
            data.replace(
                "confirmdelete_",
                "",
                1,
            )
        )

        item = get_report_item(
            user.id,
            item_id,
        )

        if not item:

            await query.message.reply_text(
                "Data sudah tidak ditemukan."
            )

            return

        delete_report_item(
            user.id,
            item_id,
        )

        await query.message.reply_text(
            "🗑️ Data berhasil dihapus.",
            reply_markup=menu_keyboard(),
        )

        return

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    await query.message.reply_text(
        "Tombol sudah tidak berlaku."
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
        context.error,
    )


# =========================================================
# MAIN
# =========================================================

def main():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CommandHandler(
            "menu",
            menu,
        )
    )

    app.add_handler(
        CommandHandler(
            "report",
            command_report,
        )
    )

    app.add_handler(
        CommandHandler(
            "nama",
            command_nama,
        )
    )

    app.add_handler(
        CommandHandler(
            "reset",
            command_reset,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            tombol,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pesan,
        )
    )

    app.add_error_handler(
        error_handler
    )

    print("Bot berjalan...")

    app.run_polling()


if __name__ == "__main__":
    main()