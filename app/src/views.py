from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, current_app
import os
import uuid
import json
import pandas as pd
from werkzeug.utils import secure_filename
from google.cloud import firestore
import qrcode
from io import BytesIO

from . import get_firestore_client
from .auth import login_required, admin_required, quartermaster_required
from .gcs_utils import list_equipment_photos, upload_blob_to_gcs, refresh_urls
from .db_firestore import (
    get_sprzet_item, get_usterki_for_sprzet, get_usterka_item,
    update_usterka, update_sprzet, get_all_sprzet, get_all_usterki, get_items_by_filters,
    COLLECTION_SPRZET, COLLECTION_USTERKI, COLLECTION_WYPOZYCZENIA, add_item, set_item,
    add_log, get_all_logs, update_item, delete_item, CATEGORIES, MAGAZYNY_NAMES,
    add_loan, get_active_loans, get_loans_for_item, mark_loan_returned, _warsaw_now,
    get_all_items, get_item
)
from .exports import export_to_csv, export_to_xlsx, export_to_docx, export_to_pdf
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

    # Walidacja jednostki dla żelastwo/kanadyjki (skróty)
    if category_value == CATEGORIES['ZELASTWO']:
        allowed = {'zest.', 'szt.'}
        # domyślnie zest.
        if 'jednostka' not in data:
            data['jednostka'] = 'zest.'
        elif data.get('jednostka') not in allowed:
            data.pop('jednostka', None)
            data['jednostka'] = 'zest.'
    if category_value == CATEGORIES['KANADYJKI']:
        # Kanadyjki tylko szt.
        data['jednostka'] = 'szt.'

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
@login_required
def sprzet_list():
    parent_id = request.args.get('parent_id')
    search_query = request.args.get('search')
    category = request.args.get('category')

    # Podstawowe filtry
    typ = request.args.get('typ')
    wodoszczelnosc = request.args.get('wodoszczelnosc')
    lokalizacja = request.args.get('lokalizacja')

    filters = []
    if category:
        filters.append(('category', '==', category))
    if typ:
        filters.append(('typ', '==', typ))
    if wodoszczelnosc:
        filters.append(('wodoszczelnosc', '==', wodoszczelnosc))
    if lokalizacja:
        filters.append(('lokalizacja', '==', lokalizacja))

    if parent_id:
        filters.append(('parent_id', '==', parent_id))

    if filters:
        items = get_items_by_filters(COLLECTION_SPRZET, filters, order_by='__name__', direction=firestore.Query.ASCENDING)
    else:
        # Jeśli nie ma filtrów ani parent_id, a nie jest to wyszukiwanie, pokaż tylko Magazyny
        if not search_query:
            items = get_all_sprzet(category=CATEGORIES['MAGAZYN'])
        else:
            items = get_all_sprzet()

    # Wyszukiwanie lokalne (Firestore nie wspiera łatwo full-text search bez zewnętrznych usług)
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

    # Pobieramy unikalne wartości do filtrów
    all_items = get_all_sprzet()
    typy = sorted(list(set(i.get('typ') for i in all_items if i.get('typ'))))
    lokalizacje = sorted(list(set(i.get('lokalizacja') for i in all_items if i.get('lokalizacja'))))
    wodoszczelnosci = sorted(list(set(i.get('wodoszczelnosc') for i in all_items if i.get('wodoszczelnosc'))))
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
                    'magazyn_display': rep.get('magazyn_display')
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
                    'magazyn_display': rep.get('magazyn_display')
                })
            else:
                grouped_items.extend(group)

        grouped_items.extend(other_items)
        items = grouped_items

    parent_item = get_sprzet_item(parent_id) if parent_id else None

    return render_template('sprzet_list.html', 
                           sprzet_list=items, 
                           typy=typy, 
                           lokalizacje=lokalizacje, 
                           wodoszczelnosci=wodoszczelnosci,
                           kategorie=kategorie,
                           parent_item=parent_item,
                           selected_filters=request.args)


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
        from .gcs_utils import extract_blob_name
        zdjecia_do_usuniecia = request.form.getlist('usun_zdjecia')
        blob_names_do_usuniecia = [extract_blob_name(url) for url in zdjecia_do_usuniecia]

        aktualne_zdjecia = sprzet.get('zdjecia', [])
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
    if sprzet.get('zdjecia'):
        sprzet['zdjecia_lista_url'] = refresh_urls(sprzet['zdjecia'])
    else:
        sprzet['zdjecia_lista_url'] = []

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
    if zdjecia_z_bazy:
        sprzet_item['zdjecia_lista_url'] = refresh_urls(zdjecia_z_bazy)
    else:
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

    return render_template('sprzet_card.html', sprzet=sprzet_item,
                           usterki=get_usterki_for_sprzet(sprzet_id),
                           logs=logs,
                           loans=loans,
                           active_loan=active_loan)


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

    # Generuj URL do strony sprzętu
    target_url = url_for('views.sprzet_card', sprzet_id=sprzet_id, _external=True)

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



