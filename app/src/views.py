from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, current_app
import os
import uuid
import json
import pandas as pd
from werkzeug.utils import secure_filename
from google.cloud import firestore
import qrcode
from io import BytesIO
import html

from . import get_firestore_client
from .auth import login_required, admin_required, quartermaster_required, full_login_required
from .gcs_utils import list_equipment_photos, upload_blob_to_gcs, refresh_urls
from .db_firestore import (
    get_sprzet_item, get_usterki_for_sprzet, get_usterka_item,
    update_usterka, update_sprzet, get_all_sprzet, get_all_usterki, get_items_by_filters,
    COLLECTION_SPRZET, COLLECTION_USTERKI, COLLECTION_WYPOZYCZENIA, add_item, set_item,
    add_log, get_all_logs, update_item, delete_item, CATEGORIES, MAGAZYNY_NAMES,
    add_loan, get_active_loans, get_loans_for_item, mark_loan_returned, _warsaw_now,
    get_all_items, get_item, get_items_by_parent
)
from .exports import export_to_csv, export_to_xlsx, export_to_docx, export_to_pdf, export_qr_codes_pdf
from .id_utils import generate_unique_magazyn_id

views_bp = Blueprint('views', __name__, url_prefix='/')

# Maksymalna liczba błędów pokazywanych użytkownikowi w bulk edit
MAX_DISPLAYED_ERRORS = 5

def process_uploads(files, folder, id_prefix=None):
    """Waliduje i wgrywa pliki do GCS."""
    ALLOWED_MIMES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    MAX_SIZE = 5 * 1024 * 1024
    
    valid_files = [f for f in files if f and f.filename]
    if not valid_files:
        return [], None
        
    saved_urls = []
    for i, f in enumerate(valid_files):
        if f.mimetype not in ALLOWED_MIMES:
            return [], f'Nieobsługiwany typ pliku: {f.filename}'
        
        f.stream.seek(0, os.SEEK_END)
        size = f.stream.tell()
        f.stream.seek(0)
        if size > MAX_SIZE:
            return [], f'Plik za duży (>5MB): {f.filename}'

        if id_prefix:
            import time
            # Dodajemy timestamp, aby uniknąć nadpisywania starych zdjęć o tych samych nazwach
            timestamp = int(time.time())
            blob_name = f"{folder}/{id_prefix}/{id_prefix}_foto{i:02d}_{timestamp}.png"
        else:
            filename = secure_filename(f.filename)
            base, ext = os.path.splitext(filename)
            blob_name = f"{folder}/{base}_{uuid.uuid4().hex[:8]}{ext}"

        url = upload_blob_to_gcs(blob_name, f.stream, f.mimetype)
        saved_urls.append(url)
    return saved_urls, None


def build_user_map(users):
    """
    Tworzy mapowanie user_id -> wyświetlana nazwa użytkownika.
    
    Args:
        users: Lista użytkowników z polami 'id', 'first_name', 'last_name', 'email'
    
    Returns:
        Dict mapujący user_id na wyświetlaną nazwę (imię nazwisko, imię, nazwisko lub email)
    """
    user_map = {}
    for user in users:
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        if first_name and last_name:
            user_map[user['id']] = f"{first_name} {last_name}"
        elif first_name:
            user_map[user['id']] = first_name
        elif last_name:
            user_map[user['id']] = last_name
        else:
            user_map[user['id']] = user.get('email', user['id'])
    return user_map


def _build_qty_suggestions(category_value: str, limit: int = 12) -> list[str]:
    """Buduje krótką listę podpowiedzi ilości na podstawie istniejących elementów."""
    seen: set[str] = set()
    out: list[str] = []
    for s in get_all_sprzet():
        if s.get('category') != category_value:
            continue
        val = s.get('ilosc')
        if val is None:
            continue
        v = str(val).strip()
        if not v:
            continue
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
        if len(out) >= limit:
            break
    return out


def _build_do_czego_suggestions() -> list[str]:
    """Buduje listę podpowiedzi dla pola 'do_czego' (typ namiotu/kanadyjki)."""
    seen: set[str] = set()
    for s in get_all_sprzet():
        cat = s.get('category')
        if cat == CATEGORIES['NAMIOT']:
            val = s.get('typ')
            if val:
                seen.add(str(val).strip())
        elif cat == CATEGORIES['KANADYJKI']:
            val = s.get('material')
            if val:
                seen.add(str(val).strip())
    return sorted(list(seen))


def _normalize_qty_fields(data: dict, category_value: str) -> None:
    """Czyści/normalizuje pola ilości/jednostka w zależności od kategorii."""
    ilosc = (data.get('ilosc') or '').strip() if isinstance(data.get('ilosc'), str) else data.get('ilosc')
    jednostka = (data.get('jednostka') or '').strip() if isinstance(data.get('jednostka'), str) else data.get('jednostka')

    # Usuń puste
    if ilosc in (None, ''):
        data.pop('ilosc', None)
    if jednostka in (None, ''):
        data.pop('jednostka', None)

    # Normalizacja jednostek: wszędzie zapisujemy sztuki jako '.szt'
    if 'jednostka' in data and isinstance(data.get('jednostka'), str):
        j = data['jednostka'].strip().lower()
        if j in {'szt', 'szt.', 'sztuki', '.szt', '.szt.', 'pcs', 'piece', 'pieces'}:
            data['jednostka'] = '.szt'

    # Walidacja jednostki dla żelastwo/kanadyjki (skróty)
    if category_value == CATEGORIES['ZELASTWO']:
        allowed = {'zest.', '.szt'}
        # domyślnie zest.
        if 'jednostka' not in data:
            data['jednostka'] = 'zest.'
        elif data.get('jednostka') not in allowed:
            data.pop('jednostka', None)
            data['jednostka'] = 'zest.'
    if category_value == CATEGORIES['KANADYJKI']:
        # Kanadyjki tylko szt.
        data['jednostka'] = '.szt'

    # Spróbuj zamienić ilość na int gdy wygląda na liczbę
    if 'ilosc' in data:
        try:
            iv = int(str(data['ilosc']).strip())
            if iv < 0:
                data.pop('ilosc', None)
            else:
                data['ilosc'] = iv
        except Exception:
            # zostaw jako string jeśli ktoś wpisze nietypową wartość
            pass

# =======================================================================
#               WIDOKI BAZOWE (Logowanie/Wylogowanie)
# =======================================================================

@views_bp.route('/')
def home():
    """Strona startowa - dostępna bez logowania."""
    return render_template('home.html')

