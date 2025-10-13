# src/views.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import os
import time
from werkzeug.utils import secure_filename

from .auth import login_required
# Importy z Twoich modułów do obsługi baz danych i storage
from .gcs_utils import list_sprzet_photos
from .db_firestore import get_sprzet_item, get_usterki_for_sprzet, get_usterka_item, update_usterka, get_all_sprzet, \
    get_all_usterki, add_usterka
from .recaptcha import verify_recaptcha

views_bp = Blueprint('views', __name__, url_prefix='/')


# =======================================================================
#               WIDOKI BAZOWE (Logowanie/Wylogowanie)
# =======================================================================

@views_bp.route('/')
def index():
    # Pobieranie listy
    items = get_all_sprzet()

    # Zwrócenie listy do szablonu
    return render_template('index.html', sprzet_list=items)


# =======================================================================
#                       WIDOKI SPRZĘTU I ZDJĘĆ
# =======================================================================

@views_bp.route('/sprzet/<sprzet_id>', methods=['GET', 'POST'])
def sprzet_card(sprzet_id):
    sprzet_item = get_sprzet_item(sprzet_id)

    if sprzet_item is None:
        flash(f'Sprzęt o ID "{sprzet_id}" nie został znaleziony.', 'danger')
        return redirect(url_for('views.home'))

    usterki = get_usterki_for_sprzet(sprzet_id)

    # ❗ KLUCZOWA ZMIANA: Pobieramy listę zdjęć dynamicznie z GCS
    photo_urls = list_sprzet_photos(sprzet_id)

    # Upewnij się, że lista zdjęć jest dostępna w szablonie pod kluczem,
    # którego używa karuzela
    sprzet_item['zdjecia_lista_url'] = photo_urls

    if request.method == 'POST':
        opis_usterki = request.form['opis_usterki']
        zgloszono_przez = request.form.get('zgloszono_przez', 'Anonim')
        recaptcha_token = request.form.get('g-recaptcha-response')

        if not opis_usterki:
            flash('Opis usterki nie może być pusty!', 'warning')
        elif not verify_recaptcha(recaptcha_token, 'submit_defect'):
            flash('Weryfikacja bezpieczeństwa (reCAPTCHA) nie powiodła się. Spróbuj ponownie.', 'danger')
        else:
            # 2. DODAWANIE USTERKI
            # ZAMIENIAMY: conn.execute(...)
            add_usterka(sprzet_id, opis_usterki, zgloszono_przez)  # <-- Używamy nowej funkcji Firestore

            flash(f'Usterka dla **{sprzet_id}** została pomyślnie zgłoszona!', 'success')
            return redirect(url_for('views.sprzet_card', sprzet_id=sprzet_id))
    return render_template('sprzet_card.html',
                           sprzet=sprzet_item,
                           usterki=usterki)



# =======================================================================
#                       WIDOKI USTERK
# =======================================================================

@views_bp.route('/usterki')
@login_required
def usterki_list():
    """
    Panel administratora - wyświetla listę wszystkich zgłoszonych usterek.
    """

    # 1. Pobranie wszystkich usterek z Firestore
    wszystkie_usterki = get_all_usterki()

    # 2. Wzbogacenie danych o nazwę sprzętu
    # Usterki zawierają tylko 'sprzet_id', ale admin potrzebuje 'nazwy'

    # Tworzymy mapowanie, aby unikać wielokrotnego odpytywania bazy o ten sam sprzęt
    sprzet_cache = {}

    for usterka in wszystkie_usterki:
        sprzet_id = usterka.get('sprzet_id')

        if sprzet_id not in sprzet_cache:
            # Wczytaj dane sprzętu z Firestore i zapisz w cache
            sprzet_data = get_sprzet_item(sprzet_id)
            sprzet_cache[sprzet_id] = sprzet_data

        # Dodaj nazwę i inne przydatne dane do słownika usterki
        if sprzet_cache[sprzet_id]:
            usterka['nazwa_sprzetu'] = sprzet_cache[sprzet_id].get('nazwa', 'Brak Nazwy')
            usterka['magazyn'] = sprzet_cache[sprzet_id].get('magazyn', 'N/A')
        else:
            usterka['nazwa_sprzetu'] = 'SPRZĘT USUNIĘTY'
            usterka['magazyn'] = 'N/A'

    # 3. Renderowanie szablonu z listą
    return render_template('usterki_list.html', usterki=wszystkie_usterki)


@views_bp.route('/usterka/edit/<usterka_id>', methods=('GET', 'POST'))
@login_required
def usterka_edit(usterka_id):
    """Widok do edycji statusu i uwag dla pojedynczej usterki (tylko dla admina)."""

    # Używamy już zaimportowanych funkcji: get_usterka_item i update_usterka
    usterka = get_usterka_item(usterka_id)

    if not usterka:
        # Ten warunek może być potrzebny, jeśli brakuje danych o sprzęcie powiązanym z usterką
        flash('Nie znaleziono usterki do edycji.', 'danger')
        return redirect(url_for('views.usterki_list'))

    if request.method == 'POST':
        nowy_status = request.form.get('status')
        uwagi_admina = request.form.get('uwagi_admina')

        valid_statuses = ['oczekuje', 'w trakcie', 'naprawiona', 'odrzucona']

        if nowy_status and nowy_status in valid_statuses:
            # Słownik z danymi do aktualizacji
            update_data = {
                'status': nowy_status,
                'uwagi_admina': uwagi_admina,
                # Możesz tu dodać: 'aktualizacja_przez': session.get('user_email')
            }

            update_usterka(usterka_id, **update_data)

            flash(f'Status usterki {usterka_id} zmieniono na: {nowy_status}.', 'success')
            return redirect(url_for('views.usterki_list'))
        else:
            flash('Wybierz prawidłowy status.', 'warning')

    return render_template('usterka_edit.html', usterka=usterka)
