from google.cloud import recaptchaenterprise_v1
from google.cloud.recaptchaenterprise_v1 import Assessment
import os


# To jest kod, który dostarczyłeś, zmieniony, aby używał zmiennych z .env
def create_assessment(
        project_id: str, recaptcha_key: str, token: str, recaptcha_action: str
) -> Assessment:
    """Tworzy ocenę reCAPTCHA Enterprise."""

    # Inicjalizacja klienta. W Cloud Run użyje Application Default Credentials.
    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()

    event = recaptchaenterprise_v1.Event(site_key=recaptcha_key, token=token)
    assessment = recaptchaenterprise_v1.Assessment(event=event)
    project_name = f"projects/{project_id}"

    request = recaptchaenterprise_v1.CreateAssessmentRequest(
        assessment=assessment, parent=project_name
    )

    response = client.create_assessment(request)
    return response


# Funkcja pomocnicza do użycia we Flasku
def verify_recaptcha(recaptcha_token: str, action: str) -> bool:
    """Weryfikuje token reCAPTCHA i sprawdza wynik."""

    project_id = os.getenv('GCP_PROJECT_ID')
    site_key = os.getenv('RECAPTCHA_SITE_KEY')

    if not project_id or not site_key:
        print("BŁĄD KONFIGURACJI: Brak GCP_PROJECT_ID lub RECAPTCHA_SITE_KEY w .env.")
        return False

    response = create_assessment(
        project_id=project_id,
        recaptcha_key=site_key,
        token=recaptcha_token,
        recaptcha_action=action
    )

    # Minimalna akceptowalna ocena (score). Standardowo dla v3 jest to 0.5.
    # Wartość 0.7 jest zalecana dla wrażliwych działań.
    MIN_SCORE = 0.5

    if not response or not response.token_properties.valid:
        print(f"RECAPTCHA INVALID: {response.token_properties.invalid_reason}")
        return False

    if response.token_properties.action != action:
        print(f"RECAPTCHA ACTION MISMATCH: Oczekiwano {action}, otrzymano {response.token_properties.action}")
        return False

    if response.risk_analysis.score < MIN_SCORE:
        print(f"RECAPTCHA ODRZUCONE: Wynik {response.risk_analysis.score} jest poniżej {MIN_SCORE}")
        return False

    print(f"RECAPTCHA ZAAKCEPTOWANE: Wynik: {response.risk_analysis.score}")
    return True
