import os
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape

from supabase import create_client, Client

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


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
# DATABASE USER
# =========================================================

def get_user(user):
    """
    Mengambil data user berdasarkan Telegram user.id.

    Setiap user mempunyai data sendiri.
    """

    telegram_user_id = user.id

    try:
        response = (
            supabase
            .table("bot_users")
            .select(
                "telegram_user_id, username, first_name, team_name"
            )
            .eq(
                "telegram_user_id",
                telegram_user_id
            )
            .limit(1)
            .execute()
        )

        if response.data:
            row = response.data[0]

            # Update informasi Telegram terbaru
            supabase.table("bot_users").update({
                "username": user.username,
                "first_name": user.first_name,
                "updated_at": datetime.now(TIMEZONE).isoformat(),
            }).eq(
                "telegram_user_id",
                telegram_user_id
            ).execute()

            return row

        # User belum pernah terdaftar
        new_user = {
            "telegram_user_id": telegram_user_id,
            "username": user.username,
            "first_name": user.first_name,
            "team_name": "Belum diatur",
        }

        supabase.table("bot_users").insert(
            new_user
        ).execute()

        return new_user

    except Exception as e:
        print(
            f"Supabase get_user error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal mengambil data user dari Supabase."
        )


def update_team_name(user_id, team_name):
    try:
        supabase.table("bot_users").update({
            "team_name": team_name,
            "updated_at": datetime.now(
                TIMEZONE
            ).isoformat(),
        }).eq(
            "telegram_user_id",
            user_id
        ).execute()

    except Exception as e:
        print(
            f"Supabase update team error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal menyimpan nama tim."
        )


# =========================================================
# DATABASE REPORT
# =========================================================

def get_report_items(user_id):
    try:
        response = (
            supabase
            .table("report_items")
            .select(
                "id, telegram_user_id, number, category, status"
            )
            .eq(
                "telegram_user_id",
                user_id
            )
            .order(
                "id",
                desc=False
            )
            .execute()
        )

        return response.data or []

    except Exception as e:
        print(
            f"Supabase get items error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal mengambil data report."
        )


def get_report_item(user_id, item_id):
    try:
        response = (
            supabase
            .table("report_items")
            .select(
                "id, telegram_user_id, number, category, status"
            )
            .eq(
                "id",
                item_id
            )
            .eq(
                "telegram_user_id",
                user_id
            )
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as e:
        print(
            f"Supabase get item error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal mengambil data."
        )


def add_report_item(
    user_id,
    number,
    category,
    status
):
    try:
        supabase.table("report_items").insert({
            "telegram_user_id": user_id,
            "number": number,
            "category": category,
            "status": status,
        }).execute()

    except Exception as e:
        print(
            f"Supabase add item error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal menambahkan data."
        )


def update_report_number(
    user_id,
    item_id,
    number
):
    try:
        supabase.table("report_items").update({
            "number": number,
        }).eq(
            "id",
            item_id
        ).eq(
            "telegram_user_id",
            user_id
        ).execute()

    except Exception as e:
        print(
            f"Supabase update number error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal mengubah nomor."
        )


def update_report_category(
    user_id,
    item_id,
    category
):
    try:
        supabase.table("report_items").update({
            "category": category,
        }).eq(
            "id",
            item_id
        ).eq(
            "telegram_user_id",
            user_id
        ).execute()

    except Exception as e:
        print(
            f"Supabase update category error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal mengubah kategori."
        )


def update_report_status(
    user_id,
    item_id,
    status
):
    try:
        supabase.table("report_items").update({
            "status": status,
        }).eq(
            "id",
            item_id
        ).eq(
            "telegram_user_id",
            user_id
        ).execute()

    except Exception as e:
        print(
            f"Supabase update status error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal mengubah status."
        )


def delete_report_item(
    user_id,
    item_id
):
    try:
        supabase.table("report_items").delete().eq(
            "id",
            item_id
        ).eq(
            "telegram_user_id",
            user_id
        ).execute()

    except Exception as e:
        print(
            f"Supabase delete item error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal menghapus data."
        )


def delete_all_report_items(user_id):
    try:
        supabase.table("report_items").delete().eq(
            "telegram_user_id",
            user_id
        ).execute()

    except Exception as e:
        print(
            f"Supabase reset error: {e}",
            flush=True
        )

        raise RuntimeError(
            "Gagal menghapus data report."
        )


# =========================================================
# KEYBOARD MENU
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
                "✏️ Edit Data",
                callback_data="edit_list"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Hapus Data",
                callback_data="delete_list"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Ubah Nama Tim",
                callback_data="nama"
            )
        ],
    ])


