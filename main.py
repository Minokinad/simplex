import sys
import numpy as np
import math
import copy

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QVBoxLayout, QLabel, 
                             QComboBox, QPushButton, QHBoxLayout, QSizePolicy, 
                             QScrollArea, QFrame, QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

# --- Matplotlib Integration ---
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon

HEADER_SPACE = 10

# --- КЛАСС ДЛЯ ГРАФИКА ---
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # Убираем лишние отступы
        self.fig.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.90)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.updateGeometry()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Simplex Solver (Интерактивный)")
        
        self.app_font = QFont("Arial", 11)
        self.setFont(self.app_font)
        
        self.CONSTRAINT_EQUALITY_SIGNS = [u"\u2264", u"\u2265", "="]
        
        # Хранилище для виджетов слайдеров
        self.slider_widgets = []
        self.canvas_widget = None
        self.toolbar_widget = None

        # Главный скролл
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

        self.resize(1100, 950)

    def create_ui(self):
        # -- Кнопки управления --
        self.add_row_btn = QPushButton('Добавить ограничение')
        self.add_col_btn = QPushButton('Добавить переменную')
        self.del_row_btn = QPushButton('Удалить ограничение')
        self.del_col_btn = QPushButton('Удалить переменную')
        
        self.solve_btn = QPushButton('РЕШИТЬ ЗАДАЧУ')
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; 
                padding: 10px; border-radius: 5px; font-size: 14px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        self.add_row_btn.clicked.connect(self.add_row_event)
        self.add_col_btn.clicked.connect(self.add_column_event)
        self.del_row_btn.clicked.connect(self.del_row_event)
        self.del_col_btn.clicked.connect(self.del_col_event)
        self.solve_btn.clicked.connect(self.full_solve_event) # Полное решение

        btn_layout_top = QHBoxLayout()
        btn_layout_top.addWidget(self.add_row_btn)
        btn_layout_top.addWidget(self.add_col_btn)
        btn_layout_top.addWidget(self.del_row_btn)
        btn_layout_top.addWidget(self.del_col_btn)

        # -- Таблицы --
        self.constraints_label = QLabel("1. Система ограничений:")
        self.constraints_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.constraint_table = self.create_table(2, 4, self.CONSTRAINT_EQUALITY_SIGNS, self.create_header_labels(2))

        obj_header_layout = QHBoxLayout()
        self.obj_label_text = QLabel("2. Целевая функция (E):")
        self.obj_label_text.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Maximize", "Minimize"])
        self.operation_combo.setFont(QFont("Arial", 10, QFont.Bold))
        self.operation_combo.setFixedWidth(120)
        # При смене режима тоже пересчитываем, если график уже есть
        self.operation_combo.currentIndexChanged.connect(lambda: self.fast_solve_event() if self.canvas_widget else None)
        
        obj_header_layout.addWidget(self.obj_label_text)
        obj_header_layout.addWidget(self.operation_combo)
        obj_header_layout.addStretch()

        self.objective_fxn_table = self.create_table(1, 4, ["="], self.create_header_labels(2))
        self.objective_fxn_table.setItem(0, 3, QTableWidgetItem("E"))
        self.objective_fxn_table.item(0,3).setFlags(Qt.ItemIsEnabled)
        self.objective_fxn_table.item(0,3).setTextAlignment(Qt.AlignCenter)

        # -- Сборка Layout --
        self.main_layout.addLayout(btn_layout_top)
        self.main_layout.addSpacing(15)
        self.main_layout.addWidget(self.constraints_label)
        self.main_layout.addWidget(self.constraint_table)
        self.main_layout.addSpacing(15)
        self.main_layout.addLayout(obj_header_layout)
        self.main_layout.addWidget(self.objective_fxn_table)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.solve_btn)

        self.sep_line = QFrame()
        self.sep_line.setFrameShape(QFrame.HLine)
        self.sep_line.setFrameShadow(QFrame.Sunken)
        self.main_layout.addSpacing(20)
        self.main_layout.addWidget(self.sep_line)

        # Контейнер для графика и слайдеров
        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)
        self.graph_layout.setContentsMargins(0,0,0,0)
        self.main_layout.addWidget(self.graph_container)

        # Блок текстовых результатов
        self.results_label = QLabel("Ход решения:")
        self.results_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.results_label.hide()
        self.main_layout.addWidget(self.results_label)
        
        self.results_layout = QVBoxLayout()
        self.main_layout.addLayout(self.results_layout)
        self.main_layout.addStretch()

    # --- ТАБЛИЦЫ ---
    def create_table(self, rows, cols, equality_signs=None, horizontal_headers=None, vertical_headers=None):
        table = QTableWidget(self)
        table.setColumnCount(cols)
        table.setRowCount(rows)
        table.setFont(self.app_font)
        if horizontal_headers: table.setHorizontalHeaderLabels(horizontal_headers)
        if vertical_headers: table.setVerticalHeaderLabels(vertical_headers)
        if equality_signs:
            for index in range(table.rowCount()):
                self.set_combo_box(table, index, equality_signs)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.adjust_table_height(table)
        return table

    def set_combo_box(self, table, row, options):
        combo = QComboBox()
        combo.setFont(self.app_font)
        combo.addItems(options)
        # При смене знака тоже пересчитываем график
        combo.currentIndexChanged.connect(lambda: self.fast_solve_event() if self.canvas_widget else None)
        table.setCellWidget(row, table.columnCount() - 2, combo)

    def adjust_table_height(self, table):
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        h = table.horizontalHeader().height() + sum([table.rowHeight(i) for i in range(table.rowCount())]) + 6
        if table.horizontalScrollBar().isVisible(): h += table.horizontalScrollBar().height()
        table.setMinimumHeight(h)
        table.setMaximumHeight(h)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def create_header_labels(self, num_vars):
        labels = [f" X{i+1} " for i in range(num_vars)]
        labels.extend([" ", " bi "])
        return labels

    def add_row_event(self):
        self.constraint_table.insertRow(self.constraint_table.rowCount())
        self.set_combo_box(self.constraint_table, self.constraint_table.rowCount()-1, self.CONSTRAINT_EQUALITY_SIGNS)
        self.adjust_table_height(self.constraint_table)

    def del_row_event(self):
        if self.constraint_table.rowCount() > 1:
            self.constraint_table.removeRow(self.constraint_table.rowCount() - 1)
            self.adjust_table_height(self.constraint_table)

    def add_column_event(self):
        self.constraint_table.insertColumn(self.constraint_table.columnCount() - 2)
        self.objective_fxn_table.insertColumn(self.objective_fxn_table.columnCount() - 2)
        new_headers = self.create_header_labels(self.constraint_table.columnCount() - 2)
        self.constraint_table.setHorizontalHeaderLabels(new_headers)
        self.objective_fxn_table.setHorizontalHeaderLabels(new_headers)
        self.adjust_table_height(self.constraint_table)
        self.adjust_table_height(self.objective_fxn_table)

    def del_col_event(self):
        if self.constraint_table.columnCount() > 4:
            self.constraint_table.removeColumn(self.constraint_table.columnCount() - 3)
            self.objective_fxn_table.removeColumn(self.objective_fxn_table.columnCount() - 3)
            self.adjust_table_height(self.constraint_table)
            self.adjust_table_height(self.objective_fxn_table)

    def read_table_items(self, table, start_row, end_row, start_col, end_col):
        data = np.zeros((end_row - start_row, end_col - start_col))
        for i in range(start_row, end_row):
            for j in range(start_col, end_col):
                item = table.item(i, j)
                text = item.text() if item else ""
                try:
                    data[i - end_row][j - end_col] = float(text) if text.strip() else 0.0
                except ValueError:
                    data[i - end_row][j - end_col] = 0.0
        return data

    def get_data(self):
        obj = self.read_table_items(self.objective_fxn_table, 0, 1, 0, self.objective_fxn_table.columnCount() - 2)
        obj = np.insert(obj, 0, 0)
        rhs = self.read_table_items(self.constraint_table, 0, self.constraint_table.rowCount(),
                                    self.constraint_table.columnCount() - 1, self.constraint_table.columnCount())
        coeffs = self.read_table_items(self.constraint_table, 0, self.constraint_table.rowCount(), 
                                       0, self.constraint_table.columnCount() - 2)
        matrix_body = np.concatenate((rhs, coeffs), axis=1)
        full_matrix = np.vstack((obj, matrix_body))
        return full_matrix

    # --- ЛОГИКА ОТОБРАЖЕНИЯ РЕЗУЛЬТАТОВ ---
    def clear_results_layout(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.results_label.show()

    def clear_graph_layout(self):
        # Удаляем график и слайдеры
        while self.graph_layout.count():
            item = self.graph_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.slider_widgets = []
        self.canvas_widget = None
        self.toolbar_widget = None

    def add_iteration_table(self, iter_num, data, headers):
        lbl = QLabel(f"Итерация {iter_num}")
        lbl.setFont(QFont("Arial", 12, QFont.Bold))
        lbl.setStyleSheet("margin-top: 15px; color: #333;")
        self.results_layout.addWidget(lbl)
        
        row_keys = list(data.keys())
        table = QTableWidget(len(row_keys), len(data[row_keys[0]]) + 1)
        table.setFont(self.app_font)
        table.setHorizontalHeaderLabels(["Базис"] + headers)
        
        for i, key in enumerate(row_keys):
            item_k = QTableWidgetItem(key)
            item_k.setBackground(QColor("#f0f0f0"))
            table.setItem(i, 0, item_k)
            for j, val in enumerate(data[key]):
                table.setItem(i, j+1, QTableWidgetItem(f"{val:.3f}"))
        
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.adjust_table_height(table)
        self.results_layout.addWidget(table)

    def add_final_result_widget(self, last_data, final_z):
        frame = QFrame()
        frame.setStyleSheet("background-color: #e8f5e9; border: 1px solid #4CAF50; border-radius: 5px; margin-top: 20px;")
        l = QVBoxLayout(frame)
        
        lbl_res = QLabel("ОПТИМАЛЬНОЕ РЕШЕНИЕ:")
        lbl_res.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_res.setStyleSheet("border: none; color: #2E7D32;")
        l.addWidget(lbl_res)

        lbl_z = QLabel(f"E = {final_z:.4f}")
        lbl_z.setFont(QFont("Arial", 12))
        lbl_z.setStyleSheet("border: none;")
        l.addWidget(lbl_z)
        
        vars_res = {}
        for k, v in last_data.items():
            if k != 'E': vars_res[k] = v[-1]
        
        sorted_keys = sorted(vars_res.keys(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
        vars_str = " | ".join([f"{k} = {vars_res[k]:.4f}" for k in sorted_keys])
        
        lbl_vars = QLabel(vars_str)
        lbl_vars.setFont(self.app_font)
        lbl_vars.setStyleSheet("border: none;")
        l.addWidget(lbl_vars)
        
        self.results_layout.addWidget(frame)

    # --- СЛАЙДЕРЫ ДЛЯ ЛИНИЙ ---
    def create_sliders(self, constraints):
        # Очистка старых слайдеров из списка (виджеты уже удалены в clear_graph_layout)
        self.slider_widgets = []
        
        sliders_box = QFrame()
        sliders_box.setFrameShape(QFrame.StyledPanel)
        sliders_box.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; margin-top: 10px; padding: 10px;")
        l = QVBoxLayout(sliders_box)
        
        header = QLabel("Интерактивное изменение ограничений (двигать линии):")
        header.setFont(QFont("Arial", 10, QFont.Bold))
        l.addWidget(header)

        for i, const in enumerate(constraints):
            row_layout = QHBoxLayout()
            
            # Label: 2X1 + 3X2 <=
            lbl_eq = QLabel(f"Огр. {i+1}:  {const['a']} X1 + {const['b']} X2 {const['sign']} ")
            lbl_eq.setFixedWidth(150)
            
            # Slider
            slider = QSlider(Qt.Horizontal)
            current_bi = const['c']
            
            # Настройка диапазона слайдера. 
            # Пусть диапазон будет от 0 до current*2 (или до 100 если 0)
            max_range = int(max(current_bi * 2, 20))
            slider.setRange(0, max_range * 10) # Умножаем на 10 для точности 0.1
            slider.setValue(int(current_bi * 10))
            
            # Label для текущего значения
            lbl_val = QLabel(f"{current_bi:.1f}")
            lbl_val.setFixedWidth(50)
            
            # Привязка события
            # Используем замыкание (closure) с index=i
            def val_changed(val, idx=i, label=lbl_val):
                real_val = val / 10.0
                label.setText(f"{real_val:.1f}")
                # Обновляем таблицу (но не вызываем полный solve_event от таблицы!)
                # Блокируем сигналы таблицы, чтобы не было рекурсии если бы там были эвенты
                self.constraint_table.blockSignals(True)
                self.constraint_table.item(idx, self.constraint_table.columnCount()-1).setText(str(real_val))
                self.constraint_table.blockSignals(False)
                # Быстрый пересчет
                self.fast_solve_event()

            slider.valueChanged.connect(val_changed)
            
            row_layout.addWidget(lbl_eq)
            row_layout.addWidget(slider)
            row_layout.addWidget(lbl_val)
            l.addLayout(row_layout)
            
            self.slider_widgets.append(slider)

        self.graph_layout.addWidget(sliders_box)

    # --- МАТЕМАТИКА SIMPLEX ---
    def calculate_simplex(self):
        # Общая функция расчета, возвращает (final_z, history, optimal_vars, error_msg)
        try:
            raw_matrix = self.get_data()
            tab = np.flip(raw_matrix).tolist()
            rows = len(tab)
            l, soln = [], []
            for r in tab:
                soln.append(r[-1])
                l.append(r[:-1])

            art = np.identity(rows - 1).tolist()[::-1]
            zeros = np.zeros(rows - 1).tolist()
            
            weird = []
            for i in range(rows):
                if i == rows - 1:
                    row = l[i][::-1] + zeros + [0]
                else:
                    row = l[i][::-1] + art[i] + [soln[i]]
                weird.append(row)
            
            weird = weird[::-1]
            weird[0] = [-1 * x for x in weird[0]]
            
            opr = self.operation_combo.currentText()
            num_vars = self.constraint_table.columnCount() - 2
            x_vars = [f'X{i+1}' for i in range(num_vars)]
            num_slack = rows - 1
            s_vars = [f'X{num_vars + i + 1}' for i in range(num_slack)]
            headers = x_vars + s_vars + ['Solution']
            l4 = x_vars + s_vars
            
            current_dic = {}
            basis = ['E'] + s_vars
            for i, row in enumerate(weird):
                current_dic[basis[i]] = row

            history = [copy.deepcopy(current_dic)]
            is_min = (opr == 'Minimize')
            max_iter = 50
            counter = 0
            curr_list = weird
            curr_dic_algo = current_dic
            
            import copy
            curr_list = copy.deepcopy(curr_list)

            while counter < max_iter:
                z_row = curr_list[0][:-1]
                if is_min:
                    if max(z_row) <= 1e-9: break
                else:
                    if min(z_row) >= -1e-9: break
                
                limit = max(z_row) if is_min else min(z_row)
                pivot_col = z_row.index(limit)
                
                ratios = []
                last_col = len(curr_list[0]) - 1
                for r in curr_list:
                    val = r[pivot_col]
                    rhs = r[last_col]
                    if val > 1e-9: ratios.append(rhs / val)
                    else: ratios.append(float('inf'))
                
                min_r = min(ratios[1:])
                if min_r == float('inf'):
                    return None, None, None, "Unbounded"
                
                pivot_row_idx = ratios.index(min_r)
                pivot_val = curr_list[pivot_row_idx][pivot_col]
                new_pivot_row = [x / pivot_val for x in curr_list[pivot_row_idx]]
                
                new_table = []
                for i in range(len(curr_list)):
                    if i == pivot_row_idx:
                        new_table.append(new_pivot_row)
                    else:
                        factor = curr_list[i][pivot_col]
                        row = [curr_list[i][k] - factor * new_pivot_row[k] for k in range(len(new_pivot_row))]
                        new_table.append(row)
                
                new_dic = {}
                old_keys = list(curr_dic_algo.keys())
                entering_var = l4[pivot_col]
                
                for i in range(len(new_table)):
                    if i == pivot_row_idx: new_dic[entering_var] = new_table[i]
                    else: new_dic[old_keys[i]] = new_table[i]
                
                curr_dic_algo = new_dic
                curr_list = list(curr_dic_algo.values())
                history.append(curr_dic_algo)
                counter += 1
                
            final_z = list(history[-1].values())[0][-1]
            final_vars = {}
            for k, v in history[-1].items():
                if k != 'E': final_vars[k] = v[-1]
                
            return final_z, history, final_vars, None, headers

        except Exception as e:
            return None, None, None, str(e), None

    # --- ГРАФИКА (ПОСТРОЕНИЕ) ---
    def plot_graph_on_canvas(self, canvas, optimal_vars):
        ax = canvas.axes
        ax.clear()
        
        try:
            rows = self.constraint_table.rowCount()
            cols = self.constraint_table.columnCount()
            constraints = []
            for i in range(rows):
                a = float(self.constraint_table.item(i, 0).text() or 0)
                b = float(self.constraint_table.item(i, 1).text() or 0)
                sign = self.constraint_table.cellWidget(i, cols - 2).currentText()
                c = float(self.constraint_table.item(i, cols - 1).text() or 0)
                constraints.append({'a': a, 'b': b, 'sign': sign, 'c': c})

            lines = []
            for const in constraints:
                lines.append((const['a'], const['b'], const['c']))
            lines.append((1, 0, 0)); lines.append((0, 1, 0))

            intersection_points = []
            for i in range(len(lines)):
                for j in range(i + 1, len(lines)):
                    a1, b1, c1 = lines[i]
                    a2, b2, c2 = lines[j]
                    det = a1 * b2 - a2 * b1
                    if abs(det) > 1e-9:
                        x = (c1 * b2 - c2 * b1) / det
                        y = (a1 * c2 - a2 * c1) / det
                        intersection_points.append((x, y))

            valid_points = []
            for px, py in intersection_points:
                if px < -1e-5 or py < -1e-5: continue 
                satisfies_all = True
                for const in constraints:
                    val = const['a'] * px + const['b'] * py
                    limit = const['c']
                    if const['sign'] == u"\u2264" and val > limit + 1e-5: satisfies_all = False; break
                    elif const['sign'] == u"\u2265" and val < limit - 1e-5: satisfies_all = False; break
                    elif const['sign'] == "=" and abs(val - limit) > 1e-5: satisfies_all = False; break
                if satisfies_all: valid_points.append((px, py))
            
            unique_points = []
            for p in valid_points:
                is_unique = True
                for up in unique_points:
                    if abs(p[0]-up[0]) < 1e-5 and abs(p[1]-up[1]) < 1e-5: is_unique = False; break
                if is_unique: unique_points.append(p)
            valid_points = unique_points

            if len(valid_points) >= 3:
                cx = sum([p[0] for p in valid_points]) / len(valid_points)
                cy = sum([p[1] for p in valid_points]) / len(valid_points)
                valid_points.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
                poly_patch = MplPolygon(valid_points, closed=True, color='#4CAF50', alpha=0.3)
                ax.add_patch(poly_patch)
                
                # Точки углов
                for p in valid_points:
                    ax.plot(p[0], p[1], 'bo', markersize=6)

            # Вычисление границ
            x_coords = [p[0] for p in valid_points]
            y_coords = [p[1] for p in valid_points]
            opt_x = optimal_vars.get('X1', 0)
            opt_y = optimal_vars.get('X2', 0)
            x_coords.append(opt_x); y_coords.append(opt_y)
            
            maxx = max(x_coords) if x_coords else 10
            maxy = max(y_coords) if y_coords else 10
            
            ax.set_xlim(0, maxx * 1.2)
            ax.set_ylim(0, maxy * 1.2)

            # Линии
            x_range = np.linspace(0, maxx * 1.5, 100)
            for const in constraints:
                a, b, c, s = const['a'], const['b'], const['c'], const['sign']
                if abs(b) > 1e-5:
                    y_line = (c - a * x_range) / b
                    ax.plot(x_range, y_line, label=f'{a}X1 + {b}X2 {s} {c}')
                else:
                    ax.axvline(x=c/a, linestyle='--', color='gray', label=f'{a}X1 {s} {c}')

            if optimal_vars:
                ax.plot(opt_x, opt_y, 'ro', markersize=9, zorder=10)
                ax.text(opt_x, opt_y, f' Opt', color='red', fontsize=10, fontweight='bold')

            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend(fontsize='small', loc='best')
            
            # Обновляем сам холст
            canvas.draw()
            return constraints # Возвращаем для создания слайдеров

        except Exception as e:
            print("Plot error:", e)
            return []

    # --- СОБЫТИЯ ---
    def full_solve_event(self):
        """Полный цикл: очистка всего, создание графика, слайдеров и истории текста"""
        self.clear_results_layout()
        self.clear_graph_layout()
        
        final_z, history, opt_vars, err, headers = self.calculate_simplex()
        
        if err:
            QMessageBox.warning(self, "Ошибка", err)
            return

        # 1. График
        num_vars = self.constraint_table.columnCount() - 2
        if num_vars == 2:
            lbl_graph = QLabel("Графическая интерпретация (X1, X2):")
            lbl_graph.setFont(QFont("Arial", 12, QFont.Bold))
            self.graph_layout.addWidget(lbl_graph)

            # Создаем холст
            self.canvas_widget = MplCanvas(self, width=6, height=5, dpi=100)
            
            # Добавляем ПАНЕЛЬ НАВИГАЦИИ (Zoom, Pan)
            self.toolbar_widget = NavigationToolbar2QT(self.canvas_widget, self)
            self.graph_layout.addWidget(self.toolbar_widget)
            self.graph_layout.addWidget(self.canvas_widget)
            
            constraints = self.plot_graph_on_canvas(self.canvas_widget, opt_vars)
            
            # Создаем слайдеры (только при первом полном запуске)
            self.create_sliders(constraints)
        
        # 2. Итерации (текст)
        for i, state in enumerate(history):
            self.add_iteration_table(i, state, headers)
            
        # 3. Финал
        self.add_final_result_widget(history[-1], final_z)
        
        self.main_scroll.verticalScrollBar().setValue(0)

    def fast_solve_event(self):
        """Быстрое обновление: только перерисовка графика и обновление текста финала"""
        if not self.canvas_widget: return
        
        final_z, history, opt_vars, err, headers = self.calculate_simplex()
        if err: return

        # Перерисовка графика
        self.plot_graph_on_canvas(self.canvas_widget, opt_vars)
        
        # Обновление финального результата (удаляем старый, добавляем новый)
        # Это хак: мы удаляем всё текстовое содержимое и перерисовываем только если надо
        # Но чтобы не тормозило, мы пока просто оставим старые таблицы, 
        # а обновим только график.
        # Если вы хотите, чтобы таблицы итераций тоже обновлялись в реальном времени, 
        # раскомментируйте следующую строку (но будет лагать):
        
        # self.clear_results_layout(); [self.add_iteration_table(i, s, headers) for i,s in enumerate(history)]; self.add_final_result_widget(history[-1], final_z)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())