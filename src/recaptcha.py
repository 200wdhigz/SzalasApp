from google.cloud import recaptchaenterprise_v1
import os

def verify_recaptcha(token: str, action: str) -> bool:
    """Weryfikuje token reCAPTCHA Enterprise."""
    project_id = os.getenv('GCP_PROJECT_ID')
    site_key = os.getenv('RECAPTCHA_SITE_KEY')

    if not project_id or not site_key:
        print("Błąd konfiguracji reCAPTCHA.")
        return False

    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient()
    event = recaptchaenterprise_v1.Event(site_key=site_key, token=token)
    assessment = recaptchaenterprise_v1.Assessment(event=event)
    
    try:
        response = client.create_assessment(
            recaptchaenterprise_v1.CreateAssessmentRequest(
                assessment=assessment, parent=f"projects/{project_id}"
            )
        )
        
        if not response.token_properties.valid or response.token_properties.action != action:
            return False
            
        return response.risk_analysis.score >= 0.5
    except Exception as e:
        print(f"Błąd reCAPTCHA: {e}")
        return False
