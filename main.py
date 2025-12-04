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
    padding: 8px 20px; 
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
        # Основной лейаут
        self.main_layout = QVBoxLayout(self.container_widget)
        self.main_layout.setSpacing(24) # Больше воздуха между блоками
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        # 1. Блок Ввода данных (Карточка)
        self.input_card = Card()
        self.input_layout = QVBoxLayout(self.input_card)
        self.input_layout.setSpacing(15)
        self.input_layout.setContentsMargins(20, 20, 20, 20)
        
        self.create_input_ui()
        self.main_layout.addWidget(self.input_card)

        # 2. Блок Графика (Карточка)
        self.graph_container_card = Card()
        self.graph_layout = QVBoxLayout(self.graph_container_card)
        self.graph_layout.setContentsMargins(20, 20, 20, 20)
        self.graph_container_card.hide() # Скрыт пока нет решения
        self.main_layout.addWidget(self.graph_container_card)

        # 3. Блок Результатов (Карточка)
        self.results_card = Card()
        self.results_layout = QVBoxLayout(self.results_card)
        self.results_layout.setContentsMargins(20, 20, 20, 20)
        self.results_layout.setSpacing(15)
        self.results_card.hide()
        self.main_layout.addWidget(self.results_card)

        self.main_layout.addStretch()
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
        
        # --- СЛАЙДЕРЫ ДЛЯ ЦЕЛЕВОЙ ФУНКЦИИ ---
        self.objective_sliders_container = QWidget()
        self.objective_sliders_layout = QVBoxLayout(self.objective_sliders_container)
        self.objective_sliders_layout.setContentsMargins(0, 10, 0, 0)
        self.objective_sliders_container.hide() # Показываем только если 2 переменные
        self.input_layout.addWidget(self.objective_sliders_container)
        # ------------------------------------

        # Кнопка РЕШИТЬ
        self.solve_btn = QPushButton('Рассчитать оптимальное решение')
        self.solve_btn.setObjectName("PrimaryButton")
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        self.solve_btn.setFixedHeight(40)
        self.input_layout.addSpacing(10)
        self.input_layout.addWidget(self.solve_btn)

        # Signals
        self.add_row_btn.clicked.connect(self.add_row_event)
        self.add_col_btn.clicked.connect(self.add_column_event)
        self.del_row_btn.clicked.connect(self.del_row_event)
        self.del_col_btn.clicked.connect(self.del_col_event)
        self.solve_btn.clicked.connect(self.full_solve_event)

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

        # Обновляем слайдеры ЦФ при изменении числа переменных
        if self.objective_fxn_table.columnCount() - 2 == 2:
            self.create_objective_sliders()
        else:
            self.clear_objective_sliders()
    
    def del_col_event(self):
        if self.constraint_table.columnCount() > 4: # Min 2 vars + sign + val
            idx = self.constraint_table.columnCount()-3
            self.constraint_table.removeColumn(idx)
            self.objective_fxn_table.removeColumn(idx)

        # Обновляем слайдеры ЦФ при изменении числа переменных
        if self.objective_fxn_table.columnCount() - 2 == 2:
            self.create_objective_sliders()
        else:
            self.clear_objective_sliders()

    # --- Solve Logic ---
    def clear_ui_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        while self.graph_layout.count():
            item = self.graph_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        self.slider_widgets = []
        self.canvas_widget = None
        self.results_card.hide()
        self.graph_container_card.hide()

    def full_solve_event(self):
        try:
            self.clear_ui_results()
            
            raw_matrix, rhs, obj_coeffs = simplex_core.get_simplex_data(self.objective_fxn_table, self.constraint_table)
            num_vars = self.constraint_table.columnCount() - 2
            operation = self.operation_combo.currentText()
            
            final_z, history, opt_vars, err, headers = simplex_core.calculate_simplex(raw_matrix, operation, num_vars)
            
            if err:
                QMessageBox.warning(self, "Ошибка решения", err)
                return

            self.results_card.show()
            
            # --- 1. График (если 2 переменные) ---
            if num_vars == 2:
                self.graph_container_card.show()
                lbl = QLabel("Графическая интерпретация")
                lbl.setProperty("class", "Header")
                self.graph_layout.addWidget(lbl)
                
                self.canvas_widget = gui_utils.MplCanvas(self, width=6, height=5)
                tb = NavigationToolbar2QT(self.canvas_widget, self)
                tb.setStyleSheet("background-color: transparent; border: none;")
                self.graph_layout.addWidget(tb)
                self.graph_layout.addWidget(self.canvas_widget)
                constrs = gui_utils.plot_constraints(self.canvas_widget, self.constraint_table, opt_vars, obj_coeffs=obj_coeffs)
                self.create_sliders(constrs)
                self.create_objective_sliders() # Создаем слайдеры для ЦФ
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
            tabs.setMinimumHeight(800)
            tabs.setStyleSheet("""
                QTabWidget::pane { border: 1px solid #E5E5EA; border-radius: 8px; background: white; }
                QTabBar::tab { background: #F2F2F7; color: #86868B; padding: 8px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
                QTabBar::tab:selected { background: #FFFFFF; color: #007AFF; font-weight: bold; border-bottom: 2px solid #007AFF; }
            """)
            
            # --- Вкладка 1: Пошаговое решение ---
            tab_steps = QWidget()
            layout_steps = QVBoxLayout(tab_steps)
            layout_steps.setSpacing(15)
            
            # Scroll area внутри таба для шагов, если их много
            scroll_steps = QScrollArea()
            scroll_steps.setWidgetResizable(True)
            scroll_steps.setFrameShape(QFrame.NoFrame)
            content_steps = QWidget()
            l_s = QVBoxLayout(content_steps)
            
            for i, step in enumerate(history):
                self.add_iteration_table_to_layout(l_s, i, step, headers)
            l_s.addStretch()
            
            scroll_steps.setWidget(content_steps)
            layout_steps.addWidget(scroll_steps)
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
        if pivot_c is not None: h_l.append("Тета")
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
        
    def create_objective_sliders(self):
        self.clear_objective_sliders()
        self.objective_sliders_container.show()
        
        box = QFrame()
        box.setStyleSheet("background-color: #F9F9F9; border-radius: 8px; padding: 10px;")
        l = QVBoxLayout(box)
        
        head = QLabel("Интерактивное изменение целевой функции (Cj)")
        head.setStyleSheet("font-weight: bold; color: #555; margin-bottom: 5px;")
        l.addWidget(head)

        # Получаем текущие значения из таблицы, если они есть
        c1_item = self.objective_fxn_table.item(0, 0)
        c2_item = self.objective_fxn_table.item(0, 1)
        c1_val = float(c1_item.text()) if c1_item and c1_item.text().strip() else 10.0
        c2_val = float(c2_item.text()) if c2_item and c2_item.text().strip() else 10.0
        
        # Слайдер для X1
        h1 = QHBoxLayout()
        sl1 = QSlider(Qt.Horizontal)
        lbl1_val = QLabel(f"{c1_val:.1f}")
        sl1.setRange(-200, 200); sl1.setValue(int(c1_val * 10))
        
        def change_c1(v):
            real_v = v / 10.0
            lbl1_val.setText(f"{real_v:.1f}")
            self.objective_fxn_table.setItem(0, 0, QTableWidgetItem(str(real_v)))
            self.fast_solve_event()
        
        sl1.valueChanged.connect(change_c1)
        h1.addWidget(QLabel("Коэф. C1 (X1):")); h1.addWidget(sl1); h1.addWidget(lbl1_val)
        l.addLayout(h1)

        # Слайдер для X2
        h2 = QHBoxLayout()
        sl2 = QSlider(Qt.Horizontal)
        lbl2_val = QLabel(f"{c2_val:.1f}")
        sl2.setRange(-200, 200); sl2.setValue(int(c2_val * 10))

        def change_c2(v):
            real_v = v / 10.0
            lbl2_val.setText(f"{real_v:.1f}")
            self.objective_fxn_table.setItem(0, 1, QTableWidgetItem(str(real_v)))
            self.fast_solve_event()

        sl2.valueChanged.connect(change_c2)
        h2.addWidget(QLabel("Коэф. C2 (X2):")); h2.addWidget(sl2); h2.addWidget(lbl2_val)
        l.addLayout(h2)

        self.objective_sliders_layout.addWidget(box)
    
    def clear_objective_sliders(self):
        while self.objective_sliders_layout.count():
            item = self.objective_sliders_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.objective_sliders_container.hide()
    
    def add_iteration_table_to_layout(self, layout, i, data, headers):
        tbl_dict = data['table']
        pivot_r = data['pivot_row']
        pivot_c = data['pivot_col']
        
        lbl = QLabel(f"Итерация {i}")
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
        table.verticalHeader().setDefaultSectionSize(50) 
        # ==========================================
        
        h_l = ["Базис"] + headers
        if pivot_c is not None: h_l.append("Тета")
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
                
        table.verticalHeader().setVisible(False)
        
        # Пересчитываем высоту таблицы с учетом новых высоких строк
        h = table.horizontalHeader().height() + (50 * table.rowCount()) + 4
        table.setMinimumHeight(h)
        table.setMaximumHeight(h)
        
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