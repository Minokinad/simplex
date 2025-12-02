import numpy as np
import copy

def get_simplex_data(objective_table, constraint_table):
    """Считывает данные из таблиц PyQt и возвращает numpy матрицу."""
    # Чтение целевой функции
    obj_cols = objective_table.columnCount() - 2
    obj_coeffs = []
    for i in range(obj_cols):
        text = objective_table.item(0, i).text()
        obj_coeffs.append(float(text) if text and text.strip() else 0.0)
    
    # Вставка 0 для Z-колонки
    obj_row = np.insert(obj_coeffs, 0, 0)
    
    # Чтение ограничений
    rows = constraint_table.rowCount()
    cols = constraint_table.columnCount()
    
    rhs_list = [] # Правые части (bi)
    coeff_matrix = []
    
    for i in range(rows):
        # bi - последняя колонка
        text_bi = constraint_table.item(i, cols - 1).text()
        rhs_list.append(float(text_bi) if text_bi and text_bi.strip() else 0.0)
        
        # Коэффициенты
        row_coeffs = []
        for j in range(cols - 2):
            text_c = constraint_table.item(i, j).text()
            row_coeffs.append(float(text_c) if text_c and text_c.strip() else 0.0)
        coeff_matrix.append(row_coeffs)
        
    matrix_body = np.concatenate((np.array(rhs_list).reshape(-1, 1), np.array(coeff_matrix)), axis=1)
    full_matrix = np.vstack((obj_row, matrix_body))
    
    return full_matrix, rhs_list, obj_coeffs

def calculate_simplex(raw_matrix, operation, num_vars):
    """Основной алгоритм симплекс-метода."""
    try:
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
        
        # Инверсия Z для максимизации
        weird[0] = [-1 * x for x in weird[0]]
        
        # Имена переменных
        x_vars = [f'X{i+1}' for i in range(num_vars)]
        num_slack = rows - 1
        s_vars = [f'X{num_vars + i + 1}' for i in range(num_slack)]
        headers = x_vars + s_vars + ['Решение']
        l4 = x_vars + s_vars
        
        current_dic = {}
        basis = ['E'] + s_vars
        for i, row in enumerate(weird):
            current_dic[basis[i]] = row

        history_steps = []
        is_min = (operation == 'Минимизация')
        max_iter = 100
        counter = 0
        
        curr_list = weird
        curr_dic_algo = current_dic
        
        curr_list = copy.deepcopy(curr_list)

        while counter < max_iter:
            z_row = curr_list[0][:-1]
            
            is_optimal = False
            if is_min:
                if max(z_row) <= 1e-9: is_optimal = True
            else:
                if min(z_row) >= -1e-9: is_optimal = True
            
            if is_optimal:
                history_steps.append({
                    'table': copy.deepcopy(curr_dic_algo),
                    'pivot_col': None, 'pivot_row': None, 'ratios': []
                })
                break

            limit = max(z_row) if is_min else min(z_row)
            pivot_col = z_row.index(limit)
            
            ratios = []
            last_col = len(curr_list[0]) - 1
            
            for i in range(1, len(curr_list)):
                row = curr_list[i]
                val = row[pivot_col]
                rhs = row[last_col]
                if val > 1e-9: 
                    ratios.append(rhs / val)
                else: 
                    ratios.append(float('inf'))
            
            valid_ratios = [r for r in ratios if r != float('inf')]
            if not valid_ratios:
                return None, None, None, "Задача не ограничена (нет конечного решения)", None
            
            min_r = min(valid_ratios)
            ratio_idx = ratios.index(min_r)
            pivot_row_idx = ratio_idx + 1
            
            entering_var = l4[pivot_col]
            current_basis_keys = list(curr_dic_algo.keys())
            leaving_var = current_basis_keys[pivot_row_idx]
            
            history_steps.append({
                'table': copy.deepcopy(curr_dic_algo),
                'pivot_col': pivot_col,
                'pivot_row': pivot_row_idx,
                'ratios': ratios,
                'entering': entering_var,
                'leaving': leaving_var
            })

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
            
            for i in range(len(new_table)):
                if i == pivot_row_idx: new_dic[entering_var] = new_table[i]
                else: new_dic[old_keys[i]] = new_table[i]
            
            curr_dic_algo = new_dic
            curr_list = list(curr_dic_algo.values())
            counter += 1
            
        final_z = list(history_steps[-1]['table'].values())[0][-1]
        final_vars = {}
        for k, v in history_steps[-1]['table'].items():
            if k != 'E': final_vars[k] = v[-1]
            
        return final_z, history_steps, final_vars, None, headers

    except Exception as e:
        return None, None, None, f"Ошибка в вычислениях: {str(e)}", None

