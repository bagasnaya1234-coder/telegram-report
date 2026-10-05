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

    data = get_user(user)

    # =====================================================
    # MENU
    # =====================================================

    if pilihan == "menu":

        context.user_data.clear()

        await tampilkan_menu_callback(
            query,
            data
        )

        return

    # =====================================================
    # TAMBAH DATA
    # =====================================================

    if pilihan == "tambah":

        context.user_data.clear()

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            "Pilih kategori:",
            parse_mode="HTML",
            reply_markup=kategori_keyboard()
        )

        return

    # =====================================================
    # KATEGORI TAMBAH
    # =====================================================

    if pilihan.startswith("cat_"):

        category = pilihan[4:]

        if category not in KATEGORI:
            await query.edit_message_text(
                "⚠️ Kategori tidak valid.",
                reply_markup=menu_keyboard()
            )
            return

        context.user_data["category"] = category
        context.user_data["waiting_number"] = True

        await query.edit_message_text(
            "➕ <b>TAMBAH DATA</b>\n\n"
            f"📂 Kategori: <b>{escape(KATEGORI[category])}</b>\n\n"
            "Silakan kirim nomor.\n\n"
            "Contoh:\n"
            "<code>1234567</code>\n\n"
            "⚠️ Masukkan angka saja.",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # STATUS TAMBAH
    # =====================================================

    if pilihan.startswith("status_"):

        status = pilihan[7:]

        if status not in STATUS:
            await query.edit_message_text(
                "⚠️ Status tidak valid.",
                reply_markup=menu_keyboard()
            )
            return

        category = context.user_data.get("category")
        number = context.user_data.get("number")

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

        status_name, emoji = STATUS[status]

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>DATA BERHASIL DITAMBAHKAN</b>\n\n"
            f"🔢 Nomor: <code>{escape(number)}</code>\n"
            f"📂 Kategori: <b>{escape(KATEGORI[category])}</b>\n"
            f"📊 Status: <b>{escape(status_name)}</b> {emoji}\n\n"
            "Data sudah tersimpan.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return

    # =====================================================
    # REPORT
    # =====================================================

    if pilihan == "report":

        context.user_data.clear()

        await kirim_report_callback(
            query,
            user_id,
            data["team_name"]
        )

        return

    # =====================================================
    # UBAH NAMA
    # =====================================================

    if pilihan == "nama":

        context.user_data.clear()
        context.user_data["waiting_name"] = True

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
    # EDIT - DAFTAR DATA
    # =====================================================

    if pilihan == "edit_list":

        context.user_data.pop("edit_item_id", None)

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

            category_name = KATEGORI.get(
                item["category"],
                item["category"]
            )

            status_data = STATUS.get(
                item["status"],
                ("Unknown", "❔")
            )

            emoji = status_data[1]

            label = (
                f"{item['number']} • "
                f"{category_name} • "
                f"{emoji}"
            )

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
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # EDIT - PILIH NOMOR DATA
    #
    # HARUS SEBELUM edit_number/edit_category/edit_status
    # =====================================================

    if (
        pilihan.startswith("edit_")
        and pilihan[5:].isdigit()
    ):

        item_id = int(pilihan[5:])

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

        context.user_data["edit_item_id"] = item_id

        category_name = KATEGORI.get(
            item["category"],
            item["category"]
        )

        status_data = STATUS.get(
            item["status"],
            ("Unknown", "❔")
        )

        status_name = status_data[0]
        emoji = status_data[1]

        await query.edit_message_text(
            "✏️ <b>EDIT DATA</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"📂 Kategori: "
            f"<b>{escape(category_name)}</b>\n"
            f"📊 Status: "
            f"<b>{escape(status_name)}</b> {emoji}\n\n"
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
                ]
            ])
        )

        return

    # =====================================================
    # EDIT - NOMOR
    # =====================================================

    if pilihan == "edit_number":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:

            await query.edit_message_text(
                "⚠️ Data edit tidak ditemukan.\n\n"
                "Silakan pilih data lagi.",
                reply_markup=menu_keyboard()
            )

            return

        context.user_data["waiting_edit_number"] = True

        await query.edit_message_text(
            "🔢 <b>UBAH NOMOR</b>\n\n"
            "Silakan kirim nomor baru.\n\n"
            "Contoh:\n"
            "<code>1234567</code>\n\n"
            "⚠️ Masukkan angka saja.",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # EDIT - KATEGORI
    # =====================================================

    if pilihan == "edit_category":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:

            await query.edit_message_text(
                "⚠️ Data edit tidak ditemukan.\n\n"
                "Silakan pilih data lagi.",
                reply_markup=menu_keyboard()
            )

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
    # EDIT - PILIH KATEGORI
    # =====================================================

    if pilihan.startswith("editcat_"):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        category = pilihan[len("editcat_"):]

        if category not in KATEGORI:
            await query.edit_message_text(
                "⚠️ Kategori tidak valid.",
                reply_markup=menu_keyboard()
            )
            return

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            context.user_data.clear()

            await query.edit_message_text(
                "⚠️ Data tidak ditemukan.",
                reply_markup=menu_keyboard()
            )

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
            reply_markup=menu_keyboard()
        )

        return

    # =====================================================
    # EDIT - STATUS
    # =====================================================

    if pilihan == "edit_status":

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:

            await query.edit_message_text(
                "⚠️ Data edit tidak ditemukan.\n\n"
                "Silakan pilih data lagi.",
                reply_markup=menu_keyboard()
            )

            return

        await query.edit_message_text(
            "📊 <b>UBAH STATUS</b>\n\n"
            "Pilih status baru:",
            parse_mode="HTML",
            reply_markup=status_keyboard(
                prefix="editstatus"
            )
        )

        return

    # =====================================================
    # EDIT - PILIH STATUS
    # =====================================================

    if pilihan.startswith("editstatus_"):

        item_id = context.user_data.get(
            "edit_item_id"
        )

        if not item_id:
            return

        status = pilihan[len("editstatus_"):]

        if status not in STATUS:

            await query.edit_message_text(
                "⚠️ Status tidak valid.",
                reply_markup=menu_keyboard()
            )

            return

        item = get_report_item(
            user_id,
            item_id
        )

        if not item:

            context.user_data.clear()

            await query.edit_message_text(
                "⚠️ Data tidak ditemukan.",
                reply_markup=menu_keyboard()
            )

            return

        update_report_status(
            user_id,
            item_id,
            status
        )

        status_name, emoji = STATUS[status]

        context.user_data.clear()

        await query.edit_message_text(
            "✅ <b>STATUS BERHASIL DIUBAH</b>\n\n"
            f"🔢 Nomor: "
            f"<code>{escape(str(item['number']))}</code>\n"
            f"📊 Status baru: "
            f"<b>{escape(status_name)}</b> {emoji}",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
        )

        return

    # =====================================================
    # HAPUS DATA - DAFTAR
    # =====================================================

    if pilihan == "delete_list":

        context.user_data.clear()

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

            category_name = KATEGORI.get(
                item["category"],
                item["category"]
            )

            status_data = STATUS.get(
                item["status"],
                ("Unknown", "❔")
            )

            emoji = status_data[1]

            label = (
                f"{item['number']} • "
                f"{category_name} • "
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
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # HAPUS DATA - KONFIRMASI
    # =====================================================

    if (
        pilihan.startswith("del_")
        and pilihan[4:].isdigit()
    ):

        item_id = int(pilihan[4:])

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
                        callback_data=f"confirmdel_{item_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ Batal",
                        callback_data="delete_list"
                    )
                ]
            ])
        )

        return

    # =====================================================
    # HAPUS DATA - EKSEKUSI
    # =====================================================

    if (
        pilihan.startswith("confirmdel_")
        and pilihan[11:].isdigit()
    ):

        item_id = int(pilihan[11:])

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
            f"Nomor <code>{escape(str(item['number']))}</code> "
            "telah dihapus.",
            parse_mode="HTML",
            reply_markup=menu_keyboard()
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
        reply_markup=menu_keyboard()
    )