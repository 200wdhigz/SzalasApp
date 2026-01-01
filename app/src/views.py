from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
import os
import uuid
import json
import pandas as pd
from werkzeug.utils import secure_filename
from google.cloud import firestore
import qrcode
from io import BytesIO

from . import get_firestore_client
from .auth import login_required, admin_required
from .gcs_utils import list_equipment_photos, upload_blob_to_gcs, refresh_urls
from .db_firestore import (
    get_sprzet_item, get_usterki_for_sprzet, get_usterka_item, 
    update_usterka, get_all_sprzet, get_all_usterki, get_items_by_filters,
    COLLECTION_SPRZET, COLLECTION_USTERKI, add_item, set_item,
    add_log, get_all_logs, update_item, delete_item
)
from .exports import export_to_csv, export_to_xlsx, export_to_docx, export_to_pdf
from .recaptcha import verify_recaptcha

views_bp = Blueprint('views', __name__, url_prefix='/')

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
            blob_name = f"{folder}/{id_prefix}/{id_prefix}_foto{i:02d}.png"
        else:
            filename = secure_filename(f.filename)
            base, ext = os.path.splitext(filename)
            blob_name = f"{folder}/{base}_{uuid.uuid4().hex[:8]}{ext}"

        url = upload_blob_to_gcs(blob_name, f.stream, f.mimetype)
        saved_urls.append(url)
    return saved_urls, None


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
    # Pobieranie parametrów filtrowania
    typ = request.args.get('typ')
    wodoszczelnosc = request.args.get('wodoszczelnosc')
    lokalizacja = request.args.get('lokalizacja')

    filters = []
    if typ:
        filters.append(('typ', '==', typ))
    if wodoszczelnosc:
        filters.append(('wodoszczelnosc', '==', wodoszczelnosc))
    if lokalizacja:
        filters.append(('lokalizacja', '==', lokalizacja))

    if filters:
        items = get_items_by_filters(COLLECTION_SPRZET, filters, order_by='__name__', direction=firestore.Query.ASCENDING)
    else:
        items = get_all_sprzet()

    # Pobieramy unikalne wartości do filtrów (można to zoptymalizować, np. trzymać w osobnej kolekcji)
    # Na razie pobieramy wszystko do wyciągnięcia opcji, jeśli nie ma ich zbyt wiele
    all_items = get_all_sprzet()
    typy = sorted(list(set(i.get('typ') for i in all_items if i.get('typ'))))
    lokalizacje = sorted(list(set(i.get('lokalizacja') for i in all_items if i.get('lokalizacja'))))
    wodoszczelnosci = sorted(list(set(i.get('wodoszczelnosc') for i in all_items if i.get('wodoszczelnosc'))))

    return render_template('sprzet_list.html', 
                           sprzet_list=items, 
                           typy=typy, 
                           lokalizacje=lokalizacje, 
                           wodoszczelnosci=wodoszczelnosci,
                           selected_filters=request.args)


# =======================================================================
#                       WIDOKI SPRZĘTU I ZDJĘĆ
# =======================================================================

@views_bp.route('/sprzet/add', methods=['GET', 'POST'])
@admin_required
def sprzet_add():
    if request.method == 'POST':
        sprzet_id = request.form.get('id').upper()
        if get_sprzet_item(sprzet_id):
            flash(f'Sprzęt o ID {sprzet_id} już istnieje!', 'danger')
        else:
            data = {k: v for k, v in request.form.items() if k != 'id'}
            set_item(COLLECTION_SPRZET, sprzet_id, data)
            add_log(session.get('user_id'), 'add', 'sprzet', sprzet_id, data)
            flash(f'Sprzęt {sprzet_id} został dodany.', 'success')
            return redirect(url_for('views.sprzet_list'))
    return render_template('sprzet_edit.html', sprzet=None)

