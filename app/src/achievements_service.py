"""
Serwis przyznawania osiągnięć.

- Definicje osiągnięć pobieramy z Firestore (kolekcja 'achievements').
- Przyznane osiągnięcia zapisujemy w polu users.achievements (mapa id -> timestamp) w Firestore.
- Automatyczne przyznawanie jest wyzwalane w hookach w widokach (po utworzeniu usterki,
  po dodaniu/zwrocie wypożyczenia, po oznaczeniu cudzej usterki jako naprawionej).

Uwagi:
- Działa tylko jeśli u użytkownika ustawiono features.achievements_enabled = True.
- Warunki MVP (pod istniejące odznaki):
  • first_report – pierwszy raport usterki przez użytkownika
  • five_reports – co najmniej 5 zgłoszonych usterek przez użytkownika
  • ten_borrows – co najmniej 10 wypożyczeń przypisanych do adresu e‑mail użytkownika (pole 'kontakt')
  • speedy_return – zwrot wypożyczenia tego samego dnia; przypisujemy odznakę wypożyczającemu (po e‑mailu z 'kontakt')
  • helping_hand – użytkownik zmienił status cudzej usterki na 'naprawiona'
"""

from __future__ import annotations

from typing import Optional, Iterable, Dict, Any
from datetime import datetime

from .db_firestore import (
    get_all_achievements, get_achievements_map, COLLECTION_WYPOZYCZENIA,
    get_items_by_filter, get_items_by_filters, _warsaw_now, COLLECTION_LOGS
)
from .db_users import (
    get_user_features, get_user_achievements_map,
    add_user_achievement
)


def _is_feature_enabled(uid: str) -> bool:
    feats = get_user_features(uid) or {}
    return bool(feats.get('achievements_enabled'))


def get_achievements_defs_map() -> dict:
    """Zwraca mapę definicji osiągnięć z bazy danych: id -> definicja."""
    return get_achievements_map()


def ensure_seeded():
    """Dba o istnienie podstawowych definicji w bazie (gdy kolekcja pusta)."""
    from .db_firestore import ensure_default_achievements_seeded
    ensure_default_achievements_seeded()


def maybe_award(uid: str, achievement_id: str) -> bool:
    """Przyznaje osiągnięcie użytkownikowi, jeśli spełnione warunki wstępne.

    Zwraca True, jeśli przyznano (lub już miał) – traktujemy jako sukces idempotentny.
    """
    if not uid:
        return False
    if not _is_feature_enabled(uid):
        return False
    defs = get_achievements_defs_map()
    adef = defs.get(achievement_id)
    if not adef or not adef.get('enabled', True):
        return False
    # idempotencja
    if achievement_id in (get_user_achievements_map(uid) or {}):
        return True
    add_user_achievement(uid, achievement_id)
    return True


def _iter_enabled_defs() -> Iterable[Dict[str, Any]]:
    try:
        for a in get_all_achievements():
            if (a or {}).get('enabled', True):
                yield a
    except Exception:
        # Jeśli nie udało się pobrać — zwróć pustą listę
        return []


def _safe_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return default


def _clamp(val: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(val)))
    except Exception:
        return lo


def _get_user_email(uid: str) -> Optional[str]:
    try:
        from .db_users import get_user_by_uid
        u = get_user_by_uid(uid)
        return (u or {}).get('email')
    except Exception:
        return None


def get_user_achievements_progress(uid: str) -> list[Dict[str, Any]]:
    """Zwraca listę osiągnięć z informacją o postępie dla danego użytkownika.

    Zwracane pola na element:
    - id, name, description, icon, enabled, order, secret
    - earned: bool
    - progress: int (bieżąca wartość)
    - target: int (próg; >=1)
    - percent: int (0..100)
    - masked: bool (sekret + niezdobyte)
    """
    defs_map = get_achievements_defs_map() or {}
    earned_map = get_user_achievements_map(uid) or {}
    email = _get_user_email(uid)

    # Prelicz podstawowe liczniki używane w warunkach
    reports_count = _get_user_reports_count(uid)
    loans_count = _get_loans_count_for_contact(email or '') if email else 0

    items: list[Dict[str, Any]] = []
    for a in sorted(defs_map.values(), key=lambda x: _safe_int((x or {}).get('order'), 9999)):
        if not a or not a.get('enabled', True):
            continue
        aid = a.get('id')
        cond = (a.get('condition') or {})
        ctype = cond.get('type')
        earned = aid in earned_map

        # Domyślnie binary 0/1
        progress = 1 if earned else 0
        target = 1

        if ctype == 'event_count':
            event = cond.get('event')
            threshold = _safe_int(cond.get('threshold'), 1)
            target = max(1, threshold)
            current = 0
            if event == 'report_created':
                current = reports_count
            elif event == 'loan_created':
                current = loans_count
            progress = _clamp(current, 0, target)
        elif ctype in ('item_add_count', 'item_edit_count'):
            threshold = _safe_int(cond.get('threshold'), 1)
            target = max(1, threshold)
            category = (cond.get('category') or '').strip() or None
            if ctype == 'item_add_count':
                current = _count_user_item_adds(uid, category)
            else:
                current = _count_user_item_edits(uid, category)
            progress = _clamp(int(current or 0), 0, target)
        elif ctype in ('speedy_return', 'help_resolve'):
            # Progres binarny — 1 gdy już zdobyto
            progress = 1 if earned else 0
            target = 1
        else:
            # Brak/nieznany condition — traktuj jako binarne
            progress = 1 if earned else 0
            target = 1

        percent = 0 if target <= 0 else int(round(100 * (progress / float(target))))
        masked = bool(a.get('secret')) and not earned

        items.append({
            'id': aid,
            'name': a.get('name'),
            'description': a.get('description'),
            'icon': a.get('icon') or '🏅',
            'enabled': a.get('enabled', True),
            'order': a.get('order'),
            'secret': bool(a.get('secret')),
            'earned': earned,
            'progress': progress,
            'target': target,
            'percent': _clamp(percent, 0, 100),
            'masked': masked,
        })

    return items


