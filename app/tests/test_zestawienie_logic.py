import unittest

import sys
import os

# Dodaj ścieżkę do app/src
sys.path.append(os.path.join(os.getcwd(), 'app'))

from src.db_firestore import CATEGORIES

class TestZestawienieLogic(unittest.TestCase):
    def test_namioty_zelastwo_logic(self):
        # Mockowanie danych
        items = [
            {'category': CATEGORIES['NAMIOT'], 'typ': 'NS'},
            {'category': CATEGORIES['NAMIOT'], 'typ': 'NS'},
            {'category': CATEGORIES['NAMIOT'], 'typ': '10-tka'},
            {'category': CATEGORIES['ZELASTWO'], 'do_czego': 'NS', 'ilosc': 1},
            {'category': CATEGORIES['ZELASTWO'], 'do_czego': 'NS', 'ilosc': '1'},
            {'category': CATEGORIES['ZELASTWO'], 'do_czego': '10-tka', 'ilosc': 0},
        ]
        
        # Symulacja logiki z views.py
        n_stats = {}
        for n in [i for i in items if i.get('category') == CATEGORIES['NAMIOT']]:
            t = n.get('typ', 'Nieokreślony')
            n_stats[t] = n_stats.get(t, 0) + 1
            
        z_stats = {}
        for z in [i for i in items if i.get('category') == CATEGORIES['ZELASTWO']]:
            t = z.get('do_czego', 'Nieokreślone')
            q = z.get('ilosc', 0)
            try: q = int(q)
            except (ValueError, TypeError): q = 0
            z_stats[t] = z_stats.get(t, 0) + q
            
        self.assertEqual(n_stats['NS'], 2)
        self.assertEqual(n_stats['10-tka'], 1)
        self.assertEqual(z_stats['NS'], 2)
        self.assertEqual(z_stats['10-tka'], 0)
        
    def test_kanadyjki_logic(self):
        items = [
            {'category': CATEGORIES['KANADYJKI'], 'nazwa': 'Kanadyjka stara'},
            {'category': CATEGORIES['KANADYJKI'], 'nazwa': 'Kanadyjka nowa'},
            {'category': CATEGORIES['KANADYJKI'], 'nazwa': 'Zestaw naprawczy kanadyjek', 'ilosc': 1},
        ]
        
        k = [i for i in items if i.get('category') == CATEGORIES['KANADYJKI'] and 'zestaw naprawczy' not in (i.get('nazwa') or '').lower()]
        r = [i for i in items if i.get('category') == CATEGORIES['KANADYJKI'] and 'zestaw naprawczy' in (i.get('nazwa') or '').lower()]
        
        k_c = len(k)
        r_c = sum(int(i.get('ilosc', 0)) for i in r if str(i.get('ilosc', '')).isdigit())
        
        self.assertEqual(k_c, 2)
        self.assertEqual(r_c, 1)

if __name__ == '__main__':
    unittest.main()
