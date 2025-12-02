import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QVBoxLayout, QLabel, 
                             QComboBox, QPushButton, QHBoxLayout, QSizePolicy, 
                             QScrollArea, QFrame, QSlider, QHeaderView, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

# Импорт наших модулей
import simplex_core
import gui_utils

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Simplex Solver Pro (Rus)")
        
        self.app_font = QFont("Arial", 11)
        self.setFont(self.app_font)
        self.CONSTRAINT_EQUALITY_SIGNS = [u"\u2264", u"\u2265", "="]
        
        self.slider_widgets = []
        self.canvas_widget = None
        self.toolbar_widget = None

        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setFrameShape(QFrame.NoFrame)

        self.container_widget = QWidget()
        self.main_layout = QVBoxLayout(self.container_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.create_ui()
        self.main_scroll.setWidget(self.container_widget)
        self.setCentralWidget(self.main_scroll)
        self.resize(1200, 950)

    def create_ui(self):
        # Панель управления
        self.add_row_btn = QPushButton('Добавить ограничение')
        self.add_col_btn = QPushButton('Добавить переменную')
        self.del_row_btn = QPushButton('Удалить ограничение')
        self.del_col_btn = QPushButton('Удалить переменную')
        
        self.solve_btn = QPushButton('РЕШИТЬ ЗАДАЧУ')
        self.solve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        
        self.add_row_btn.clicked.connect(self.add_row_event)
        self.add_col_btn.clicked.connect(self.add_column_event)
        self.del_row_btn.clicked.connect(self.del_row_event)
        self.del_col_btn.clicked.connect(self.del_col_event)
        self.solve_btn.clicked.connect(self.full_solve_event)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_row_btn); btn_layout.addWidget(self.add_col_btn)
        btn_layout.addWidget(self.del_row_btn); btn_layout.addWidget(self.del_col_btn)

        # Таблицы
        self.constraints_label = QLabel("1. Система ограничений:")
        self.constraints_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.constraint_table = self.create_table(2, 4, self.CONSTRAINT_EQUALITY_SIGNS, self.create_header_labels(2))

        obj_layout = QHBoxLayout()
        self.obj_label = QLabel("2. Целевая функция (E):")
        self.obj_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Максимизация", "Минимизация"])
        self.operation_combo.currentIndexChanged.connect(lambda: self.fast_solve_event() if self.canvas_widget else None)
        obj_layout.addWidget(self.obj_label); obj_layout.addWidget(self.operation_combo); obj_layout.addStretch()

        self.objective_fxn_table = self.create_table(1, 4, ["="], self.create_header_labels(2))
        self.objective_fxn_table.setItem(0, 3, QTableWidgetItem("E"))
        self.objective_fxn_table.item(0, 3).setFlags(Qt.ItemIsEnabled)
        self.objective_fxn_table.item(0, 3).setTextAlignment(Qt.AlignCenter)

        # Сборка
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.constraints_label)
        self.main_layout.addWidget(self.constraint_table)
        self.main_layout.addLayout(obj_layout)
        self.main_layout.addWidget(self.objective_fxn_table)
        self.main_layout.addWidget(self.solve_btn)
        
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        self.main_layout.addWidget(sep)

        # Контейнер для графика
        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)
        self.main_layout.addWidget(self.graph_container)

        # Результаты
        self.results_label = QLabel("Ход решения:")
        self.results_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.results_label.hide()
        self.main_layout.addWidget(self.results_label)
        
        self.results_layout = QVBoxLayout()
        self.main_layout.addLayout(self.results_layout)
        self.main_layout.addStretch()

    # --- Table Methods ---
    def create_table(self, rows, cols, signs=None, h_headers=None):
        table = QTableWidget(self)
        table.setColumnCount(cols); table.setRowCount(rows)
        table.setFont(self.app_font)
        table.horizontalHeader().setMinimumSectionSize(100)
        
        if h_headers: table.setHorizontalHeaderLabels(h_headers)
        if signs:
            for i in range(rows): self.set_combo_box(table, i, signs)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.adjust_table_height(table)
        return table

    def set_combo_box(self, table, row, options):
        combo = QComboBox()
        combo.setFont(self.app_font)
        combo.addItems(options)
        combo.currentIndexChanged.connect(lambda: self.fast_solve_event() if self.canvas_widget else None)
        table.setCellWidget(row, table.columnCount() - 2, combo)

    def adjust_table_height(self, table):
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        for i in range(table.columnCount()):
            if table.columnWidth(i) < 100: table.setColumnWidth(i, 100)
        h = table.horizontalHeader().height() + sum([table.rowHeight(i) for i in range(table.rowCount())]) + 6
        table.setMinimumHeight(h); table.setMaximumHeight(h)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def create_header_labels(self, n):
        return [f" X{i+1} " for i in range(n)] + [" ", " bi "]

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
        self.constraint_table.insertColumn(self.constraint_table.columnCount()-2)
        self.objective_fxn_table.insertColumn(self.objective_fxn_table.columnCount()-2)
        h = self.create_header_labels(self.constraint_table.columnCount()-2)
        self.constraint_table.setHorizontalHeaderLabels(h)
        self.objective_fxn_table.setHorizontalHeaderLabels(h)
        self.adjust_table_height(self.constraint_table)
        self.adjust_table_height(self.objective_fxn_table)

    def del_col_event(self):
        if self.constraint_table.columnCount() > 4:
            self.constraint_table.removeColumn(self.constraint_table.columnCount()-3)
            self.objective_fxn_table.removeColumn(self.objective_fxn_table.columnCount()-3)
            self.adjust_table_height(self.constraint_table)
            self.adjust_table_height(self.objective_fxn_table)

    # --- Solve Logic ---
    def clear_ui_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        while self.graph_layout.count():
            item = self.graph_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.slider_widgets = []; self.canvas_widget = None

    def full_solve_event(self):
        try:
            self.clear_ui_results()
            self.results_label.show()
            
            raw_matrix, rhs, obj_coeffs = simplex_core.get_simplex_data(self.objective_fxn_table, self.constraint_table)
            
            num_vars = self.constraint_table.columnCount() - 2
            operation = self.operation_combo.currentText()
            
            final_z, history, opt_vars, err, headers = simplex_core.calculate_simplex(raw_matrix, operation, num_vars)
            
            if err:
                QMessageBox.warning(self, "Ошибка решения", err)
                return

            # График
            if num_vars == 2:
                lbl = QLabel("Графическая интерпретация (X1, X2):")
                lbl.setFont(QFont("Arial", 12, QFont.Bold))
                self.graph_layout.addWidget(lbl)
                
                self.canvas_widget = gui_utils.MplCanvas(self, width=6, height=5)
                tb = NavigationToolbar2QT(self.canvas_widget, self)
                self.graph_layout.addWidget(tb)
                self.graph_layout.addWidget(self.canvas_widget)
                
                constrs = gui_utils.plot_constraints(self.canvas_widget, self.constraint_table, opt_vars)
                self.create_sliders(constrs)

            # Итерации
            for i, step in enumerate(history):
                self.add_iteration_table(i, step, headers)

            # Финал
            self.add_final_result(history[-1]['table'], final_z)
            
            # Чувствительность
            is_max = (operation == "Максимизация")
            var_an, constr_an, detail_report = simplex_core.perform_sensitivity_analysis(
                history[-1]['table'], rhs, obj_coeffs, num_vars, self.constraint_table.rowCount(), is_max
            )
            self.add_sensitivity_report(var_an, constr_an, detail_report)
            
            self.main_scroll.verticalScrollBar().setValue(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Произошел сбой: {str(e)}")

    def fast_solve_event(self):
        if not self.canvas_widget: return
        try:
            raw_matrix, _, _ = simplex_core.get_simplex_data(self.objective_fxn_table, self.constraint_table)
            num_vars = self.constraint_table.columnCount() - 2
            op = self.operation_combo.currentText()
            _, _, opt_vars, err, _ = simplex_core.calculate_simplex(raw_matrix, op, num_vars)
            if not err:
                gui_utils.plot_constraints(self.canvas_widget, self.constraint_table, opt_vars)
        except:
            pass

    # --- UI Helpers ---
    def add_iteration_table(self, i, data, headers):
        tbl_dict = data['table']
        pivot_r = data['pivot_row']
        pivot_c = data['pivot_col']
        
        lbl = QLabel(f"Итерация {i}")
        lbl.setFont(QFont("Arial", 12, QFont.Bold))
        self.results_layout.addWidget(lbl)
        
        row_keys = list(tbl_dict.keys())
        col_count = len(tbl_dict[row_keys[0]]) + 1
        if pivot_c is not None: col_count += 1
        
        table = QTableWidget(len(row_keys), col_count)
        table.setFont(self.app_font)
        table.horizontalHeader().setMinimumSectionSize(80)
        
        h_l = ["Базис"] + headers
        if pivot_c is not None: h_l.append("Тета")
        table.setHorizontalHeaderLabels(h_l)
        
        hl_row = QColor(200, 255, 200)
        hl_col = QColor(255, 255, 200)
        hl_both = QColor(255, 165, 0, 150)
        
        for r_idx, key in enumerate(row_keys):
            item_k = QTableWidgetItem(key)
            if r_idx == pivot_r: item_k.setBackground(hl_row)
            table.setItem(r_idx, 0, item_k)
            
            vals = tbl_dict[key]
            for c_idx, val in enumerate(vals):
                it = QTableWidgetItem(f"{val:.3f}")
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
                if r_idx == pivot_r: it_th.setBackground(hl_row)
                table.setItem(r_idx, col_count-1, it_th)
                
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.adjust_table_height(table)
        self.results_layout.addWidget(table)
        
        if pivot_c is not None:
            entering = data.get('entering', '')
            leaving = data.get('leaving', '')
            info_lbl = QLabel(f"➡ Входит: {entering}, Выходит: {leaving}")
            info_lbl.setStyleSheet("color: #555; margin-bottom: 10px;")
            self.results_layout.addWidget(info_lbl)

    def add_final_result(self, data, z):
        fr = QFrame(); fr.setStyleSheet("background-color: #e8f5e9; padding: 10px; border-radius: 5px;")
        l = QVBoxLayout(fr)
        l.addWidget(QLabel(f"Оптимальное решение E = {z:.4f}"))
        self.results_layout.addWidget(fr)

    def add_sensitivity_report(self, var_data, constr_data, detail_text):
        lbl = QLabel("Анализ на чувствительность:")
        lbl.setFont(QFont("Arial", 14, QFont.Bold))
        self.results_layout.addWidget(lbl)
        
        # Таблица переменных
        v_headers = ["Переменная", "Значение", "Редуц. стоимость", "Коэф. ЦФ", "Доп. увелич.", "Доп. уменьш."]
        t_v = QTableWidget(len(var_data), 6)
        t_v.setFont(self.app_font)
        t_v.setHorizontalHeaderLabels(v_headers)
        t_v.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t_v.horizontalHeader().setMinimumSectionSize(100)
        
        for i, d in enumerate(var_data):
            t_v.setItem(i, 0, QTableWidgetItem(d['name']))
            t_v.setItem(i, 1, QTableWidgetItem(f"{d['final_value']:.4f}"))
            t_v.setItem(i, 2, QTableWidgetItem(f"{d['reduced_cost']:.4f}"))
            t_v.setItem(i, 3, QTableWidgetItem(f"{d['obj_coeff']:.4f}"))
            t_v.setItem(i, 4, QTableWidgetItem(str(d['allow_increase'])))
            t_v.setItem(i, 5, QTableWidgetItem(str(d['allow_decrease'])))
            
        t_v.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        t_v.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.adjust_table_height(t_v)
        self.results_layout.addWidget(t_v)
        
        # Таблица ограничений
        c_headers = ["Ограничение", "Теневая цена", "RHS", "Доп. увелич.", "Доп. уменьш."]
        t_c = QTableWidget(len(constr_data), 5)
        t_c.setFont(self.app_font)
        t_c.setHorizontalHeaderLabels(c_headers)
        t_c.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t_c.horizontalHeader().setMinimumSectionSize(100)
        
        for i, d in enumerate(constr_data):
            t_c.setItem(i, 0, QTableWidgetItem(d['name']))
            t_c.setItem(i, 1, QTableWidgetItem(f"{d['shadow_price']:.4f}"))
            t_c.setItem(i, 2, QTableWidgetItem(f"{d['rhs']:.4f}"))
            t_c.setItem(i, 3, QTableWidgetItem(str(d['allow_increase'])))
            t_c.setItem(i, 4, QTableWidgetItem(str(d['allow_decrease'])))
            
        t_c.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        t_c.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.adjust_table_height(t_c)
        self.results_layout.addWidget(t_c)

        # Текстовый отчет с неравенствами
        lbl_det = QLabel("Подробный расчет (с параметром D):")
        lbl_det.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_det.setStyleSheet("margin-top: 15px;")
        self.results_layout.addWidget(lbl_det)
        
        # ИСПОЛЬЗУЕМ QLabel ВМЕСТО QTextEdit
        # QLabel автоматически растягивается на весь текст
        report_label = QLabel(detail_text)
        report_label.setFont(QFont("Consolas", 10)) # Моноширинный шрифт для выравнивания
        report_label.setWordWrap(True) # Перенос строк если текст слишком широкий
        report_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # Разрешить выделение и копирование текста
        
        # Белый фон и рамка для красоты
        report_label.setStyleSheet("""
            QLabel {
                background-color: white; 
                border: 1px solid #ccc; 
                padding: 10px;
            }
        """)
        
        self.results_layout.addWidget(report_label)

    def create_sliders(self, constraints):
        box = QFrame(); l = QVBoxLayout(box)
        l.addWidget(QLabel("Интерактивное изменение ограничений:"))
        
        for i, c in enumerate(constraints):
            h = QHBoxLayout()
            sl = QSlider(Qt.Horizontal)
            val = c['c']; sl.setRange(0, int(max(val*2, 20)*10)); sl.setValue(int(val*10))
            
            lbl_val = QLabel(f"{val:.1f}")
            
            def change(v, idx=i, lb=lbl_val):
                real = v/10.0
                lb.setText(f"{real:.1f}")
                self.constraint_table.item(idx, self.constraint_table.columnCount()-1).setText(str(real))
                self.fast_solve_event()
                
            sl.valueChanged.connect(change)
            h.addWidget(QLabel(f"Огр {i+1}")); h.addWidget(sl); h.addWidget(lbl_val)
            l.addLayout(h)
            self.slider_widgets.append(sl)
            
        self.graph_layout.addWidget(box)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())