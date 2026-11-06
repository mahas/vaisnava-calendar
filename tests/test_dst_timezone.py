import unittest
from gaurabda.GCGregorianDate import GCGregorianDate
from gaurabda import GCTimeZone, GCLocationList
from gaurabda.TCalendar import TCalendar


class TestDSTTimezone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        GCTimeZone.LoadFile('')
        GCLocationList.OpenFile('')

    def test_paris_dst_transitions_2026(self):
        """In Paris (Europe/Paris), DST starts on the last Sunday of March (29 Mar 2026)
        and ends on the last Sunday of October (25 Oct 2026).
        November, December, January, February must NEVER have DST."""
        tz = GCTimeZone.GetTimeZone(name='Europe/Paris')

        # Winter (Jan, Feb)
        for m in [1, 2]:
            vc = GCGregorianDate(year=2026, month=m, day=15)
            vc.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc, tz), 0, f"Month {m} should have no DST")

        # March transition (Last Sunday of March 2026 is March 29)
        vc_pre = GCGregorianDate(year=2026, month=3, day=28)
        vc_pre.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_pre, tz), 0, "28 Mar 2026 should be standard time")

        vc_start = GCGregorianDate(year=2026, month=3, day=29)
        vc_start.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_start, tz), 1, "29 Mar 2026 should be summer time")

        # Summer (Apr - Sep)
        for m in range(4, 10):
            vc = GCGregorianDate(year=2026, month=m, day=15)
            vc.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc, tz), 1, f"Month {m} should have DST")

        # October transition (Last Sunday of October 2026 is October 25)
        vc_oct_pre = GCGregorianDate(year=2026, month=10, day=24)
        vc_oct_pre.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_oct_pre, tz), 1, "24 Oct 2026 should still have DST")

        vc_oct_end = GCGregorianDate(year=2026, month=10, day=25)
        vc_oct_end.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_oct_end, tz), 0, "25 Oct 2026 should revert to standard time")

        vc_oct_post = GCGregorianDate(year=2026, month=10, day=26)
        vc_oct_post.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_oct_post, tz), 0, "26 Oct 2026 should be standard time")

        # Winter (Nov, Dec) - Critical regression test
        for m in [11, 12]:
            for d in [1, 5, 6, 15, 28]:
                vc = GCGregorianDate(year=2026, month=m, day=d)
                vc.InitWeekDay()
                self.assertEqual(GCTimeZone.GetDaylightBias(vc, tz), 0,
                                 f"Date 2026-{m:02d}-{d:02d} in Paris must NOT have DST")

    def test_southern_hemisphere_dst(self):
        """In Sydney (Australia/Sydney), DST is active during Southern Summer (Oct to Apr).
        June/July must be standard time (0), while Jan/Nov must have DST (1)."""
        tz = GCTimeZone.GetTimeZone(name='Australia/Sydney')

        vc_jan = GCGregorianDate(year=2026, month=1, day=15)
        vc_jan.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_jan, tz), 1, "Sydney in January should have DST")

        vc_jun = GCGregorianDate(year=2026, month=6, day=15)
        vc_jun.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_jun, tz), 0, "Sydney in June should NOT have DST")

        vc_nov = GCGregorianDate(year=2026, month=11, day=15)
        vc_nov.InitWeekDay()
        self.assertEqual(GCTimeZone.GetDaylightBias(vc_nov, tz), 1, "Sydney in November should have DST")

    def test_paris_rama_ekadasi_nov_2026_calendar(self):
        """Verify Paris calendar for Rama Ekadasi in November 2026:
        - Nov 5: Fasting for Rama Ekadasi, hasDST = 0
        - Nov 6: Parana at 07:45 - 10:57 (LT), hasDST = 0, no false (DST) annotation."""
        paris = GCLocationList.FindLocation('Paris', 'France')
        self.assertIsNotNone(paris)

        start = GCGregorianDate(year=2026, month=11, day=4)
        cal = TCalendar()
        cal.CalculateCalendar(paris, start, 3)

        days = list(cal.days_iter())
        self.assertEqual(len(days), 3)

        day4, day5, day6 = days[0], days[1], days[2]

        # Nov 4 (Dasami-viddha at arunodaya, so NO fast)
        self.assertEqual(day4.nFastType, 0)
        self.assertEqual(day4.hasDST, 0)

        # Nov 5 (Paksa-vardhini Mahadvadasi / Rama Ekadasi fasting)
        self.assertEqual(day5.nFastType, 518)
        self.assertEqual(day5.hasDST, 0)
        day5_events = [e['text'] for e in day5.dayEvents]
        self.assertIn('Fasting for Rama Ekadasi', day5_events)

        # Nov 6 (Parana morning)
        self.assertEqual(day6.hasDST, 0)
        self.assertTrue(day6.ekadasi_parana)
        # Parana start should be 07:45 AM (approx 7.75h)
        self.assertAlmostEqual(day6.eparana_time1, 7.756, places=2)
        # Parana end should be 10:57 AM (approx 10.96h)
        self.assertAlmostEqual(day6.eparana_time2, 10.963, places=2)

        # Event text should say (LT) not (DST)
        day6_events = [e['text'] for e in day6.dayEvents]
        self.assertTrue(any('Break fast 07:45 - 10:57 (LT)' in ev for ev in day6_events),
                        f"Expected parana string with (LT), got: {day6_events}")


    def test_multi_year_european_dst_transitions(self):
        """Verify that DST transitions in Europe (Paris) work dynamically for all future years (2024 to 2035):
        - Last Sunday of March switches to Summer Time (bias = 1).
        - Last Sunday of October switches back to Winter / Standard Time (bias = 0).
        - November, December, January, February always have bias = 0 in every year."""
        tz = GCTimeZone.GetTimeZone(name='Europe/Paris')

        from gaurabda.GCGregorianDate import GetMonthMaxDays
        for year in range(2024, 2036):
            # 1. October transition: find last Sunday of October
            last_oct_day = GetMonthMaxDays(year, 10)
            last_sun_oct = None
            for d in range(last_oct_day, 20, -1):
                vc = GCGregorianDate(year=year, month=10, day=d)
                vc.InitWeekDay()
                if vc.dayOfWeek == 0:
                    last_sun_oct = d
                    break

            # Day before last Sunday of Oct: Summer Time
            vc_oct_pre = GCGregorianDate(year=year, month=10, day=last_sun_oct - 1)
            vc_oct_pre.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc_oct_pre, tz), 1,
                             f"Year {year}: {last_sun_oct-1} Oct should be summer time")

            # Last Sunday of Oct: reverts to Standard/Winter Time
            vc_oct_post = GCGregorianDate(year=year, month=10, day=last_sun_oct)
            vc_oct_post.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc_oct_post, tz), 0,
                             f"Year {year}: {last_sun_oct} Oct should revert to winter time")

            # 2. Winter months (Nov, Dec, Jan, Feb): strictly Standard Time in all years
            for m in [11, 12, 1, 2]:
                vc_winter = GCGregorianDate(year=year, month=m, day=15)
                vc_winter.InitWeekDay()
                self.assertEqual(GCTimeZone.GetDaylightBias(vc_winter, tz), 0,
                                 f"Year {year}, Month {m} must NOT have DST")

            # 3. Summer months (Apr, May, Jun, Jul, Aug, Sep): strictly Summer Time
            for m in range(4, 10):
                vc_summer = GCGregorianDate(year=year, month=m, day=15)
                vc_summer.InitWeekDay()
                self.assertEqual(GCTimeZone.GetDaylightBias(vc_summer, tz), 1,
                                 f"Year {year}, Month {m} must have DST")

    def test_north_america_multi_year_dst_transitions(self):
        """Verify that DST transitions in North America (New York) work dynamically:
        - DST begins on the 2nd Sunday of March (bias = 1).
        - DST continues throughout all of October (unlike Europe which ends in Oct).
        - DST ends on the 1st Sunday of November (reverts to bias = 0).
        - December, January, February always have bias = 0 in every year."""
        tz = GCTimeZone.GetTimeZone(name='America/New_York')

        for year in range(2024, 2036):
            # 1. March: 2nd Sunday of March
            sundays_mar = []
            for d in range(1, 15):
                vc = GCGregorianDate(year=year, month=3, day=d)
                vc.InitWeekDay()
                if vc.dayOfWeek == 0:
                    sundays_mar.append(d)
            second_sun_mar = sundays_mar[1]

            vc_mar_pre = GCGregorianDate(year=year, month=3, day=second_sun_mar - 1)
            vc_mar_pre.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc_mar_pre, tz), 0,
                             f"Year {year}: Day before 2nd Sun Mar should be Standard Time")

            vc_mar_post = GCGregorianDate(year=year, month=3, day=second_sun_mar)
            vc_mar_post.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc_mar_post, tz), 1,
                             f"Year {year}: 2nd Sun Mar should switch to Summer Time")

            # 2. October: MUST have DST throughout the entire month in North America!
            vc_oct_end = GCGregorianDate(year=year, month=10, day=31)
            vc_oct_end.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc_oct_end, tz), 1,
                             f"Year {year}: 31 Oct in New York MUST still be in Summer Time")

            # 3. November: 1st Sunday of November
            first_sun_nov = None
            for d in range(1, 8):
                vc = GCGregorianDate(year=year, month=11, day=d)
                vc.InitWeekDay()
                if vc.dayOfWeek == 0:
                    first_sun_nov = d
                    break

            if first_sun_nov > 1:
                vc_nov_pre = GCGregorianDate(year=year, month=11, day=first_sun_nov - 1)
                vc_nov_pre.InitWeekDay()
                self.assertEqual(GCTimeZone.GetDaylightBias(vc_nov_pre, tz), 1,
                                 f"Year {year}: Day before 1st Sun Nov should still be Summer Time")

            vc_nov_post = GCGregorianDate(year=year, month=11, day=first_sun_nov)
            vc_nov_post.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc_nov_post, tz), 0,
                             f"Year {year}: 1st Sun Nov must revert to Standard Time")

            # 4. Deep Winter: December, January, February always bias = 0
            for m in [12, 1, 2]:
                vc_winter = GCGregorianDate(year=year, month=m, day=15)
                vc_winter.InitWeekDay()
                self.assertEqual(GCTimeZone.GetDaylightBias(vc_winter, tz), 0,
                                 f"Year {year}, Month {m} in New York must NOT have DST")

    def test_abolished_dst_countries(self):
        """Verify that countries that abolished DST (Mexico, Argentina, Brazil, Turkey, Russia)
        have bias = 0 all year round and accurate permanent UTC offsets."""
        # 1. Mexico City: permanent UTC-6, bias = 0 all year
        mexico_tz = GCTimeZone.GetTimeZone(name='-6:00 America/Mexico_City')
        self.assertEqual(mexico_tz['offset'], -360)
        self.assertEqual(mexico_tz['bias'], 0)
        for m in range(1, 13):
            vc = GCGregorianDate(year=2026, month=m, day=15)
            vc.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc, mexico_tz), 0)

        # 2. Cancun: permanent UTC-5 (Southeastern zone)
        cancun_tz = GCTimeZone.GetTimeZone(name='-5:00 America/Cancun')
        self.assertEqual(cancun_tz['offset'], -300)
        self.assertEqual(cancun_tz['bias'], 0)

        # 3. Argentina (Buenos Aires): permanent UTC-3, bias = 0
        arg_tz = GCTimeZone.GetTimeZone(name='-3:00 America/Argentina/Buenos_Aires')
        self.assertEqual(arg_tz['offset'], -180)
        self.assertEqual(arg_tz['bias'], 0)
        for m in range(1, 13):
            vc = GCGregorianDate(year=2026, month=m, day=15)
            vc.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc, arg_tz), 0)

        # 4. Brazil (Sao Paulo): permanent UTC-3, bias = 0
        brazil_tz = GCTimeZone.GetTimeZone(name='-3:00 America/Sao_Paulo')
        self.assertEqual(brazil_tz['offset'], -180)
        self.assertEqual(brazil_tz['bias'], 0)
        for m in range(1, 13):
            vc = GCGregorianDate(year=2026, month=m, day=15)
            vc.InitWeekDay()
            self.assertEqual(GCTimeZone.GetDaylightBias(vc, brazil_tz), 0)

        # 5. Turkey (Istanbul): permanent UTC+3, bias = 0
        turkey_tz = GCTimeZone.GetTimeZone(name='+3:00 Europe/Istanbul')
        self.assertEqual(turkey_tz['offset'], 180)
        self.assertEqual(turkey_tz['bias'], 0)

        # 6. Russia (Moscow): permanent UTC+3, bias = 0
        moscow_tz = GCTimeZone.GetTimeZone(name='+3:00 Europe/Moscow')
        self.assertEqual(moscow_tz['offset'], 180)
        self.assertEqual(moscow_tz['bias'], 0)


if __name__ == '__main__':
    unittest.main()


