from datetime import date, timedelta


class EthiopianCalendar:
    MONTH_NAMES = {
        1: ("Meskarem", "መስከረም"), 2: ("Tikimt", "ጥቅምት"), 3: ("Hidar", "ኅዳር"),
        4: ("Tahsas", "ታኅሣሥ"), 5: ("Tir", "ጥር"), 6: ("Yekatit", "የካቲት"),
        7: ("Megabit", "መጋቢት"), 8: ("Miyazia", "ሚያዝያ"), 9: ("Ginbot", "ግንቦት"),
        10: ("Sene", "ሰኔ"), 11: ("Hamle", "ሐምሌ"), 12: ("Nehasse", "ነሐሴ"),
        13: ("Pagume", "ጳጉሜ")
    }

    @staticmethod
    def is_ethiopian_leap(year):
        # Ethiopian leap year occurs every 4 years without exception
        return (year + 1) % 4 == 0

    @classmethod
    def to_gregorian(cls, ey, em, ed):
        """Converts Ethiopian (Y, M, D) to a Python date object."""
        # Find the Gregorian year the Ethiopian year started in
        g_year_start = ey + 7

        # Determine if the previous Pagume had 6 days (meaning New Year is Sept 12)
        # This happens if the Ethiopian year was a leap year
        new_year_day = 12 if cls.is_ethiopian_leap(ey - 1) else 11

        anchor = date(g_year_start, 9, new_year_day)
        days_passed = ((em - 1) * 30) + (ed - 1)

        return anchor + timedelta(days=days_passed)

    @classmethod
    def from_gregorian(cls, g_date):
        """Converts a Python date object to Ethiopian (Y, M, D)."""
        year, month, day = g_date.year, g_date.month, g_date.day

        # New Year's Day (Sept 11 or 12)
        new_year_day = 12 if (year % 4 == 0) else 11

        # Calculate Ethiopian Year
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


# --- Testing the Class ---
today = date.today()
ey, em, ed = EthiopianCalendar.from_gregorian(today)

print(f"Today (Gregorian): {today}")
print(
    f"Today (Ethiopian): {ed} {EthiopianCalendar.MONTH_NAMES[em][0]} ({EthiopianCalendar.MONTH_NAMES[em][1]}) {ey}")

# Convert back to verify
rev_g = EthiopianCalendar.to_gregorian(ey, em, ed)
print(f"Back to Gregorian: {rev_g}")