@views_bp.route('/sprzet/import', methods=['GET', 'POST'])
@login_required
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
                        old_data = all_sprzet[sid]
                        diffs = {}
                        for k, v in new_data.items():
                            old_val = str(old_data.get(k, '')).strip()
                            if v and v != old_val:
                                diffs[k] = {'old': old_val, 'new': v}
                        
                        if diffs:
                            diff_data.append({'id': sid, 'diffs': diffs, 'new_data': new_data})
                    else:
                        diff_data.append({'id': sid, 'diffs': {}, 'new_data': new_data})
                
                if not diff_data:
                    flash('Brak różnic lub nowych danych do zaimportowania.', 'info')

            except Exception as e:
                flash(f'Błąd przetwarzania pliku: {e}', 'danger')

    return render_template('sprzet_import.html', diff_data=diff_data)

@views_bp.route('/sprzet/import/confirm', methods=['POST'])
@admin_required
def sprzet_import_confirm():
    import_ids = request.form.getlist('import_ids')
    count = 0
    for sid in import_ids:
        data_json = request.form.get(f'data_{sid}')
        if data_json:
            data = json.loads(data_json)
            set_item(COLLECTION_SPRZET, sid, data)
            add_log(session.get('user_id'), 'import', 'sprzet', sid, data)
            count += 1
    
    flash(f'Pomyślnie zaimportowano/zaktualizowano {count} pozycji.', 'success')
    return redirect(url_for('views.sprzet_list'))

