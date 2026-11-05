#!/usr/bin/env python3
"""
SUITE DE TESTS DE CARACTERIZACIÓN Y REGRESIÓN DE MAHĀ-DVĀDAŚĪ
Valida:
1. Delhi Vyañjulī (2026-08-23 a 2026-08-25)
2. París Negative Control (2026-08-23 a 2026-08-25)
3. Contrato estricto y valores de retorno de IsMhd58()
4. Test unitario de Sentinel (Gaura Dvādaśī sin nakṣatra MHD no debe secuestrar el flujo)
5. Casos reales verificados de cada clase de Mahā-dvādaśī:
   - Vijaya (EV_VIJAYA)
   - Trisprsa (EV_TRISPRSA)
   - Unmilani (EV_UNMILANI)
   - Paksavardhini (EV_PAKSAVARDHINI)
   - Vyanjuli histórica (EV_VYANJULI)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gaurabda.GCLocation import GCLocation
from gaurabda.GCGregorianDate import GCGregorianDate
from gaurabda.TCalendar import TCalendar
from gaurabda.GCCalendarDay import GCCalendarDay
from gaurabda.GCEnums.MahadvadasiType import *
from gaurabda.GCEnums.FastType import *
from gaurabda.GCEnums.TithiId import *


class TestIsMhd58Contract(unittest.TestCase):
    """Auditoría exhaustiva del contrato de IsMhd58()"""

    def setUp(self):
        self.cal = TCalendar()
        self.cal.m_data = [GCCalendarDay(), GCCalendarDay()]

    def test_ismhd58_return_values_are_nonzero(self):
        """Verifica que IsMhd58 NUNCA devuelve 0, sino EV_NULL (256) u otros enum > 0x100"""
        t = self.cal.m_data[0]
        u = self.cal.m_data[1]

        # Caso 1: Nakshatras diferentes
        t.astrodata.nTithi = TITHI_GAURA_DVADASI
        t.astrodata.nNaksatra = 1
        u.astrodata.nNaksatra = 2
        res = self.cal.IsMhd58(0)
        self.assertEqual(res, EV_NULL)
        self.assertEqual(res, 0x100)
        self.assertNotEqual(res, 0)

        # Caso 2: Paksa != 1 (Krsna Paksa, nTithi < 15)
        t.astrodata.nTithi = TITHI_KRSNA_DVADASI
        t.astrodata.nNaksatra = 6
        u.astrodata.nNaksatra = 6
        res = self.cal.IsMhd58(0)
        self.assertEqual(res, EV_NULL)
        self.assertNotEqual(res, 0)

        # Caso 3: Gaura Paksa, mismo naksatra, pero naksatra sin MHD (ej. Asvini=0)
        t.astrodata.nTithi = TITHI_GAURA_DVADASI
        t.astrodata.nTithiSunset = TITHI_GAURA_DVADASI
        t.astrodata.nNaksatra = 0
        u.astrodata.nNaksatra = 0
        res = self.cal.IsMhd58(0)
        self.assertEqual(res, EV_NULL)
        self.assertNotEqual(res, 0)

    def test_ismhd58_nakshatra_mhd_detection(self):
        """Verifica detección de las 4 Nakshatra Mahadvadasis cuando las condiciones se cumplen"""
        t = self.cal.m_data[0]
        u = self.cal.m_data[1]
        t.astrodata.nTithi = TITHI_GAURA_DVADASI
        t.astrodata.nTithiSunset = TITHI_GAURA_DVADASI

        # Punarvasu (6) -> EV_JAYA (0x107 = 263)
        t.astrodata.nNaksatra = 6
        u.astrodata.nNaksatra = 6
        self.assertEqual(self.cal.IsMhd58(0), EV_JAYA)
        self.assertEqual(EV_JAYA, 0x107)

        # Rohini (3) -> EV_JAYANTI (0x108 = 264)
        t.astrodata.nNaksatra = 3
        u.astrodata.nNaksatra = 3
        self.assertEqual(self.cal.IsMhd58(0), EV_JAYANTI)
        self.assertEqual(EV_JAYANTI, 0x108)

        # Pusyami (7) -> EV_PAPA_NASINI (0x109 = 265)
        t.astrodata.nNaksatra = 7
        u.astrodata.nNaksatra = 7
        self.assertEqual(self.cal.IsMhd58(0), EV_PAPA_NASINI)
        self.assertEqual(EV_PAPA_NASINI, 0x109)

        # Sravana (21) -> EV_VIJAYA (0x110 = 272)
        t.astrodata.nNaksatra = 21
        u.astrodata.nNaksatra = 21
        self.assertEqual(self.cal.IsMhd58(0), EV_VIJAYA)
        self.assertEqual(EV_VIJAYA, 0x110)


class TestSentinelBranching(unittest.TestCase):
    """Test unitario de Sentinel: Gaura Dvadasi donde IsMhd58() == EV_NULL no debe secuestrar el flujo"""

    def test_sentinel_does_not_claim_mhd(self):
        """Si tithi=Gaura Dvadasi sunrise & sunset pero IsMhd58() == EV_NULL,
        NO debe clasificarse como Nakshatra MHD ni escribir EV_NULL como nMhdType."""
        loc = GCLocation(city="Delhi", country='', latitude=28.6667, longitude=77.2167, tzname="Asia/Calcutta")
        start = GCGregorianDate()
        start.day = 21; start.month = 8; start.year = 2026; start.tzone = loc.m_fTimezone
        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 8)

        # Buscar el día 24 de agosto
        day_24 = None
        for d in cal.days_iter():
            if d.date.month == 8 and d.date.day == 24:
                day_24 = d
                break

        self.assertIsNotNone(day_24)
        self.assertEqual(day_24.nMhdType, EV_VYANJULI, "El día 24 de agosto en Delhi debe ser EV_VYANJULI, no EV_NULL")


class TestEkadasiIntegration(unittest.TestCase):
    """Tests de integración con cálculos astronómicos reales de calendario"""

    def test_delhi_vyanjuli_august_2026(self):
        """OBLIGATORIO #1: Delhi, 23-25 agosto 2026 debe observar Vyañjulī Mahā-dvādaśī el 24 de agosto"""
        loc = GCLocation(city="Delhi", country="India", latitude=28.6667, longitude=77.2167, tzname="Asia/Calcutta")
        start = GCGregorianDate()
        start.day = 21; start.month = 8; start.year = 2026; start.tzone = loc.m_fTimezone

        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 8)

        days = {d.date.day: d for d in cal.days_iter() if d.date.month == 8}

        d23 = days[23]
        d24 = days[24]
        d25 = days[25]

        # 23 de agosto: NO debe haber ayuno de Ekadasi (pasa al 24 por Vyanjuli)
        self.assertEqual(d23.nFastType, FAST_NULL, "El 23 de agosto en Delhi no debe ser día de ayuno")
        self.assertFalse(d23.ekadasi_parana, "El 23 de agosto no es parana")

        # 24 de agosto: Ayuno por Vyañjulī Mahā-dvādaśī
        self.assertEqual(d24.nFastType, FAST_EKADASI, "El 24 de agosto en Delhi DEBE ser día de ayuno (FAST_EKADASI)")
        self.assertEqual(d24.nMhdType, EV_VYANJULI, "El 24 de agosto en Delhi DEBE ser EV_VYANJULI")
        self.assertFalse(d24.ekadasi_parana, "El 24 de agosto no es parana")

        # 25 de agosto: Pāraṇa
        self.assertEqual(d25.nFastType, FAST_NULL, "El 25 de agosto es el día de romper el ayuno")
        self.assertTrue(d25.ekadasi_parana, "El 25 de agosto DEBE ser parana")

    def test_paris_negative_control_august_2026(self):
        """OBLIGATORIO #2: París, 23-25 agosto 2026 debe observar Śuddha Ekādaśī el 23 de agosto (Negative Control)"""
        loc = GCLocation(city="Paris", country="France", latitude=48.8567, longitude=2.3508, tzname="Europe/Paris")
        start = GCGregorianDate()
        start.day = 21; start.month = 8; start.year = 2026; start.tzone = loc.m_fTimezone

        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 8)

        days = {d.date.day: d for d in cal.days_iter() if d.date.month == 8}

        d23 = days[23]
        d24 = days[24]
        d25 = days[25]

        # 23 de agosto: Ayuno normal Śuddha Ekādaśī
        self.assertEqual(d23.nFastType, FAST_EKADASI, "El 23 de agosto en París DEBE ser ayuno (FAST_EKADASI)")
        self.assertEqual(d23.nMhdType, EV_SUDDHA, "El 23 de agosto en París DEBE ser EV_SUDDHA")

        # 24 de agosto: Pāraṇa
        self.assertEqual(d24.nFastType, FAST_NULL, "El 24 de agosto en París es parana")
        self.assertTrue(d24.ekadasi_parana, "El 24 de agosto en París DEBE ser parana")

        # 25 de agosto: Día regular (Trayodasi)
        self.assertEqual(d25.nFastType, FAST_NULL)
        self.assertFalse(d25.ekadasi_parana)

    def test_other_mhd_varieties(self):
        """Verificación de otras variedades reales de Mahā-dvādaśī"""
        loc = GCLocation(city="Mayapur", country="India", latitude=23.42, longitude=88.38, tzname="Asia/Calcutta")

        # 1. Vijaya (EV_VIJAYA): 2027-09-12 en Mayapur
        start = GCGregorianDate()
        start.day = 10; start.month = 9; start.year = 2027; start.tzone = loc.m_fTimezone
        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 5)
        d_vijaya = [d for d in cal.days_iter() if d.date.month == 9 and d.date.day == 12][0]
        self.assertEqual(d_vijaya.nMhdType, EV_VIJAYA, "2027-09-12 debe ser EV_VIJAYA")
        self.assertEqual(d_vijaya.nFastType, FAST_EKADASI, "2027-09-12 debe tener ayuno")

        # 2. Trisprsa (EV_TRISPRSA): 2020-05-04 en Mayapur
        start = GCGregorianDate()
        start.day = 1; start.month = 5; start.year = 2020; start.tzone = loc.m_fTimezone
        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 6)
        d_tri = [d for d in cal.days_iter() if d.date.month == 5 and d.date.day == 4][0]
        self.assertEqual(d_tri.nMhdType, EV_TRISPRSA, "2020-05-04 debe ser EV_TRISPRSA")
        self.assertEqual(d_tri.nFastType, FAST_EKADASI)

        # 3. Unmilani (EV_UNMILANI): 2022-08-23 en Mayapur
        start = GCGregorianDate()
        start.day = 20; start.month = 8; start.year = 2022; start.tzone = loc.m_fTimezone
        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 6)
        d_unmilani = [d for d in cal.days_iter() if d.date.month == 8 and d.date.day == 23][0]
        self.assertEqual(d_unmilani.nMhdType, EV_UNMILANI, "2022-08-23 debe ser EV_UNMILANI")
        self.assertEqual(d_unmilani.nFastType, FAST_EKADASI)

        # 4. Paksavardhini (EV_PAKSAVARDHINI): 2023-09-11 en Mayapur
        start = GCGregorianDate()
        start.day = 9; start.month = 9; start.year = 2023; start.tzone = loc.m_fTimezone
        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 5)
        d_paksa = [d for d in cal.days_iter() if d.date.month == 9 and d.date.day == 11][0]
        self.assertEqual(d_paksa.nMhdType, EV_PAKSAVARDHINI, "2023-09-11 debe ser EV_PAKSAVARDHINI")
        self.assertEqual(d_paksa.nFastType, FAST_EKADASI)

        # 5. Vyanjuli histórica (EV_VYANJULI): 2024-11-27 en Mayapur
        start = GCGregorianDate()
        start.day = 25; start.month = 11; start.year = 2024; start.tzone = loc.m_fTimezone
        cal = TCalendar()
        cal.CalculateCalendar(loc, start, 5)
        d_vyan = [d for d in cal.days_iter() if d.date.month == 11 and d.date.day == 27][0]
        self.assertEqual(d_vyan.nMhdType, EV_VYANJULI, "2024-11-27 debe ser EV_VYANJULI")
        self.assertEqual(d_vyan.nFastType, FAST_EKADASI)

    def test_suddha_ekadasi_not_labeled_mahadvadasi_and_parana_window(self):
        """Verifica que un Śuddha Ekādaśī puro (Rama Ekadasi en Delhi 2026-11-05) NO tenga evento Maha-dvadasi
        y que su Parana en Dvādaśī (2026-11-06) sea matutino (06:36 - 10:15) y NUNCA hasta el atardecer (17:32)."""
        from gaurabda.GCLocationList import FindLocation
        loc = FindLocation(city='Delhi', country='India')
        cal = TCalendar()
        start = GCGregorianDate(year=2026, month=11, day=1)
        cal.CalculateCalendar(loc, start, 10)

        d5 = [d for d in cal.days_iter() if d.date.month == 11 and d.date.day == 5][0]
        d6 = [d for d in cal.days_iter() if d.date.month == 11 and d.date.day == 6][0]

        # Día 5 de nov: Ayuno de Rama Ekadasi puro
        self.assertEqual(d5.nFastType, FAST_EKADASI)
        event_names_d5 = [e['text'] for e in d5.dayEvents]
        self.assertIn("Fasting for Rama Ekadasi", event_names_d5)
        self.assertNotIn("Maha-dvadasi", event_names_d5, "Un Śuddha Ekādaśī puro en día de Ekādaśī NO debe llevar 'Maha-dvadasi'")

        # Día 6 de nov: Día de Parana
        self.assertTrue(d6.ekadasi_parana)
        self.assertAlmostEqual(d6.eparana_time1, 6.61, places=1) # ~06:36 AM
        self.assertAlmostEqual(d6.eparana_time2, 10.25, places=1) # ~10:15 AM
        self.assertLess(d6.eparana_time2, 12.0, "Parana DEBE terminar por la mañana, no al atardecer")
        event_names_d6 = [e['text'] for e in d6.dayEvents]
        self.assertTrue(any("Break fast 06:36 - 10:15" in t for t in event_names_d6))


if __name__ == '__main__':
    unittest.main()
