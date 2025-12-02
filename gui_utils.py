import math
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg') 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon
from PyQt5.QtWidgets import QSizePolicy

# Настройка стилей Matplotlib под "Clean Design"
try:
    import matplotlib.pyplot as plt
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    pass

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Прозрачный фон фигуры, чтобы сливался с карточкой интерфейса
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#FFFFFF')
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#FFFFFF')
        
        # Более свободные отступы
        self.fig.subplots_adjust(left=0.08, bottom=0.1, right=0.95, top=0.92)
        
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.updateGeometry()

def plot_constraints(canvas, constraint_table, optimal_vars):
    """Рисует график ограничений и оптимальной точки в стиле Apple."""
    ax = canvas.axes
    ax.clear()
    
    # Apple Colors
    COLOR_AREA = '#34C759'  # Apple Green
    COLOR_OPT = '#FF3B30'   # Apple Red
    COLOR_LINE = '#007AFF'  # Apple Blue
    COLOR_GRID = '#E5E5EA'  # Light Gray for grid
    
    try:
        rows = constraint_table.rowCount()
        cols = constraint_table.columnCount()
        constraints = []
        
        for i in range(rows):
            a_item = constraint_table.item(i, 0)
            b_item = constraint_table.item(i, 1)
            c_item = constraint_table.item(i, cols - 1)
            
            a = float(a_item.text()) if a_item and a_item.text().strip() else 0.0
            b = float(b_item.text()) if b_item and b_item.text().strip() else 0.0
            c = float(c_item.text()) if c_item and c_item.text().strip() else 0.0
            
            sign_widget = constraint_table.cellWidget(i, cols - 2)
            sign = sign_widget.currentText()
            
            constraints.append({'a': a, 'b': b, 'sign': sign, 'c': c})

        lines = []
        for const in constraints:
            lines.append((const['a'], const['b'], const['c']))
        lines.append((1, 0, 0)) 
        lines.append((0, 1, 0)) 

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

        # Рисуем область допустимых значений
        if len(valid_points) >= 3:
            cx = sum([p[0] for p in valid_points]) / len(valid_points)
            cy = sum([p[1] for p in valid_points]) / len(valid_points)
            valid_points.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
            
            # Более мягкая заливка
            poly_patch = MplPolygon(valid_points, closed=True, color=COLOR_AREA, alpha=0.2, label="Область решений")
            ax.add_patch(poly_patch)
            
            # Контур области
            poly_line = MplPolygon(valid_points, closed=True, fill=False, edgecolor=COLOR_AREA, linewidth=2, alpha=0.8)
            ax.add_patch(poly_line)
            
            for p in valid_points: ax.plot(p[0], p[1], 'o', color=COLOR_AREA, markersize=5)

        x_coords = [p[0] for p in valid_points]
        y_coords = [p[1] for p in valid_points]
        opt_x = optimal_vars.get('X1', 0)
        opt_y = optimal_vars.get('X2', 0)
        x_coords.append(opt_x); y_coords.append(opt_y)
        
        maxx = max(x_coords) if x_coords else 10
        maxy = max(y_coords) if y_coords else 10
        
        ax.set_xlim(0, maxx * 1.2)
        ax.set_ylim(0, maxy * 1.2)

        x_range = np.linspace(0, maxx * 1.5, 100)
        
        # Отрисовка линий ограничений
        color_cycle = [COLOR_LINE, '#5856D6', '#FF9500', '#AF52DE'] # Apple Palette colors
        
        for idx, const in enumerate(constraints):
            a, b, c, s = const['a'], const['b'], const['c'], const['sign']
            line_color = color_cycle[idx % len(color_cycle)]
            
            if abs(b) > 1e-5:
                y_line = (c - a * x_range) / b
                ax.plot(x_range, y_line, color=line_color, linewidth=1.5, alpha=0.7, label=f'{a}X1 + {b}X2 {s} {c}')
            else:
                if abs(a) > 1e-9:
                    ax.axvline(x=c/a, linestyle='--', color=line_color, linewidth=1.5, alpha=0.7, label=f'{a}X1 {s} {c}')

        if optimal_vars:
            ax.plot(opt_x, opt_y, 'o', color=COLOR_OPT, markersize=10, zorder=10, markeredgecolor='white', markeredgewidth=1.5)
            # Тень для текста
            ax.text(opt_x, opt_y + (maxy*0.02), f' Оптимум', color=COLOR_OPT, fontsize=10, fontweight='bold')

        # Стилизация сетки и осей
        ax.grid(True, linestyle='-', color=COLOR_GRID, alpha=0.6)
        ax.set_title("Графическое решение", fontsize=12, fontweight='bold', color='#1D1D1F', pad=15)
        ax.set_xlabel("X1", fontsize=10, color='#86868B')
        ax.set_ylabel("X2", fontsize=10, color='#86868B')
        
        # Убираем верхнюю и правую рамки для минимализма
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#D2D2D7')
        ax.spines['bottom'].set_color('#D2D2D7')
        
        ax.legend(fontsize='small', loc='best', frameon=True, framealpha=0.9, edgecolor='#D2D2D7')
        canvas.draw()
        
        return constraints
        
    except Exception as e:
        print(f"Ошибка отрисовки графика: {e}")
        return []