@views_bp.route('/sprzet/edit/<sprzet_id>', methods=['GET', 'POST'])
@login_required
def sprzet_edit(sprzet_id):
    sprzet = get_sprzet_item(sprzet_id)
    if not sprzet:
        flash('Nie znaleziono sprzętu.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    if request.method == 'POST':
        data = {k: v for k, v in request.form.items() if k != 'id'}

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

        set_item(COLLECTION_SPRZET, sprzet_id, data)
        add_log(session.get('user_id'), 'edit', 'sprzet', sprzet_id, data)
        flash(f'Sprzęt {sprzet_id} został zaktualizowany.', 'success')
        return redirect(url_for('views.sprzet_card', sprzet_id=sprzet_id))
    
    # Priorytet dla zdjęć zapisanych w bazie danych (odświeżamy linki), fallback do listowania GCS
    if sprzet.get('zdjecia'):
        sprzet['zdjecia_lista_url'] = refresh_urls(sprzet['zdjecia'])
    else:
        sprzet['zdjecia_lista_url'] = []

    return render_template('sprzet_edit.html', sprzet=sprzet)

@views_bp.route('/sprzet/delete/<sprzet_id>', methods=['POST'])
@admin_required
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
        recaptcha_token = request.form.get('g-recaptcha-response')

        if not opis:
            flash('Opis usterki nie może być pusty!', 'warning')
        elif not verify_recaptcha(recaptcha_token, 'submit_defect'):
            flash('Weryfikacja reCAPTCHA nie powiodła się.', 'danger')
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
                        'data_zgloszenia': firestore.SERVER_TIMESTAMP,
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

    return render_template('sprzet_card.html', sprzet=sprzet_item, 
                           usterki=get_usterki_for_sprzet(sprzet_id))


@views_bp.route('/sprzet/<sprzet_id>/qrcode')
def generate_qr_code(sprzet_id):
    """Generuje kod QR dla danego sprzętu i zwraca go jako obraz PNG."""
    # Sprawdź czy sprzęt istnieje
    sprzet_item = get_sprzet_item(sprzet_id)
    if not sprzet_item:
        flash(f'Sprzęt "{sprzet_id}" nie został znaleziony.', 'danger')
        return redirect(url_for('views.sprzet_list'))

    # Generuj URL do strony sprzętu
    base_url = request.host_url.rstrip('/')
    target_url = f'https://200wdhigz.github.io/sprzet/{sprzet_id}'

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

    # Zwróć plik do pobrania
    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
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
    return render_template('usterka_card.html', usterka=usterka)

@views_bp.route('/usterka/edit/<usterka_id>', methods=['GET', 'POST'])
@login_required
def usterka_edit(usterka_id):
    """Widok edycji usterki."""
    usterka = get_usterka_item(usterka_id)
    if not usterka:
        flash('Nie znaleziono usterki.', 'danger')
        return redirect(url_for('views.usterki_list'))

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

        status = request.form.get('status')
        data = {
            'uwagi_admina': request.form.get('uwagi_admina'),
            'opis': request.form.get('opis'),
            'zdjecia': nowa_lista_zdjec
        }
        if status in ['oczekuje', 'w trakcie', 'naprawiona', 'odrzucona']:
            data['status'] = status

        update_usterka(usterka_id, **data)
        add_log(session.get('user_id'), 'edit', 'usterka', usterka_id, data)
        flash(f'Usterka {usterka_id} zaktualizowana.', 'success')
        return redirect(url_for('views.usterka_card', usterka_id=usterka_id))

    usterka['zdjecia_lista_url'] = refresh_urls(usterka.get('zdjecia', []))
    return render_template('usterka_edit.html', usterka=usterka)

@views_bp.route('/usterka/delete/<usterka_id>', methods=['POST'])
@login_required
def usterka_delete(usterka_id):
    """Usuwanie usterki."""
    delete_item(COLLECTION_USTERKI, usterka_id)
    add_log(session.get('user_id'), 'delete', 'usterka', usterka_id)
    flash(f'Usterka {usterka_id} została usunięta.', 'success')
    return redirect(url_for('views.usterki_list'))


@views_bp.route('/logs')
@login_required
def logs_list():
    """Wyświetla listę wszystkich logów (dostępne dla zalogowanych)."""
    from .db_users import get_all_users

    logs = get_all_logs()
    users = get_all_users()

    # Tworzymy mapowanie user_id -> imię i nazwisko
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

    # Dodajemy user_name do każdego logu
    for log in logs:
        log['user_name'] = user_map.get(log.get('user_id'), log.get('user_id', 'Nieznany'))

    return render_template('logs.html', logs=logs)

# =======================================================================
#                       EKSPORTY
# =======================================================================

@views_bp.route('/export/sprzet')
@login_required
def export_sprzet():
    fmt = request.args.get('format', 'csv')
    typ = request.args.get('typ')
    wodoszczelnosc = request.args.get('wodoszczelnosc')
    lokalizacja = request.args.get('lokalizacja')

    filters = []
    if typ: filters.append(('typ', '==', typ))
    if wodoszczelnosc: filters.append(('wodoszczelnosc', '==', wodoszczelnosc))
    if lokalizacja: filters.append(('lokalizacja', '==', lokalizacja))

    if filters:
        items = get_items_by_filters(COLLECTION_SPRZET, filters, order_by='__name__', direction=firestore.Query.ASCENDING)
    else:
        items = get_all_sprzet()

    # Usuwamy pola niepotrzebne w raporcie
    for i in items:
        i.pop('zdjecia_lista_url', None)
        i.pop('zdjecie_glowne_url', None)

    filename = "raport_sprzet"
    title = "Raport Sprzętu"

    if fmt == 'xlsx': return export_to_xlsx(items, filename)
    if fmt == 'docx': return export_to_docx(items, filename, title)
    if fmt == 'pdf': return export_to_pdf(items, filename, title)
    return export_to_csv(items, filename)

@views_bp.route('/export/usterki')
@login_required
def export_usterki():
    fmt = request.args.get('format', 'csv')
    status = request.args.get('status')
    magazyn = request.args.get('magazyn')
    sprzet_id = request.args.get('sprzet_id')

    usterki = get_all_usterki()
    sprzet_items = get_all_sprzet()
    sprzet_map = {s['id']: s for s in sprzet_items}
    
    filtered = []
    for u in usterki:
        s = sprzet_map.get(u.get('sprzet_id'))
        u['nazwa_sprzetu'] = s.get('nazwa', 'N/A') if s else 'USUNIĘTY'
        u['magazyn'] = s.get('lokalizacja', 'N/A') if s else 'N/A'
        
        match = True
        if status and u.get('status') != status: match = False
        if magazyn and u.get('magazyn') != magazyn: match = False
        if sprzet_id and u.get('sprzet_id') != sprzet_id: match = False
            
        if match:
            # Usuwamy pola niepotrzebne
            u.pop('zdjecia', None)
            u.pop('zdjecia_lista_url', None)
            filtered.append(u)

    filename = "raport_usterki"
    title = "Raport Usterek"

    if fmt == 'xlsx': return export_to_xlsx(filtered, filename)
    if fmt == 'docx': return export_to_docx(filtered, filename, title)
    if fmt == 'pdf': return export_to_pdf(filtered, filename, title)
    return export_to_csv(filtered, filename)