@views_bp.route('/sprzety')
@full_login_required
def sprzet_list():
    parent_id = request.args.get('parent_id')
    search_query = request.args.get('search')
    category = request.args.get('category')

    # Podstawowe filtry
    typ = request.args.get('typ')
    wodoszczelnosc = request.args.get('wodoszczelnosc')
    lokalizacja = request.args.get('lokalizacja')
    oficjalna_ewidencja = request.args.get('oficjalna_ewidencja')

    filters = []
    if category:
        filters.append(('category', '==', category))
    if typ:
        filters.append(('typ', '==', typ))
    if wodoszczelnosc:
        filters.append(('wodoszczelnosc', '==', wodoszczelnosc))
    if lokalizacja:
        filters.append(('lokalizacja', '==', lokalizacja))
    if oficjalna_ewidencja:
        filters.append(('oficjalna_ewidencja', '==', oficjalna_ewidencja))

    if parent_id:
        filters.append(('parent_id', '==', parent_id))

    if filters:
        items = get_items_by_filters(COLLECTION_SPRZET, filters, order_by='__name__', direction=firestore.Query.ASCENDING)
    else:
        # Jeśli nie ma filtrów ani parent_id, a nie jest to wyszukiwanie, pokaż tylko Magazyny
        items = get_all_sprzet(category=CATEGORIES['MAGAZYN']) if not search_query else get_all_sprzet()

    # Wyszukiwanie lokalne (Firestore nie wspiera łatwo full-text search bez zewnętrznych usług)
    if search_query:
        s = search_query.lower().strip()

        # Lista pól, po których chcemy szukać (dużo danych jest opcjonalnych, więc wszystko przez str()).
        # Celowo obejmujemy pola ogólne + specyficzne dla kategorii.
        searchable_fields = [
            'id', 'nazwa', 'typ',
            'przeznaczenie',
            'lokalizacja', 'magazyn_display',
            'informacje', 'uwagi',
            'stan_ogolny',
            'wodoszczelnosc',
            'ilosc', 'jednostka',
            'oficjalna_ewidencja',
            # namioty
            'zapalki', 'kolor_dachu', 'kolor_bokow',
            # żelastwo
            'typ_zelastwa', 'do_czego',
            # kanadyjki
            'material',
            # kompatybilność wsteczna/importy
            'historia',
        ]

        def _matches(item: dict) -> bool:
            for key in searchable_fields:
                try:
                    if s in str(item.get(key, '')).lower():
                        return True
                except Exception:
                    # W razie nietypowych typów danych w polach – pomiń.
                    continue
            return False

        items = [i for i in items if _matches(i)]

    # Pobieramy unikalne wartości do filtrów
    all_items = get_all_sprzet()
    typy = sorted(list(set(i.get('typ') for i in all_items if i.get('typ'))))
    lokalizacje = sorted(list(set(i.get('lokalizacja') for i in all_items if i.get('lokalizacja'))))
    wodoszczelnosci = sorted(list(set(i.get('wodoszczelnosc') for i in all_items if i.get('wodoszczelnosc'))))
    ewidencje = sorted(list(set(i.get('oficjalna_ewidencja') for i in all_items if i.get('oficjalna_ewidencja'))))
    kategorie = CATEGORIES

    # Pobieramy mapę ID -> obiekt dla wszystkich sprzętów
    sprzet_map = {s['id']: s for s in all_items if 'id' in s}

    # Dodajemy informację o nazwie magazynu nadrzędnego
    for item in items:
        # Poczyszczenie po ewentualnych brakach w logice filtrów/importów
        if not item.get('magazyn_display'):
            # Szukamy nadrzędnego magazynu w hierarchii
            curr = item
            visited = set()
            while curr.get('parent_id') and curr['parent_id'] not in visited:
                visited.add(curr['id'])
                parent = sprzet_map.get(curr['parent_id'])
                if not parent:
                    break
                if parent.get('category') == CATEGORIES['MAGAZYN']:
                    item['magazyn_display'] = parent.get('nazwa') or parent.get('id')
                    item['magazyn_id'] = parent.get('id')
                    break
                curr = parent

        if not item.get('magazyn_display'):
            if item.get('lokalizacja'):
                item['magazyn_display'] = item['lokalizacja']
            else:
                item['magazyn_display'] = 'N/A'

        # Ochrona danych osobowych dla Zgłaszającego
        if session.get('user_role') not in ['quartermaster', 'admin']:
            # Sprawdzamy czy jest jakieś aktywne wypożyczenie
            active_loans = get_active_loans()
            item_loans = [l for l in active_loans if l.get('item_id') == item['id']]
            if item_loans:
                item['is_loaned'] = True
            else:
                item['is_loaned'] = False

    # Grupowanie Żelastwa i Kanadyjek (tylko jeśli nie jest to wyszukiwanie globalne i jesteśmy wewnątrz jakiegoś rodzica)
    grouped_items = []
    if parent_id and not search_query:
        # Grupowanie Żelastwa
        zelastwo = [i for i in items if i.get('category') == CATEGORIES['ZELASTWO']]
        other_items = [i for i in items if i.get('category') != CATEGORIES['ZELASTWO'] and i.get('category') != CATEGORIES['KANADYJKI']]
        kanadyjki = [i for i in items if i.get('category') == CATEGORIES['KANADYJKI']]

        # Grupowanie Żelastwa: (do_czego, typ_zelastwa, sprawny)
        zel_groups = {}
        for z in zelastwo:
            key = (z.get('do_czego', 'Inne'), z.get('typ_zelastwa', 'Brak typu'), z.get('sprawny', 'Tak'))
            if key not in zel_groups:
                zel_groups[key] = []
            zel_groups[key].append(z)

        for key, group in zel_groups.items():
            if len(group) > 1:
                # Tworzymy wirtualny obiekt grupy
                rep = group[0]
                grouped_items.append({
                    'id': f"GROUP_ZEL_{rep.get('id')}",
                    'category': CATEGORIES['ZELASTWO'],
                    'nazwa': f"{len(group)}x {rep.get('typ_zelastwa')} ({rep.get('do_czego')}) - {'Sprawne' if key[2] == 'Tak' else 'Niesprawne'}",
                    'is_group': True,
                    'group_ids': [g['id'] for g in group],
                    'magazyn_display': rep.get('magazyn_display'),
                    'oficjalna_ewidencja': rep.get('oficjalna_ewidencja', 'Nie')
                })
            else:
                grouped_items.extend(group)

        # Grupowanie Kanadyjek: (material, sprawny)
        kan_groups = {}
        for k in kanadyjki:
            key = (k.get('material', 'materiałowe'), k.get('sprawny', 'Tak'))
            if key not in kan_groups:
                kan_groups[key] = []
            kan_groups[key].append(k)

        for key, group in kan_groups.items():
            if len(group) > 1:
                rep = group[0]
                grouped_items.append({
                    'id': f"GROUP_KAN_{rep.get('id')}",
                    'category': CATEGORIES['KANADYJKI'],
                    'nazwa': f"{len(group)}x Kanadyjka {key[0]} - {'Sprawna' if key[1] == 'Tak' else 'Niesprawna'}",
                    'is_group': True,
                    'group_ids': [g['id'] for g in group],
                    'magazyn_display': rep.get('magazyn_display'),
                    'oficjalna_ewidencja': rep.get('oficjalna_ewidencja', 'Nie')
                })
            else:
                grouped_items.extend(group)

        grouped_items.extend(other_items)
        items = grouped_items

    # Fast-card: jeśli jesteśmy w folderze (parent_id) -> policz które elementy mają dzieci.
    # Dotyczy: namiot/przedmiot/żelastwo/kanadyjki.
    if parent_id and items:
        children = get_items_by_parent(parent_id)
        parent_ids_with_children = {c.get('parent_id') for c in children if c.get('parent_id')}
        fast_card_cats = {CATEGORIES['NAMIOT'], CATEGORIES['PRZEDMIOT'], CATEGORIES['ZELASTWO'], CATEGORIES['KANADYJKI']}
        for it in items:
            it['has_children'] = (it.get('id') in parent_ids_with_children)
            it['fast_card'] = (it.get('category') in fast_card_cats)

    # Fast-card: ustaw flagi dla namiot/przedmiot/żelastwo/kanadyjki, żeby UI mógł
    # przekierować klik w nazwę prosto na kartę, jeśli element nie ma dzieci.
    if items:
        fast_card_cats = {CATEGORIES['NAMIOT'], CATEGORIES['PRZEDMIOT'], CATEGORIES['ZELASTWO'], CATEGORIES['KANADYJKI']}
        # Minimalnie: sprawdzamy dzieci tylko dla elementów, które mogą używać fast-card.
        candidate_parent_ids = [it.get('id') for it in items if it.get('id') and it.get('category') in fast_card_cats]
        parent_ids_with_children: set[str] = set()
        for pid in candidate_parent_ids:
            try:
                children = get_items_by_parent(pid)
            except Exception:
                children = []
            if children:
                parent_ids_with_children.add(pid)

        for it in items:
            it['fast_card'] = (it.get('category') in fast_card_cats)
            # default False; tylko dla kandydatów liczymy realnie
            it['has_children'] = (it.get('id') in parent_ids_with_children)

    parent_item = get_sprzet_item(parent_id) if parent_id else None
    if parent_item:
        from .gcs_utils import list_equipment_photos, refresh_urls
        zdjecia_z_bazy = parent_item.get('zdjecia')
        if zdjecia_z_bazy is not None:
            parent_item['zdjecia_lista_url'] = refresh_urls(zdjecia_z_bazy)
        else:
            parent_item['zdjecia_lista_url'] = list_equipment_photos(parent_id)

    return render_template('sprzet_list.html',
                           sprzet_list=items,
                           typy=typy,
                           lokalizacje=lokalizacje,
                           wodoszczelnosci=wodoszczelnosci,
                           ewidencje=ewidencje,
                           kategorie=kategorie,
                           parent_item=parent_item,
                           selected_filters=request.args,
                           qr_url=os.getenv('QR_URL'))


# =======================================================================
#                       WIDOKI SPRZĘTU I ZDJĘĆ
# =======================================================================

@views_bp.route('/sprzet/add', methods=['GET', 'POST'])
@quartermaster_required
def sprzet_add():
    if request.method == 'POST':
        category = request.form.get('category')

        # Automatyczne generowanie ID dla wybranych kategorii
        if category in [CATEGORIES['ZELASTWO'], CATEGORIES['KANADYJKI'], CATEGORIES['PRZEDMIOT']]:
            db = get_firestore_client()
            sprzet_id = db.collection(COLLECTION_SPRZET).document().id.upper()
        elif category == CATEGORIES['MAGAZYN']:
            # Human-readable ID based on warehouse name, e.g. MAG_WARSZAWA / MAG_WARSZAWA_2
            magazyn_name = (request.form.get('nazwa') or request.form.get('lokalizacja') or '').strip()
            existing_ids = {s.get('id') for s in get_all_sprzet() if s.get('id')}
            sprzet_id = generate_unique_magazyn_id(magazyn_name, existing_ids)
        else:
            sprzet_id = request.form.get('id', '').strip().upper()

        if not sprzet_id:
            flash('Błąd: Nie wygenerowano lub nie podano ID.', 'danger')
            return redirect(url_for('views.sprzet_add'))

        if get_sprzet_item(sprzet_id):
            flash(f'Sprzęt o ID {sprzet_id} już istnieje!', 'danger')
        else:
            data = {k: v for k, v in request.form.items() if k != 'id'}
            if 'oficjalna_ewidencja' not in data:
                data['oficjalna_ewidencja'] = 'Nie'
            _normalize_qty_fields(data, category)

            # Obsługa zdjęć także przy dodawaniu
            urls, err = process_uploads(request.files.getlist('nowe_zdjecia'), 'sprzet', sprzet_id)
            if err:
                flash(err, 'warning')
            if urls:
                data['zdjecia'] = urls

            set_item(COLLECTION_SPRZET, sprzet_id, data)
            add_log(session.get('user_id'), 'add', 'sprzet', sprzet_id, after=data)
            flash(f'Sprzęt {sprzet_id} został dodany.', 'success')
            return redirect(url_for('views.sprzet_list'))

    # Filtrujemy potencjalnych rodziców: tylko Magazyny i Półki/Skrzynie
    potential_parents = [s for s in get_all_sprzet() if s.get('category') in [CATEGORIES['MAGAZYN'], CATEGORIES['POLKA']]]

    return render_template('sprzet_edit.html',
                           sprzet=None,
                           categories=CATEGORIES,
                           magazyny_names=MAGAZYNY_NAMES,
                           all_items=potential_parents,
                           qty_suggestions_zelastwo=_build_qty_suggestions(CATEGORIES['ZELASTWO']),
                           qty_suggestions_kanadyjki=_build_qty_suggestions(CATEGORIES['KANADYJKI']),
                           do_czego_suggestions=_build_do_czego_suggestions())

