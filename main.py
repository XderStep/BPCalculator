import customtkinter as ctk
import json
import os
from datetime import datetime

# Настройки темы
ctk.set_appearance_mode("dark")

# Палитра (Градиентный серо-лаймовый минимализм)
BG_MAIN = "#121316"          # Глубокий графитовый фон
BG_PANEL = "#1A1C20"         # Фон боковой панели и контейнеров
BG_CARD = "#22252A"          # Фон карточки задачи
BG_CARD_HOVER = "#2A2E35"    # Фон карточки при наведении
BG_CARD_ACTIVE = "#1E2B18"   # Темно-лаймовый оттенок выполненной задачи

LIME_PRIMARY = "#84CC16"     # Основной лаймовый акцент
LIME_BRIGHT = "#A3E635"      # Яркий лайм для ховеров и акцентов
LIME_DARK = "#4D7C0F"        # Приглушенный лайм для рамок
EMERALD_GOAL = "#10B981"     # Цвет при достижении 100% цели

TEXT_MAIN = "#F3F4F6"        # Основной белый текст
TEXT_MUTED = "#9CA3AF"       # Приглушенный серый текст
BORDER_COLOR = "#2E323B"     # Стандартный цвет рамок
DANGER_COLOR = "#EF4444"     # Красный для удаления/сброса
DANGER_HOVER = "#DC2626"

DATA_FILE = "data.json"
DEFAULT_GOAL = 50

# Базовые задания по умолчанию
DEFAULT_TASKS = {
    "25 действий на стройке": 2,
    "25 действий в порту": 2,
    "25 действий в шахте": 2,
    "20 подходов в тренажерном зале": 1,
    "Успешная тренировка в тире": 1,
    "10 посылок на почте": 1,
    "Арендовать киностудию": 2,
    "Купить лотерейный билет": 1,
    "Выиграть гонку в картинге": 1,
    "10 действий на ферме (любой способ)": 1,
    "Выкопать 1 сокровище (не мусор)": 1,
    "Проехать 1 уличную гонку (ставка от 1000$)": 1,
    "Выполнить 15 заказов дальнобойщиком в порт": 2,
    "Добавить 5 видео в кинотеатре": 1,
    "2 круга на любом маршруте автобусника": 2,
    "5 раз снять 100% шкуру с животных": 2,
    "Посетить любой сайт в браузере": 1,
    "Зайти в любой канал в Brawl": 1,
    "Поставить лайк любой анкете в Match": 1,
    "Кинуть мяч питомцу 15 раз": 2,
    "15 выполненных питомцем команд": 2,
    "Ставка в колесе удачи в казино": 3,
    "Проехать 1 станцию на метро": 2,
    "Поймать 20 рыб": 4,
    "Выполнить 2 квеста любых клубов": 4,
    "Починить деталь в автосервисе": 1,
    "Забросить 2 мяча в баскетболе": 1,
    "Забить 2 гола в футболе": 1,
    "Победить в армрестлинге": 1,
    "Победить в дартс": 1,
    "Забить 10 голов в волейболе": 1,
    "Поиграть 1 минуту в настольный теннис": 1,
    "Поиграть 1 минуту в большой теннис": 1,
    "Сыграть в мафию в казино": 3,
    "Сделать платеж по лизингу": 1
}


class BPCalculatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BPCalculator 2.0 | by Morris Lemark")
        self.geometry("1120x780")
        self.minsize(950, 650)
        self.configure(fg_color=BG_MAIN)
        self.attributes("-alpha", 0.0)  # Старт с прозрачности для плавного появления

        # Данные и состояние
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.data = self.load_and_migrate_data()
        self.tasks_config = self.data["tasks_config"]
        self.daily_goal = self.data.get("daily_goal", DEFAULT_GOAL)

        # Переменные анимации
        self.displayed_score = 0.0
        self.displayed_progress = 0.0
        self.target_score = 0
        self.target_progress = 0.0
        self.animating = False
        self.toast_job = None

        # Состояние UI
        self.task_vars = {}
        self.task_cards = {}
        self.current_filter = "Все"
        self.editing_task_original_name = None

        self.setup_layout()
        self.restore_day_state()
        self.render_calculator_tasks()
        self.render_editor_tasks()
        self.recalculate(animate=False)

        # Плавное появление окна
        self.fade_in()

    # ==========================================
    # РАБОТА С ДАННЫМИ (JSON + МИГРАЦИЯ)
    # ==========================================
    def load_and_migrate_data(self):
        raw_data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception:
                raw_data = {}

        # Проверка: если это старый формат файла (где ключи — сразу даты)
        if "tasks_config" not in raw_data or "history" not in raw_data:
            history = {}
            for k, v in raw_data.items():
                if isinstance(v, dict) and "total_bp" in v:
                    history[k] = v
            new_data = {
                "tasks_config": DEFAULT_TASKS.copy(),
                "daily_goal": DEFAULT_GOAL,
                "history": history
            }
        else:
            new_data = raw_data

        # Гарантируем наличие записи для сегодняшнего дня
        if self.current_date not in new_data["history"]:
            new_data["history"][self.current_date] = {
                "tasks": [],
                "platinum": False,
                "server_mult": "x1",
                "total_bp": 0
            }

        self.save_data_dict(new_data)
        return new_data

    def save_data_dict(self, data_dict=None):
        target = data_dict if data_dict is not None else self.data
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=4, ensure_ascii=False)

    # ==========================================
    # ПОСТРОЕНИЕ ИНТЕРФЕЙСА
    # ==========================================
    def setup_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=340)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_workspace()

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, width=340)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Заголовок программы
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(24, 16))

        ctk.CTkLabel(
            header_frame, text="BP", font=ctk.CTkFont(size=28, weight="bold"),
            text_color=BG_MAIN, fg_color=LIME_PRIMARY, corner_radius=8, width=48, height=42
        ).pack(side="left")

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=12)
        ctk.CTkLabel(title_box, text="CALCULATOR", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text=f"Дата: {self.current_date}", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w")

        # --- Карточка главного счета ---
        score_card = ctk.CTkFrame(self.sidebar, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        score_card.pack(fill="x", padx=20, pady=8)

        top_score_row = ctk.CTkFrame(score_card, fg_color="transparent")
        top_score_row.pack(fill="x", padx=16, pady=(14, 0))

        self.mode_title_lbl = ctk.CTkLabel(top_score_row, text="ЗАРАБОТАНО ЗА ДЕНЬ", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED)
        self.mode_title_lbl.pack(side="left")

        self.mult_badge = ctk.CTkLabel(
            top_score_row, text="Множитель: x1", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=LIME_DARK, text_color=TEXT_MAIN, corner_radius=6, padx=8, pady=2
        )
        self.mult_badge.pack(side="right")

        self.score_label = ctk.CTkLabel(score_card, text="0 BP", font=ctk.CTkFont(size=52, weight="bold"), text_color=LIME_PRIMARY)
        self.score_label.pack(pady=(4, 4))

        self.sub_stats_label = ctk.CTkLabel(score_card, text="Выполнено: 0 из 0", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self.sub_stats_label.pack(pady=(0, 10))

        # Прогресс-бар
        self.progress_bar = ctk.CTkProgressBar(score_card, progress_color=LIME_PRIMARY, fg_color="#141619", height=10, corner_radius=5)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 14))
        self.progress_bar.set(0)

        # Переключатель: За сегодня / За все дни
        self.stats_mode_var = ctk.StringVar(value="За сегодня")
        self.stats_switch = ctk.CTkSegmentedButton(
            score_card, values=["За сегодня", "За все дни"],
            variable=self.stats_mode_var, command=lambda _: self.recalculate(animate=True),
            selected_color=LIME_PRIMARY, selected_hover_color=LIME_BRIGHT,
            unselected_color="#16181C", unselected_hover_color=BG_CARD_HOVER,
            text_color=TEXT_MAIN, font=ctk.CTkFont(size=12, weight="bold"), height=34
        )
        self.stats_switch.pack(fill="x", padx=16, pady=(0, 16))

        # --- Карточка множителей ---
        mult_card = ctk.CTkFrame(self.sidebar, fg_color=BG_CARD, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        mult_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(mult_card, text="АКТИВНЫЕ БОНУСЫ", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(14, 8))

        self.plat_var = ctk.BooleanVar(value=False)
        self.plat_switch = ctk.CTkSwitch(
            mult_card, text="Платинум статус (x2)", variable=self.plat_var,
            command=lambda: self.recalculate(animate=True),
            progress_color=LIME_PRIMARY, button_color=TEXT_MAIN, button_hover_color=LIME_BRIGHT,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.plat_switch.pack(fill="x", padx=16, pady=(4, 12))

        ctk.CTkLabel(mult_card, text="Серверный множитель:", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 6))

        self.server_mult_var = ctk.StringVar(value="x1")
        self.server_seg = ctk.CTkSegmentedButton(
            mult_card, values=["x1", "x2", "x3"],
            variable=self.server_mult_var, command=lambda _: self.recalculate(animate=True),
            selected_color=LIME_PRIMARY, selected_hover_color=LIME_BRIGHT,
            unselected_color="#16181C", unselected_hover_color=BG_CARD_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"), height=34
        )
        self.server_seg.pack(fill="x", padx=16, pady=(0, 16))

        # --- Навигация между Калькулятором и Редактором ---
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=6)

        ctk.CTkLabel(nav_frame, text="РЕЖИМ РАБОТЫ", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=4, pady=(0, 6))

        self.nav_var = ctk.StringVar(value="📋 Калькулятор")
        self.nav_btn = ctk.CTkSegmentedButton(
            nav_frame, values=["📋 Калькулятор", "⚙️ Редактор"],
            variable=self.nav_var, command=self.switch_workspace_view,
            selected_color=LIME_PRIMARY, selected_hover_color=LIME_BRIGHT,
            unselected_color=BG_CARD, unselected_hover_color=BG_CARD_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"), height=38
        )
        self.nav_btn.pack(fill="x")

        # --- Нижние кнопки быстрых действий ---
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        self.select_all_btn = ctk.CTkButton(
            bottom_frame, text="✓ Отметить все", fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            text_color=TEXT_MAIN, border_width=1, border_color=BORDER_COLOR,
            height=36, font=ctk.CTkFont(size=13, weight="bold"), command=self.select_all_tasks
        )
        self.select_all_btn.pack(fill="x", pady=(0, 8))

        self.reset_day_btn = ctk.CTkButton(
            bottom_frame, text="↺ Сбросить текущий день", fg_color="#2A181A", hover_color=DANGER_HOVER,
            text_color="#FCA5A5", border_width=1, border_color=DANGER_COLOR,
            height=36, font=ctk.CTkFont(size=13, weight="bold"), command=self.reset_day
        )
        self.reset_day_btn.pack(fill="x")

    def build_workspace(self):
        self.workspace = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.workspace.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(1, weight=1)

        # Верхняя панель уведомлений (Toast)
        self.toast_label = ctk.CTkLabel(
            self.workspace, text="", font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=LIME_DARK, text_color=TEXT_MAIN, corner_radius=8, height=32, padx=14
        )

        # Контейнер 1: Режим калькулятора
        self.calc_view = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.calc_view.grid(row=1, column=0, sticky="nsew")
        self.calc_view.grid_columnconfigure(0, weight=1)
        self.calc_view.grid_rowconfigure(1, weight=1)

        self.build_calculator_view()

        # Контейнер 2: Режим редактора заданий
        self.editor_view = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.editor_view.grid_columnconfigure(0, weight=1)
        self.editor_view.grid_rowconfigure(1, weight=1)

        self.build_editor_view()

    def build_calculator_view(self):
        # Панель поиска и фильтрации
        top_bar = ctk.CTkFrame(self.calc_view, fg_color=BG_PANEL, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        top_bar.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            top_bar, placeholder_text="🔍 Быстрый поиск задания...",
            textvariable=self.search_var, height=38, corner_radius=8,
            fg_color=BG_MAIN, border_color=BORDER_COLOR, text_color=TEXT_MAIN,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.grid(row=0, column=0, padx=12, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _: self.apply_task_filters())
        self.add_focus_border_animation(self.search_entry)

        self.filter_seg = ctk.CTkSegmentedButton(
            top_bar, values=["Все", "Осталось", "Выполненные"],
            command=self.change_filter,
            selected_color=LIME_PRIMARY, selected_hover_color=LIME_BRIGHT,
            unselected_color=BG_MAIN, unselected_hover_color=BG_CARD_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"), height=36
        )
        self.filter_seg.set("Все")
        self.filter_seg.grid(row=0, column=1, padx=(0, 12), pady=10)

        # Скролл-список карточек заданий
        self.tasks_scroll = ctk.CTkScrollableFrame(
            self.calc_view, fg_color=BG_PANEL, corner_radius=14,
            border_width=1, border_color=BORDER_COLOR,
            scrollbar_button_color="#333842", scrollbar_button_hover_color=LIME_PRIMARY
        )
        self.tasks_scroll.grid(row=1, column=0, sticky="nsew")
        self.tasks_scroll.grid_columnconfigure(0, weight=1)

    def build_editor_view(self):
        # Карточка добавления / изменения задания
        form_card = ctk.CTkFrame(self.editor_view, fg_color=BG_PANEL, corner_radius=14, border_width=1, border_color=BORDER_COLOR)
        form_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        form_card.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(form_card, fg_color="transparent")
        header_row.grid(row=0, column=0, columnspan=4, sticky="ew", padx=16, pady=(14, 6))

        self.editor_form_title = ctk.CTkLabel(
            header_row, text="➕ ДОБАВИТЬ НОВОЕ ЗАДАНИЕ",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=LIME_PRIMARY
        )
        self.editor_form_title.pack(side="left")

        reset_defaults_btn = ctk.CTkButton(
            header_row, text="Вернуть стандартный список", fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            text_color=TEXT_MUTED, height=28, width=180, font=ctk.CTkFont(size=12),
            command=self.restore_default_tasks
        )
        reset_defaults_btn.pack(side="right")

        # Поля ввода названия и BP
        self.edit_name_var = ctk.StringVar()
        self.edit_name_entry = ctk.CTkEntry(
            form_card, placeholder_text="Название задания (например: Выиграть гонку в картинге)",
            textvariable=self.edit_name_var, height=40, fg_color=BG_MAIN, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=13)
        )
        self.edit_name_entry.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="ew")
        self.add_focus_border_animation(self.edit_name_entry)

        self.edit_bp_var = ctk.StringVar()
        self.edit_bp_entry = ctk.CTkEntry(
            form_card, placeholder_text="Базовые BP (число)",
            textvariable=self.edit_bp_var, width=150, height=40, fg_color=BG_MAIN, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=13)
        )
        self.edit_bp_entry.grid(row=1, column=1, padx=8, pady=(0, 16))
        self.add_focus_border_animation(self.edit_bp_entry)

        self.save_task_btn = ctk.CTkButton(
            form_card, text="Сохранить", fg_color=LIME_PRIMARY, hover_color=LIME_BRIGHT,
            text_color=BG_MAIN, font=ctk.CTkFont(size=13, weight="bold"), height=40, width=130,
            command=self.save_task_from_editor
        )
        self.save_task_btn.grid(row=1, column=2, padx=(8, 8), pady=(0, 16))

        self.cancel_edit_btn = ctk.CTkButton(
            form_card, text="Отмена", fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            text_color=TEXT_MAIN, font=ctk.CTkFont(size=13), height=40, width=90,
            command=self.cancel_task_edit
        )
        self.cancel_edit_btn.grid(row=1, column=3, padx=(0, 16), pady=(0, 16))
        self.cancel_edit_btn.grid_remove()

        # Список всех задач для редактирования/удаления
        self.editor_scroll = ctk.CTkScrollableFrame(
            self.editor_view, fg_color=BG_PANEL, corner_radius=14,
            border_width=1, border_color=BORDER_COLOR,
            scrollbar_button_color="#333842", scrollbar_button_hover_color=LIME_PRIMARY
        )
        self.editor_scroll.grid(row=1, column=0, sticky="nsew")
        self.editor_scroll.grid_columnconfigure(0, weight=1)

    # ==========================================
    # ОТРИСОВКА КАРТОЧЕК КАЛЬКУЛЯТОРА И РЕДАКТОРА
    # ==========================================
    def render_calculator_tasks(self):
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()

        old_states = {k: v.get() for k, v in self.task_vars.items()}
        self.task_vars.clear()
        self.task_cards.clear()

        today_saved = set(self.data["history"][self.current_date]["tasks"])

        for task_name, base_bp in self.tasks_config.items():
            is_checked = old_states.get(task_name, task_name in today_saved)
            var = ctk.BooleanVar(value=is_checked)
            self.task_vars[task_name] = var

            card = ctk.CTkFrame(
                self.tasks_scroll,
                fg_color=BG_CARD_ACTIVE if is_checked else BG_CARD,
                corner_radius=10,
                border_width=1,
                border_color=LIME_PRIMARY if is_checked else BORDER_COLOR
            )
            card.grid_columnconfigure(0, weight=1)

            cb = ctk.CTkCheckBox(
                card, text=task_name, variable=var,
                font=ctk.CTkFont(size=14, weight="bold" if is_checked else "normal"),
                fg_color=LIME_PRIMARY, hover_color=LIME_BRIGHT,
                checkmark_color=BG_MAIN, border_color="#525866",
                text_color=TEXT_MAIN,
                command=lambda t=task_name: self.on_task_toggled(t)
            )
            cb.grid(row=0, column=0, padx=14, pady=12, sticky="w")

            bp_badge = ctk.CTkLabel(
                card, text=f"+{base_bp} BP",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=LIME_PRIMARY if is_checked else "#16181D",
                text_color=BG_MAIN if is_checked else LIME_PRIMARY,
                corner_radius=6, padx=10, pady=4
            )
            bp_badge.grid(row=0, column=1, padx=14, pady=10, sticky="e")

            # Позволяем кликать по всей карточке и бейджу для переключения
            card.bind("<Button-1>", lambda e, t=task_name: self.toggle_card_click(t))
            bp_badge.bind("<Button-1>", lambda e, t=task_name: self.toggle_card_click(t))

            # Плавная подсветка карточки при наведении мыши
            card.bind("<Enter>", lambda e, t=task_name: self.on_card_hover(t, True))
            card.bind("<Leave>", lambda e, t=task_name: self.on_card_hover(t, False))

            self.task_cards[task_name] = {
                "frame": card,
                "checkbox": cb,
                "badge": bp_badge
            }

        self.apply_task_filters()

    def render_editor_tasks(self):
        for widget in self.editor_scroll.winfo_children():
            widget.destroy()

        for idx, (task_name, base_bp) in enumerate(self.tasks_config.items()):
            row = ctk.CTkFrame(self.editor_scroll, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            row.grid(row=idx, column=0, sticky="ew", padx=8, pady=5)
            row.grid_columnconfigure(0, weight=1)

            name_lbl = ctk.CTkLabel(row, text=task_name, font=ctk.CTkFont(size=14), text_color=TEXT_MAIN, anchor="w")
            name_lbl.grid(row=0, column=0, padx=14, pady=12, sticky="ew")

            info_badge = ctk.CTkLabel(
                row, text=f"База: {base_bp} BP  |  Plat: {base_bp * 2} BP",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#16181D", text_color=LIME_PRIMARY, corner_radius=6, padx=10, pady=4
            )
            info_badge.grid(row=0, column=1, padx=8, pady=10)

            edit_btn = ctk.CTkButton(
                row, text="✎ Изменить", width=95, height=32,
                fg_color="#2B303B", hover_color=LIME_PRIMARY, text_color=TEXT_MAIN,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda t=task_name, b=base_bp: self.start_task_edit(t, b)
            )
            edit_btn.grid(row=0, column=2, padx=4, pady=10)

            del_btn = ctk.CTkButton(
                row, text="✕", width=36, height=32,
                fg_color="#2A181A", hover_color=DANGER_HOVER, text_color="#FCA5A5",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda t=task_name: self.delete_task(t)
            )
            del_btn.grid(row=0, column=3, padx=(4, 12), pady=10)

    # ==========================================
    # ЛОГИКА РЕДАКТОРА ЗАДАНИЙ
    # ==========================================
    def start_task_edit(self, task_name, base_bp):
        self.editing_task_original_name = task_name
        self.edit_name_var.set(task_name)
        self.edit_bp_var.set(str(base_bp))
        self.editor_form_title.configure(text=f"✎ РЕДАКТИРОВАНИЕ: {task_name[:35]}...")
        self.save_task_btn.configure(text="Обновить")
        self.cancel_edit_btn.grid()
        self.edit_name_entry.focus_set()

    def cancel_task_edit(self):
        self.editing_task_original_name = None
        self.edit_name_var.set("")
        self.edit_bp_var.set("")
        self.editor_form_title.configure(text="➕ ДОБАВИТЬ НОВОЕ ЗАДАНИЕ")
        self.save_task_btn.configure(text="Сохранить")
        self.cancel_edit_btn.grid_remove()

    def save_task_from_editor(self):
        name = self.edit_name_var.get().strip()
        bp_str = self.edit_bp_var.get().strip()

        if not name:
            self.show_toast("⚠ Введите название задания!", is_error=True)
            return

        if not bp_str.isdigit() or int(bp_str) <= 0:
            self.show_toast("⚠ Базовые BP должны быть положительным числом!", is_error=True)
            return

        bp_val = int(bp_str)

        # Если редактируем существующее задание
        if self.editing_task_original_name:
            old_name = self.editing_task_original_name
            new_config = {}
            for k, v in self.tasks_config.items():
                if k == old_name:
                    new_config[name] = bp_val
                else:
                    new_config[k] = v
            self.tasks_config = new_config
            self.data["tasks_config"] = self.tasks_config

            # Обновляем имя в истории за сегодня, если задание было отмечено
            today_tasks = self.data["history"][self.current_date]["tasks"]
            if old_name in today_tasks:
                today_tasks[today_tasks.index(old_name)] = name
            if old_name in self.task_vars:
                self.task_vars[name] = ctk.BooleanVar(value=self.task_vars.pop(old_name).get())

            self.show_toast(f"✓ Задание «{name}» успешно обновлено")
        else:
            # Добавление нового
            self.tasks_config[name] = bp_val
            self.data["tasks_config"] = self.tasks_config
            self.show_toast(f"✓ Задание «{name}» (+{bp_val} BP) добавлено")

        self.cancel_task_edit()
        self.save_data_dict()
        self.render_calculator_tasks()
        self.render_editor_tasks()
        self.recalculate(animate=True)

    # Удалить задание
    def delete_task(self, task_name):
        if task_name in self.tasks_config:
            del self.tasks_config[task_name]
            self.data["tasks_config"] = self.tasks_config

        if task_name in self.task_vars:
            del self.task_vars[task_name]

        today_tasks = self.data["history"][self.current_date]["tasks"]
        if task_name in today_tasks:
            today_tasks.remove(task_name)

        if self.editing_task_original_name == task_name:
            self.cancel_task_edit()

        self.save_data_dict()
        self.render_calculator_tasks()
        self.render_editor_tasks()
        self.recalculate(animate=True)
        self.show_toast(f"🗑 Задание «{task_name}» удалено")

    # Вернуть старые задания
    def restore_default_tasks(self):
        self.tasks_config = DEFAULT_TASKS.copy()
        self.data["tasks_config"] = self.tasks_config
        self.cancel_task_edit()
        self.save_data_dict()
        self.render_calculator_tasks()
        self.render_editor_tasks()
        self.recalculate(animate=True)
        self.show_toast("↺ Восстановлен стандартный список заданий")

    # ==========================================
    # ВЗАИМОДЕЙСТВИЕ И ПОДСЧЕТ BP
    # ==========================================
    def get_current_multiplier(self):
        mult = 2 if self.plat_var.get() else 1
        srv = self.server_mult_var.get()
        if srv == "x2":
            mult *= 2
        elif srv == "x3":
            mult *= 3
        return mult

    def toggle_card_click(self, task_name):
        var = self.task_vars[task_name]
        var.set(not var.get())
        self.on_task_toggled(task_name)

    def on_task_toggled(self, task_name):
        self.update_single_card_style(task_name)
        self.recalculate(animate=True)
        if self.current_filter != "Все":
            self.apply_task_filters()

    def update_single_card_style(self, task_name):
        if task_name not in self.task_cards:
            return
        is_checked = self.task_vars[task_name].get()
        widgets = self.task_cards[task_name]
        mult = self.get_current_multiplier()
        effective_bp = self.tasks_config.get(task_name, 0) * mult

        widgets["frame"].configure(
            fg_color=BG_CARD_ACTIVE if is_checked else BG_CARD,
            border_color=LIME_PRIMARY if is_checked else BORDER_COLOR
        )
        widgets["checkbox"].configure(
            font=ctk.CTkFont(size=14, weight="bold" if is_checked else "normal")
        )
        widgets["badge"].configure(
            text=f"+{effective_bp} BP",
            fg_color=LIME_PRIMARY if is_checked else "#16181D",
            text_color=BG_MAIN if is_checked else LIME_PRIMARY
        )

    def on_card_hover(self, task_name, entering):
        if task_name not in self.task_cards:
            return
        is_checked = self.task_vars[task_name].get()
        frame = self.task_cards[task_name]["frame"]
        if entering:
            frame.configure(
                fg_color="#26381E" if is_checked else BG_CARD_HOVER,
                border_color=LIME_BRIGHT if is_checked else "#4B5262"
            )
        else:
            frame.configure(
                fg_color=BG_CARD_ACTIVE if is_checked else BG_CARD,
                border_color=LIME_PRIMARY if is_checked else BORDER_COLOR
            )

    def recalculate(self, animate=True):
        mult = self.get_current_multiplier()
        self.mult_badge.configure(text=f"Множитель: x{mult}")

        # Обновляем динамические бейджи на всех карточках
        for task_name in self.task_cards:
            self.update_single_card_style(task_name)

        completed_tasks = [t for t, v in self.task_vars.items() if v.get() and t in self.tasks_config]
        base_sum = sum(self.tasks_config[t] for t in completed_tasks)
        final_today_bp = base_sum * mult

        # Сохраняем прогресс текущего дня
        self.data["history"][self.current_date] = {
            "tasks": completed_tasks,
            "platinum": self.plat_var.get(),
            "server_mult": self.server_mult_var.get(),
            "total_bp": final_today_bp
        }
        self.save_data_dict()

        total_tasks_count = len(self.tasks_config)
        done_count = len(completed_tasks)

        if self.stats_mode_var.get() == "За сегодня":
            self.mode_title_lbl.configure(text="ЗАРАБОТАНО ЗА СЕГОДНЯ")
            self.target_score = final_today_bp
            self.target_progress = min(final_today_bp / max(self.daily_goal, 1), 1.0)
            self.sub_stats_label.configure(
                text=f"Задач: {done_count}/{total_tasks_count}  •  Цель дня: {final_today_bp}/{self.daily_goal} BP"
            )
        else:
            self.mode_title_lbl.configure(text="НАКОПЛЕНО ЗА ВСЕ ДНИ")
            all_time_bp = sum(day.get("total_bp", 0) for day in self.data["history"].values())
            days_count = len(self.data["history"])
            self.target_score = all_time_bp
            self.target_progress = 1.0
            self.sub_stats_label.configure(
                text=f"Активных дней в истории: {days_count}  •  Сегодня: {final_today_bp} BP"
            )

        # Цвет прогресс-бара меняется на изумрудный при достижении цели
        bar_color = EMERALD_GOAL if self.target_progress >= 1.0 else LIME_PRIMARY
        self.progress_bar.configure(progress_color=bar_color)

        if animate:
            if not self.animating:
                self.animating = True
                self.animate_counter()
        else:
            self.displayed_score = float(self.target_score)
            self.displayed_progress = self.target_progress
            self.score_label.configure(text=f"{int(self.displayed_score)} BP")
            self.progress_bar.set(self.displayed_progress)

    def change_filter(self, filter_value):
        self.current_filter = filter_value
        self.apply_task_filters()

    def apply_task_filters(self):
        query = self.search_var.get().lower().strip()
        row_idx = 0

        for task_name, widgets in self.task_cards.items():
            frame = widgets["frame"]
            is_checked = self.task_vars[task_name].get()

            matches_search = query in task_name.lower()
            matches_filter = (
                self.current_filter == "Все"
                or (self.current_filter == "Выполненные" and is_checked)
                or (self.current_filter == "Осталось" and not is_checked)
            )

            if matches_search and matches_filter:
                frame.grid(row=row_idx, column=0, sticky="ew", padx=8, pady=5)
                row_idx += 1
            else:
                frame.grid_remove()

    def select_all_tasks(self):
        for var in self.task_vars.values():
            var.set(True)
        self.recalculate(animate=True)
        self.apply_task_filters()
        self.show_toast("✓ Отмечены все задания")

    def reset_day(self):
        for var in self.task_vars.values():
            var.set(False)
        self.plat_var.set(False)
        self.server_mult_var.set("x1")
        self.recalculate(animate=True)
        self.apply_task_filters()
        self.show_toast("↺ Прогресс сегодняшнего дня сброшен")

    def switch_workspace_view(self, view_name):
        if "Калькулятор" in view_name:
            self.editor_view.grid_remove()
            self.calc_view.grid(row=1, column=0, sticky="nsew")
        else:
            self.calc_view.grid_remove()
            self.editor_view.grid(row=1, column=0, sticky="nsew")

    def restore_day_state(self):
        today_info = self.data["history"][self.current_date]
        self.plat_var.set(today_info.get("platinum", False))
        self.server_mult_var.set(today_info.get("server_mult", "x1"))

    # ==========================================
    # АНИМАЦИИ ИНТЕРФЕЙСА
    # ==========================================
    def animate_counter(self):
        diff_score = self.target_score - self.displayed_score
        diff_prog = self.target_progress - self.displayed_progress

        if abs(diff_score) < 0.4 and abs(diff_prog) < 0.008:
            self.displayed_score = float(self.target_score)
            self.displayed_progress = self.target_progress
            self.score_label.configure(text=f"{int(self.displayed_score)} BP")
            self.progress_bar.set(self.displayed_progress)
            self.animating = False
            return

        self.displayed_score += diff_score * 0.22
        self.displayed_progress += diff_prog * 0.22

        self.score_label.configure(text=f"{int(round(self.displayed_score))} BP")
        self.progress_bar.set(max(0.0, min(1.0, self.displayed_progress)))

        self.after(16, self.animate_counter)

    def add_focus_border_animation(self, entry_widget):
        """Безопасная анимация рамки поля ввода при фокусе (вместо focus_border_color)"""
        entry_widget.bind("<FocusIn>", lambda e: entry_widget.configure(border_color=LIME_PRIMARY))
        entry_widget.bind("<FocusOut>", lambda e: entry_widget.configure(border_color=BORDER_COLOR))

    def show_toast(self, message, is_error=False):
        if self.toast_job:
            self.after_cancel(self.toast_job)

        self.toast_label.configure(
            text=message,
            fg_color=DANGER_COLOR if is_error else LIME_DARK,
            text_color=TEXT_MAIN
        )
        self.toast_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.toast_job = self.after(2800, self.toast_label.grid_remove)

    def fade_in(self, alpha=0.0):
        if alpha < 1.0:
            alpha = min(1.0, alpha + 0.08)
            self.attributes("-alpha", alpha)
            self.after(16, lambda: self.fade_in(alpha))


if __name__ == "__main__":
    app = BPCalculatorApp()
    app.mainloop()