def _award_event_count(uid: str, event_name: str, count_value: int):
    """Przyznaje wszystkie osiągnięcia typu event_count spełnione dla danego eventu i licznika."""
    if count_value is None:
        return
    for a in _iter_enabled_defs():
        cond = (a or {}).get('condition') or {}
        if cond.get('type') != 'event_count':
            continue
        if cond.get('event') != event_name:
            continue
        try:
            threshold = int(cond.get('threshold') or 0)
        except Exception:
            threshold = 0
        if threshold and count_value >= threshold:
            maybe_award(uid, a.get('id'))


def _award_simple_event(uid: str, condition_type: str):
    """Przyznaje wszystkie osiągnięcia, których condition.type == condition_type."""
    for a in _iter_enabled_defs():
        cond = (a or {}).get('condition') or {}
        if cond.get('type') == condition_type:
            maybe_award(uid, a.get('id'))


# =========================
#  SPRZĘT – DODANIA I EDYCJE
# =========================

def _count_user_item_adds(uid: str, category: Optional[str] = None) -> int:
    """Zlicza dodania elementów 'sprzet' przez użytkownika (opcjonalnie w danej kategorii)."""
    if not uid:
        return 0
    filters = [
        ('user_id', '==', uid),
        ('action', '==', 'add'),
        ('target_type', '==', 'sprzet'),
    ]
    if category:
        # filtr po kategorii w danych 'after'
        filters.append(('after.category', '==', category))
    try:
        items = get_items_by_filters(COLLECTION_LOGS, filters)
        return len(items or [])
    except Exception:
        return 0


def _count_user_item_edits(uid: str, category: Optional[str] = None) -> int:
    """Zlicza edycje elementów 'sprzet' przez użytkownika (opcjonalnie w danej kategorii).

    Uwaga: jeżeli podano kategorię, akceptujemy zgodność kategorii przed lub po edycji.
    """
    if not uid:
        return 0
    base_filters = [
        ('user_id', '==', uid),
        ('action', '==', 'edit'),
        ('target_type', '==', 'sprzet'),
    ]
    try:
        logs = get_items_by_filters(COLLECTION_LOGS, base_filters)
        if not category:
            return len(logs or [])
        cat = (category or '').strip()
        cnt = 0
        for lg in logs or []:
            after = (lg or {}).get('after') or {}
            before = (lg or {}).get('before') or {}
            if (after.get('category') == cat) or (before.get('category') == cat):
                cnt += 1
        return cnt
    except Exception:
        return 0


def _award_item_adds(uid: str, category: Optional[str]):
    """Przyznaje osiągnięcia typu item_add_count spełnione dla użytkownika (opcjonalnie w danej kategorii)."""
    # Zbierz wymagane kategorie z definicji, aby policzyć raz na kategorię
    needed_cats = set()
    defs = []
    for a in _iter_enabled_defs():
        cond = (a or {}).get('condition') or {}
        if cond.get('type') == 'item_add_count':
            defs.append((a, cond))
            needed_cats.add((cond.get('category') or '').strip() or None)
    if not defs:
        return
    # Zbuduj mapa countów
    counts: Dict[Optional[str], int] = {}
    for cat in needed_cats:
        # jeśli przekazano konkretną kategorię zdarzenia, a definicja oczekuje innej, to i tak policzymy,
        # bo użytkownik mógł mieć wcześniejsze dodania w innej kategorii
        counts[cat] = _count_user_item_adds(uid, cat)
    # Oceń progi
    for a, cond in defs:
        thr = _safe_int(cond.get('threshold'), 0)
        cat = (cond.get('category') or '').strip() or None
        val = counts.get(cat, 0)
        if thr and val >= thr:
            maybe_award(uid, a.get('id'))