@views_bp.route('/sprzet/import', methods=['GET', 'POST'])
@quartermaster_required
def sprzet_import():
    diff_data = []
    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        if f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            try:
                if ext == '.csv':
                    df = pd.read_csv(f, on_bad_lines='skip').fillna('')
                elif ext == '.xlsx':
                    df = pd.read_excel(f).fillna('')
                else:
                    flash('Nieobsługiwany format pliku.', 'danger')
                    return redirect(url_for('views.sprzet_import'))
                
                mapping = {
                    'Typ': 'typ', 'ID': 'id', 'Zakup': 'zakup', 'Przejęty': 'przejecie',
                    'Znak szczególny': 'znak_szczegolny', 'Zapałki': 'zapalki',
                    'Kolor dachu': 'kolor_dachu', 'Kolor boków': 'kolor_bokow',
                    'ZMIANA STANU (WRACA DO WARSZAWY)': 'czyWraca',
                    'Wodoszczelność': 'wodoszczelnosc', 'Stan ogólny': 'stan_ogolny',
                    'Uwagi konserwacyjne': 'uwagi', 'Magazyn': 'lokalizacja',
                    'Lokalizacja': 'lokalizacja',
                    'Przeznaczenie': 'przeznaczenie', 'Historia': 'historia'
                }
                df = df.rename(columns=mapping)
                
                # Standaryzacja ID
                if 'id' not in df.columns:
                    flash('Brak kolumny ID w pliku.', 'danger')
                    return redirect(url_for('views.sprzet_import'))

                all_sprzet = {s['id']: s for s in get_all_sprzet()}
                
                for _, row in df.iterrows():
                    sid = str(row['id']).upper().strip()
                    if not sid or sid == 'NAN': continue
                    
                    new_data = {mapping[k]: str(v).strip() for k, v in row.to_dict().items() if k in mapping and mapping[k] != 'id'}
                    
                    if sid in all_sprzet:
                        old_data = {k: v for k, v in all_sprzet[sid].items() if k not in ['id', 'zdjecia_lista_url']}
                        diffs = {}
                        for k, v in new_data.items():
                            old_val = str(old_data.get(k, '')).strip()
                            if v and v != old_val:
                                diffs[k] = {'old': old_val, 'new': v}
                        
                        if diffs:
                            diff_data.append({'id': sid, 'diffs': diffs, 'new_data': new_data, 'before_data': old_data})
                    else:
                        diff_data.append({'id': sid, 'diffs': {}, 'new_data': new_data})
                
                if not diff_data:
                    flash('Brak różnic lub nowych danych do zaimportowania.', 'info')

            except Exception as e:
                flash(f'Błąd przetwarzania pliku: {e}', 'danger')

    return render_template('sprzet_import.html', diff_data=diff_data)

@views_bp.route('/sprzet/import/confirm', methods=['POST'])
@quartermaster_required
def sprzet_import_confirm():
    import_ids = request.form.getlist('import_ids')
    count = 0
    for sid in import_ids:
        data_json = request.form.get(f'data_{sid}')
        if data_json:
            data = json.loads(data_json)
            before_json = request.form.get(f'before_{sid}')
            before_data = json.loads(before_json) if before_json else None
            
            set_item(COLLECTION_SPRZET, sid, data)
            add_log(session.get('user_id'), 'import', 'sprzet', sid, before=before_data, after=data)
            count += 1
    
    flash(f'Pomyślnie zaimportowano/zaktualizowano {count} pozycji.', 'success')
    return redirect(url_for('views.sprzet_list'))

