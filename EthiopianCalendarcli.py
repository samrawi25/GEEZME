import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import date, timedelta, datetime


class EthiopianCalendar:
    MONTH_NAMES = {
        1: ("Meskerem", "መስከረም"), 2: ("Tikimt", "ጥቅምት"), 3: ("Hidar", "ኅዳር"),
        4: ("Tahsas", "ታኅሣሥ"), 5: ("Tir", "ጥር"), 6: ("Yekatit", "የካቲት"),
        7: ("Megabit", "መጋቢት"), 8: ("Miyazia", "ሚያዝያ"), 9: ("Ginbot", "ግንቦት"),
        10: ("Sene", "ሰኔ"), 11: ("Hamle", "ሐምሌ"), 12: ("Nehasse", "ነሐሴ"),
        13: ("Pagume", "ጳጉሜ")
    }
    WEEKDAY_NAMES_AM = ["እሁድ", "ሰኞ", "ማክ", "ሮብ", "ሐሙ", "አርብ", "ቅዳሜ"]

    @staticmethod
    def is_ethiopian_leap(year):
        return (year + 1) % 4 == 0

    @classmethod
    def to_gregorian(cls, ey, em, ed):
        g_year_start = ey + 7
        new_year_day = 12 if cls.is_ethiopian_leap(ey - 1) else 11
        anchor = date(g_year_start, 9, new_year_day)
        days_passed = ((em - 1) * 30) + (ed - 1)
        return anchor + timedelta(days=days_passed)

    @classmethod
    def from_gregorian(cls, g_date):
        year, month, day = g_date.year, g_date.month, g_date.day
        new_year_day = 12 if (year % 4 == 0) else 11

        if month < 9 or (month == 9 and day < new_year_day):
            ey = year - 8
            prev_new_year = date(
                year - 1, 9, 12 if ((year - 1) % 4 == 0) else 11)
        else:
            ey = year - 7
            prev_new_year = date(year, 9, new_year_day)

        days_diff = (g_date - prev_new_year).days
        em = (days_diff // 30) + 1
        ed = (days_diff % 30) + 1
        return ey, em, ed


class EthiopianCalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ethiopian Calendar")
        self.root.configure(bg="#d4e1f0")
        self.root.resizable(False, False)

        self.amharic_months = [v[1] for k, v in sorted(
            EthiopianCalendar.MONTH_NAMES.items())]
        today_gregorian = date.today()
        et_today = EthiopianCalendar.from_gregorian(today_gregorian)
        self.year_var = tk.IntVar(value=et_today[0])
        self.month_var = tk.StringVar(
            value=self.amharic_months[et_today[1] - 1])
        self.selected_day = tk.IntVar(value=et_today[2])
        self.day_labels = []

        main_frame = tk.Frame(root, bg="#d4e1f0", padx=10, pady=5)
        main_frame.pack(fill="both", expand=True)

        self.create_calendar_view(main_frame)
        self.create_converter_view(main_frame)

        footer = tk.Label(main_frame, text="(c) SAMIBlue COMPUTING PLC",
                          bg="#d4e1f0", fg="black", font=("Helvetica", 8))
        footer.pack(side='bottom', pady=(10, 0))

        self.update_calendar()
        self.set_converter_defaults(today_gregorian, et_today)

    def create_calendar_view(self, parent):
        container = tk.Frame(parent, bg="#d4e1f0",
                             relief="groove", borderwidth=1)
        container.pack(pady=(0, 10))

        controls = tk.Frame(container, bg="#d4e1f0")
        controls.pack(pady=5)

        tk.Label(controls, text="ወር:", bg="#d4e1f0", font=(
            "Nyala", 11)).pack(side="left", padx=(10, 2))
        month_cb = ttk.Combobox(controls, textvariable=self.month_var,
                                values=self.amharic_months, width=8, state="readonly", font=("Nyala", 11))
        month_cb.pack(side="left")
        month_cb.bind("<<ComboboxSelected>>", self.update_calendar)

        tk.Label(controls, text="ዓ.ም:", bg="#d4e1f0", font=(
            "Nyala", 11)).pack(side="left", padx=(20, 2))
        year_spinbox = tk.Spinbox(controls, from_=1900, to=2100, textvariable=self.year_var,
                                  width=6, command=self.update_calendar, font=("Helvetica", 9))
        year_spinbox.pack(side="left", padx=(0, 10))

        days_frame = tk.Frame(container, bg="#d4e1f0")
        days_frame.pack(padx=10, pady=(0, 10))

        for i, day_name in enumerate(EthiopianCalendar.WEEKDAY_NAMES_AM):
            lbl = tk.Label(days_frame, text=day_name, bg="#d4e1f0",
                           font=("Nyala", 11, 'bold'), fg="#00008B")
            lbl.grid(row=0, column=i, padx=5, pady=2)

        for r in range(6):
            row_labels = []
            for c in range(7):
                day_lbl = tk.Label(days_frame, text="", width=4, height=2, bg="white",
                                   relief="solid", borderwidth=1, font=("Helvetica", 9))
                day_lbl.grid(row=r + 1, column=c, padx=1, pady=1)
                day_lbl.bind("<Button-1>", lambda e, r=r,
                             c=c: self.on_day_click(r, c))
                row_labels.append(day_lbl)
            self.day_labels.append(row_labels)

    def create_converter_view(self, parent):
        container = tk.Frame(parent, bg="#d4e1f0")
        container.pack(fill='x')

        tk.Label(container, text="Date Converter", bg="#d4e1f0",
                 font=("Helvetica", 12, "bold")).pack()

        io_frame = tk.Frame(container, bg="#d4e1f0")
        io_frame.pack(pady=5)

        et_frame = tk.Frame(io_frame, bg="#d4e1f0")
        et_frame.pack(side="left", padx=10)
        tk.Label(et_frame, text="Ethiopian", bg="#d4e1f0", font=(
            "Helvetica", 10)).grid(row=0, column=0, columnspan=3)
        tk.Label(et_frame, text="ቀን", bg="#d4e1f0",
                 font=("Nyala", 10)).grid(row=1, column=0)
        tk.Label(et_frame, text="ወር", bg="#d4e1f0",
                 font=("Nyala", 10)).grid(row=1, column=1)
        tk.Label(et_frame, text="ዓ.ም.", bg="#d4e1f0",
                 font=("Nyala", 10)).grid(row=1, column=2)
        self.et_d_entry = tk.Entry(et_frame, width=4, justify='center')
        self.et_d_entry.grid(row=2, column=0, padx=2)
        self.et_m_entry = tk.Entry(et_frame, width=4, justify='center')
        self.et_m_entry.grid(row=2, column=1, padx=2)
        self.et_y_entry = tk.Entry(et_frame, width=6, justify='center')
        self.et_y_entry.grid(row=2, column=2, padx=2)

        btn_frame = tk.Frame(io_frame, bg="#d4e1f0")
        btn_frame.pack(side="left", padx=5, anchor='center')
        tk.Button(btn_frame, text="← To EC",
                  command=self.convert_to_ec).pack(pady=4)
        tk.Button(btn_frame, text="→ To GC", command=self.convert_to_gc).pack()

        gc_frame = tk.Frame(io_frame, bg="#d4e1f0")
        gc_frame.pack(side="left", padx=10)
        tk.Label(gc_frame, text="Gregorian", bg="#d4e1f0", font=(
            "Helvetica", 10)).grid(row=0, column=0, columnspan=3)
        tk.Label(gc_frame, text="Day", bg="#d4e1f0",
                 font=("Helvetica", 8)).grid(row=1, column=0)
        tk.Label(gc_frame, text="Month", bg="#d4e1f0",
                 font=("Helvetica", 8)).grid(row=1, column=1)
        tk.Label(gc_frame, text="Year", bg="#d4e1f0",
                 font=("Helvetica", 8)).grid(row=1, column=2)
        self.gc_d_entry = tk.Entry(gc_frame, width=4, justify='center')
        self.gc_d_entry.grid(row=2, column=0, padx=2)
        self.gc_m_entry = tk.Entry(gc_frame, width=4, justify='center')
        self.gc_m_entry.grid(row=2, column=1, padx=2)
        self.gc_y_entry = tk.Entry(gc_frame, width=6, justify='center')
        self.gc_y_entry.grid(row=2, column=2, padx=2)

    def update_calendar(self, *args):
        try:
            year, month_name = self.year_var.get(), self.month_var.get()
            month = self.amharic_months.index(month_name) + 1
        except (ValueError, tk.TclError):
            return

        for r in range(6):  # Clear grid
            for c in range(7):
                self.day_labels[r][c].config(
                    text="", bg="white", relief="solid")

        days_in_month = 6 if month == 13 and EthiopianCalendar.is_ethiopian_leap(
            year) else (5 if month == 13 else 30)
        start_col = (EthiopianCalendar.to_gregorian(
            year, month, 1).weekday() + 1) % 7

        day_num = 1
        for r in range(6):
            for c in range(7):
                if (r == 0 and c < start_col) or day_num > days_in_month:
                    self.day_labels[r][c].config(bg="#f0f0f0", relief="flat")
                else:
                    lbl = self.day_labels[r][c]
                    lbl.config(text=str(day_num),
                               fg="black" if c != 0 else "red")
                    if day_num == self.selected_day.get() and year == self.year_var.get() and month == self.amharic_months.index(self.month_var.get()) + 1:
                        lbl.config(bg="#ffb732")
                    else:
                        lbl.config(bg="white")
                    day_num += 1

    def on_day_click(self, row, col):
        day_text = self.day_labels[row][col]['text']
        if not day_text:
            return

        self.selected_day.set(int(day_text))
        self.et_d_entry.delete(0, tk.END)
        self.et_d_entry.insert(0, day_text)
        self.et_m_entry.delete(0, tk.END)
        self.et_m_entry.insert(
            0, self.amharic_months.index(self.month_var.get()) + 1)
        self.et_y_entry.delete(0, tk.END)
        self.et_y_entry.insert(0, self.year_var.get())
        self.update_calendar()
        self.convert_to_gc()

    def set_converter_defaults(self, g_date, e_date):
        self.gc_d_entry.insert(0, g_date.day)
        self.gc_m_entry.insert(0, g_date.month)
        self.gc_y_entry.insert(0, g_date.year)
        self.et_d_entry.insert(0, e_date[2])
        self.et_m_entry.insert(0, e_date[1])
        self.et_y_entry.insert(0, e_date[0])

    def convert_to_ec(self):
        try:
            g_date = date(int(self.gc_y_entry.get()), int(
                self.gc_m_entry.get()), int(self.gc_d_entry.get()))
            ey, em, ed = EthiopianCalendar.from_gregorian(g_date)

            self.et_d_entry.delete(0, tk.END)
            self.et_d_entry.insert(0, ed)
            self.et_m_entry.delete(0, tk.END)
            self.et_m_entry.insert(0, em)
            self.et_y_entry.delete(0, tk.END)
            self.et_y_entry.insert(0, ey)

            self.year_var.set(ey)
            self.month_var.set(self.amharic_months[em - 1])
            self.selected_day.set(ed)
            self.update_calendar()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid Gregorian Date: {e}")

    def convert_to_gc(self):
        try:
            ey, em, ed = int(self.et_y_entry.get()), int(
                self.et_m_entry.get()), int(self.et_d_entry.get())
            g_date = EthiopianCalendar.to_gregorian(ey, em, ed)

            self.gc_d_entry.delete(0, tk.END)
            self.gc_d_entry.insert(0, g_date.day)
            self.gc_m_entry.delete(0, tk.END)
            self.gc_m_entry.insert(0, g_date.month)
            self.gc_y_entry.delete(0, tk.END)
            self.gc_y_entry.insert(0, g_date.year)

            self.year_var.set(ey)
            self.month_var.set(self.amharic_months[em - 1])
            self.selected_day.set(ed)
            self.update_calendar()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid Ethiopian Date: {e}")


def main():
    root = tk.Tk()
    if "Nyala" not in font.families():
        print("Warning: 'Nyala' font not found. Amharic text might not render correctly.")
    app = EthiopianCalendarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