# =======================================================================
#                       WIDOKI USTERK
# =======================================================================

@views_bp.route('/usterki')
@login_required
def usterki_list():
    """Panel administratora - lista wszystkich usterek."""
    status = request.args.get('status')
    magazyn = request.args.get('magazyn')
    sprzet_id = request.args.get('sprzet_id')

    usterki = get_all_usterki()
    sprzet_items = get_all_sprzet()
    sprzet_map = {s['id']: s for s in sprzet_items}
    
    filtered_usterki = []
    for u in usterki:
        s = sprzet_map.get(u.get('sprzet_id'))
        u['nazwa_sprzetu'] = s.get('nazwa', 'N/A') if s else 'USUNIĘTY'
        u['magazyn'] = s.get('lokalizacja', 'N/A') if s else 'N/A' # Używamy lokalizacja jako magazyn
        
        # Filtrowanie w pamięci
        match = True
        if status and u.get('status') != status:
            match = False
        if magazyn and u.get('magazyn') != magazyn:
            match = False
        if sprzet_id and u.get('sprzet_id') != sprzet_id:
            match = False
            
        if match:
            filtered_usterki.append(u)
    
    statuses = sorted(list(set(u.get('status') for u in usterki if u.get('status'))))
    magazyny = sorted(list(set(s.get('lokalizacja') for s in sprzet_items if s.get('lokalizacja'))))
    ids_sprzetu = sorted(list(set(u.get('sprzet_id') for u in usterki if u.get('sprzet_id'))))

    return render_template('usterki_list.html', 
                           usterki=filtered_usterki,
                           statuses=statuses,
                           magazyny=magazyny,
                           ids_sprzetu=ids_sprzetu,
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
    
    # Pobieramy tylko ostatnie 15 logów dla wydajności karty
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
        from .gcs_utils import extract_blob_name
        zdjecia_do_usuniecia = request.form.getlist('usun_zdjecia')
        blob_names_do_usuniecia = [extract_blob_name(url) for url in zdjecia_do_usuniecia]

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

@views_bp.route('/sprzet/export/<format>')
@login_required
def export_sprzet(format):
    """Eksportuje listę sprzętu zgodnie z aktualnymi filtrami."""
    fmt = (format or '').lower().strip()
    if fmt not in {'csv', 'xlsx', 'docx', 'pdf'}:
        flash('Nieobsługiwany format eksportu.', 'danger')
        return redirect(url_for('views.sprzet_list', **request.args))

    # Odtwarzamy filtry identycznie jak w sprzet_list (bez logiki "domyślnie tylko magazyny")
    parent_id = request.args.get('parent_id')
    search_query = request.args.get('search')
    category = request.args.get('category')
    typ = request.args.get('typ')
    wodoszczelnosc = request.args.get('wodoszczelnosc')
    lokalizacja = request.args.get('lokalizacja')

    filters = []
    if category:
        filters.append(('category', '==', category))
    if typ:
        filters.append(('typ', '==', typ))
    if wodoszczelnosc:
        filters.append(('wodoszczelnosc', '==', wodoszczelnosc))
    if lokalizacja:
        filters.append(('lokalizacja', '==', lokalizacja))
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
        return export_to_xlsx(export_rows, filename)
    if fmt == 'docx':
        return export_to_docx(export_rows, filename, title)
    return export_to_pdf(export_rows, filename, title)

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

    usterki = get_all_usterki()
    sprzet_items = get_all_sprzet()
    sprzet_map = {s['id']: s for s in sprzet_items if 'id' in s}

    filtered = []
    for u in usterki:
        s = sprzet_map.get(u.get('sprzet_id'))
        u_row = dict(u)
        u_row['nazwa_sprzetu'] = s.get('nazwa', 'N/A') if s else 'USUNIĘTY'
        u_row['magazyn'] = s.get('lokalizacja', 'N/A') if s else 'N/A'

        match = True
        if status and u_row.get('status') != status:
            match = False
        if magazyn and u_row.get('magazyn') != magazyn:
            match = False
        if sprzet_id and u_row.get('sprzet_id') != sprzet_id:
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

    return_query = (request.form.get('return_query') or '').strip()
    cancel_url = url_for('views.sprzet_list') + (f'?{return_query}' if return_query else '')

    # Lista potencjalnych rodziców (magazyny + półki)
    sprzet_all = [s for s in get_all_sprzet() if s.get('category') in [CATEGORIES['MAGAZYN'], CATEGORIES['POLKA']]]

    return render_template(
        'sprzet_bulk_edit.html',
        sprzet_ids=sprzet_ids,
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
    for field in ['lokalizacja', 'category', 'wodoszczelnosc', 'stan_ogolny', 'uwagi']:
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