@views_bp.route('/sprzet/edit/<sprzet_id>', methods=['GET', 'POST'])
@quartermaster_required
def sprzet_edit(sprzet_id):
    sprzet = get_sprzet_item(sprzet_id)
    if not sprzet:
        flash('Nie znaleziono sprzętu.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    if request.method == 'POST':
        data = {k: v for k, v in request.form.items() if k != 'id'}
        _normalize_qty_fields(data, sprzet.get('category'))

        # Obsługa nowych zdjęć
        urls, err = process_uploads(request.files.getlist('nowe_zdjecia'), 'sprzet', sprzet_id)
        if err:
            flash(err, 'warning')

        # Obsługa usuwania zdjęć - porównujemy blob_name zamiast pełnych URL
        from .gcs_utils import extract_blob_name, list_equipment_photos, delete_blob_from_gcs
        zdjecia_do_usuniecia = request.form.getlist('usun_zdjecia')
        blob_names_do_usuniecia = []
        for url in zdjecia_do_usuniecia:
            bn = extract_blob_name(url)
            if bn:
                blob_names_do_usuniecia.append(bn)
                # Fizycznie usuwamy plik z GCS, aby uniknąć fallbacku i osieroconych plików
                delete_blob_from_gcs(bn)

        # Priorytet dla zdjęć w bazie danych, jeśli brak - sprawdzamy fallback (GCS)
        aktualne_zdjecia = sprzet.get('zdjecia')
        if aktualne_zdjecia is None:
            # Jeśli w bazie nie ma listy, pobierz ją z GCS (tak jak widzi to użytkownik na karcie)
            # Uwaga: list_equipment_photos zwraca Signed URLs, które extract_blob_name potrafi obsłużyć.
            aktualne_zdjecia = list_equipment_photos(sprzet_id)

        # Usuwamy z listy te zdjęcia, które użytkownik zaznaczył do usunięcia.
        # Porównujemy blob_name, aby uniknąć problemów z wygasającymi tokenami w Signed URLs.
        nowa_lista_zdjec = [
            z for z in aktualne_zdjecia
            if extract_blob_name(z) not in blob_names_do_usuniecia
        ]
        if urls:
            nowa_lista_zdjec.extend(urls)

        data['zdjecia'] = nowa_lista_zdjec

        # Przygotuj dane przed zapisem do loga
        before_data = {k: v for k, v in sprzet.items() if k not in ['id', 'zdjecia_lista_url']}

        update_sprzet(sprzet_id, **data)
        add_log(session.get('user_id'), 'edit', 'sprzet', sprzet_id, before=before_data, after=data)
        flash(f'Sprzęt {sprzet_id} został zaktualizowany.', 'success')
        return redirect(url_for('views.sprzet_card', sprzet_id=sprzet_id))

    # Priorytet dla zdjęć zapisanych w bazie danych (odświeżamy linki), fallback do listowania GCS
    from .gcs_utils import list_equipment_photos
    zdjecia_z_bazy = sprzet.get('zdjecia')
    if zdjecia_z_bazy is not None:
        sprzet['zdjecia_lista_url'] = refresh_urls(zdjecia_z_bazy)
    else:
        sprzet['zdjecia_lista_url'] = list_equipment_photos(sprzet_id)

    # Filtrujemy potencjalnych rodziców: tylko Magazyny i Półki/Skrzynie
    potential_parents = [s for s in get_all_sprzet() if s.get('category') in [CATEGORIES['MAGAZYN'], CATEGORIES['POLKA']]]

    return render_template('sprzet_edit.html',
                           sprzet=sprzet,
                           categories=CATEGORIES,
                           magazyny_names=MAGAZYNY_NAMES,
                           all_items=potential_parents,
                           qty_suggestions_zelastwo=_build_qty_suggestions(CATEGORIES['ZELASTWO']),
                           qty_suggestions_kanadyjki=_build_qty_suggestions(CATEGORIES['KANADYJKI']),
                           do_czego_suggestions=_build_do_czego_suggestions())

@views_bp.route('/sprzet/delete/<sprzet_id>', methods=['POST'])
@quartermaster_required
def sprzet_delete(sprzet_id):
    delete_item(COLLECTION_SPRZET, sprzet_id)
    add_log(session.get('user_id'), 'delete', 'sprzet', sprzet_id)
    flash(f'Sprzęt {sprzet_id} został usunięty.', 'success')
    return redirect(url_for('views.sprzet_list'))

@views_bp.route('/sprzet/<sprzet_id>', methods=['GET', 'POST'])
@login_required
def sprzet_card(sprzet_id):
    sprzet_item = get_sprzet_item(sprzet_id)
    if not sprzet_item:
        flash(f'Sprzęt "{sprzet_id}" nie został znaleziony.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    if request.method == 'POST':
        if not session.get('user_id'):
            flash('Musisz być zalogowany, aby dodać usterkę.', 'warning')
            return redirect(url_for('auth.login'))

        opis = request.form.get('opis_usterki')

        if not opis:
            flash('Opis usterki nie może być pusty!', 'warning')
        else:
            try:
                db = get_firestore_client()
                doc_ref = db.collection('usterki').document()
                urls, err = process_uploads(request.files.getlist('zdjecia_usterki'), 'usterki', doc_ref.id)
                if err:
                    flash(err, 'warning')
                else:
                    data = {
                        'sprzet_id': sprzet_id,
                        'opis': opis,
                        'zgloszono_przez': session.get('user_name', 'Anonim'),
                        'user_id': session.get('user_id'),
                        'data_zgloszenia': _warsaw_now(),
                        'status': 'oczekuje',
                        'zdjecia': urls
                    }
                    doc_ref.set(data)
                    add_log(session.get('user_id'), 'add', 'usterka', doc_ref.id, data)
                    flash(f'Usterka dla {sprzet_id} została zgłoszona!', 'success')
            except Exception as e:
                flash(f'Błąd: {e}', 'danger')
            return redirect(url_for('views.sprzet_card', sprzet_id=sprzet_id))

    # Priorytet dla zdjęć zapisanych w bazie danych, fallback do listowania GCS
    zdjecia_z_bazy = sprzet_item.get('zdjecia')
    # Używamy jawnego sprawdzenia is not None, aby [] (pusta lista) nie wyzwalała fallbacku
    if zdjecia_z_bazy is not None:
        sprzet_item['zdjecia_lista_url'] = refresh_urls(zdjecia_z_bazy)
    else:
        # Fallback tylko jeśli pole 'zdjecia' w ogóle nie istnieje w dokumencie
        sprzet_item['zdjecia_lista_url'] = list_equipment_photos(sprzet_id)

    # Pobieranie logów aktywności dla tego sprzętu
    from .db_firestore import get_logs_by_target
    from .db_users import get_all_users

    # Pobieramy tylko ostatnie 15 logów dla wydajności karty
    logs = get_logs_by_target(sprzet_id, limit=15)
    users = get_all_users()
    user_map = build_user_map(users)

    for log in logs:
        log['user_name'] = user_map.get(log.get('user_id'), log.get('user_id', 'Nieznany'))

    # Dodaj mapę sprzętów do sprzet_card, aby wyciągnąć magazyn_id i magazyn_display
    all_items = get_all_sprzet()
    sprzet_map = {s['id']: s for s in all_items if 'id' in s}
    if not sprzet_item.get('magazyn_display'):
        curr = sprzet_item
        visited = set()
        while curr.get('parent_id') and curr['parent_id'] not in visited:
            visited.add(curr['id'])
            parent = sprzet_map.get(curr['parent_id'])
            if not parent:
                break
            if parent.get('category') == CATEGORIES['MAGAZYN']:
                sprzet_item['magazyn_display'] = parent.get('nazwa') or parent.get('id')
                sprzet_item['magazyn_id'] = parent.get('id')
                break
            curr = parent
        if not sprzet_item.get('magazyn_display') and sprzet_item.get('lokalizacja'):
            sprzet_item['magazyn_display'] = sprzet_item['lokalizacja']

    # Aktywne wypożyczenie
    loans = get_loans_for_item(sprzet_id)
    active_loan = next((l for l in loans if l.get('status') == 'active'), None)

    qr_env = (os.getenv('QR_URL') or '').strip()
    qr_url_base = (qr_env.rstrip('/') if qr_env else request.host_url.rstrip('/'))

    return render_template('sprzet_card.html', sprzet=sprzet_item,
                           usterki=get_usterki_for_sprzet(sprzet_id),
                           logs=logs,
                           loans=loans,
                           active_loan=active_loan,
                           qr_url_base=qr_url_base)


@views_bp.route('/sprzet/<sprzet_id>/quick_photo', methods=['POST'])
@quartermaster_required
def quick_photo(sprzet_id):
    """Szybkie dodawanie zdjęcia aparatem z poziomu karty sprzętu."""
    sprzet = get_sprzet_item(sprzet_id)
    if not sprzet:
        flash("Nie znaleziono sprzętu", "danger")
        return redirect(url_for('views.sprzet_list'))

    if 'foto' in request.files:
        urls, err = process_uploads([request.files['foto']], 'sprzet', sprzet_id)
        if err:
            flash(err, 'warning')
        if urls:
            aktualne_zdjecia = sprzet.get('zdjecia', [])
            aktualne_zdjecia.extend(urls)
            update_sprzet(sprzet_id, zdjecia=aktualne_zdjecia)
            add_log(session.get('user_id'), 'edit', 'sprzet', sprzet_id, details={'action': 'quick_photo_add'})
            flash('Zdjęcie zostało dodane.', 'success')

    return redirect(url_for('views.sprzet_card', sprzet_id=sprzet_id))


@views_bp.route('/sprzet/<sprzet_id>/qrcode')
def generate_qr_code(sprzet_id):
    """Generuje kod QR dla danego sprzętu i zwraca go jako obraz PNG."""
    # Sprawdź czy sprzęt istnieje
    sprzet_item = get_sprzet_item(sprzet_id)
    if not sprzet_item:
        # Zamiast redirect (który psuje tag <img>), zwracamy 404 lub puste
        return "Sprzęt nie istnieje", 404

    # Preferuj QR_URL z .env; jeśli brak, fallback na aktualny host.
    qr_url = (os.getenv('QR_URL') or '').strip()
    if qr_url:
        base = qr_url.rstrip('/')
    else:
        # request.host_url ma trailing slash
        base = request.host_url.rstrip('/')

    # Preferuj QR_URL z .env; jeśli brak, fallback na aktualny host.
    qr_url = (os.getenv('QR_URL') or '').strip()
    if qr_url:
        base = qr_url.rstrip('/')
    else:
        # request.host_url ma trailing slash
        base = request.host_url.rstrip('/')

    # Generuj URL do strony sprzętu
    target_url = f"{base}/sprzet/{sprzet_id}"

    # Sprawdź czy jest tryb debug
    is_debug = os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG') == 'True'
    if is_debug:
        target_url += '?dev'

    # Generuj kod QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    # Twórz obraz
    img = qr.make_image(fill_color="black", back_color="white")

    # Zapisz do BytesIO
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Zwróć plik
    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=request.args.get('download') == '1',
        download_name=f'QR_{sprzet_id}.png'
    )

@views_bp.route('/sprzet/<sprzet_id>/qr')
def sprzet_qr_page(sprzet_id):
    """Prosta strona HTML z QR dla danego sprzętu.

    To jest alternatywa dla modala na liście. Otwieramy w nowej karcie –
    dzięki temu omijamy problemy z bootstrap modal/focus/cache i łatwo diagnozować błędy.
    """
    sprzet_item = get_sprzet_item(sprzet_id)
    if not sprzet_item:
        return "Sprzęt nie istnieje", 404

    target_url = url_for('views.sprzet_card', sprzet_id=sprzet_id, _external=True)

    # Używamy istniejącego endpointu PNG (można też pobrać bezpośrednio)
    qr_png_url = url_for('views.generate_qr_code', sprzet_id=sprzet_id)

    name = sprzet_item.get('nazwa') or sprzet_item.get('typ') or sprzet_id

    # Escape values before embedding into HTML to prevent XSS
    sprzet_id_escaped = html.escape(str(sprzet_id), quote=True)
    name_escaped = html.escape(str(name), quote=True)
    qr_png_url_escaped = html.escape(qr_png_url, quote=True)
    target_url_escaped = html.escape(target_url, quote=True)

    # Minimalny HTML inline – bez dodatkowych template'ów.
    return (
        "<!doctype html>\n"
        "<html lang=\"pl\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>QR: {sprzet_id_escaped}</title>\n"
        "  <style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:24px;}"
        ".box{max-width:520px;margin:0 auto;text-align:center;}"
        "img{max-width:420px;width:100%;height:auto;border:1px solid #ddd;border-radius:8px;padding:12px;background:#fff;}"
        "a{display:inline-block;margin:10px 6px;}"
        ".id{font-family:ui-monospace,Consolas,monospace;}"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"box\">\n"
        f"    <h2>QR: <span class=\"id\">{sprzet_id_escaped}</span></h2>\n"
        f"    <div style=\"margin-bottom:6px;color:#555\">{name_escaped}</div>\n"
        f"    <img src=\"{qr_png_url_escaped}\" alt=\"QR {sprzet_id_escaped}\">\n"
        "    <div>\n"
        f"      <a href=\"{target_url_escaped}\" target=\"_blank\" rel=\"noopener\">Otwórz kartę sprzętu</a>\n"
        f"      <a href=\"{qr_png_url_escaped}?download=1\">Pobierz PNG</a>\n"
        "    </div>\n"
        "  </div>\n"
        "</body>\n"
        "</html>\n"
    )


# =======================================================================
#                       WIDOKI USTERK
# =======================================================================

@views_bp.route('/usterki')
@full_login_required
def usterki_list():
    """Panel administratora - lista wszystkich usterek."""
    status = request.args.get('status')
    magazyn = request.args.get('magazyn')
    sprzet_id = request.args.get('sprzet_id')
    oficjalna_ewidencja = request.args.get('oficjalna_ewidencja')

    usterki = get_all_usterki()
    sprzet_items = get_all_sprzet()
    sprzet_map = {s['id']: s for s in sprzet_items}

    filtered_usterki = []
    for u in usterki:
        s = sprzet_map.get(u.get('sprzet_id'))
        u['nazwa_sprzetu'] = s.get('nazwa', 'N/A') if s else 'USUNIĘTY'
        u['magazyn'] = s.get('lokalizacja', 'N/A') if s else 'N/A' # Używamy lokalizacja jako magazyn
        u['oficjalna_ewidencja'] = s.get('oficjalna_ewidencja', 'Nie') if s else 'Nie'

        # Filtrowanie w pamięci
        match = True
        if status and u.get('status') != status:
            match = False
        if magazyn and u.get('magazyn') != magazyn:
            match = False
        if sprzet_id and u.get('sprzet_id') != sprzet_id:
            match = False
        if oficjalna_ewidencja and u.get('oficjalna_ewidencja') != oficjalna_ewidencja:
            match = False

        if match:
            filtered_usterki.append(u)

    statuses = sorted(list(set(u.get('status') for u in usterki if u.get('status'))))
    magazyny = sorted(list(set(s.get('lokalizacja') for s in sprzet_items if s.get('lokalizacja'))))
    ids_sprzetu = sorted(list(set(u.get('sprzet_id') for u in usterki if u.get('sprzet_id'))))
    ewidencje = sorted(list(set(u.get('oficjalna_ewidencja') for u in filtered_usterki if u.get('oficjalna_ewidencja'))))

    return render_template('usterki_list.html',
                           usterki=filtered_usterki,
                           statuses=statuses,
                           magazyny=magazyny,
                           ids_sprzetu=ids_sprzetu,
                           ewidencje=ewidencje,
                           selected_filters=request.args)

@views_bp.route('/usterka/<usterka_id>')
@login_required
def usterka_card(usterka_id):
    """Widok karty usterki (publiczny dostęp do szczegółów)."""
    usterka = get_usterka_item(usterka_id)
    if not usterka:
        flash('Nie znaleziono usterki.', 'danger')
        return redirect(url_for('views.usterki_list'))

    # Używamy pola 'zdjecia' zapisanego w dokumencie (odświeżamy linki).
    # Jeśli usterka została zgłoszona starą metodą, może być konieczne listowanie z GCS
    # (choć usterki zawsze miały URL-e w dokumencie, warto mieć fallback)
    photos = refresh_urls(usterka.get('zdjecia') or [])

    # Jeśli lista zdjęć jest pusta, spróbujmy poszukać ich w GCS (fallback)
    if not photos:
        from .gcs_utils import list_files
        photos = list_files(f"usterki/{usterka_id}/")

    usterka['zdjecia_lista_url'] = photos

    # Pobieranie logów aktywności dla tej usterki
    from .db_firestore import get_logs_by_target
    from .db_users import get_all_users
    
    # Pobieramy tylko ostatnie 15 logów dla wydajności profilu
    logs = get_logs_by_target(usterka_id, limit=15)
    users = get_all_users()
    user_map = build_user_map(users)
    
    for log in logs:
        log['user_name'] = user_map.get(log.get('user_id'), log.get('user_id', 'Nieznany'))

    return render_template('usterka_card.html', usterka=usterka, logs=logs)

@views_bp.route('/usterka/edit/<usterka_id>', methods=['GET', 'POST'])
@login_required
def usterka_edit(usterka_id):
    """Widok edycji usterki."""
    usterka = get_usterka_item(usterka_id)
    if not usterka:
        flash('Nie znaleziono usterki.', 'danger')
        return redirect(url_for('views.usterki_list'))

    # Uprawnienia: Kwatermistrz może wszystko, Reporter tylko swoje
    is_quartermaster = session.get('user_role') in ['quartermaster', 'admin']
    is_owner = usterka.get('user_id') == session.get('user_id')
    
    if not is_quartermaster and not is_owner:
        flash('Nie masz uprawnień do edycji tej usterki.', 'danger')
        return redirect(url_for('views.usterka_card', usterka_id=usterka_id))

    if request.method == 'POST':
        # Obsługa nowych zdjęć
        urls, err = process_uploads(request.files.getlist('nowe_zdjecia'), 'usterki', usterka_id)
        if err:
            flash(err, 'warning')

        # Obsługa usuwania zdjęć - porównujemy blob_name zamiast pełnych URL
        from .gcs_utils import extract_blob_name, delete_blob_from_gcs
        zdjecia_do_usuniecia = request.form.getlist('usun_zdjecia')
        blob_names_do_usuniecia = []
        for url in zdjecia_do_usuniecia:
            bn = extract_blob_name(url)
            if bn:
                blob_names_do_usuniecia.append(bn)
                delete_blob_from_gcs(bn)

        aktualne_zdjecia = usterka.get('zdjecia', [])
        nowa_lista_zdjec = [
            z for z in aktualne_zdjecia
            if extract_blob_name(z) not in blob_names_do_usuniecia
        ]
        if urls:
            nowa_lista_zdjec.extend(urls)

        data = {
            'opis': request.form.get('opis'),
            'zdjecia': nowa_lista_zdjec
        }
        
        # Tylko kwatermistrz może zmieniać status i dodawać uwagi admina
        if is_quartermaster:
            status = request.form.get('status')
            if status in ['oczekuje', 'w trakcie', 'naprawiona', 'odrzucona']:
                data['status'] = status
            data['uwagi_admina'] = request.form.get('uwagi_admina')

        # Przygotuj dane przed zapisem do loga
        before_data = {k: v for k, v in usterka.items() if k not in ['id', 'zdjecia_lista_url']}

        update_usterka(usterka_id, **data)
        add_log(session.get('user_id'), 'edit', 'usterka', usterka_id, before=before_data, after=data)
        flash(f'Usterka {usterka_id} zaktualizowana.', 'success')
        return redirect(url_for('views.usterka_card', usterka_id=usterka_id))

    usterka['zdjecia_lista_url'] = refresh_urls(usterka.get('zdjecia', []))
    return render_template('usterka_edit.html', usterka=usterka)

@views_bp.route('/usterka/delete/<usterka_id>', methods=['POST'])
@admin_required
def usterka_delete(usterka_id):
    """Usuwanie usterki (tylko dla admina)."""
    delete_item(COLLECTION_USTERKI, usterka_id)
    add_log(session.get('user_id'), 'delete', 'usterka', usterka_id)
    flash(f'Usterka {usterka_id} została usunięta.', 'success')
    return redirect(url_for('views.usterki_list'))


@views_bp.route('/usterki/bulk-edit', methods=['POST'])
@quartermaster_required
def usterki_bulk_edit():
    """Masowa edycja statusów usterek."""
    token = request.form.get('_csrf_token')
    if not token or token != session.get('_csrf_token'):
        flash('Błąd weryfikacji CSRF.', 'danger')
        return redirect(url_for('views.usterki_list'))

    usterka_ids = request.form.getlist('usterka_ids')
    new_status = request.form.get('status')

    if not usterka_ids:
        flash('Nie wybrano żadnych usterek.', 'warning')
        return redirect(url_for('views.usterki_list'))
    
    if not new_status or new_status not in ['oczekuje', 'w trakcie', 'naprawiona', 'odrzucona']:
        flash('Nieprawidłowy status.', 'warning')
        return redirect(url_for('views.usterki_list'))

    count = 0
    for uid in usterka_ids:
        usterka = get_usterka_item(uid)
        if usterka:
            before_data = {k: v for k, v in usterka.items() if k not in ['id', 'zdjecia_lista_url']}
            update_usterka(uid, status=new_status)
            after_data = dict(before_data)
            after_data['status'] = new_status
            add_log(session.get('user_id'), 'bulk_edit', 'usterka', uid, before=before_data, after=after_data)
            count += 1
    
    flash(f'Pomyślnie zaktualizowano {count} usterek.', 'success')
    return redirect(url_for('views.usterki_list'))


@views_bp.route('/sprzet/bulk-delete', methods=['POST'])
@quartermaster_required
def sprzet_bulk_delete():
    """Masowe usuwanie sprzętu (QUARTERMASTER/ADMIN)."""
    token = request.form.get('_csrf_token')
    if not token or token != session.get('_csrf_token'):
        flash('Błąd weryfikacji CSRF.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    sprzet_ids = request.form.getlist('sprzet_ids')
    if not sprzet_ids:
        flash('Nie wybrano żadnych elementów.', 'warning')
        return redirect(url_for('views.sprzet_list'))

    count = 0
    errors = 0
    error_details = []

    for sid in sprzet_ids:
        try:
            delete_item(COLLECTION_SPRZET, sid)
            add_log(session.get('user_id'), 'delete', 'sprzet', sid)
            count += 1
        except Exception as e:
            errors += 1
            error_msg = f"{sid}: {str(e)}"
            error_details.append(error_msg)
            current_app.logger.error(f"Bulk delete error: {error_msg}", exc_info=True)

    if count:
        flash(f'Pomyślnie usunięto {count} elementów.', 'success')
    
    if errors:
        if errors <= MAX_DISPLAYED_ERRORS:
            flash(f'Wystąpiły błędy przy usuwaniu {errors} pozycji:', 'danger')
        else:
            flash(f'Wystąpiły błędy przy usuwaniu {errors} pozycji. Pierwsze {MAX_DISPLAYED_ERRORS} błędów:', 'danger')
        
        for error_detail in error_details[:MAX_DISPLAYED_ERRORS]:
            flash(error_detail, 'danger')

    return_query = (request.form.get('return_query') or '').strip()
    return redirect(url_for('views.sprzet_list') + (f'?{return_query}' if return_query else ''))

# =======================================================================
#                       WIDOKI WYPOŻYCZEŃ
# =======================================================================

@views_bp.route('/loans')
@quartermaster_required
def loans_list():
    show_history = request.args.get('history', '0') == '1'
    if show_history:
        loans = get_all_items(COLLECTION_WYPOZYCZENIA, order_by='timestamp')
    else:
        loans = get_active_loans()

    # Dodajemy informacje o sprzęcie do każdego wypożyczenia
    for loan in loans:
        loan['item'] = get_sprzet_item(loan.get('item_id'))
    return render_template('loans_list.html', loans=loans, show_history=show_history)

@views_bp.route('/loan/add/<item_id>', methods=['GET', 'POST'])
@quartermaster_required
def loan_add(item_id):
    item = get_sprzet_item(item_id)
    if not item:
        flash('Nie znaleziono przedmiotu.', 'danger')
        return redirect(url_for('views.sprzet_list'))
    
    if item.get('category') == 'magazyn':
        flash('Nie można wypożyczyć magazynu.', 'danger')
        return redirect(url_for('views.sprzet_card', sprzet_id=item_id))
    
    if request.method == 'POST':
        data = {
            'item_id': item_id,
            'do_kiedy': request.form.get('do_kiedy'),
            'przez_kogo': request.form.get('przez_kogo'),
            'kontakt': request.form.get('kontakt'),
            'uwagi': request.form.get('uwagi'),
            'added_by': session.get('user_id')
        }
        add_loan(data)
        add_log(session.get('user_id'), 'loan', 'sprzet', item_id, after=data)
        flash(f'Wypożyczono {item_id}.', 'success')
        return redirect(url_for('views.loans_list'))
    
    from .db_users import get_all_users
    users = get_all_users()
    user_names = sorted(list(set(build_user_map(users).values())))
    
    # Budujemy mapę użytkowników do auto-uzupełniania kontaktu
    user_contact_map = {}
    for user in users:
        display_name = (f"{user.get('first_name', '')} {user.get('last_name', '')}").strip() or user.get('email', user['id'])
        user_contact_map[display_name] = user.get('email', '')
    
    return render_template('loan_edit.html', 
                           item=item, 
                           user_names=user_names, 
                           user_contact_map=user_contact_map)

@views_bp.route('/loan/return/<loan_id>', methods=['POST'])
@quartermaster_required
def loan_return(loan_id):
    loan = get_item(COLLECTION_WYPOZYCZENIA, loan_id)
    if not loan:
        flash('Nie znaleziono wypożyczenia.', 'danger')
        return redirect(url_for('views.loans_list'))

    # Sprawdzamy czy użytkownik nie zwraca własnego wypożyczenia
    current_user_id = session.get('user_id')
    from .db_users import get_user_by_uid
    current_user = get_user_by_uid(current_user_id)
    
    if current_user:
        # Budujemy nazwę aktualnego użytkownika do porównania
        first_name = current_user.get('first_name', '')
        last_name = current_user.get('last_name', '')
        full_name = (f"{first_name} {last_name}").strip()
        email = current_user.get('email', '')
        
        przez_kogo = loan.get('przez_kogo', '')
        
        if (full_name and przez_kogo == full_name) or (email and przez_kogo == email):
            flash('Osoba która wypożyczała nie może sama sobie zwrócić wypożyczenia.', 'danger')
            return redirect(url_for('views.loans_list'))

    mark_loan_returned(loan_id)
    flash('Przedmiot został zwrócony.', 'success')
    return redirect(url_for('views.loans_list'))

@views_bp.route('/logs')
@quartermaster_required
def logs_list():
    """Wyświetla listę wszystkich logów (QUARTERMASTER/ADMIN)."""
    from .db_firestore import get_all_logs, get_logs_count, get_logs_by_user, get_logs_by_target
    from .db_users import get_all_users

    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    user_id_filter = request.args.get('user_id')
    target_id_filter = request.args.get('target_id')

    if user_id_filter:
        logs = get_logs_by_user(user_id_filter, limit=per_page, offset=offset)
        total_logs = get_logs_count(user_id=user_id_filter)
    elif target_id_filter:
        logs = get_logs_by_target(target_id_filter, limit=per_page, offset=offset)
        total_logs = get_logs_count(target_id=target_id_filter)
    else:
        logs = get_all_logs(limit=per_page, offset=offset)
        total_logs = get_logs_count()

    users = get_all_users()
    user_map = build_user_map(users)

    for log in logs:
        log['user_name'] = user_map.get(log.get('user_id'), log.get('user_id', 'Nieznany'))

    total_pages = (total_logs + per_page - 1) // per_page

    return render_template('logs.html', 
                           logs=logs, 
                           page=page, 
                           total_pages=total_pages,
                           total_logs=total_logs,
                           user_id_filter=user_id_filter,
                           target_id_filter=target_id_filter)

@views_bp.route('/user/<user_id>')
@login_required
def user_profile(user_id):
    """Wyświetla profil użytkownika."""
    from .db_users import get_user_by_uid
    from .db_firestore import get_logs_by_user

    user = get_user_by_uid(user_id)
    if not user:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    # Pobieramy tylko ostatnie 15 logów dla wydajności profilu
    logs = get_logs_by_user(user_id, limit=15)

    # Ustawiamy czytelną nazwę użytkownika dla logów
    user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get('email', user_id)
    for log in logs:
        log['user_name'] = user_name

    return render_template('user_profile.html', user_info=user, logs=logs)

@views_bp.route('/sprzet/zestawienie')
@full_login_required
def sprzet_zestawienie():
    """Widok zestawienia elementów (porównanie zasobów)."""
    # Parametry dynamiczne
    cat_a = request.args.get('cat_a')
    cat_b = request.args.get('cat_b')
    magazyn_id = request.args.get('magazyn_id')

    # Predefiniowane presety (kompatybilność wsteczna)
    preset = request.args.get('preset')
    if preset == 'namioty_zelastwo':
        cat_a = CATEGORIES['NAMIOT']
        cat_b = CATEGORIES['ZELASTWO']
    elif preset == 'kanadyjki':
        cat_a = CATEGORIES['KANADYJKI']
        cat_b = CATEGORIES['KANADYJKI']

    items = get_all_sprzet()

    # Filtrowanie po magazynie (opcjonalne)
    if magazyn_id:
        # Znajdź wszystkie dzieci tego magazynu (rekurencyjnie lub tylko bezpośrednie?)
        # W tej aplikacji struktura jest zazwyczaj: Magazyn -> Polka/Skrzynia -> Przedmiot
        # lub Magazyn -> Przedmiot.
        # Pobierzmy wszystkie przedmioty i przefiltrujmy po parent_id lub lokalizacji.
        magazyn_children_ids = {magazyn_id}
        # Dodajmy półki które są w tym magazynie
        for i in items:
            if i.get('parent_id') == magazyn_id:
                magazyn_children_ids.add(i.get('id'))

        items = [i for i in items if i.get('id') == magazyn_id or i.get('parent_id') in magazyn_children_ids]

    summary = {}

    if cat_a and cat_b:
        group_a = [i for i in items if i.get('category') == cat_a]
        group_b = [i for i in items if i.get('category') == cat_b]

        # Specyficzna logika dla kanadyjek
        if preset == 'kanadyjki' or (cat_a == CATEGORIES['KANADYJKI'] and cat_b == CATEGORIES['KANADYJKI']):
            kanadyjki = [i for i in group_a if 'zestaw naprawczy' not in (i.get('nazwa') or '').lower()]
            naprawcze = [i for i in group_b if 'zestaw naprawczy' in (i.get('nazwa') or '').lower()]

            k_count = len(kanadyjki)
            n_count = sum(int(i.get('ilosc', 0)) for i in naprawcze if str(i.get('ilosc', '')).isdigit())

            summary = {
                'title': 'Zestawienie: Kanadyjki vs Zestawy Naprawcze',
                'rows': [{
                    'label': 'Kanadyjki',
                    'demand': k_count,
                    'supply': n_count,
                    'diff': n_count - k_count,
                    'status': 'ok' if n_count == k_count else ('excess' if n_count > k_count else 'shortage')
                }]
            }
        # Specyficzna logika dla Namioty vs Żelastwo
        elif (cat_a == CATEGORIES['NAMIOT'] and cat_b == CATEGORIES['ZELASTWO']) or \
             (cat_a == CATEGORIES['ZELASTWO'] and cat_b == CATEGORIES['NAMIOT']):

            namioty = group_a if cat_a == CATEGORIES['NAMIOT'] else group_b
            zelastwo = group_b if cat_b == CATEGORIES['ZELASTWO'] else group_a

            namioty_stats = {}
            for n in namioty:
                t = n.get('typ', 'Nieokreślony')
                namioty_stats[t] = namioty_stats.get(t, 0) + 1

            zelastwo_stats = {}
            for z in zelastwo:
                target = z.get('do_czego', 'Nieokreślone')
                qty = z.get('ilosc', 0)
                try: qty = int(qty)
                except (ValueError, TypeError): qty = 0
                zelastwo_stats[target] = zelastwo_stats.get(target, 0) + qty

            summary = {
                'title': 'Zestawienie: Namioty vs Omasztowanie',
                'rows': []
            }
            all_types = sorted(list(set(namioty_stats.keys()) | set(zelastwo_stats.keys())))
            for t in all_types:
                n_val = namioty_stats.get(t, 0)
                z_val = zelastwo_stats.get(t, 0)
                diff = z_val - n_val
                summary['rows'].append({
                    'label': t,
                    'demand': n_val,
                    'supply': z_val,
                    'diff': diff,
                    'status': 'ok' if diff == 0 else ('excess' if diff > 0 else 'shortage')
                })
        else:
            # Generyczna logika dla innych kategorii
            # Próbujemy grupować po 'typ' lub 'nazwa'
            stats_a = {}
            for i in group_a:
                label = i.get('typ') or i.get('nazwa') or 'Inne'
                stats_a[label] = stats_a.get(label, 0) + (int(i.get('ilosc', 1)) if str(i.get('ilosc', '')).isdigit() else 1)

            stats_b = {}
            for i in group_b:
                label = i.get('typ') or i.get('nazwa') or 'Inne'
                stats_b[label] = stats_b.get(label, 0) + (int(i.get('ilosc', 1)) if str(i.get('ilosc', '')).isdigit() else 1)

            summary = {
                'title': f'Zestawienie: {cat_a.capitalize()} vs {cat_b.capitalize()}',
                'rows': []
            }
            all_labels = sorted(list(set(stats_a.keys()) | set(stats_b.keys())))
            for l in all_labels:
                a_val = stats_a.get(l, 0)
                b_val = stats_b.get(l, 0)
                diff = b_val - a_val
                summary['rows'].append({
                    'label': l,
                    'demand': a_val,
                    'supply': b_val,
                    'diff': diff,
                    'status': 'ok' if diff == 0 else ('excess' if diff > 0 else 'shortage')
                })

    magazyny = [i for i in get_all_sprzet() if i.get('category') == CATEGORIES['MAGAZYN']]

    return render_template('sprzet_zestawienie.html',
                           summary=summary,
                           preset=preset,
                           cat_a=cat_a,
                           cat_b=cat_b,
                           magazyn_id=magazyn_id,
                           kategorie=CATEGORIES,
                           magazyny=magazyny)

@views_bp.route('/sprzet/export/<format>')
@login_required
def export_sprzet(format):
    """Eksportuje listę sprzętu zgodnie z aktualnymi filtrami lub wynik zestawienia."""
    fmt = (format or '').lower().strip()
    if fmt not in {'csv', 'xlsx', 'docx', 'pdf', 'qr'}:
        flash('Nieobsługiwany format eksportu.', 'danger')
        return redirect(url_for('views.sprzet_list', **request.args))

    mode = request.args.get('mode')
    if mode == 'zestawienie':
        preset = request.args.get('preset')
        cat_a = request.args.get('cat_a')
        cat_b = request.args.get('cat_b')
        magazyn_id = request.args.get('magazyn_id')

        if preset == 'namioty_zelastwo':
            cat_a = CATEGORIES['NAMIOT']
            cat_b = CATEGORIES['ZELASTWO']
        elif preset == 'kanadyjki':
            cat_a = CATEGORIES['KANADYJKI']
            cat_b = CATEGORIES['KANADYJKI']

        # Ponownie obliczamy zestawienie
        items = get_all_sprzet()
        
        if magazyn_id:
            magazyn_children_ids = {magazyn_id}
            for i in items:
                if i.get('parent_id') == magazyn_id:
                    magazyn_children_ids.add(i.get('id'))
            items = [i for i in items if i.get('id') == magazyn_id or i.get('parent_id') in magazyn_children_ids]

        export_rows = []
        title = "Zestawienie Elementów"
        
        if cat_a and cat_b:
            group_a = [i for i in items if i.get('category') == cat_a]
            group_b = [i for i in items if i.get('category') == cat_b]

            if preset == 'kanadyjki' or (cat_a == CATEGORIES['KANADYJKI'] and cat_b == CATEGORIES['KANADYJKI']):
                title = "Zestawienie: Kanadyjki vs Zestawy Naprawcze"
                kanadyjki = [i for i in group_a if 'zestaw naprawczy' not in (i.get('nazwa') or '').lower()]
                naprawcze = [i for i in group_b if 'zestaw naprawczy' in (i.get('nazwa') or '').lower()]
                k_c = len(kanadyjki)
                r_c = sum(int(i.get('ilosc', 0)) for i in naprawcze if str(i.get('ilosc', '')).isdigit())
                export_rows.append({
                    'Element': 'Kanadyjki',
                    'Potrzeba': k_c,
                    'Stan (Zestawy)': r_c,
                    'Różnica': r_c - k_c
                })
            elif (cat_a == CATEGORIES['NAMIOT'] and cat_b == CATEGORIES['ZELASTWO']) or \
                 (cat_a == CATEGORIES['ZELASTWO'] and cat_b == CATEGORIES['NAMIOT']):

                title = "Zestawienie: Namioty vs Omasztowanie"
                namioty = group_a if cat_a == CATEGORIES['NAMIOT'] else group_b
                zelastwo = group_b if cat_b == CATEGORIES['ZELASTWO'] else group_a
                
                n_stats = {}
                for n in namioty: t = n.get('typ', 'Nieokreślony'); n_stats[t] = n_stats.get(t, 0) + 1
                z_stats = {}
                for z in zelastwo: 
                    t = z.get('do_czego', 'Nieokreślone')
                    q = z.get('ilosc', 0)
                    try: q = int(q)
                    except (ValueError, TypeError): q = 0
                    z_stats[t] = z_stats.get(t, 0) + q
                all_t = sorted(list(set(n_stats.keys()) | set(z_stats.keys())))
                for t in all_t:
                    export_rows.append({
                        'Typ/Element': t,
                        'Potrzeba (Namioty)': n_stats.get(t, 0),
                        'Stan (Żelastwo)': z_stats.get(t, 0),
                        'Różnica': z_stats.get(t, 0) - n_stats.get(t, 0)
                    })
            else:
                title = f"Zestawienie: {cat_a.capitalize()} vs {cat_b.capitalize()}"
                stats_a = {}
                for i in group_a:
                    label = i.get('typ') or i.get('nazwa') or 'Inne'
                    stats_a[label] = stats_a.get(label, 0) + (int(i.get('ilosc', 1)) if str(i.get('ilosc', '')).isdigit() else 1)
                stats_b = {}
                for i in group_b:
                    label = i.get('typ') or i.get('nazwa') or 'Inne'
                    stats_b[label] = stats_b.get(label, 0) + (int(i.get('ilosc', 1)) if str(i.get('ilosc', '')).isdigit() else 1)
                all_l = sorted(list(set(stats_a.keys()) | set(stats_b.keys())))
                for l in all_l:
                    export_rows.append({
                        'Typ/Element': l,
                        'Potrzeba (A)': stats_a.get(l, 0),
                        'Stan (B)': stats_b.get(l, 0),
                        'Różnica': stats_b.get(l, 0) - stats_a.get(l, 0)
                    })
            
        filename = f"zestawienie_{preset or 'dynamic'}"
        if magazyn_id:
            filename += f"_{magazyn_id}"
            title += f" (Magazyn: {magazyn_id})"
        if fmt == 'csv': return export_to_csv(export_rows, filename)
        if fmt == 'xlsx': return export_to_xlsx(export_rows, filename)
        if fmt == 'docx': return export_to_docx(export_rows, filename, title)
        return export_to_pdf(export_rows, filename, title)

    # Standardowy eksport listy sprzętu (z opcją wyboru kolumn)
    columns = request.args.getlist('columns')
    
    # Odtwarzamy filtry identycznie jak w sprzet_list
    parent_id = request.args.get('parent_id')
    search_query = request.args.get('search')
    category = request.args.get('category')
    typ = request.args.get('typ')
    wodoszczelnosc = request.args.get('wodoszczelnosc')
    lokalizacja = request.args.get('lokalizacja')
    oficjalna_ewidencja = request.args.get('oficjalna_ewidencja')

    filters = []
    if category:
        filters.append(('category', '==', category))
    if typ:
        filters.append(('typ', '==', typ))
    if wodoszczelnosc:
        filters.append(('wodoszczelnosc', '==', wodoszczelnosc))
    if lokalizacja:
        filters.append(('lokalizacja', '==', lokalizacja))
    if oficjalna_ewidencja:
        filters.append(('oficjalna_ewidencja', '==', oficjalna_ewidencja))
    if parent_id:
        filters.append(('parent_id', '==', parent_id))

    if filters:
        items = get_items_by_filters(COLLECTION_SPRZET, filters, order_by='__name__', direction=firestore.Query.ASCENDING)
    else:
        items = get_all_sprzet()

    if search_query:
        s = search_query.lower()
        items = [
            i for i in items
            if s in str(i.get('id', '')).lower() or
               s in str(i.get('nazwa', '')).lower() or
               s in str(i.get('typ', '')).lower() or
               s in str(i.get('uwagi', '')).lower() or
               s in str(i.get('informacje', '')).lower()
        ]

    export_rows = []
    for it in items:
        export_rows.append({k: v for k, v in it.items() if k != 'zdjecia_lista_url'})

    filename = 'sprzet_export'
    title = 'Eksport sprzętu'

    if fmt == 'csv':
        return export_to_csv(export_rows, filename)
    if fmt == 'xlsx':
        return export_to_xlsx(export_rows, filename, columns=columns)
    if fmt == 'docx':
        return export_to_docx(export_rows, filename, title, columns=columns)
    if fmt == 'qr':
        qr_url = os.getenv('QR_URL')
        if not qr_url:
            flash('Eksport QR jest niedostępny: brak konfiguracji QR_URL.', 'warning')
            return export_to_pdf(export_rows, filename, title, columns=columns)
        return export_qr_codes_pdf(export_rows, filename, qr_url)
    return export_to_pdf(export_rows, filename, title, columns=columns)

@views_bp.route('/usterki/export/<format>')
@login_required
def export_usterki(format):
    """Eksportuje listę usterek zgodnie z aktualnymi filtrami."""
    fmt = (format or '').lower().strip()
    if fmt not in {'csv', 'xlsx', 'docx', 'pdf'}:
        flash('Nieobsługiwany format eksportu.', 'danger')
        return redirect(url_for('views.usterki_list', **request.args))

    status = request.args.get('status')
    magazyn = request.args.get('magazyn')
    sprzet_id = request.args.get('sprzet_id')
    oficjalna_ewidencja = request.args.get('oficjalna_ewidencja')

    usterki = get_all_usterki()
    sprzet_items = get_all_sprzet()
    sprzet_map = {s['id']: s for s in sprzet_items if 'id' in s}

    filtered = []
    for u in usterki:
        s = sprzet_map.get(u.get('sprzet_id'))
        u_row = dict(u)
        u_row['nazwa_sprzetu'] = s.get('nazwa', 'N/A') if s else 'USUNIĘTY'
        u_row['magazyn'] = s.get('lokalizacja', 'N/A') if s else 'N/A'
        u_row['oficjalna_ewidencja'] = s.get('oficjalna_ewidencja', 'Nie') if s else 'Nie'

        match = True
        if status and u_row.get('status') != status:
            match = False
        if magazyn and u_row.get('magazyn') != magazyn:
            match = False
        if sprzet_id and u_row.get('sprzet_id') != sprzet_id:
            match = False
        if oficjalna_ewidencja and u_row.get('oficjalna_ewidencja') != oficjalna_ewidencja:
            match = False

        if match:
            filtered.append(u_row)

    export_rows = [{k: v for k, v in row.items() if k != 'zdjecia_lista_url'} for row in filtered]

    filename = 'usterki_export'
    title = 'Eksport usterek'

    if fmt == 'csv':
        return export_to_csv(export_rows, filename)
    if fmt == 'xlsx':
        return export_to_xlsx(export_rows, filename)
    if fmt == 'docx':
        return export_to_docx(export_rows, filename, title)
    return export_to_pdf(export_rows, filename, title)

@views_bp.route('/sprzet/bulk-edit', methods=['POST'])
@quartermaster_required
def sprzet_bulk_edit():
    """Ekran masowej edycji sprzętu (QUARTERMASTER/ADMIN)."""
    token = request.form.get('_csrf_token')
    if not token or token != session.get('_csrf_token'):
        flash('Błąd weryfikacji CSRF.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    sprzet_ids = request.form.getlist('sprzet_ids')
    if not sprzet_ids:
        flash('Nie wybrano żadnych elementów.', 'warning')
        return redirect(url_for('views.sprzet_list'))

    # Pobieramy dane wybranych sprzętów, aby wyświetlić podsumowanie/przegląd przed masową edycją.
    all_sprzet = get_all_sprzet()
    sprzet_map = {s.get('id'): s for s in all_sprzet if isinstance(s, dict)}
    sprzet_selected = [sprzet_map[s_id] for s_id in sprzet_ids if s_id in sprzet_map]

    return_query = (request.form.get('return_query') or '').strip()
    cancel_url = url_for('views.sprzet_list') + (f'?{return_query}' if return_query else '')

    # Lista potencjalnych rodziców (magazyny + półki)
    sprzet_all = [s for s in get_all_sprzet() if s.get('category') in [CATEGORIES['MAGAZYN'], CATEGORIES['POLKA']]]

    return render_template(
        'sprzet_bulk_edit.html',
        sprzet_ids=sprzet_ids,
        sprzet_selected=sprzet_selected,
        return_query=return_query,
        cancel_url=cancel_url,
        sprzet_all=sprzet_all,
    )


@views_bp.route('/sprzet/bulk-edit/confirm', methods=['POST'])
@quartermaster_required
def sprzet_bulk_edit_confirm():
    """Wykonuje masową edycję sprzętu (QUARTERMASTER/ADMIN)."""
    token = request.form.get('_csrf_token')
    if not token or token != session.get('_csrf_token'):
        flash('Błąd weryfikacji CSRF.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    sprzet_ids = request.form.getlist('sprzet_ids')
    if not sprzet_ids:
        flash('Nie wybrano żadnych elementów.', 'warning')
        return redirect(url_for('views.sprzet_list'))

    # Zbieramy tylko pola niepuste = do aktualizacji.
    updates: dict[str, str] = {}
    for field in ['lokalizacja', 'category', 'wodoszczelnosc', 'stan_ogolny', 'oficjalna_ewidencja', 'uwagi']:
        val = (request.form.get(field) or '').strip()
        if val:
            updates[field] = val

    # parent_id obsługuje specjalne "none" => brak rodzica
    parent_id_val = (request.form.get('parent_id') or '').strip()
    if parent_id_val:
        updates['parent_id'] = '' if parent_id_val.lower() == 'none' else parent_id_val

    if not updates:
        flash('Nie ustawiono żadnych zmian.', 'info')
        return_query = (request.form.get('return_query') or '').strip()
        return redirect(url_for('views.sprzet_list') + (f'?{return_query}' if return_query else ''))

    changed = 0
    skipped_missing = 0
    errors = 0
    error_details: list[str] = []

    for sid in sprzet_ids:
        try:
            current = get_sprzet_item(sid)
            if not current:
                skipped_missing += 1
                continue

            before_data = {k: v for k, v in current.items() if k not in ['id', 'zdjecia_lista_url']}

            effective_updates = {}
            for k, v in updates.items():
                if before_data.get(k) != v:
                    effective_updates[k] = v

            if not effective_updates:
                continue

            update_sprzet(sid, **effective_updates)

            after_data = dict(before_data)
            after_data.update(effective_updates)
            add_log(session.get('user_id'), 'bulk_edit', 'sprzet', sid,
                    before=before_data, after=after_data,
                    details={'fields': list(effective_updates.keys())})
            changed += 1
        except Exception as e:
            errors += 1
            error_msg = f"{sid}: {str(e)}"
            error_details.append(error_msg)
            current_app.logger.error(f"Bulk edit error: {error_msg}", exc_info=True)

    if changed:
        flash(f'Zapisano zmiany dla {changed} pozycji.', 'success')
    if skipped_missing:
        flash(f'Pominięto {skipped_missing} pozycji (nie znaleziono w bazie).', 'warning')
    if errors:
        if errors <= MAX_DISPLAYED_ERRORS:
            flash(f'Wystąpiły błędy dla {errors} pozycji:', 'danger')
        else:
            flash(f'Wystąpiły błędy dla {errors} pozycji. Pierwsze {MAX_DISPLAYED_ERRORS} błędów:', 'danger')
        for err in error_details[:MAX_DISPLAYED_ERRORS]:
            flash(err, 'danger')
        if errors > MAX_DISPLAYED_ERRORS:
            flash(f'... i {errors - MAX_DISPLAYED_ERRORS} więcej. Sprawdź logi serwera dla szczegółów.', 'danger')

    return_query = (request.form.get('return_query') or '').strip()
    return redirect(url_for('views.sprzet_list') + (f'?{return_query}' if return_query else ''))

@views_bp.route('/usterki/bulk-delete', methods=['POST'])
@admin_required
def usterki_bulk_delete():
    """Masowe usuwanie usterek (tylko ADMIN)."""
    token = request.form.get('_csrf_token')
    if not token or token != session.get('_csrf_token'):
        flash('Błąd weryfikacji CSRF.', 'danger')
        return redirect(url_for('views.usterki_list'))

    usterka_ids = request.form.getlist('usterka_ids')
    if not usterka_ids:
        flash('Nie wybrano żadnych usterek.', 'warning')
        return redirect(url_for('views.usterki_list'))

    count = 0
    errors = 0
    error_details = []

    for uid in usterka_ids:
        try:
            delete_item(COLLECTION_USTERKI, uid)
            add_log(session.get('user_id'), 'delete', 'usterka', uid)
            count += 1
        except Exception as e:
            errors += 1
            error_msg = f"{uid}: {str(e)}"
            error_details.append(error_msg)
            current_app.logger.error(f"Bulk delete usterki error: {error_msg}", exc_info=True)

    if count:
        flash(f'Pomyślnie usunięto {count} usterek.', 'success')

    if errors:
        if errors <= MAX_DISPLAYED_ERRORS:
            flash(f'Wystąpiły błędy przy usuwaniu {errors} usterek:', 'danger')
        else:
            flash(f'Wystąpiły błędy przy usuwaniu {errors} usterek. Pierwsze {MAX_DISPLAYED_ERRORS} błędów:', 'danger')

        for err in error_details[:MAX_DISPLAYED_ERRORS]:
            flash(err, 'danger')

    return redirect(url_for('views.usterki_list'))
