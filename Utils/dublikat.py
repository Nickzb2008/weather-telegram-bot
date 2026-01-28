import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
from datetime import datetime
import shutil
import hashlib

class AdvancedDuplicateRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Розширений очищувач дублікатів")
        self.root.geometry("1000x700")
        
        # Змінні
        self.input_file = ""
        self.output_file = ""
        self.duplicates = []
        self.backup_file = ""
        self.lines_data = []
        
        # Налаштування пошуку
        self.search_criteria = {
            "compare_name": tk.BooleanVar(value=True),
            "compare_region": tk.BooleanVar(value=True),
            "compare_coordinates": tk.BooleanVar(value=True),
            "compare_population": tk.BooleanVar(value=False),
            "tolerance": tk.DoubleVar(value=0.0001)  # Толерантність для координат
        }
        
        # Створення інтерфейсу
        self.create_widgets()
        
    def create_widgets(self):
        # Верхня панель з кнопками
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(top_frame, text="📂 Вибрати файл", command=self.select_file).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(top_frame, text="Файл не вибрано", font=('Arial', 10))
        self.file_label.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(top_frame, text="🔍 Аналізувати", command=self.analyze_file, state="disabled").pack(side=tk.LEFT, padx=5)
        self.analyze_btn = self.root.nametowidget(top_frame.winfo_children()[2])
        
        ttk.Button(top_frame, text="🗑️ Видалити дублікати", command=self.remove_duplicates, state="disabled").pack(side=tk.LEFT, padx=5)
        self.remove_btn = self.root.nametowidget(top_frame.winfo_children()[3])
        
        ttk.Button(top_frame, text="📊 Статистика", command=self.show_statistics).pack(side=tk.LEFT, padx=5)
        
        # Ліва панель - налаштування
        left_frame = ttk.LabelFrame(self.root, text="Критерії пошуку дублікатів", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), padx=5, pady=5)
        
        ttk.Checkbutton(left_frame, text="Порівнювати назви", 
                       variable=self.search_criteria["compare_name"]).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(left_frame, text="Порівнювати області", 
                       variable=self.search_criteria["compare_region"]).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(left_frame, text="Порівнювати координати", 
                       variable=self.search_criteria["compare_coordinates"]).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(left_frame, text="Порівнювати населення", 
                       variable=self.search_criteria["compare_population"]).grid(row=3, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(left_frame, text="Толерантність координат:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Scale(left_frame, from_=0.00001, to=0.01, variable=self.search_criteria["tolerance"],
                 orient=tk.HORIZONTAL, length=200).grid(row=5, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(left_frame, text=f"Поточне значення: {self.search_criteria['tolerance'].get():.5f}").grid(row=6, column=0, sticky=tk.W)
        
        # Кнопки управління
        ttk.Button(left_frame, text="Застосувати всі критерії", 
                  command=self.set_all_criteria).grid(row=7, column=0, pady=10, sticky=tk.W)
        
        ttk.Button(left_frame, text="Тільки назва та область", 
                  command=self.set_name_region_only).grid(row=8, column=0, pady=5, sticky=tk.W)
        
        # Права панель - результати
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.N, tk.S, tk.W, tk.E), padx=5, pady=5)
        
        # Notebook для різних вкладок
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка з таблицею дублікатів
        table_frame = ttk.Frame(self.notebook)
        self.notebook.add(table_frame, text="Дублікати")
        
        columns = ("row", "name", "region", "lat", "lon", "population", "type", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        headings = {
            "row": ("Рядок", 60),
            "name": ("Назва", 150),
            "region": ("Область", 120),
            "lat": ("Широта", 80),
            "lon": ("Довгота", 80),
            "population": ("Населення", 90),
            "type": ("Тип", 100),
            "status": ("Статус", 120)
        }
        
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Вкладка з прев'ю рядків
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="Попередній перегляд")
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=20, width=80, font=('Courier', 9))
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка з деталями
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="Деталі")
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=20, width=80)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Панель статистики
        stats_frame = ttk.Frame(self.root, padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.stats_label = ttk.Label(stats_frame, text="Статистика: очікування аналізу...", font=('Arial', 10))
        self.stats_label.pack(side=tk.LEFT)
        
        # Конфігурація розмірів
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Прив'язка подій
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Виберіть файл settlements_db.py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if file_path:
            self.input_file = file_path
            self.file_label.config(text=f"📄 {os.path.basename(file_path)}")
            self.analyze_btn.config(state="normal")
            self.clear_table()
            self.preview_text.delete(1.0, tk.END)
            self.details_text.delete(1.0, tk.END)
            
    def analyze_file(self):
        if not self.input_file or not os.path.exists(self.input_file):
            messagebox.showerror("Помилка", "Файл не вибрано або не існує")
            return
            
        try:
            self.duplicates = self.find_duplicates()
            self.lines_data = self.extract_all_settlements()
            self.display_duplicates()
            self.update_stats()
            
            if self.duplicates:
                self.remove_btn.config(state="normal")
                self.show_preview()
                messagebox.showinfo("Аналіз завершено", 
                                  f"Знайдено {len(self.duplicates)} дублікатів для видалення")
            else:
                self.remove_btn.config(state="disabled")
                messagebox.showinfo("Аналіз завершено", "Дублікатів не знайдено")
                
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка під час аналізу: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def find_duplicates(self):
        """Знаходить дублікати згідно з обраними критеріями"""
        duplicates = []
        seen = {}
        tolerance = self.search_criteria["tolerance"].get()
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        pattern = r'self\._add_settlement\("([^"]+)",\s*([\d.]+),\s*([\d.]+),\s*"([^"]+)",\s*"([^"]+)",\s*(\d+)'
        
        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                name = match.group(1)
                lat = float(match.group(2))
                lon = float(match.group(3))
                region = match.group(4)
                settlement_type = match.group(5)
                population = int(match.group(6))
                
                # Формуємо ключ на основі обраних критеріїв
                key_parts = []
                if self.search_criteria["compare_name"].get():
                    key_parts.append(f"name:{name}")
                if self.search_criteria["compare_region"].get():
                    key_parts.append(f"region:{region}")
                if self.search_criteria["compare_coordinates"].get():
                    # Округлюємо координати з урахуванням толерантності
                    lat_rounded = round(lat / tolerance) * tolerance
                    lon_rounded = round(lon / tolerance) * tolerance
                    key_parts.append(f"lat:{lat_rounded:.6f}")
                    key_parts.append(f"lon:{lon_rounded:.6f}")
                if self.search_criteria["compare_population"].get():
                    key_parts.append(f"pop:{population}")
                
                key = "|".join(key_parts)
                
                if key in seen:
                    duplicates.append({
                        "line_num": i + 1,
                        "name": name,
                        "region": region,
                        "population": population,
                        "lat": lat,
                        "lon": lon,
                        "type": settlement_type,
                        "line_text": line.strip(),
                        "original_line": seen[key]["line"],
                        "original_data": seen[key]
                    })
                else:
                    seen[key] = {
                        "line": i + 1,
                        "name": name,
                        "region": region,
                        "population": population,
                        "lat": lat,
                        "lon": lon,
                        "type": settlement_type
                    }
        
        return duplicates
    
    def extract_all_settlements(self):
        """Витягує всі населені пункти з файлу"""
        settlements = []
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        pattern = r'self\._add_settlement\("([^"]+)",\s*([\d.]+),\s*([\d.]+),\s*"([^"]+)",\s*"([^"]+)",\s*(\d+)'
        
        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                settlements.append({
                    "line_num": i + 1,
                    "name": match.group(1),
                    "lat": float(match.group(2)),
                    "lon": float(match.group(3)),
                    "region": match.group(4),
                    "type": match.group(5),
                    "population": int(match.group(6)),
                    "line_text": line.strip()
                })
        
        return settlements
    
    def display_duplicates(self):
        """Відображає знайдені дублікати в таблиці"""
        self.clear_table()
        
        for dup in self.duplicates:
            self.tree.insert("", tk.END, values=(
                dup["line_num"],
                dup["name"],
                dup["region"],
                f"{dup['lat']:.4f}",
                f"{dup['lon']:.4f}",
                dup["population"],
                dup["type"],
                "Дублікат"
            ))
    
    def clear_table(self):
        """Очищає таблицю"""
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def update_stats(self):
        """Оновлює статистику"""
        total_settlements = len(self.lines_data)
        total_duplicates = len(self.duplicates)
        unique_count = total_settlements - total_duplicates
        
        stats_text = f"Загальна кількість: {total_settlements} | Унікальних: {unique_count} | Дублікатів: {total_duplicates}"
        self.stats_label.config(text=stats_text)
    
    def show_preview(self):
        """Показує прев'ю з прикладами дублікатів"""
        self.preview_text.delete(1.0, tk.END)
        
        if not self.duplicates:
            self.preview_text.insert(tk.END, "Дублікатів не знайдено")
            return
        
        self.preview_text.insert(tk.END, "ЗНАЙДЕНІ ДУБЛІКАТИ:\n")
        self.preview_text.insert(tk.END, "=" * 80 + "\n\n")
        
        for i, dup in enumerate(self.duplicates[:10]):  # Показуємо перші 10
            self.preview_text.insert(tk.END, f"Дублікат {i+1} (рядок {dup['line_num']}):\n")
            self.preview_text.insert(tk.END, f"  Назва: {dup['name']}\n")
            self.preview_text.insert(tk.END, f"  Область: {dup['region']}\n")
            self.preview_text.insert(tk.END, f"  Координати: {dup['lat']:.6f}, {dup['lon']:.6f}\n")
            self.preview_text.insert(tk.END, f"  Населення: {dup['population']}\n")
            self.preview_text.insert(tk.END, f"  Оригінал в рядку: {dup['original_line']}\n")
            self.preview_text.insert(tk.END, "-" * 40 + "\n\n")
        
        if len(self.duplicates) > 10:
            self.preview_text.insert(tk.END, f"... та ще {len(self.duplicates) - 10} дублікатів\n")
    
    def on_tree_select(self, event):
        """Обробляє вибір рядка в таблиці"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        line_num = item['values'][0]
        
        # Знаходимо повну інформацію про дублікат
        dup = next((d for d in self.duplicates if d["line_num"] == line_num), None)
        if not dup:
            return
        
        # Показуємо деталі
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, "ДЕТАЛЬНА ІНФОРМАЦІЯ ПРО ДУБЛІКАТ:\n")
        self.details_text.insert(tk.END, "=" * 60 + "\n\n")
        
        self.details_text.insert(tk.END, f"Рядок: {dup['line_num']}\n")
        self.details_text.insert(tk.END, f"Повний текст рядка:\n{dup['line_text']}\n\n")
        
        self.details_text.insert(tk.END, "Параметри:\n")
        self.details_text.insert(tk.END, f"  • Назва: {dup['name']}\n")
        self.details_text.insert(tk.END, f"  • Область: {dup['region']}\n")
        self.details_text.insert(tk.END, f"  • Тип: {dup['type']}\n")
        self.details_text.insert(tk.END, f"  • Населення: {dup['population']}\n")
        self.details_text.insert(tk.END, f"  • Широта: {dup['lat']:.6f}\n")
        self.details_text.insert(tk.END, f"  • Довгота: {dup['lon']:.6f}\n\n")
        
        if "original_data" in dup:
            self.details_text.insert(tk.END, "ОРИГІНАЛЬНИЙ ЗАПИС (залишиться):\n")
            self.details_text.insert(tk.END, f"  • Рядок: {dup['original_line']}\n")
            self.details_text.insert(tk.END, f"  • Назва: {dup['original_data']['name']}\n")
            self.details_text.insert(tk.END, f"  • Область: {dup['original_data']['region']}\n")
            self.details_text.insert(tk.END, f"  • Населення: {dup['original_data']['population']}\n")
    
    def remove_duplicates(self):
        if not self.duplicates:
            messagebox.showwarning("Немає дублікатів", "Дублікатів для видалення не знайдено")
            return
            
        # Підтвердження
        confirm = messagebox.askyesno(
            "Підтвердження",
            f"Ви впевнені, що хочете видалити {len(self.duplicates)} дублікатів?\n"
            f"Буде створено резервну копію оригінального файлу."
        )
        
        if not confirm:
            return
        
        try:
            # Створення резервної копії
            backup_dir = os.path.join(os.path.dirname(self.input_file), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_file = os.path.join(backup_dir, f"settlements_db_backup_{timestamp}.py")
            shutil.copy2(self.input_file, self.backup_file)
            
            # Читаємо всі рядки
            with open(self.input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Визначаємо рядки для видалення
            lines_to_remove = [dup["line_num"] - 1 for dup in self.duplicates]
            
            # Створюємо новий список рядків без дублікатів
            new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
            
            # Створюємо новий файл
            base_name = os.path.basename(self.input_file)
            name_without_ext = os.path.splitext(base_name)[0]
            self.output_file = os.path.join(
                os.path.dirname(self.input_file),
                f"{name_without_ext}_cleaned_{timestamp}.py"
            )
            
            # Записуємо новий файл
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # Оновлюємо інтерфейс
            self.show_results()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка під час видалення: {str(e)}")
    
    def show_results(self):
        """Показує результати роботи"""
        original_count = len(self.lines_data)
        new_count = self.count_lines(self.output_file)
        removed_count = original_count - new_count + (original_count - new_count)  # Корекція
        
        result_text = f"""
        ✅ ОПЕРАЦІЯ ЗАВЕРШЕНА УСПІШНО!
        
        📊 Статистика:
        • Вихідних записів: {original_count}
        • Видалено дублікатів: {removed_count}
        • Залишено записів: {new_count}
        
        📁 Файли:
        • Вхідний файл: {os.path.basename(self.input_file)}
        • Резервна копія: {os.path.basename(self.backup_file)}
        • Очищений файл: {os.path.basename(self.output_file)}
        
        Файли збережено в тій самій папці, що й оригінал.
        """
        
        # Створюємо диалогове вікно з результатами
        result_window = tk.Toplevel(self.root)
        result_window.title("Результати очищення")
        result_window.geometry("500x400")
        
        # Текст результату
        text_widget = scrolledtext.ScrolledText(result_window, width=60, height=20)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, result_text)
        text_widget.config(state=tk.DISABLED)
        
        # Кнопки
        button_frame = ttk.Frame(result_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Відкрити очищений файл", 
                  command=lambda: self.open_file(self.output_file)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Відкрити папку", 
                  command=lambda: self.open_folder(os.path.dirname(self.output_file))).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Закрити", 
                  command=result_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Додаємо кнопки в головне вікно
        self.show_main_buttons()
    
    def show_main_buttons(self):
        """Додає кнопки в головне вікно"""
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="🔄 Аналізувати знову", 
                  command=self.analyze_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="📂 Відкрити папку з результатами", 
                  command=lambda: self.open_folder(os.path.dirname(self.output_file))).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="❌ Закрити програму", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
    
    def show_statistics(self):
        """Показує детальну статистику"""
        if not self.lines_data:
            messagebox.showinfo("Статистика", "Спочатку виконайте аналіз файлу")
            return
        
        # Групуємо по областям
        regions = {}
        types = {}
        
        for settlement in self.lines_data:
            region = settlement["region"]
            settlement_type = settlement["type"]
            
            if region not in regions:
                regions[region] = 0
            regions[region] += 1
            
            if settlement_type not in types:
                types[settlement_type] = 0
            types[settlement_type] += 1
        
        # Створюємо текст статистики
        stats_text = "📊 ДЕТАЛЬНА СТАТИСТИКА\n"
        stats_text += "=" * 50 + "\n\n"
        
        stats_text += f"Загальна кількість записів: {len(self.lines_data)}\n"
        stats_text += f"Знайдено дублікатів: {len(self.duplicates)}\n\n"
        
        stats_text += "РОЗПОДІЛ ПО ОБЛАСТЯХ:\n"
        stats_text += "-" * 30 + "\n"
        for region, count in sorted(regions.items(), key=lambda x: x[1], reverse=True):
            stats_text += f"{region}: {count} записів\n"
        
        stats_text += "\nРОЗПОДІЛ ПО ТИПАХ:\n"
        stats_text += "-" * 30 + "\n"
        for stype, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            stats_text += f"{stype}: {count} записів\n"
        
        # Показуємо в новому вікні
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика")
        stats_window.geometry("500x500")
        
        text_widget = scrolledtext.ScrolledText(stats_window, width=60, height=30)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, stats_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(stats_window, text="Закрити", 
                  command=stats_window.destroy).pack(pady=10)
    
    def set_all_criteria(self):
        """Встановлює всі критерії"""
        for var in self.search_criteria.values():
            if isinstance(var, tk.BooleanVar):
                var.set(True)
    
    def set_name_region_only(self):
        """Встановлює тільки назву та область"""
        self.search_criteria["compare_name"].set(True)
        self.search_criteria["compare_region"].set(True)
        self.search_criteria["compare_coordinates"].set(False)
        self.search_criteria["compare_population"].set(False)
    
    def count_lines(self, filepath):
        """Підраховує кількість рядків у файлі"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    
    def open_file(self, filepath):
        """Відкриває файл в системному редакторі"""
        try:
            os.startfile(filepath)
        except AttributeError:
            # Для Linux/Mac
            import subprocess
            subprocess.call(['xdg-open', filepath])
    
    def open_folder(self, folderpath):
        """Відкриває папку в системному файловому менеджері"""
        try:
            os.startfile(folderpath)
        except AttributeError:
            # Для Linux/Mac
            import subprocess
            subprocess.call(['xdg-open', folderpath])

def main():
    root = tk.Tk()
    app = AdvancedDuplicateRemover(root)
    root.mainloop()

if __name__ == "__main__":
    main()