def kategori_keyboard(prefix="cat"):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "IB Reguler",
                callback_data=f"{prefix}_ib_reguler"
            ),
            InlineKeyboardButton(
                "IB Sameday",
                callback_data=f"{prefix}_ib_sameday"
            ),
        ],
        [
            InlineKeyboardButton(
                "MT Reguler",
                callback_data=f"{prefix}_mt_reguler"
            ),
            InlineKeyboardButton(
                "MT Sameday",
                callback_data=f"{prefix}_mt_sameday"
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="menu"
            )
        ],
    ])


def status_keyboard(prefix="status"):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Done",
                callback_data=f"{prefix}_done"
            ),
            InlineKeyboardButton(
                "⏳ Pending",
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
                callback_data="menu"
            )
        ],
    ])


# =========================================================
# MENU UTAMA
# =========================================================

def menu_text(data):

    return (
        "📋 <b>REPORT PROGRESS</b>\n\n"
        f"📅 {tanggal_sekarang()}\n"
        f"👤 Nama: <b>{escape(data['team_name'])}</b>\n\n"
        "Silakan pilih menu:"
    )


async def tampilkan_menu(update, data):

    await update.message.reply_text(
        menu_text(data),
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


async def tampilkan_menu_callback(query, data):

    await query.edit_message_text(
        menu_text(data),
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user or not update.message:
        return

    # Bersihkan proses sebelumnya
    context.user_data.clear()

    data = get_user(user)

    nama_user = escape(
        user.first_name or "Teman"
    )

    # User belum memiliki nama tim
    if data["team_name"] == "Belum diatur":

        context.user_data[
            "waiting_name"
        ] = True

        await update.message.reply_text(
            "👋 <b>Selamat datang, "
            f"{nama_user}!</b>\n\n"
            "📋 <b>REPORT PROGRESS</b>\n\n"
            "Sebelum mulai, silakan isi "
            "nama tim kamu di bawah.\n\n"
            "Contoh:\n"
            "👉 <code>Bagas-Toni</code>\n\n"
            "Nama ini akan digunakan sebagai "
            "nama pada report kamu.",
            parse_mode="HTML"
        )

        return

    await update.message.reply_text(
        menu_text(data),
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# COMMAND MENU
# =========================================================

async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user or not update.message:
        return

    data = get_user(user)

    if data["team_name"] == "Belum diatur":

        context.user_data.clear()

        context.user_data[
            "waiting_name"
        ] = True

        await update.message.reply_text(
            "👋 Silakan isi nama tim kamu.\n\n"
            "Contoh:\n"
            "<code>Bagas-Toni</code>",
            parse_mode="HTML"
        )

        return

    context.user_data.clear()

    await update.message.reply_text(
        menu_text(data),
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# BUAT REPORT
# =========================================================

def buat_report(user_id, team_name):

    items = get_report_items(user_id)

    teks = (
        f"📋 <b>Report Progress "
        f"{tanggal_sekarang()}</b>\n\n"
        f"👥 <b>{escape(team_name)}</b>\n\n"
    )

    for category_key, category_name in KATEGORI.items():

        category_items = [
            item
            for item in items
            if item["category"] == category_key
        ]

        teks += (
            f"<b>{category_name}</b>\n"
        )

        if not category_items:
            teks += "—\n\n"
            continue

        for item in category_items:

            status_name, emoji = STATUS[
                item["status"]
            ]

            teks += (
                f"• <code>{escape(item['number'])}</code> "
                f"({status_name}) {emoji}\n"
            )

        teks += "\n"

    return teks.rstrip()


async def kirim_report_callback(
    query,
    user_id,
    team_name
):

    teks = buat_report(
        user_id,
        team_name
    )

    await query.edit_message_text(
        teks,
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


async def command_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    data = get_user(user)

    if data["team_name"] == "Belum diatur":

        await update.message.reply_text(
            "⚠️ Silakan atur nama tim terlebih dahulu "
            "dengan /start.",
        )

        return

    context.user_data.clear()

    teks = buat_report(
        user.id,
        data["team_name"]
    )

    await update.message.reply_text(
        teks,
        parse_mode="HTML",
        reply_markup=menu_keyboard()
    )


# =========================================================
# CALLBACK UTAMA
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


    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    if pilihan == "menu":

        context.user_data.clear()

        await tampilkan_menu_callback(
            query,
            data
        )

        return


    # -----------------------------------------------------
    # TAMBAH DATA
    # -----------------------------------------------------

    if pilihan == "tambah":

        context.user_data.clear()

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            "Pilih kategori:",
            parse_mode="HTML",
            reply_markup=kategori_keyboard()
        )

        return


    if pilihan.startswith("edit_") and pilihan[5:].isdigit():

        category = pilihan.replace(
            "cat_",
            "",
            1
        )

        context.user_data[
            "category"
        ] = category

        context.user_data[
            "waiting_number"
        ] = True

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            f"📂 Kategori: "
            f"<b>{KATEGORI[category]}</b>\n\n"
            "Silakan kirim nomor.\n\n"
            "Contoh:\n"
            "<code>1234567</code>\n\n"
            "⚠️ Masukkan angka saja.",
            parse_mode="HTML"
        )

        return


    # -----------------------------------------------------
    # STATUS TAMBAH
    # -----------------------------------------------------

    if pilihan.startswith("status_"):

        status = pilihan.replace(
            "status_",
            "",
            1
        )

        category = context.user_data.get(
            "category"
        )

        number = context.user_data.get(
            "number"
        )

        if not category or not number:

            await query.edit_message_text(
                "⚠️ Data tidak ditemukan.\n\n"
                "Silakan mulai kembali.",
                reply_markup=menu_keyboard()
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
            f"🔢 Nomor: <code>{escape(number)}</code>\n"
            f"📂 Kategori: "
            f"<b>{KATEGORI[category]}</b>\n"
            f"📊 Status: "
            f"<b>{status_name}</b> {emoji}\n\n"
            "Data sudah tersimpan.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return


    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    if pilihan == "report":

        context.user_data.clear()

        await kirim_report_callback(
            query,
            user_id,
            data["team_name"]
        )

        return


    # -----------------------------------------------------
    # UBAH NAMA
    # -----------------------------------------------------

    if pilihan == "nama":

        context.user_data.clear()

        context.user_data[
            "waiting_name"
        ] = True

        await query.edit_message_text(
            "👤 <b>UBAH NAMA TIM</b>\n\n"
            f"Nama sekarang:\n"
            f"<b>{escape(data['team_name'])}</b>\n\n"
            "Silakan kirim nama tim baru.\n\n"
            "Contoh:\n"
            "<code>Bagas-Toni</code>",
            parse_mode="HTML"
        )

        return


    # =====================================================
    # EDIT DATA
    # =====================================================

    if pilihan == "edit_list":

        items = get_report_items(user_id)

        if not items:

            await query.edit_message_text(
                "✏️ <b>EDIT DATA</b>\n\n"
                "Belum ada data yang bisa diedit.",
                parse_mode="HTML",
                reply_markup=menu_keyboard()
            )

            return

        keyboard = []

        for item in items:

            status_name, emoji = STATUS[
                item["status"]
            ]

            label = (
                f"{item['number']} • "
                f"{KATEGORI[item['category']]} • "
                f"{emoji}"
            )

            # Batasi panjang tombol
            if len(label) > 55:
                label = label[:52] + "..."

            keyboard.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"edit_{item['id']}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="menu"
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


    # -----------------------------------------------------
    # PILIH DATA EDIT
    # -----------------------------------------------------

    if pilihan.startswith("edit_"):

        try:
            item_id = int(
                pilihan.replace(
                    "edit_",
                    "",
                    1
                )
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
                reply_markup=menu_keyboard()
            )

            return

        context.user_data[
            "edit_item_id"
        ] = item_id

        status_name, emoji = STATUS[
            item["status"]
        ]

        await query.edit_message_text(
            "✏️ <b>EDIT DATA</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(item['number'])}</code>\n"
            f"📂 Kategori: "
            f"<b>{KATEGORI[item['category']]}</b>\n"
            f"📊 Status: "
            f"<b>{status_name}</b> {emoji}\n\n"
            "Apa yang ingin diubah?",
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
                        callback_data="edit_list"
                    )
                ],
            ])
        )

        return


    # -----------------------------------------------------
    # EDIT NOMOR
    # -----------------------------------------------------

    if pilihan == "edit_number":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        context.user_data[
            "waiting_edit_number"
        ] = True

        await query.edit_message_text(
            "🔢 <b>UBAH NOMOR</b>\n\n"
            "Silakan kirim nomor baru.\n\n"
            "Contoh:\n"
            "<code>1234567</code>",
            parse_mode="HTML"
        )

        return


    # -----------------------------------------------------
    # EDIT KATEGORI
    # -----------------------------------------------------

    if pilihan == "edit_category":

        await query.edit_message_text(
            "📂 <b>UBAH KATEGORI</b>\n\n"
            "Pilih kategori baru:",
            parse_mode="HTML",
            reply_markup=kategori_keyboard(
                prefix="editcat"
            )
        )

        return


    if pilihan.startswith("editcat_"):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        category = pilihan.replace(
            "editcat_",
            "",
            1
        )

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
            f"<code>{escape(item['number'])}</code>\n"
            f"📂 Kategori baru: "
            f"<b>{KATEGORI[category]}</b>",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return


    # -----------------------------------------------------
    # EDIT STATUS
    # -----------------------------------------------------

    if pilihan == "edit_status":

        await query.edit_message_text(
            "📊 <b>UBAH STATUS</b>\n\n"
            "Pilih status baru:",
            parse_mode="HTML",
            reply_markup=status_keyboard(
                prefix="editstatus"
            )
        )

        return


    if pilihan.startswith("editstatus_"):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        status = pilihan.replace(
            "editstatus_",
            "",
            1
        )

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
            f"<code>{escape(item['number'])}</code>\n"
            f"📊 Status baru: "
            f"<b>{status_name}</b> {emoji}",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return


    # =====================================================
    # HAPUS DATA
    # =====================================================

    if pilihan == "delete_list":

        items = get_report_items(user_id)

        if not items:

            await query.edit_message_text(
                "🗑️ <b>HAPUS DATA</b>\n\n"
                "Belum ada data yang bisa dihapus.",
                parse_mode="HTML",
                reply_markup=menu_keyboard()
            )

            return

        keyboard = []

        for item in items:

            status_name, emoji = STATUS[
                item["status"]
            ]

            label = (
                f"{item['number']} • "
                f"{KATEGORI[item['category']]} • "
                f"{emoji}"
            )

            if len(label) > 55:
                label = label[:52] + "..."

            keyboard.append([
                InlineKeyboardButton(
                    label,
                    callback_data=f"del_{item['id']}"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="menu"
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


    # -----------------------------------------------------
    # KONFIRMASI HAPUS
    # -----------------------------------------------------

    if pilihan.startswith("del_"):

        try:
            item_id = int(
                pilihan.replace(
                    "del_",
                    "",
                    1
                )
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
                reply_markup=menu_keyboard()
            )

            return

        await query.edit_message_text(
            "⚠️ <b>KONFIRMASI HAPUS</b>\n\n"
            "Apakah kamu yakin ingin menghapus:\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(item['number'])}</code>\n"
            f"📂 Kategori: "
            f"<b>{KATEGORI[item['category']]}</b>\n\n"
            "Data yang dihapus tidak dapat "
            "dikembalikan.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ Ya, Hapus",
                        callback_data=f"confirmdel_{item_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Batal",
                        callback_data="delete_list"
                    )
                ],
            ])
        )

        return


    if pilihan.startswith("confirmdel_"):

        try:
            item_id = int(
                pilihan.replace(
                    "confirmdel_",
                    "",
                    1
                )
            )

        except ValueError:
            return

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            await query.edit_message_text(
                "⚠️ Data sudah tidak ditemukan.",
                reply_markup=menu_keyboard()
            )

            return

        delete_report_item(
            user_id,
            item_id
        )

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>DATA BERHASIL DIHAPUS</b>\n\n"
            f"Nomor <code>{escape(item['number'])}</code> "
            "telah dihapus.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return


