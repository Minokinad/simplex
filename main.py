import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QVBoxLayout, QLabel, 
                             QComboBox, QPushButton, QHBoxLayout, QSizePolicy, 
                             QScrollArea, QFrame, QSlider, QHeaderView, 
                             QGraphicsDropShadowEffect, QTabWidget, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

# Импорт наших модулей
import simplex_core
import gui_utils

# --- STYLESHEET (Apple Style) ---
STYLESHEET = """
/* Основной фон приложения */
QMainWindow, QScrollArea {
    background-color: #F5F5F7;
}

QWidget {
    font-family: "SF Pro Display", "Helvetica Neue", "Segoe UI", Arial, sans-serif;
    color: #1D1D1F;
}

/* Карточки - ТЕПЕРЬ БЕЗ ТЕНИ, НО С ЧЕТКОЙ ГРАНИЦЕЙ */
QFrame.Card {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #D1D1D6; /* Более темная граница вместо тени */
}

/* Заголовки */
QLabel.Header {
    font-size: 18px;
    font-weight: bold;
    color: #1D1D1F;
    margin-bottom: 5px;
}

QLabel.SubHeader {
    font-size: 14px;
    font-weight: 600;
    color: #86868B;
}

/* Кнопки */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 500;
    color: #1D1D1F;
}
QPushButton:hover {
    background-color: #F2F2F7;
    border-color: #8E8E93; /* Затемнение при наведении */
}
QPushButton:pressed {
    background-color: #E5E5EA;
}

/* Акцентная кнопка */
QPushButton#PrimaryButton {
    background-color: #007AFF;
    border: 1px solid #007AFF;
    color: #FFFFFF;
    font-weight: 600;
    font-size: 14px;
    padding: 8px 16px;
}
QPushButton#PrimaryButton:hover {
    background-color: #0062CC;
}
QPushButton#PrimaryButton:pressed {
    background-color: #0051A8;
}

/* Таблицы */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #D1D1D6;
    border-radius: 8px;
    gridline-color: #F2F2F7;
    selection-background-color: #E4EFFF;
    selection-color: #007AFF;
}
QHeaderView::section {
    background-color: #FFFFFF;
    padding: 4px;
    border: none;
    border-bottom: 1px solid #E5E5EA;
    font-weight: 600;
    color: #86868B;
    font-size: 12px;
}
QTableCornerButton::section {
    background-color: #FFFFFF;
    border: none;
    border-bottom: 1px solid #E5E5EA;
}

/* ComboBox */
QComboBox {
    border: 1px solid #D1D1D6;
    border-radius: 6px;
    padding: 4px 8px;
    background-color: #FFFFFF;
    selection-background-color: #007AFF;
}
QComboBox:hover {
    border-color: #007AFF;
}

/* Слайдеры */
QSlider::groove:horizontal {
    border: 1px solid #E5E5EA;
    height: 4px;
    background: #E5E5EA;
    margin: 2px 0;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 1px solid #D1D1D6;
    width: 20px; /* Чуть больше для удобства */
    height: 20px;
    margin: -8px 0;
    border-radius: 10px;
}
QSlider::handle:horizontal:hover {
    border-color: #007AFF;
    background: #F2F2F7;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #F5F5F7;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #C7C7CC;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tabs */
QTabWidget::pane { 
    border: 1px solid #D1D1D6; 
    border-radius: 8px; 
    background: white; 
}
QTabBar::tab { 
    background: #F2F2F7; 
    color: #86868B; 
    padding: 8px 24px; 
    border-top-left-radius: 6px; 
    border-top-right-radius: 6px; 
    margin-right: 2px; 
}
QTabBar::tab:selected { 
    background: #FFFFFF; 
    color: #007AFF; 
    font-weight: bold; 
    border-bottom: 2px solid #007AFF; 
}
"""

