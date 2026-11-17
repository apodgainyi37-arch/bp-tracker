import os
import sqlite3
from datetime import datetime
from kivy.lang import Builder
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.toast import toast

from fpdf import FPDF

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    md_bg_color: 0.96, 0.97, 0.98, 1

    MDTopAppBar:
        title: "Дневник АД и пульса"
        elevation: 2
        md_bg_color: 0.85, 0.18, 0.22, 1
        right_action_items:
            [
            ["account-details", lambda x: app.open_user_dialog(), "Профиль пользователя"],
            ["file-pdf-box", lambda x: app.open_pdf_dialog(), "Экспорт в PDF"]
            ]

    ScrollView:
        do_scroll_x: False

        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(14)
            spacing: dp(12)
            size_hint_y: None
            height: self.minimum_height

            # Плашка текущего пользователя
            MDCard:
                orientation: 'horizontal'
                padding: [dp(14), dp(10)]
                size_hint_y: None
                height: dp(62)
                radius: [dp(12)]
                elevation: 1
                md_bg_color: 1, 1, 1, 1
                on_release: app.open_user_dialog()

                MDBoxLayout:
                    orientation: 'vertical'
                    spacing: dp(2)

                    MDLabel:
                        id: user_name_label
                        text: "Пользователь не выбран"
                        font_style: "Subtitle1"
                        bold: True
                        theme_text_color: "Primary"

                    MDLabel:
                        id: user_info_label
                        text: "Нажмите, чтобы заполнить ФИО, год рождения, рост и вес"
                        font_style: "Caption"
                        theme_text_color: "Secondary"

                MDIconButton:
                    icon: "account-edit-outline"
                    pos_hint: {"center_y": .5}
                    theme_text_color: "Custom"
                    text_color: 0.85, 0.18, 0.22, 1
                    on_release: app.open_user_dialog()

            # Карточка ввода нового замера
            MDCard:
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
                radius: [dp(14)]
                elevation: 1
                md_bg_color: 1, 1, 1, 1

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(28)

                    MDLabel:
                        text: "Новое измерение"
                        font_style: "H6"
                        theme_text_color: "Primary"

                    MDLabel:
                        id: period_badge
                        text: "Период: —"
                        font_style: "Caption"
                        halign: "right"
                        theme_text_color: "Custom"
                        text_color: 0.85, 0.18, 0.22, 1
                        bold: True

                MDBoxLayout:
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(60)

                    MDTextField:
                        id: sys_input
                        hint_text: "Верхнее (САД)"
                        helper_text: "мм рт. ст."
                        helper_text_mode: "persistent"
                        input_filter: "int"
                        mode: "rectangle"

                    MDTextField:
                        id: dia_input
                        hint_text: "Нижнее (ДАД)"
                        helper_text: "мм рт. ст."
                        helper_text_mode: "persistent"
                        input_filter: "int"
                        mode: "rectangle"

                    MDTextField:
                        id: pulse_input
                        hint_text: "Пульс"
                        helper_text: "уд/мин"
                        helper_text_mode: "persistent"
                        input_filter: "int"
                        mode: "rectangle"

                MDBoxLayout:
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(56)

                    MDTextField:
                        id: dt_input
                        hint_text: "Дата и время (авто)"
                        mode: "rectangle"
                        on_text: app.update_period_preview(self.text)

                    MDIconButton:
                        icon: "clock-refresh-outline"
                        pos_hint: {"center_y": .5}
                        on_release: app.set_current_datetime()

                MDTextField:
                    id: note_input
                    hint_text: "Самочувствие / комментарий (необязательно)"
                    mode: "rectangle"
                    size_hint_y: None
                    height: dp(56)

                MDRaisedButton:
                    text: "СОХРАНИТЬ ЗАПИСЬ"
                    size_hint_x: 1
                    md_bg_color: 0.85, 0.18, 0.22, 1
                    on_release: app.add_record()

            # Карточка графика динамики
            MDCard:
                orientation: 'vertical'
                padding: dp(14)
                spacing: dp(8)
                size_hint_y: None
                height: dp(220)
                radius: [dp(14)]
                elevation: 1
                md_bg_color: 1, 1, 1, 1

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(24)

                    MDLabel:
                        text: "Динамика (последние 15 замеров)"
                        font_style: "Subtitle2"
                        bold: True

                    MDLabel:
                        text: "[color=#D92E38]● САД[/color]  [color=#2962FF]● ДАД[/color]  [color=#FF8F00]● Пульс[/color]"
                        markup: True
                        font_style: "Caption"
                        halign: "right"

                BPChartWidget:
                    id: chart_widget

            # Заголовок истории и кнопка PDF
            MDBoxLayout:
                size_hint_y: None
                height: dp(32)
                padding: [dp(4), 0]

                MDLabel:
                    text: "История измерений"
                    font_style: "Subtitle1"
                    bold: True

                MDFlatButton:
                    text: "Выгрузить PDF"
                    theme_text_color: "Custom"
                    text_color: 0.85, 0.18, 0.22, 1
                    on_release: app.open_pdf_dialog()

            MDBoxLayout:
                id: history_container
                orientation: 'vertical'
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
'''


def get_day_period(dt_obj: datetime) -> str:
    """Определяет период суток: Утро (04-11), День (12-17), Вечер (18-03)."""
    hour = dt_obj.hour
    if 4 <= hour < 12:
        return "Утро"
    elif 12 <= hour < 18:
        return "День"
    return "Вечер"


class BPChartWidget(Widget):
    """Нативный виджет графика САД, ДАД и пульса на Canvas Kivy."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_points = []
        self.bind(pos=self.redraw, size=self.redraw)

    def set_data(self, points):
        self.data_points = points
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        if len(self.data_points) < 1:
            return

        pad = dp(8)
        x0, y0 = self.x + pad, self.y + pad
        w = max(dp(10), self.width - 2 * pad)
        h = max(dp(10), self.height - 2 * pad)
        min_v, max_v = 45, 200

        def val_to_y(v):
            vc = max(min_v, min(max_v, v))
            return y0 + ((vc - min_v) / (max_v - min_v)) * h

        with self.canvas:
            Color(0.88, 0.96, 0.89, 1)
            y_80, y_120 = val_to_y(80), val_to_y(120)
            Rectangle(pos=(x0, y_80), size=(w, y_120 - y_80))

            Color(0.82, 0.84, 0.86, 1)
            for ref in (80, 120, 140):
                yr = val_to_y(ref)
                Line(points=[x0, yr, x0 + w, yr], width=1)

            n = len(self.data_points)
            step_x = w / (n - 1) if n > 1 else 0

            sys_pts, dia_pts, pls_pts = [], [], []
            for idx, (s, d, p) in enumerate(self.data_points):
                cx = x0 + (idx * step_x if n > 1 else w / 2)
                sys_pts.extend([cx, val_to_y(s)])
                dia_pts.extend([cx, val_to_y(d)])
                pls_pts.extend([cx, val_to_y(p)])

            if n > 1:
                Color(0.85, 0.18, 0.22, 1)
                Line(points=sys_pts, width=dp(1.8))
                Color(0.16, 0.38, 1.0, 1)
                Line(points=dia_pts, width=dp(1.8))
                Color(1.0, 0.56, 0.0, 1)
                Line(points=pls_pts, width=dp(1.4))

            r = dp(3)
            for idx in range(n):
                Color(0.85, 0.18, 0.22, 1)
                Ellipse(pos=(sys_pts[2*idx] - r, sys_pts[2*idx+1] - r), size=(2*r, 2*r))
                Color(0.16, 0.38, 1.0, 1)
                Ellipse(pos=(dia_pts[2*idx] - r, dia_pts[2*idx+1] - r), size=(2*r, 2*r))
                Color(1.0, 0.56, 0.0, 1)
                Ellipse(pos=(pls_pts[2*idx] - r, pls_pts[2*idx+1] - r), size=(2*r, 2*r))


class UserDialogContent(MDBoxLayout):
    """Окно добавления/редактирования данных пользователя и выбора профиля."""
    def __init__(self, app, user_data=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(320)

        fio_val = user_data[1] if user_data else ""
        byear_val = str(user_data[2]) if (user_data and user_data[2]) else ""
        height_val = str(user_data[3]) if (user_data and user_data[3]) else ""
        weight_val = str(user_data[4]) if (user_data and user_data[4]) else ""

        self.fio_input = MDTextField(
            text=fio_val,
            hint_text="ФИО пациента",
            mode="rectangle"
        )
        self.byear_input = MDTextField(
            text=byear_val,
            hint_text="Год рождения (например, 1980)",
            input_filter="int",
            mode="rectangle"
        )

        row_hw = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(58))
        self.height_input = MDTextField(
            text=height_val,
            hint_text="Рост (см)",
            input_filter="int",
            mode="rectangle"
        )
        self.weight_input = MDTextField(
            text=weight_val,
            hint_text="Вес (кг)",
            input_filter="float",
            mode="rectangle"
        )
        row_hw.add_widget(self.height_input)
        row_hw.add_widget(self.weight_input)

        self.add_widget(self.fio_input)
        self.add_widget(self.byear_input)
        self.add_widget(row_hw)

        # Кнопка переключения или добавления еще одного профиля
        self.switch_btn = MDFlatButton(
            text="ПЕРЕКЛЮЧИТЬ / НОВЫЙ ПРОФИЛЬ",
            theme_text_color="Custom",
            text_color=(0.16, 0.38, 1.0, 1),
            on_release=lambda x: self.app.open_profile_list_dialog()
        )
        self.add_widget(self.switch_btn)


class PDFDialogContent(MDBoxLayout):
    def __init__(self, start_default, end_default, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(12)
        self.size_hint_y = None
        self.height = dp(130)

        self.start_date = MDTextField(
            text=start_default,
            hint_text="Начало периода (ДД.ММ.ГГГГ)",
            mode="rectangle"
        )
        self.end_date = MDTextField(
            text=end_default,
            hint_text="Конец периода (ДД.ММ.ГГГГ)",
            mode="rectangle"
        )
        self.add_widget(self.start_date)
        self.add_widget(self.end_date)


class BPTrackerApp(MDApp):
    dialog = None
    user_dialog = None
    profile_list_dialog = None
    current_user_id = None

    def build(self):
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.theme_style = "Light"
        self.db_path = self.get_db_path()
        self.init_db()
        return Builder.load_string(KV)

    def on_start(self):
        self.set_current_datetime()
        self.load_active_user()
        self.load_history()
        if platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])

    def get_db_path(self):
        if platform == "android":
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), "bp_records.db")
        return "bp_records.db"

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    birth_year INTEGER,
                    height INTEGER,
                    weight REAL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    dt_iso TEXT NOT NULL,
                    period TEXT NOT NULL,
                    sys INTEGER NOT NULL,
                    dia INTEGER NOT NULL,
                    pulse INTEGER NOT NULL,
                    note TEXT
                )
            ''')
            # Автоматическая миграция старой таблицы records
            cols = [row[1] for row in conn.execute("PRAGMA table_info(records)").fetchall()]
            if "period" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN period TEXT DEFAULT 'Утро'")
            if "user_id" not in cols:
                conn.execute("ALTER TABLE records ADD COLUMN user_id INTEGER DEFAULT 1")

            # Создаем дефолтный профиль, если таблица пользователей пуста
            cur = conn.execute("SELECT id FROM users ORDER BY is_active DESC, id ASC LIMIT 1").fetchone()
            if not cur:
                conn.execute(
                    "INSERT INTO users (full_name, birth_year, height, weight, is_active) VALUES (?, ?, ?, ?, 1)",
                    ("Основной пользователь", 1980, 175, 75.0)
                )

    def load_active_user(self):
        with sqlite3.connect(self.db_path) as conn:
            user = conn.execute(
                "SELECT id, full_name, birth_year, height, weight FROM users ORDER BY is_active DESC, id ASC LIMIT 1"
            ).fetchone()

        if user:
            self.current_user_id = user[0]
            fio, byear, h, w = user[1], user[2], user[3], user[4]
            self.root.ids.user_name_label.text = fio
            details = []
            if byear:
                age = datetime.now().year - int(byear)
                details.append(f"{byear} г.р. ({age} л.)")
            if h:
                details.append(f"Рост: {h} см")
            if w:
                details.append(f"Вес: {w:g} кг")
            self.root.ids.user_info_label.text = "  •  ".join(details) if details else "Нажмите для ввода года рождения, роста и веса"

    def get_current_user_data(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT id, full_name, birth_year, height, weight FROM users WHERE id = ?",
                (self.current_user_id,)
            ).fetchone()

    def open_user_dialog(self, new_profile=False):
        user_data = None if new_profile else self.get_current_user_data()
        self.user_dialog_content = UserDialogContent(app=self, user_data=user_data)
        self.editing_new_profile = new_profile

        title_str = "Новый пользователь" if new_profile else "Данные пользователя"
        self.user_dialog = MDDialog(
            title=title_str,
            type="custom",
            content_cls=self.user_dialog_content,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.user_dialog.dismiss()),
                MDRaisedButton(
                    text="СОХРАНИТЬ",
                    md_bg_color=(0.85, 0.18, 0.22, 1),
                    on_release=self.save_user_data
                ),
            ],
        )
        self.user_dialog.open()

    def save_user_data(self, *args):
        fio = self.user_dialog_content.fio_input.text.strip()
        byear_txt = self.user_dialog_content.byear_input.text.strip()
        h_txt = self.user_dialog_content.height_input.text.strip()
        w_txt = self.user_dialog_content.weight_input.text.strip().replace(",", ".")

        if not fio:
            toast("Введите ФИО пользователя")
            return

        byear = int(byear_txt) if byear_txt.isdigit() else 0
        height = int(h_txt) if h_txt.isdigit() else 0
        try:
            weight = float(w_txt) if w_txt else 0.0
        except ValueError:
            weight = 0.0

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET is_active = 0")
            if self.editing_new_profile or not self.current_user_id:
                cur = conn.execute(
                    "INSERT INTO users (full_name, birth_year, height, weight, is_active) VALUES (?, ?, ?, ?, 1)",
                    (fio, byear, height, weight)
                )
                self.current_user_id = cur.lastrowid
            else:
                conn.execute(
                    "UPDATE users SET full_name=?, birth_year=?, height=?, weight=?, is_active=1 WHERE id=?",
                    (fio, byear, height, weight, self.current_user_id)
                )

        self.user_dialog.dismiss()
        self.load_active_user()
        self.load_history()
        toast("Профиль сохранен")

    def open_profile_list_dialog(self):
        if self.user_dialog:
            self.user_dialog.dismiss()

        with sqlite3.connect(self.db_path) as conn:
            users = conn.execute("SELECT id, full_name, birth_year FROM users ORDER BY id ASC").fetchall()

        box = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(min(260, len(users)*52 + 60)))
        for uid, uname, uyear in users:
            sub = f" ({uyear} г.р.)" if uyear else ""
            item = OneLineAvatarIconListItem(
                text=f"{uname}{sub}",
                on_release=lambda x, target_id=uid: self.select_user_profile(target_id)
            )
            icon_left = IconLeftWidget(icon="account-check" if uid == self.current_user_id else "account-outline")
            item.add_widget(icon_left)
            box.add_widget(item)

        add_btn = MDRaisedButton(
            text="+ ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ",
            size_hint_x=1,
            md_bg_color=(0.85, 0.18, 0.22, 1),
            on_release=lambda x: self.start_new_profile()
        )
        box.add_widget(add_btn)

        self.profile_list_dialog = MDDialog(
            title="Выберите профиль",
            type="custom",
            content_cls=box,
            buttons=[MDFlatButton(text="ЗАКРЫТЬ", on_release=lambda x: self.profile_list_dialog.dismiss())]
        )
        self.profile_list_dialog.open()

    def select_user_profile(self, uid):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE users SET is_active = 0")
            conn.execute("UPDATE users SET is_active = 1 WHERE id = ?", (uid,))
        if self.profile_list_dialog:
            self.profile_list_dialog.dismiss()
        self.load_active_user()
        self.load_history()
        toast("Профиль переключен")

    def start_new_profile(self):
        if self.profile_list_dialog:
            self.profile_list_dialog.dismiss()
        self.open_user_dialog(new_profile=True)

    def set_current_datetime(self):
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.root.ids.dt_input.text = now_str
        self.update_period_preview(now_str)

    def update_period_preview(self, dt_text):
        try:
            dt_obj = datetime.strptime(dt_text.strip(), "%d.%m.%Y %H:%M")
            self.root.ids.period_badge.text = f"Период: {get_day_period(dt_obj)}"
        except ValueError:
            self.root.ids.period_badge.text = "Период: —"

    def add_record(self):
        sys_txt = self.root.ids.sys_input.text.strip()
        dia_txt = self.root.ids.dia_input.text.strip()
        pulse_txt = self.root.ids.pulse_input.text.strip()
        dt_txt = self.root.ids.dt_input.text.strip()
        note_txt = self.root.ids.note_input.text.strip()

        if not (sys_txt and dia_txt and pulse_txt):
            toast("Заполните САД, ДАД и пульс")
            return

        try:
            sys_val = int(sys_txt)
            dia_val = int(dia_txt)
            pulse_val = int(pulse_txt)
            dt_obj = datetime.strptime(dt_txt, "%d.%m.%Y %H:%M")
            dt_iso = dt_obj.strftime("%Y-%m-%d %H:%M")
            period = get_day_period(dt_obj)
        except ValueError:
            toast("Формат даты: ДД.ММ.ГГГГ ЧЧ:ММ")
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO records (user_id, dt_iso, period, sys, dia, pulse, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.current_user_id, dt_iso, period, sys_val, dia_val, pulse_val, note_txt)
            )

        self.root.ids.sys_input.text = ""
        self.root.ids.dia_input.text = ""
        self.root.ids.pulse_input.text = ""
        self.root.ids.note_input.text = ""
        self.set_current_datetime()
        self.load_history()
        toast(f"Запись сохранена ({period})")

    def get_bp_status_color(self, sys_v, dia_v):
        if sys_v >= 140 or dia_v >= 90:
            return (0.98, 0.88, 0.88, 1)
        elif sys_v >= 130 or dia_v >= 85:
            return (1.0, 0.95, 0.84, 1)
        elif sys_v < 90 or dia_v < 60:
            return (0.88, 0.93, 0.98, 1)
        return (0.89, 0.97, 0.90, 1)

    def load_history(self):
        container = self.root.ids.history_container
        container.clear_widgets()

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, dt_iso, period, sys, dia, pulse, note FROM records "
                "WHERE user_id = ? ORDER BY dt_iso DESC LIMIT 50",
                (self.current_user_id,)
            ).fetchall()

        chart_rows = list(reversed(rows[:15]))
        self.root.ids.chart_widget.set_data([(r[3], r[4], r[5]) for r in chart_rows])

        for rec_id, dt_iso, period, sys_v, dia_v, pulse_v, note in rows:
            dt_disp = datetime.strptime(dt_iso, "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
            card = MDCard(
                orientation="horizontal",
                padding=dp(12),
                size_hint_y=None,
                height=dp(74) if not note else dp(90),
                radius=[dp(10)],
                md_bg_color=self.get_bp_status_color(sys_v, dia_v),
                elevation=0
            )

            info_box = MDBoxLayout(orientation="vertical")
            title_lbl = MDLabel(
                text=f"[b]{sys_v}/{dia_v}[/b] ({pulse_v})  •  [size=12sp]{period}[/size]",
                markup=True,
                theme_text_color="Primary"
            )
            sub_text = f"{dt_disp}" + (f" • {note}" if note else "")
            sub_lbl = MDLabel(
                text=sub_text,
                font_style="Caption",
                theme_text_color="Secondary"
            )
            info_box.add_widget(title_lbl)
            info_box.add_widget(sub_lbl)

            del_btn = MDIconButton(
                icon="delete-outline",
                pos_hint={"center_y": 0.5},
                on_release=lambda x, r_id=rec_id: self.delete_record(r_id)
            )

            card.add_widget(info_box)
            card.add_widget(del_btn)
            container.add_widget(card)

    def delete_record(self, rec_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM records WHERE id = ?", (rec_id,))
        self.load_history()
        toast("Запись удалена")

    def open_pdf_dialog(self):
        today = datetime.now().strftime("%d.%m.%Y")
        first_day = datetime.now().replace(day=1).strftime("%d.%m.%Y")
        self.dialog_content = PDFDialogContent(start_default=first_day, end_default=today)

        self.dialog = MDDialog(
            title="Экспорт в PDF за период",
            type="custom",
            content_cls=self.dialog_content,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(
                    text="СФОРМИРОВАТЬ PDF",
                    md_bg_color=(0.85, 0.18, 0.22, 1),
                    on_release=self.generate_pdf
                ),
            ],
        )
        self.dialog.open()

    def generate_pdf(self, *args):
        start_str = self.dialog_content.start_date.text.strip()
        end_str = self.dialog_content.end_date.text.strip()

        try:
            start_iso = datetime.strptime(start_str, "%d.%m.%Y").strftime("%Y-%m-%d 00:00")
            end_iso = datetime.strptime(end_str, "%d.%m.%Y").strftime("%Y-%m-%d 23:59")
        except ValueError:
            toast("Неверный формат даты (нужен ДД.ММ.ГГГГ)")
            return

        user_data = self.get_current_user_data()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT dt_iso, period, sys, dia, pulse, note FROM records "
                "WHERE user_id = ? AND dt_iso BETWEEN ? AND ? ORDER BY dt_iso ASC",
                (self.current_user_id, start_iso, end_iso)
            ).fetchall()

        if not rows:
            toast("За выбранный период записей нет")
            return

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        font_candidates = [
            "DejaVuSans.ttf",
            "/system/fonts/Roboto-Regular.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        font_loaded = False
        for fp in font_candidates:
            if os.path.exists(fp):
                pdf.add_font("CustomFont", "", fp, uni=True)
                pdf.set_font("CustomFont", "", 12)
                font_loaded = True
                break

        if not font_loaded:
            toast("Ошибка: не найден системный шрифт с кириллицей")
            return

        # Заголовок отчета
        pdf.set_font("CustomFont", "", 15)
        pdf.set_text_color(140, 15, 20)
        pdf.cell(0, 8, "Дневник контроля артериального давления и пульса", ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("CustomFont", "", 10)
        pdf.cell(0, 6, f"Отчетный период: {start_str} — {end_str}", ln=True, align="C")
        pdf.ln(2)

        # Блок информации о пациенте (ФИО, Год рождения, Рост, Вес, ИМТ)
        if user_data:
            _, fio, byear, h, w = user_data
            pdf.set_fill_color(244, 246, 249)
            pdf.set_draw_color(200, 205, 212)
            y_box = pdf.get_y()
            pdf.rect(10, y_box, 190, 15, style="DF")

            pdf.set_xy(14, y_box + 1.5)
            pdf.set_font("CustomFont", "", 10.5)
            pdf.cell(0, 6, f"Пациент: {fio}", ln=True)

            info_parts = []
            if byear:
                age = datetime.now().year - int(byear)
                info_parts.append(f"Год рождения: {byear} ({age} лет)")
            if h:
                info_parts.append(f"Рост: {h} см")
            if w:
                info_parts.append(f"Вес: {w:g} кг")
            if h and w and h > 0:
                bmi = round(w / ((h / 100) ** 2), 1)
                info_parts.append(f"ИМТ: {bmi}")

            pdf.set_xy(14, y_box + 7.5)
            pdf.set_font("CustomFont", "", 9.5)
            pdf.cell(0, 6, "   |   ".join(info_parts) if info_parts else "Антропометрические данные не указаны", ln=True)
            pdf.set_y(y_box + 18)

        pdf.set_draw_color(0, 0, 0)

        # 1. Сводная статистика
        pdf.set_font("CustomFont", "", 11)
        pdf.cell(0, 6, "1. Сводная статистика по времени суток:", ln=True)
        pdf.ln(1)

        pdf.set_font("CustomFont", "", 9)
        pdf.set_fill_color(45, 62, 80)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(45, 7.5, "Период суток", border=1, fill=True, align="C")
        pdf.cell(35, 7.5, "Кол-во замеров", border=1, fill=True, align="C")
        pdf.cell(55, 7.5, "Среднее АД (САД/ДАД)", border=1, fill=True, align="C")
        pdf.cell(55, 7.5, "Средний пульс", border=1, fill=True, align="C", ln=True)

        pdf.set_text_color(0, 0, 0)
        for p_label in ("Утро", "День", "Вечер", "Весь период"):
            subset = rows if p_label == "Весь период" else [r for r in rows if r[1] == p_label]
            cnt = len(subset)
            if cnt > 0:
                avg_s = round(sum(r[2] for r in subset) / cnt)
                avg_d = round(sum(r[3] for r in subset) / cnt)
                avg_p = round(sum(r[4] for r in subset) / cnt)
                bp_str = f"{avg_s}/{avg_d} ({avg_p})"
                p_str = f"{avg_p} уд/мин"
            else:
                bp_str = "—"
                p_str = "—"

            pdf.cell(45, 6, p_label, border=1, align="C")
            pdf.cell(35, 6, str(cnt), border=1, align="C")
            pdf.cell(55, 6, bp_str, border=1, align="C")
            pdf.cell(55, 6, p_str, border=1, align="C", ln=True)

        pdf.ln(4)

        # 2. Журнал измерений (Дата | Утро | День | Вечер | Примечание)
        pdf.set_font("CustomFont", "", 11)
        pdf.cell(0, 6, "2. Журнал измерений (САД/ДАД (пульс)):", ln=True)
        pdf.ln(1)

        col_w_date = 26
        col_w_period = 34
        col_w_note = 62

        def draw_table_header():
            pdf.set_fill_color(155, 22, 28)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("CustomFont", "", 9.5)
            pdf.cell(col_w_date, 8, "Дата", border=1, fill=True, align="C")
            pdf.cell(col_w_period, 8, "Утро", border=1, fill=True, align="C")
            pdf.cell(col_w_period, 8, "День", border=1, fill=True, align="C")
            pdf.cell(col_w_period, 8, "Вечер", border=1, fill=True, align="C")
            pdf.cell(col_w_note, 8, "Примечание", border=1, fill=True, align="C", ln=True)
            pdf.set_text_color(0, 0, 0)

        draw_table_header()

        # Группируем по дате
        grouped_data = {}
        for dt_iso, period, sys_v, dia_v, pulse_v, note in rows:
            dt_obj = datetime.strptime(dt_iso, "%Y-%m-%d %H:%M")
            date_str = dt_obj.strftime("%d.%m.%Y")
            time_str = dt_obj.strftime("%H:%M")

            if date_str not in grouped_data:
                grouped_data[date_str] = {"Утро": None, "День": None, "Вечер": None, "notes": []}

            val_format = f"{sys_v}/{dia_v} ({pulse_v})"
            grouped_data[date_str][period] = (time_str, val_format)
            if note:
                grouped_data[date_str]["notes"].append(f"{time_str}: {note}")

        for date_str, periods in sorted(
            grouped_data.items(),
            key=lambda x: datetime.strptime(x[0], "%d.%m.%Y"),
            reverse=True
        ):
            notes_text = "\n".join(periods["notes"]) if periods["notes"] else "—"
            lines_count = max(1, len(periods["notes"]))
            row_h = max(11.5, lines_count * 5.5)

            if pdf.get_y() + row_h > 275:
                pdf.add_page()
                draw_table_header()

            y_before = pdf.get_y()

            # Ячейка Даты
            pdf.set_xy(10, y_before)
            pdf.set_font("CustomFont", "", 9.5)
            pdf.cell(col_w_date, row_h, date_str, border=1, align="C")

            # Ячейки Утро / День / Вечер (сверху время, снизу САД/ДАД (пульс))
            def render_period_cell(p_name, offset_x):
                x_pos = 10 + col_w_date + offset_x
                data = periods[p_name]
                if data:
                    t_str, val_str = data
                    pdf.set_xy(x_pos, y_before + 1.0)
                    pdf.set_font("CustomFont", "", 7)
                    pdf.set_text_color(90, 90, 90)
                    pdf.cell(col_w_period, 3.8, t_str, align="C")

                    pdf.set_xy(x_pos, y_before + 4.5)
                    pdf.set_font("CustomFont", "", 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(col_w_period, row_h - 5.0, val_str, align="C")
                else:
                    pdf.set_xy(x_pos, y_before)
                    pdf.set_font("CustomFont", "", 10)
                    pdf.set_text_color(120, 120, 120)
                    pdf.cell(col_w_period, row_h, "—", align="C")
                    pdf.set_text_color(0, 0, 0)

                pdf.set_xy(x_pos, y_before)
                pdf.cell(col_w_period, row_h, "", border=1)

            render_period_cell("Утро", 0)
            render_period_cell("День", col_w_period)
            render_period_cell("Вечер", col_w_period * 2)

            # Ячейка Примечания
            x_note = 10 + col_w_date + col_w_period * 3
            pdf.set_xy(x_note, y_before)
            pdf.cell(col_w_note, row_h, "", border=1)
            pdf.set_xy(x_note + 1.5, y_before + 1.2)
            pdf.set_font("CustomFont", "", 8)
            pdf.multi_cell(col_w_note - 3, 4.2, notes_text, border=0, align="L")

            pdf.set_y(y_before + row_h)

        filename = f"BP_A4_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        if platform == "android":
            from android.storage import primary_external_storage_path
            download_dir = os.path.join(primary_external_storage_path(), "Download")
            os.makedirs(download_dir, exist_ok=True)
            out_path = os.path.join(download_dir, filename)
        else:
            out_path = filename

        pdf.output(out_path)
        self.dialog.dismiss()
        toast(f"PDF сохранен: {filename}")


if __name__ == "__main__":
    BPTrackerApp().run()