def _award_item_edits(uid: str, category: Optional[str]):
    """Przyznaje osiągnięcia typu item_edit_count spełnione dla użytkownika (opcjonalnie w danej kategorii)."""
    needed_cats = set()
    defs = []
    for a in _iter_enabled_defs():
        cond = (a or {}).get('condition') or {}
        if cond.get('type') == 'item_edit_count':
            defs.append((a, cond))
            needed_cats.add((cond.get('category') or '').strip() or None)
    if not defs:
        return
    counts: Dict[Optional[str], int] = {}
    for cat in needed_cats:
        counts[cat] = _count_user_item_edits(uid, cat)
    for a, cond in defs:
        thr = _safe_int(cond.get('threshold'), 0)
        cat = (cond.get('category') or '').strip() or None
        val = counts.get(cat, 0)
        if thr and val >= thr:
            maybe_award(uid, a.get('id'))


def maybe_award_on_item_created(actor_uid: str, category: Optional[str]):
    """Wywoływane po utworzeniu nowego elementu SPRZĘTU przez użytkownika."""
    if not actor_uid or not _is_feature_enabled(actor_uid):
        return
    _award_item_adds(actor_uid, category)


def maybe_award_on_item_edited(actor_uid: str, category: Optional[str]):
    """Wywoływane po edycji elementu SPRZĘTU przez użytkownika."""
    if not actor_uid or not _is_feature_enabled(actor_uid):
        return
    _award_item_edits(actor_uid, category)


# =========================
#  RAPORTY USTEREK
# =========================

def _get_user_reports_count(uid: str) -> int:
    from .db_firestore import COLLECTION_USTERKI
    items = get_items_by_filter(COLLECTION_USTERKI, 'user_id', '==', uid)
    return len(items)


def maybe_award_on_report_created(uid: str):
    """Wywoływane po utworzeniu nowej usterki przez użytkownika."""
    if not uid or not _is_feature_enabled(uid):
        return
    cnt = _get_user_reports_count(uid)
    # Nowy generczny evaluator
    _award_event_count(uid, 'report_created', cnt)
    # Kompatybilność z istniejącymi bez-condition (jeśli nadal istnieją takie rekordy)
    if cnt >= 1:
        maybe_award(uid, 'first_report')
    if cnt >= 5:
        maybe_award(uid, 'five_reports')


# =========================
#  WYPOŻYCZENIA
# =========================

def _find_user_by_email(email: Optional[str]):
    if not email:
        return None
    from .db_users import get_user_by_email
    try:
        return get_user_by_email(email)
    except Exception:
        return None


def _get_loans_count_for_contact(email: str) -> int:
    if not email:
        return 0
    items = get_items_by_filter(COLLECTION_WYPOZYCZENIA, 'kontakt', '==', email)
    return len(items)


def maybe_award_on_loan_created(borrower_email: Optional[str]):
    """Wywoływane po dodaniu wypożyczenia. Próbuje dopasować użytkownika po e‑mailu w polu 'kontakt'."""
    user = _find_user_by_email(borrower_email)
    if not user:
        return
    uid = user.get('id')
    if not _is_feature_enabled(uid):
        return
    cnt = _get_loans_count_for_contact(borrower_email or '')
    # Genericzny evaluator: liczba wypożyczeń
    _award_event_count(uid, 'loan_created', cnt)
    # Kompatybilność wstecz
    if cnt >= 10:
        maybe_award(uid, 'ten_borrows')


def maybe_award_on_loan_return(loan: dict):
    """Wywoływane po oznaczeniu zwrotu. Jeśli zwrot nastąpił tego samego dnia co wypożyczenie,
    przyznaj odznakę 'speedy_return' wypożyczającemu (dopasowanie po e‑mailu 'kontakt')."""
    if not loan:
        return
    ts: datetime = loan.get('timestamp')
    borrower_email: Optional[str] = loan.get('kontakt')
    if not ts or not borrower_email:
        return
    # Porównanie dat (lokalne, jak zapisywane są timestampy)
    now = _warsaw_now()
    try:
        same_day = (now.date() == ts.date())
    except Exception:
        same_day = False
    if not same_day:
        return
    user = _find_user_by_email(borrower_email)
    if not user:
        return
    uid = user.get('id')
    # Genericzny evaluator: szybki zwrot
    _award_simple_event(uid, 'speedy_return')
    # Kompatybilność wstecz
    maybe_award(uid, 'speedy_return')


# =========================
#  POMOC W ROZWIĄZANIU USTERKI
# =========================

def maybe_award_on_help_resolve(actor_uid: str, usterka: dict):
    """Przyznaje 'helping_hand' jeśli aktor oznaczył jako naprawioną cudzą usterkę."""
    if not actor_uid or not _is_feature_enabled(actor_uid):
        return
    owner_uid = (usterka or {}).get('user_id')
    if not owner_uid or owner_uid == actor_uid:
        return
    _award_simple_event(actor_uid, 'help_resolve')
    # Kompatybilność wstecz
    maybe_award(actor_uid, 'helping_hand')