class Card(QFrame):
    """Виджет-карточка без тени (для производительности)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Simplex Solver Pro")
        
        # Настройка шрифта приложения
        self.app_font = QFont("SF Pro Display", 11)
        if not self.app_font.exactMatch():
            self.app_font = QFont("Helvetica Neue", 11)
        if not self.app_font.exactMatch():
            self.app_font = QFont("Arial", 11)
            
        self.setFont(self.app_font)
        self.setStyleSheet(STYLESHEET)
        
        self.CONSTRAINT_EQUALITY_SIGNS = [u"\u2264", u"\u2265", "="]
        
        self.slider_widgets = []
        self.canvas_widget = None
        
        # self.recalc_timer = QTimer()
        # self.recalc_timer.setSingleShot(True)
        # self.recalc_timer.setInterval(25) # Пересчет не чаще раз в 100мс
        # self.recalc_timer.timeout.connect(self.fast_solve_event)
        
        self.setup_layout()
        self.resize(1280, 900)

    def setup_layout(self):
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.NoFrame)

        self.container_widget = QWidget()
        self.main_layout = QGridLayout(self.container_widget)
        self.main_layout.setSpacing(24) # Больше воздуха между блоками
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # 1. Блок Ввода данных (Карточка)
        self.input_card = Card()
        self.input_layout = QVBoxLayout(self.input_card)
        self.input_layout.setSpacing(15)
        self.input_layout.setContentsMargins(20, 20, 20, 20)
        
        self.create_input_ui()
      
        # 2. Блок Графика (Карточка)
        self.graph_container_card = Card()
        self.graph_layout = QVBoxLayout(self.graph_container_card)
        self.graph_layout.setContentsMargins(20, 20, 20, 20)
        self.graph_container_card.hide() # Скрыт пока нет решения

        # 3. Блок Результатов (Карточка)
        self.results_card = Card()
        self.results_layout = QVBoxLayout(self.results_card)
        self.results_layout.setContentsMargins(20, 20, 20, 20)
        self.results_layout.setSpacing(15)
        
        # Placeholder
        placeholder_label = QLabel("Здесь будет решение")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("color: #86868B; font-size: 16px; font-style: italic;")
        self.results_layout.addWidget(placeholder_label)
        
        # Размещение в сетке
        self.main_layout.addWidget(self.input_card, 0, 0)
        self.main_layout.addWidget(self.graph_container_card, 0, 1)
        self.main_layout.addWidget(self.results_card, 1, 0, 1, 2)
        
        self.main_layout.setColumnStretch(0, 1) # Колонка ввода
        self.main_layout.setColumnStretch(1, 1) # Колонка графика
        self.main_layout.setRowStretch(1, 1)    # Растягиваем строку с результатами

        self.main_scroll.setWidget(self.container_widget)
        self.setCentralWidget(self.main_scroll)

    def create_input_ui(self):
        # Заголовок
        header = QLabel("Параметры задачи")
        header.setProperty("class", "Header")
        self.input_layout.addWidget(header)

        # Панель инструментов (Кнопки)
        tools_layout = QHBoxLayout()
        
        self.add_row_btn = QPushButton('+ Ограничение')
        self.add_col_btn = QPushButton('+ Переменная')
        self.del_row_btn = QPushButton('- Ограничение')
        self.del_col_btn = QPushButton('- Переменная')
        
        for btn in [self.add_row_btn, self.add_col_btn, self.del_row_btn, self.del_col_btn]:
            btn.setCursor(Qt.PointingHandCursor)
            tools_layout.addWidget(btn)
        
        tools_layout.addStretch()
        self.input_layout.addLayout(tools_layout)

        # Секция ограничений
        lbl_constr = QLabel("1. Система ограничений")
        lbl_constr.setProperty("class", "SubHeader")
        self.input_layout.addWidget(lbl_constr)
        
        self.constraint_table = self.create_table(2, 4, self.CONSTRAINT_EQUALITY_SIGNS, self.create_header_labels(2))
        self.input_layout.addWidget(self.constraint_table)

        # Секция целевой функции
        obj_layout = QHBoxLayout()
        lbl_obj = QLabel("2. Целевая функция")
        lbl_obj.setProperty("class", "SubHeader")
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Максимизация", "Минимизация"])
        self.operation_combo.setCursor(Qt.PointingHandCursor)
        self.operation_combo.currentIndexChanged.connect(lambda: self.fast_solve_event() if self.canvas_widget else None)
        
        obj_layout.addWidget(lbl_obj)
        obj_layout.addSpacing(10)
        obj_layout.addWidget(self.operation_combo)
        obj_layout.addStretch()
        self.input_layout.addLayout(obj_layout)

        self.objective_fxn_table = self.create_table(1, 4, ["="], self.create_header_labels(2))
        # Скрываем combo box для Z строки или блокируем
        self.objective_fxn_table.setItem(0, 3, QTableWidgetItem("E"))
        self.objective_fxn_table.item(0, 3).setFlags(Qt.ItemIsEnabled)
        self.objective_fxn_table.item(0, 3).setTextAlignment(Qt.AlignCenter)
        # Убираем комбобокс знака для целевой функции, там всегда =
        combo_widget = QWidget(); combo_widget.setDisabled(True)
        self.objective_fxn_table.setCellWidget(0, 2, combo_widget)
        self.objective_fxn_table.setItem(0, 2, QTableWidgetItem("="))
        self.objective_fxn_table.item(0, 2).setTextAlignment(Qt.AlignCenter)
        
        self.input_layout.addWidget(self.objective_fxn_table)
        
        # --- СЛАЙДЕРЫ ДЛЯ ЦЕЛЕВОЙ ФУНКЦИИ (инициализация контейнера) ---
        self.objective_sliders_container = QWidget()
        self.objective_sliders_layout = QVBoxLayout(self.objective_sliders_container)
        self.objective_sliders_layout.setContentsMargins(0, 10, 0, 0)
        # Контейнер будет добавлен в graph_layout при решении, если переменных 2.
        # ------------------------------------

        # Кнопка РЕШИТЬ
        self.solve_btn = QPushButton('Рассчитать оптимальное решение')
        self.solve_btn.setObjectName("PrimaryButton")
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        self.solve_btn.setFixedHeight(40)
        self.input_layout.addSpacing(10)
        self.input_layout.addWidget(self.solve_btn)
        
        # --- NEW: Add stretch to prevent collapsing ---
        self.input_layout.addStretch()
        # --- END NEW ---

        # Signals
        self.add_row_btn.clicked.connect(self.add_row_event)
        self.add_col_btn.clicked.connect(self.add_column_event)
        self.del_row_btn.clicked.connect(self.del_row_event)
        self.del_col_btn.clicked.connect(self.del_col_event)
        self.solve_btn.clicked.connect(self.full_solve_event)

    # --- Zoom Methods ---
    def zoom_event(self, factor):
        if not self.canvas_widget: return
        ax = self.canvas_widget.axes
        
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        x_center = (cur_xlim[0] + cur_xlim[1]) / 2
        y_center = (cur_ylim[0] + cur_ylim[1]) / 2
        
        new_width = (cur_xlim[1] - cur_xlim[0]) * factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * factor
        
        ax.set_xlim([x_center - new_width / 2, x_center + new_width / 2])
        ax.set_ylim([y_center - new_height / 2, y_center + new_height / 2])
        
        self.canvas_widget.draw()

    def zoom_in_event(self):
        self.zoom_event(0.85) 

    def zoom_out_event(self):
        self.zoom_event(1.15) 

    def reset_view_event(self):
        if not self.canvas_widget or not hasattr(self, 'initial_xlim'): return
        self.canvas_widget.axes.set_xlim(self.initial_xlim)
        self.canvas_widget.axes.set_ylim(self.initial_ylim)
        self.canvas_widget.draw()

    # --- Table Methods ---
    def create_table(self, rows, cols, signs=None, h_headers=None):
        table = QTableWidget(self)
        table.setColumnCount(cols)
        table.setRowCount(rows)
        table.setShowGrid(False) # Apple style cleaner look (borders handled by CSS)
        table.setAlternatingRowColors(True) # Чередование цветов
        
        if h_headers: table.setHorizontalHeaderLabels(h_headers)
        
        # Настройка растягивания
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Последние две колонки фиксируем поменьше
        header.setSectionResizeMode(cols-1, QHeaderView.Fixed)
        header.setSectionResizeMode(cols-2, QHeaderView.Fixed)
        table.setColumnWidth(cols-1, 80)
        table.setColumnWidth(cols-2, 60)

        if signs:
            for i in range(rows): self.set_combo_box(table, i, signs)
            
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.adjust_table_height(table)
        return table

    def set_combo_box(self, table, row, options):
        combo = QComboBox()
        combo.addItems(options)
        # Стилизация для ячейки таблицы
        combo.setStyleSheet("border: none; background: transparent;") 
        combo.currentIndexChanged.connect(lambda: self.fast_solve_event() if self.canvas_widget else None)
        table.setCellWidget(row, table.columnCount() - 2, combo)

    def adjust_table_height(self, table):
        # Высота строки + хедер + отступы
        row_h = 36 # Чуть выше стандартного
        table.verticalHeader().setDefaultSectionSize(row_h)
        h = table.horizontalHeader().height() + (row_h * table.rowCount()) + 4
        table.setMinimumHeight(min(h, 300))
        table.setMaximumHeight(min(h, 300))
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def create_header_labels(self, n):
        return [f"X{i+1}" for i in range(n)] + ["Знак", "Значение"]

    # --- Events ---
    def add_row_event(self):
        self.constraint_table.insertRow(self.constraint_table.rowCount())
        self.set_combo_box(self.constraint_table, self.constraint_table.rowCount()-1, self.CONSTRAINT_EQUALITY_SIGNS)
        self.adjust_table_height(self.constraint_table)

    def del_row_event(self):
        if self.constraint_table.rowCount() > 1:
            self.constraint_table.removeRow(self.constraint_table.rowCount()-1)
            self.adjust_table_height(self.constraint_table)

    def add_column_event(self):
        # Вставляем перед "Знаком" и "Значением"
        idx = self.constraint_table.columnCount()-2
        self.constraint_table.insertColumn(idx)
        self.objective_fxn_table.insertColumn(idx)
        
        h = self.create_header_labels(self.constraint_table.columnCount()-2)
        self.constraint_table.setHorizontalHeaderLabels(h)
        self.objective_fxn_table.setHorizontalHeaderLabels(h)
        
        # Сброс растяжения
        self.constraint_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.constraint_table.horizontalHeader().setSectionResizeMode(self.constraint_table.columnCount()-1, QHeaderView.Fixed)
        self.constraint_table.horizontalHeader().setSectionResizeMode(self.constraint_table.columnCount()-2, QHeaderView.Fixed)
        self.constraint_table.setColumnWidth(self.constraint_table.columnCount()-1, 80)
        self.constraint_table.setColumnWidth(self.constraint_table.columnCount()-2, 60)

        self.objective_fxn_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.objective_fxn_table.horizontalHeader().setSectionResizeMode(self.objective_fxn_table.columnCount()-1, QHeaderView.Fixed)
        self.objective_fxn_table.horizontalHeader().setSectionResizeMode(self.objective_fxn_table.columnCount()-2, QHeaderView.Fixed)
        self.objective_fxn_table.setColumnWidth(self.objective_fxn_table.columnCount()-1, 80)
        self.objective_fxn_table.setColumnWidth(self.objective_fxn_table.columnCount()-2, 60)

        # Обновляем слайдеры ЦФ при изменении числа переменных
        if self.objective_fxn_table.columnCount() - 2 == 2:
            self.create_objective_sliders()
        else:
            self.clear_objective_sliders()
    
    def del_col_event(self):
        if self.constraint_table.columnCount() > 4: # Min 2 vars + sign + val
            idx = self.constraint_table.columnCount() - 3
            self.constraint_table.removeColumn(idx)
            self.objective_fxn_table.removeColumn(idx)
            
            # Повторно создаем и устанавливаем заголовки
            h = self.create_header_labels(self.constraint_table.columnCount() - 2)
            self.constraint_table.setHorizontalHeaderLabels(h)
            self.objective_fxn_table.setHorizontalHeaderLabels(h)

        # Обновляем слайдеры ЦФ при изменении числа переменных
        if self.objective_fxn_table.columnCount() - 2 == 2:
            self.create_objective_sliders()
        else:
            self.clear_objective_sliders()

    def clear_ui_results(self):
        # Очищаем лейаут результатов (удаляем placeholder или старое решение)
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        # === NEW: Отделяем контейнер слайдеров перед очисткой графика ===
        if self.objective_sliders_container and self.objective_sliders_container.parent():
            self.objective_sliders_container.setParent(None)
        # === END NEW ===
        
        # Очищаем лейаут графика
        while self.graph_layout.count():
            item = self.graph_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        self.slider_widgets = []
        self.canvas_widget = None
        self.graph_container_card.hide() # Скрываем только контейнер графика

    def full_solve_event(self):
        try:
            raw_matrix, rhs, obj_coeffs = simplex_core.get_simplex_data(self.objective_fxn_table, self.constraint_table)
            num_vars = self.constraint_table.columnCount() - 2
            operation = self.operation_combo.currentText()
            
            final_z, history, opt_vars, err, headers = simplex_core.calculate_simplex(raw_matrix, operation, num_vars)
            
            if err:
                # При ошибке просто выходим, не трогая UI, чтобы placeholder остался
                QMessageBox.warning(self, "Ошибка решения", err)
                return

            # Только при успешном решении очищаем старые данные
            self.clear_ui_results()
            
            # --- 1. График (если 2 переменные) ---
            if num_vars == 2:
                self.graph_container_card.show()
                
                # --- NEW: Header with zoom controls ---
                graph_header_layout = QHBoxLayout()
                lbl = QLabel("Графическая интерпретация")
                lbl.setProperty("class", "Header")
                graph_header_layout.addWidget(lbl)
                graph_header_layout.addStretch()

                self.zoom_out_btn = QPushButton("-")
                self.zoom_in_btn = QPushButton("+")
                self.reset_view_btn = QPushButton("Сброс")
                
                for btn in [self.zoom_out_btn, self.zoom_in_btn]:
                    btn.setFixedSize(30, 30)
                    btn.setCursor(Qt.PointingHandCursor)
                    graph_header_layout.addWidget(btn)
                
                self.reset_view_btn.setCursor(Qt.PointingHandCursor)
                graph_header_layout.addWidget(self.reset_view_btn)

                self.zoom_in_btn.clicked.connect(self.zoom_in_event)
                self.zoom_out_btn.clicked.connect(self.zoom_out_event)
                self.reset_view_btn.clicked.connect(self.reset_view_event)
                
                self.graph_layout.addLayout(graph_header_layout)
                # --- END NEW ---
                
                self.canvas_widget = gui_utils.MplCanvas(self, width=6, height=5)
                self.graph_layout.addWidget(self.canvas_widget)
                
                constrs = gui_utils.plot_constraints(self.canvas_widget, self.constraint_table, opt_vars, obj_coeffs=obj_coeffs)
                
                # --- NEW: Store initial zoom ---
                self.initial_xlim = self.canvas_widget.axes.get_xlim()
                self.initial_ylim = self.canvas_widget.axes.get_ylim()
                # --- END NEW ---

                self.create_sliders(constrs)
                self.create_objective_sliders() # Создаем слайдеры для ЦФ
                self.graph_layout.addWidget(self.objective_sliders_container) # ДОБАВЛЯЕМ СЛАЙДЕРЫ СЮДА
            else:
                self.clear_objective_sliders() # Убираем, если переменных не 2

            # --- 2. Результаты (Табы) ---
            res_lbl = QLabel("Результаты решения")
            res_lbl.setProperty("class", "Header")
            self.results_layout.addWidget(res_lbl)

            # Отображаем финальный ответ сразу сверху
            self.add_final_result(history[-1]['table'], final_z)

            # Создаем Tabs
            tabs = QTabWidget()
            tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            tabs.setMinimumHeight(800)
            tabs.setStyleSheet("""
                QTabWidget::pane { border: 1px solid #E5E5EA; border-radius: 8px; background: white; }
                QTabBar::tab { background: #F2F2F7; color: #86868B; padding: 8px 24px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
                QTabBar::tab:selected { background: #FFFFFF; color: #007AFF; font-weight: bold; border-bottom: 2px solid #007AFF; }
            """)
            
            # --- Вкладка 1: Пошаговое решение ---
            tab_steps = QWidget()
            layout_steps = QVBoxLayout(tab_steps)
            layout_steps.setSpacing(15)

            # Итерационные таблицы добавляются напрямую в layout вкладки,
            # чтобы избежать двойного скроллбара.
            for i, step in enumerate(history):
                self.add_iteration_table_to_layout(layout_steps, i, step, headers)
            layout_steps.addStretch()

            tabs.addTab(tab_steps, "Пошаговый расчет")

            # --- Вкладка 2: Анализ чувствительности (Красивый) ---
            is_max = (operation == "Максимизация")
            var_an, constr_an, detail_report = simplex_core.perform_sensitivity_analysis(
                history[-1]['table'], rhs, obj_coeffs, num_vars, self.constraint_table.rowCount(), is_max
            )
            
            tab_sens = QWidget()
            self.setup_sensitivity_tab(tab_sens, var_an, constr_an)
            tabs.addTab(tab_sens, "Анализ чувствительности")

            self.results_layout.addWidget(tabs)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Критическая ошибка", f"Произошел сбой: {str(e)}")

    def fast_solve_event(self):
        if not self.canvas_widget: return
        try:
            # Получаем obj_coeffs (третий аргумент)
            raw_matrix, _, obj_coeffs = simplex_core.get_simplex_data(self.objective_fxn_table, self.constraint_table)
            
            num_vars = self.constraint_table.columnCount() - 2
            op = self.operation_combo.currentText()
            _, _, opt_vars, err, _ = simplex_core.calculate_simplex(raw_matrix, op, num_vars)
            
            if not err:
                # ИЗМЕНЕНИЕ ЗДЕСЬ: добавляем obj_coeffs=obj_coeffs
                gui_utils.plot_constraints(self.canvas_widget, self.constraint_table, opt_vars, obj_coeffs=obj_coeffs)
        except:
            pass

    # --- UI Helpers ---
    def add_iteration_table(self, i, data, headers):
        tbl_dict = data['table']
        pivot_r = data['pivot_row']
        pivot_c = data['pivot_col']
        
        lbl = QLabel(f"Итерация {i}")
        lbl.setProperty("class", "SubHeader")
        self.results_layout.addWidget(lbl)
        
        row_keys = list(tbl_dict.keys())
        col_count = len(tbl_dict[row_keys[0]]) + 1
        if pivot_c is not None: col_count += 1
        
        table = QTableWidget(len(row_keys), col_count)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        
        h_l = ["Базис"] + headers
        if pivot_c is not None: h_l.append("Симпл. отношения")
        table.setHorizontalHeaderLabels(h_l)
        
        # Colors
        hl_row = QColor("#E4EFFF") # Soft Blue
        hl_col = QColor("#FFF8E1") # Soft Yellow
        hl_both = QColor("#FFE0B2") # Soft Orange
        
        for r_idx, key in enumerate(row_keys):
            item_k = QTableWidgetItem(key)
            item_k.setTextAlignment(Qt.AlignCenter)
            if r_idx == pivot_r: item_k.setBackground(hl_row)
            table.setItem(r_idx, 0, item_k)
            
            vals = tbl_dict[key]
            for c_idx, val in enumerate(vals):
                it = QTableWidgetItem(f"{val:.3f}")
                it.setTextAlignment(Qt.AlignCenter)
                is_r = (r_idx == pivot_r)
                is_c = (c_idx == pivot_c)
                if is_r and is_c: it.setBackground(hl_both)
                elif is_r: it.setBackground(hl_row)
                elif is_c: it.setBackground(hl_col)
                table.setItem(r_idx, c_idx+1, it)
                
            if pivot_c is not None:
                th_val = ""
                ratios = data['ratios']
                if r_idx > 0 and (r_idx-1) < len(ratios):
                    v = ratios[r_idx-1]
                    th_val = f"{v:.3f}" if v != float('inf') else "-"
                it_th = QTableWidgetItem(th_val)
                it_th.setTextAlignment(Qt.AlignCenter)
                if r_idx == pivot_r: it_th.setBackground(hl_row)
                table.setItem(r_idx, col_count-1, it_th)
                
        table.verticalHeader().setVisible(False)
        self.adjust_table_height(table)
        self.results_layout.addWidget(table)
        
        if pivot_c is not None:
            entering = data.get('entering', '')
            leaving = data.get('leaving', '')
            info_lbl = QLabel(f"➡ Входит: <b>{entering}</b>, Выходит: <b>{leaving}</b>")
            info_lbl.setStyleSheet("color: #86868B; margin-bottom: 10px; font-size: 13px;")
            self.results_layout.addWidget(info_lbl)

    def add_final_result(self, data, z):
        frame = QFrame()
        frame.setStyleSheet("background-color: #34C759; border-radius: 8px;")
        l = QHBoxLayout(frame)
        lbl = QLabel(f"Оптимальное решение найдено: E = {z:.4f}")
        lbl.setStyleSheet("color: white; font-weight: bold; font-size: 15px;")
        l.addWidget(lbl)
        self.results_layout.addWidget(frame)

    def add_sensitivity_report(self, var_data, constr_data, detail_text):
        lbl = QLabel("Анализ на чувствительность")
        lbl.setProperty("class", "Header")
        lbl.setStyleSheet("margin-top: 20px;")
        self.results_layout.addWidget(lbl)
        
        # Helper to simplify table creation
        def make_report_table(headers, data_list, keys):
            t = QTableWidget(len(data_list), len(headers))
            t.setHorizontalHeaderLabels(headers)
            t.setShowGrid(False)
            t.setAlternatingRowColors(True)
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            for i, d in enumerate(data_list):
                for j, key in enumerate(keys):
                    val = d[key]
                    if isinstance(val, float): val = f"{val:.4f}"
                    it = QTableWidgetItem(str(val))
                    it.setTextAlignment(Qt.AlignCenter)
                    t.setItem(i, j, it)
            self.adjust_table_height(t)
            return t

        # Таблица переменных
        v_headers = ["Переменная", "Значение", "Ред. стоим.", "Коэф. ЦФ", "Доп. +", "Доп. -"]
        v_keys = ['name', 'final_value', 'reduced_cost', 'obj_coeff', 'allow_increase', 'allow_decrease']
        t_v = make_report_table(v_headers, var_data, v_keys)
        self.results_layout.addWidget(t_v)
        
        # Таблица ограничений
        c_headers = ["Ограничение", "Теневая цена", "RHS", "Доп. +", "Доп. -"]
        c_keys = ['name', 'shadow_price', 'rhs', 'allow_increase', 'allow_decrease']
        t_c = make_report_table(c_headers, constr_data, c_keys)
        self.results_layout.addWidget(t_c)

        # Текст
        lbl_det = QLabel("Подробный расчет (параметр D)")
        lbl_det.setProperty("class", "SubHeader")
        lbl_det.setStyleSheet("margin-top: 15px;")
        self.results_layout.addWidget(lbl_det)
        
        report_label = QLabel(detail_text)
        report_label.setFont(QFont("Menlo", 11)) # Monospace для отчета
        report_label.setWordWrap(True)
        report_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        report_label.setStyleSheet("""
            background-color: #F5F5F7; 
            border-radius: 8px; 
            padding: 15px; 
            color: #333;
        """)
        self.results_layout.addWidget(report_label)

    def create_sliders(self, constraints):
        # Очистка и создание контейнера (без изменений)
        box = QFrame()
        box.setStyleSheet("background-color: #F9F9F9; border-radius: 8px; padding: 10px;")
        l = QVBoxLayout(box)
        
        head = QLabel("Интерактивное изменение ресурсов (Bi)")
        head.setStyleSheet("font-weight: bold; color: #555; margin-bottom: 5px;")
        l.addWidget(head)
        
        self.slider_widgets = [] 
        
        for i, c in enumerate(constraints):
            h = QHBoxLayout()
            sl = QSlider(Qt.Horizontal)
            sl.setCursor(Qt.PointingHandCursor)
            
            val = c['c']
            max_val = max(abs(val)*2, 20)
            sl.setRange(0, int(max_val*10))
            sl.setValue(int(val*10))
            
            lbl_name = QLabel(f"Огр. {i+1}:")
            # БЫЛО: 50 -> СТАЛО: 75 (чтобы влезло "Огр. 10:")
            lbl_name.setFixedWidth(75) 
            lbl_name.setStyleSheet("font-weight: 600; color: #333;")
            
            lbl_val = QLabel(f"{val:.1f}")
            # БЫЛО: 40 -> СТАЛО: 65 (чтобы влезли числа вроде 100.0)
            lbl_val.setFixedWidth(65)
            lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            def change_handler(v, idx=i, lb=lbl_val):
                real = v / 10.0
                lb.setText(f"{real:.1f}")
                self.constraint_table.item(idx, self.constraint_table.columnCount()-1).setText(str(real))
                #self.recalc_timer.start()
                self.fast_solve_event()
                
            sl.valueChanged.connect(change_handler)
            h.addWidget(lbl_name); h.addWidget(sl); h.addWidget(lbl_val)
            l.addLayout(h)
            self.slider_widgets.append(sl)
            
        self.graph_layout.addWidget(box)
        
    def clear_objective_sliders(self):
        """Safely clears sliders from the objective function layout."""
        try:
            # Проверяем, был ли контейнер удален
            if not self.objective_sliders_container or not self.objective_sliders_layout:
                raise RuntimeError("Container was deleted")
            
            # Clear all widgets from the layout
            while self.objective_sliders_layout.count():
                child = self.objective_sliders_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        except RuntimeError:
            # If container was deleted, recreate it
            self.objective_sliders_container = QWidget()
            self.objective_sliders_layout = QVBoxLayout(self.objective_sliders_container)
            self.objective_sliders_layout.setContentsMargins(0, 10, 0, 0)
    
    def update_obj_from_slider(self, value, index, label_widget):
        """Handles value changes from an objective function slider."""
        real_value = value / 10.0
        label_widget.setText(f"{real_value:.1f}")
        self.objective_fxn_table.setItem(0, index, QTableWidgetItem(str(real_value)))
        self.fast_solve_event()

    def create_objective_sliders(self):
        self.clear_objective_sliders()
        self.objective_sliders_container.show()
        
        box = QFrame()
        box.setStyleSheet("background-color: #F9F9F9; border-radius: 8px; padding: 10px;")
        l = QVBoxLayout(box)
        
        head = QLabel("Интерактивное изменение целевой функции (Cj)")
        head.setStyleSheet("font-weight: bold; color: #555; margin-bottom: 5px;")
        l.addWidget(head)

        num_vars = self.objective_fxn_table.columnCount() - 2
        
        for i in range(num_vars):
            item = self.objective_fxn_table.item(0, i)
            current_val = float(item.text()) if item and item.text().strip() else 10.0
            
            h_layout = QHBoxLayout()
            slider = QSlider(Qt.Horizontal)
            slider.setCursor(Qt.PointingHandCursor)
            val_label = QLabel(f"{current_val:.1f}")
            val_label.setFixedWidth(65)
            val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            slider.setRange(-200, 200)
            slider.setValue(int(current_val * 10))
            
            slider.valueChanged.connect(
                lambda val, idx=i, label=val_label: self.update_obj_from_slider(val, idx, label)
            )
            
            h_layout.addWidget(QLabel(f"Коэф. C{i+1} (X{i+1}):"))
            h_layout.addWidget(slider)
            h_layout.addWidget(val_label)
            l.addLayout(h_layout)

        self.objective_sliders_layout.addWidget(box)

    def add_iteration_table_to_layout(self, layout, i, data, headers):
        tbl_dict = data['table']
        pivot_r = data['pivot_row']
        pivot_c = data['pivot_col']
        
        lbl = QLabel(f"Итерация {i+1}")
        lbl.setProperty("class", "SubHeader")
        lbl.setStyleSheet("margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        row_keys = list(tbl_dict.keys())
        col_count = len(tbl_dict[row_keys[0]]) + 1
        if pivot_c is not None: col_count += 1
        
        table = QTableWidget(len(row_keys), col_count)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # === ВОТ ЗДЕСЬ УВЕЛИЧИВАЕМ ВЫСОТУ СТРОК ===
        table.verticalHeader().setDefaultSectionSize(40) # Сделаем строки чуть ниже
        table.verticalHeader().setVisible(False)
        # ==========================================
        
        h_l = ["Базис"] + headers
        if pivot_c is not None: h_l.append("Симпл. отношения")
        table.setHorizontalHeaderLabels(h_l)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Стилизация заголовка таблицы
        table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #FFFFFF;
                padding: 8px;
                border-bottom: 2px solid #E5E5EA;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        # Цвета подсветки
        hl_row = QColor("#E4EFFF") 
        hl_col = QColor("#FFF8E1") 
        hl_both = QColor("#FFE0B2") 
        
        for r_idx, key in enumerate(row_keys):
            # Базис (первая колонка)
            item_k = QTableWidgetItem(key)
            item_k.setTextAlignment(Qt.AlignCenter)
            item_k.setFont(QFont("SF Pro Text", 11, QFont.Bold)) # Жирный шрифт для базиса
            if r_idx == pivot_r: item_k.setBackground(hl_row)
            table.setItem(r_idx, 0, item_k)
            
            vals = tbl_dict[key]
            for c_idx, val in enumerate(vals):
                it = QTableWidgetItem(f"{val:.3f}")
                it.setTextAlignment(Qt.AlignCenter)
                is_r = (r_idx == pivot_r)
                is_c = (c_idx == pivot_c)
                if is_r and is_c: it.setBackground(hl_both)
                elif is_r: it.setBackground(hl_row)
                elif is_c: it.setBackground(hl_col)
                table.setItem(r_idx, c_idx+1, it)
                
            if pivot_c is not None:
                th_val = ""
                ratios = data['ratios']
                if r_idx > 0 and (r_idx-1) < len(ratios):
                    v = ratios[r_idx-1]
                    th_val = f"{v:.3f}" if v != float('inf') else "-"
                it_th = QTableWidgetItem(th_val)
                it_th.setTextAlignment(Qt.AlignCenter)
                if r_idx == pivot_r: it_th.setBackground(hl_row)
                table.setItem(r_idx, col_count-1, it_th)
                
        # --- УБРАЛИ ФИКСИРОВАННУЮ ВЫСОТУ ---
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        # Даем таблице возможность самой рассчитать свою высоту
        table.setMinimumHeight(table.horizontalHeader().height() + table.rowHeight(0) * table.rowCount())
        
        layout.addWidget(table)
        
        if pivot_c is not None:
            entering = data.get('entering', '')
            leaving = data.get('leaving', '')
            info_lbl = QLabel(f"➡ Входит в базис: <b>{entering}</b>, Выходит из базиса: <b>{leaving}</b>")
            info_lbl.setStyleSheet("color: #555; margin-bottom: 20px; font-size: 14px; background: #F9F9F9; padding: 8px; border-radius: 6px;")
            layout.addWidget(info_lbl)
            
    def setup_sensitivity_tab(self, parent_widget, var_data, constr_data):
        layout = QVBoxLayout(parent_widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        l_content = QVBoxLayout(content)
        l_content.setSpacing(20)
        l_content.setContentsMargins(10, 20, 10, 20)

        grid_cards = QGridLayout()
        grid_cards.setSpacing(15)
        
        # --- ФУНКЦИЯ ИСПРАВЛЕНИЯ ДИАПАЗОНОВ ---
        def get_range_str(base_val, dec, inc):
            # Обработка нижней границы
            # Если allow_decrease == inf, значит можно уменьшать до -бесконечности
            if dec == float('inf'):
                low_str = "-∞"
            else:
                # Иначе отнимаем от базы
                low_str = f"{(base_val - dec):.2f}"
            
            # Обработка верхней границы
            # Если allow_increase == inf, значит можно увеличивать до +бесконечности
            if inc == float('inf'):
                high_str = "+∞"
            else:
                # Иначе прибавляем к базе
                high_str = f"{(base_val + inc):.2f}"
            
            return f"[{low_str} ; {high_str}]"
        # ---------------------------------------

        # --- Колонка переменных ---
        lbl_v = QLabel("Анализ переменных (Коэффициенты ЦФ)")
        lbl_v.setStyleSheet("font-size: 16px; font-weight: bold; color: #007AFF; margin-bottom: 10px;")
        grid_cards.addWidget(lbl_v, 0, 0)
        
        for idx, item in enumerate(var_data):
            base_c = item['obj_coeff']
            range_str = get_range_str(base_c, item['allow_decrease'], item['allow_increase'])
            
            card = self.create_analysis_card(
                title=f"{item['name']}",
                main_val=f"Текущий коэф. Cj: <b>{base_c}</b>",
                sub_val=f"Финальное значение: {item['final_value']:.2f}",
                delta_low=item['allow_decrease'],
                delta_high=item['allow_increase'],
                abs_range=range_str,
                is_resource=False
            )
            grid_cards.addWidget(card, idx+1, 0)

        # --- Колонка ограничений ---
        lbl_c = QLabel("Анализ ограничений (Запасы ресурсов)")
        lbl_c.setStyleSheet("font-size: 16px; font-weight: bold; color: #34C759; margin-bottom: 10px;")
        grid_cards.addWidget(lbl_c, 0, 1)

        for idx, item in enumerate(constr_data):
            base_b = item['rhs']
            range_str = get_range_str(base_b, item['allow_decrease'], item['allow_increase'])

            card = self.create_analysis_card(
                title=f"{item['name']}",
                main_val=f"Текущий запас Bi: <b>{base_b}</b>",
                sub_val=f"Теневая цена: {item['shadow_price']:.2f}",
                delta_low=item['allow_decrease'],
                delta_high=item['allow_increase'],
                abs_range=range_str,
                is_resource=True
            )
            grid_cards.addWidget(card, idx+1, 1)
            
        grid_cards.setColumnStretch(0, 1)
        grid_cards.setColumnStretch(1, 1)
        
        l_content.addLayout(grid_cards)
        l_content.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def create_analysis_card(self, title, main_val, sub_val, delta_low, delta_high, abs_range, is_resource):
        """Создает карточку с данными анализа и диапазонами."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { 
                background-color: #FFFFFF; 
                border: 1px solid #D1D1D6; 
                border-radius: 12px; 
            }
        """)

        l = QVBoxLayout(frame)
        l.setSpacing(8)
        l.setContentsMargins(20, 15, 20, 15)
        
        # Заголовок
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-weight: bold; font-size: 16px; border: none; color: #1D1D1F;")
        l.addWidget(t_lbl)
        
        # Линия
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #F2F2F7; max-height: 1px; border: none;")
        l.addWidget(line)
        
        # Основные значения
        v_lbl = QLabel(main_val)
        v_lbl.setStyleSheet("color: #1D1D1F; font-size: 14px; border: none;")
        l.addWidget(v_lbl)
        
        s_lbl = QLabel(sub_val)
        s_lbl.setStyleSheet("color: #86868B; font-size: 13px; border: none;")
        l.addWidget(s_lbl)
        
        # Блок с диапазонами (цветной фон)
        range_frame = QFrame()
        color_bg = "#F0FFF4" if is_resource else "#F2F8FF" # Зеленый или Синий фон
        color_txt = "#248A3D" if is_resource else "#007AFF"
        
        range_frame.setStyleSheet(f"background-color: {color_bg}; border-radius: 8px; border: none;")
        rl = QVBoxLayout(range_frame)
        rl.setContentsMargins(10, 10, 10, 10)
        rl.setSpacing(4)
        
        # Форматирование дельт
        d_low = delta_low if isinstance(delta_low, str) else f"{delta_low:.2f}"
        d_high = delta_high if isinstance(delta_high, str) else f"{delta_high:.2f}"
        
        # Строка 1: Дельты
        lbl_delta = QLabel(f"Доп. изменение: [-{d_low} ; +{d_high}]")
        lbl_delta.setStyleSheet(f"color: {color_txt}; font-size: 12px; border: none;")
        
        # Строка 2: Абсолютный диапазон (Жирный)
        lbl_abs = QLabel(f"Интервал устойчивости: {abs_range}")
        lbl_abs.setStyleSheet(f"color: {color_txt}; font-weight: bold; font-size: 13px; border: none;")
        
        rl.addWidget(lbl_delta)
        rl.addWidget(lbl_abs)
        
        l.addWidget(range_frame)
        
        return frame

if __name__ == "__main__":
    # Настройка HiDPI для четкости на экранах Retina/4K
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())