# Исправленная строка определения функции ниже:
def perform_sensitivity_analysis(final_tableau, original_rhs, original_obj_coeffs, num_dec_vars, num_constrs, is_max):
    """
    Расчет анализа чувствительности с подробным отчетом по D.
    """
    try:
        z_row = final_tableau.get('E')
        if not z_row: return [], [], ""

        sol_idx = len(z_row) - 1
        detailed_report = ""

        # ==========================================
        # 1. АНАЛИЗ ПРАВЫХ ЧАСТЕЙ (ОГРАНИЧЕНИЙ)
        # ==========================================
        detailed_report += "=== АНАЛИЗ ОГРАНИЧЕНИЙ (Изменение запасов) ===\n\n"
        
        constr_analysis = []
        slack_indices = range(num_dec_vars, num_dec_vars + num_constrs)
        
        for i, slack_idx in enumerate(slack_indices):
            constr_name = f"Огр. {i+1}"
            rhs_val = original_rhs[i]
            shadow_price = z_row[slack_idx]
            
            detailed_report += f"--- Анализ для {constr_name} (RHS = {rhs_val}) ---\n"
            detailed_report += f"Пусть изменение запаса = D. Тогда:\n"

            d_min = float('-inf')
            d_max = float('inf')
            
            rows_equations = []

            for key, row_vals in final_tableau.items():
                if key == 'E': continue
                
                current_val = row_vals[sol_idx]
                coeff = row_vals[slack_idx]
                
                if abs(coeff) < 1e-9: 
                    continue

                sign_str = "+" if coeff >= 0 else ""
                eq_str = f"{key}: {current_val:.2f} {sign_str}{coeff:.2f}D ≥ 0"
                rows_equations.append(eq_str)

                if coeff > 0:
                    # D >= -Val / Coeff
                    limit = -current_val / coeff
                    if limit > d_min: d_min = limit
                else:
                    # D <= -Val / Coeff
                    limit = -current_val / coeff
                    if limit < d_max: d_max = limit

            for eq in rows_equations:
                detailed_report += f"  {eq}\n"
            
            if not rows_equations:
                 detailed_report += "  Нет активных ограничений для D (диапазон бесконечен)\n"

            d_min_str = f"{d_min:.2f}" if d_min != float('-inf') else "-∞"
            d_max_str = f"{d_max:.2f}" if d_max != float('inf') else "+∞"
            
            detailed_report += f"Диапазон для D: [{d_min_str} ; {d_max_str}]\n"
            
            final_range_min = rhs_val + d_min if d_min != float('-inf') else "-∞"
            final_range_max = rhs_val + d_max if d_max != float('inf') else "+∞"
            
            if isinstance(final_range_min, float): final_range_min = f"{final_range_min:.2f}"
            if isinstance(final_range_max, float): final_range_max = f"{final_range_max:.2f}"

            detailed_report += f"Диапазон устойчивости ресурса: [{final_range_min} ; {final_range_max}]\n"
            detailed_report += "-"*40 + "\n"

            constr_analysis.append({
                "name": constr_name,
                "rhs": rhs_val,
                "shadow_price": shadow_price,
                "allow_increase": d_max_str,
                "allow_decrease": abs(d_min) if d_min != float('-inf') else "∞"
            })

        # ==========================================
        # 2. АНАЛИЗ ЦЕЛЕВОЙ ФУНКЦИИ (ПРИБЫЛИ)
        # ==========================================
        detailed_report += "\n=== АНАЛИЗ ЦЕЛЕВОЙ ФУНКЦИИ (Изменение прибыли) ===\n\n"
        var_analysis = []
        
        basic_vars = list(final_tableau.keys())
        if 'E' in basic_vars: basic_vars.remove('E')

        for i in range(num_dec_vars):
            var_name = f"X{i+1}"
            orig_c = original_obj_coeffs[i]
            current_val = final_tableau[var_name][sol_idx] if var_name in final_tableau else 0.0
            reduced_cost = z_row[i] 
            
            detailed_report += f"--- Анализ для {var_name} (Коэф = {orig_c}) ---\n"
            detailed_report += f"Пусть изменение прибыли = D. \n"

            d_min = float('-inf')
            d_max = float('inf')
            
            rows_equations = []
            
            if var_name not in basic_vars:
                rows_equations.append(f"Небазисная: {reduced_cost:.2f} - D ≥ 0")
                d_max = reduced_cost
            else:
                row_vals = final_tableau[var_name]
                for j in range(len(z_row) - 1):
                    if abs(z_row[j]) < 1e-9: continue
                    
                    rc_val = z_row[j]
                    a_val = row_vals[j]
                    
                    sign_str = "-" if a_val >= 0 else "+"
                    rows_equations.append(f"Столбец {j+1}: {rc_val:.2f} {sign_str}{abs(a_val):.2f}D ≥ 0")
                    
                    if abs(a_val) > 1e-9:
                        if a_val > 0:
                            limit = rc_val / a_val
                            if limit < d_max: d_max = limit
                        else:
                            limit = rc_val / a_val
                            if limit > d_min: d_min = limit

            for eq in rows_equations:
                detailed_report += f"  {eq}\n"

            d_min_str = f"{d_min:.2f}" if d_min != float('-inf') else "-∞"
            d_max_str = f"{d_max:.2f}" if d_max != float('inf') else "+∞"
            
            detailed_report += f"Диапазон для D: [{d_min_str} ; {d_max_str}]\n"
            
            final_range_min = orig_c + d_min if d_min != float('-inf') else "-∞"
            final_range_max = orig_c + d_max if d_max != float('inf') else "+∞"
            
            if isinstance(final_range_min, float): final_range_min = f"{final_range_min:.2f}"
            if isinstance(final_range_max, float): final_range_max = f"{final_range_max:.2f}"

            detailed_report += f"Диапазон коэф. Cj: [{final_range_min} ; {final_range_max}]\n"
            detailed_report += "-"*40 + "\n"

            var_analysis.append({
                "name": var_name,
                "final_value": current_val,
                "obj_coeff": orig_c,
                "reduced_cost": reduced_cost,
                "allow_increase": d_max_str,
                "allow_decrease": abs(d_min) if d_min != float('-inf') else "∞"
            })

        return var_analysis, constr_analysis, detailed_report
        
    except Exception as e:
        print(f"Ошибка в анализе чувствительности: {e}")
        return [], [], f"Ошибка построения отчета: {str(e)}"