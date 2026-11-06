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


if __name__ == '__main__':
    unittest.main()
