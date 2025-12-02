import math
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg') 
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon
from PyQt5.QtWidgets import QSizePolicy

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.90)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.updateGeometry()

def plot_constraints(canvas, constraint_table, optimal_vars):
    """Рисует график ограничений и оптимальной точки."""
    ax = canvas.axes
    ax.clear()
    
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

        if len(valid_points) >= 3:
            cx = sum([p[0] for p in valid_points]) / len(valid_points)
            cy = sum([p[1] for p in valid_points]) / len(valid_points)
            valid_points.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
            poly_patch = MplPolygon(valid_points, closed=True, color='#4CAF50', alpha=0.3, label="Доп. область")
            ax.add_patch(poly_patch)
            for p in valid_points: ax.plot(p[0], p[1], 'bo', markersize=6)

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
        for const in constraints:
            a, b, c, s = const['a'], const['b'], const['c'], const['sign']
            if abs(b) > 1e-5:
                y_line = (c - a * x_range) / b
                ax.plot(x_range, y_line, label=f'{a}X1 + {b}X2 {s} {c}')
            else:
                if abs(a) > 1e-9:
                    ax.axvline(x=c/a, linestyle='--', color='gray', label=f'{a}X1 {s} {c}')

        if optimal_vars:
            ax.plot(opt_x, opt_y, 'ro', markersize=9, zorder=10)
            ax.text(opt_x, opt_y, f' Опт', color='red', fontsize=10, fontweight='bold')

        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_title("Графическое решение")
        ax.set_xlabel("X1")
        ax.set_ylabel("X2")
        ax.legend(fontsize='small', loc='best')
        canvas.draw()
        
        return constraints
        
    except Exception as e:
        print(f"Ошибка отрисовки графика: {e}")
        return []