# =========================================================
# PESAN TEKS
# =========================================================

async def pesan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user or not update.message:
        return

    teks = update.message.text.strip()

    user_id = user.id


    # =====================================================
    # INPUT NAMA TIM
    # =====================================================

    if context.user_data.get(
        "waiting_name"
    ):

        if len(teks) < 2:

            await update.message.reply_text(
                "⚠️ Nama tim terlalu pendek.\n\n"
                "Silakan masukkan minimal 2 karakter."
            )

            return

        if len(teks) > 50:

            await update.message.reply_text(
                "⚠️ Nama tim terlalu panjang.\n\n"
                "Maksimal 50 karakter."
            )

            return

        update_team_name(
            user_id,
            teks
        )

        context.user_data.clear()

        data = get_user(user)

        await update.message.reply_text(
            "✅ <b>Nama tim berhasil disimpan!</b>\n\n"
            f"👥 Tim: <b>{escape(teks)}</b>\n\n"
            "Sekarang kamu bisa mulai membuat "
            "report progress.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return


    # =====================================================
    # INPUT NOMOR BARU
    # =====================================================

    if context.user_data.get(
        "waiting_number"
    ):

        if not teks.isdigit():

            await update.message.reply_text(
                "⚠️ <b>Nomor tidak valid.</b>\n\n"
                "Nomor harus berupa angka saja.\n\n"
                "Contoh:\n"
                "<code>1234567</code>",
                parse_mode="HTML"
            )

            return

        if not 4 <= len(teks) <= 20:

            await update.message.reply_text(
                "⚠️ Panjang nomor tidak valid.\n\n"
                "Nomor harus terdiri dari "
                "4 sampai 20 angka."
            )

            return

        context.user_data[
            "number"
        ] = teks

        context.user_data[
            "waiting_number"
        ] = False

        await update.message.reply_text(
            "🔢 <b>Nomor diterima</b>\n\n"
            f"Nomor: <code>{escape(teks)}</code>\n\n"
            "📊 Pilih status:",
            parse_mode="HTML",
            reply_markup=status_keyboard()
        )

        return


    # =====================================================
    # INPUT NOMOR SAAT EDIT
    # =====================================================

    if context.user_data.get(
        "waiting_edit_number"
    ):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:

            context.user_data.clear()

            await update.message.reply_text(
                "⚠️ Data edit tidak ditemukan.\n\n"
                "Silakan mulai lagi dari menu.",
                reply_markup=menu_keyboard()
            )

            return

        if not teks.isdigit():

            await update.message.reply_text(
                "⚠️ <b>Nomor tidak valid.</b>\n\n"
                "Masukkan angka saja.\n\n"
                "Contoh:\n"
                "<code>1234567</code>",
                parse_mode="HTML"
            )

            return

        if not 4 <= len(teks) <= 20:

            await update.message.reply_text(
                "⚠️ Panjang nomor tidak valid.\n\n"
                "Nomor harus terdiri dari "
                "4 sampai 20 angka."
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

        old_number = item["number"]

        update_report_number(
            user_id,
            item_id,
            teks
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ <b>NOMOR BERHASIL DIUBAH</b>\n\n"
            f"<code>{escape(old_number)}</code>"
            f" → <code>{escape(teks)}</code>",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return


    # =====================================================
    # PESAN BIASA
    # =====================================================

    await update.message.reply_text(
        "Silakan gunakan menu di bawah:",
        reply_markup=menu_keyboard()
    )


# =========================================================
# COMMAND NAMA
# =========================================================

async def command_nama(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    context.user_data[
        "waiting_name"
    ] = True

    await update.message.reply_text(
        "👤 <b>UBAH NAMA TIM</b>\n\n"
        "Silakan kirim nama tim baru.\n\n"
        "Contoh:\n"
        "<code>Bagas-Toni</code>",
        parse_mode="HTML"
    )


# =========================================================
# RESET
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

    context.user_data.clear()

    await update.message.reply_text(
        "🗑️ <b>SEMUA DATA REPORT KAMU DIHAPUS</b>\n\n"
        "Nama tim tetap tersimpan.\n\n"
        "⚠️ Data pengguna lain tidak terpengaruh.",
        parse_mode="HTML",
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
        "Bot sedang berjalan...",
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
        "MODE FINAL - USER REPORT",
        flush=True
    )

    print(
        "====================================",
        flush=True
    )


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    # Commands

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


    # Buttons

    app.add_handler(
        CallbackQueryHandler(
            tombol
        )
    )


    # Text

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pesan
        )
    )


    # Error

    app.add_error_handler(
        error_handler
    )


    print(
        "Bot siap menerima pesan Telegram.",
        flush=True
    )


    app.run_polling()


# =========================================================

if __name__ == "__main__":
    main()