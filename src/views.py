# python
# file: src/views.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import uuid
from werkzeug.utils import secure_filename
from google.cloud import firestore

from . import get_firestore_client
from .auth import login_required
from .gcs_utils import list_equipment_photos, upload_blob_to_gcs
from .db_firestore import (
    get_sprzet_item, get_usterki_for_sprzet, get_usterka_item, 
    update_usterka, get_all_sprzet, get_all_usterki
)
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
def index():
    # Pobieranie listy
    items = get_all_sprzet()

    # Zwrócenie listy do szablonu
    return render_template('sprzet_list.html', sprzet_list=items)


# =======================================================================
#                       WIDOKI SPRZĘTU I ZDJĘĆ
# =======================================================================

@views_bp.route('/sprzet/<sprzet_id>', methods=['GET', 'POST'])
def sprzet_card(sprzet_id):
    sprzet_item = get_sprzet_item(sprzet_id)
    if not sprzet_item:
        flash(f'Sprzęt "{sprzet_id}" nie został znaleziony.', 'danger')
        return redirect(url_for('views.index'))

    if request.method == 'POST':
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
                    doc_ref.set({
                        'sprzet_id': sprzet_id,
                        'opis': opis,
                        'zgloszono_przez': request.form.get('zgloszono_przez', 'Anonim'),
                        'data_zgloszenia': firestore.SERVER_TIMESTAMP,
                        'status': 'oczekuje',
                        'zdjecia': urls
                    })
                    flash(f'Usterka dla {sprzet_id} została zgłoszona!', 'success')
            except Exception as e:
                flash(f'Błąd: {e}', 'danger')
            return redirect(url_for('views.sprzet_card', sprzet_id=sprzet_id))

    sprzet_item['zdjecia_lista_url'] = list_equipment_photos(sprzet_id)
    return render_template('sprzet_card.html', sprzet=sprzet_item, 
                           usterki=get_usterki_for_sprzet(sprzet_id))



# =======================================================================
#                       WIDOKI USTERK
# =======================================================================

@views_bp.route('/usterki')
@login_required
def usterki_list():
    """Panel administratora - lista wszystkich usterek."""
    usterki = get_all_usterki()
    sprzet_map = {s['id']: s for s in get_all_sprzet()}
    
    for u in usterki:
        s = sprzet_map.get(u.get('sprzet_id'))
        u['nazwa_sprzetu'] = s.get('nazwa', 'N/A') if s else 'USUNIĘTY'
        u['magazyn'] = s.get('magazyn', 'N/A') if s else 'N/A'
        
    return render_template('usterki_list.html', usterki=usterki)

@views_bp.route('/usterka/<usterka_id>', methods=['GET', 'POST'])
@login_required
def usterka_card(usterka_id):
    """Widok edycji usterki (admin)."""
    usterka = get_usterka_item(usterka_id)
    if not usterka:
        flash('Nie znaleziono usterki.', 'danger')
        return redirect(url_for('views.usterki_list'))

    if request.method == 'POST':
        urls, err = process_uploads(request.files.getlist('zdjecia_usterki'), f'usterki/{usterka_id}')
        if err:
            flash(err, 'warning')
        else:
            status = request.form.get('status')
            data = {'uwagi_admina': request.form.get('uwagi_admina')}
            if status in ['oczekuje', 'w trakcie', 'naprawiona', 'odrzucona']:
                data['status'] = status
            if urls:
                data['zdjecia'] = (usterka.get('zdjecia') or []) + urls
            
            update_usterka(usterka_id, **data)
            flash(f'Usterka {usterka_id} zaktualizowana.', 'success')
            return redirect(url_for('views.usterki_list'))

    usterka['zdjecia_lista_url'] = usterka.get('zdjecia', [])
    return render_template('usterka_card.html', usterka=usterka)
