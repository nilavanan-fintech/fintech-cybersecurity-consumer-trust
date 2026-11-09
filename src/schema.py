"""Canonical column names and categorical domains (single source of truth)."""

CHANNELS = ["mobile_app", "web", "pos", "atm"]
MERCHANT_CATEGORIES = [
    "groceries", "restaurants", "travel", "electronics", "digital_goods",
    "utilities", "transfers", "entertainment", "healthcare", "fuel", "cash_withdrawal",
]
AUTH_METHODS = ["password", "otp", "biometric", "none"]
DEVICE_TYPES = ["android", "ios", "desktop", "pos_terminal", "atm_terminal"]
COUNTRIES = ["IN", "US", "GB", "SG", "AE", "DE", "NG", "BR", "RU", "CN"]
HOME_COUNTRIES = ["IN", "US", "GB", "SG", "AE", "DE"]
FRAUD_PATTERNS = ["account_takeover", "card_testing", "synthetic_identity", "social_engineering"]

TRANSACTION_COLUMNS = [
    "transaction_id", "customer_id", "timestamp", "amount", "merchant_category", "channel",
    "device_type", "country", "home_country", "is_new_device", "ip_risk_score",
    "velocity_1h", "account_age_days", "auth_method", "is_fraud", "fraud_pattern",
]

EVENT_TYPES_BENIGN = ["login_success", "password_reset", "api_call"]
EVENT_TYPES_ATTACK = [
    "brute_force", "credential_stuffing", "phishing_click", "malware_alert",
    "api_abuse", "data_exfiltration", "ddos_probe",
]
SECURITY_COLUMNS = [
    "event_id", "timestamp", "event_type", "severity", "source_country", "target_service",
    "blocked", "response_time_s", "bytes_out", "failed_attempts", "is_attack",
]
SERVICES = ["payments_api", "auth_service", "mobile_gateway", "customer_portal", "ledger_db"]

# Survey instrument: item -> (dimension, text, reverse_coded)
SURVEY_ITEMS = {
    "q01": ("perceived_security", "I feel my money is safe when I use my main FinTech app.", False),
    "q02": ("perceived_security", "My FinTech provider uses strong security measures (e.g. MFA, encryption).", False),
    "q03": ("perceived_security", "I am confident my FinTech provider can detect and stop fraud.", False),
    "q04": ("privacy_assurance", "My FinTech provider handles my personal data responsibly.", False),
    "q05": ("privacy_assurance", "I understand how my financial data is used and shared.", False),
    "q06": ("transparency", "My provider clearly communicates security incidents and policy changes.", False),
    "q07": ("transparency", "Security and privacy settings are easy to find and understand.", False),
    "q08": ("reliability", "The app works reliably when I make payments.", False),
    "q09": ("reliability", "My provider resolves fraud or dispute cases quickly and fairly.", False),
    "q10": ("behavioural_intent", "I would recommend my FinTech provider to friends or family.", False),
    "q11": ("behavioural_intent", "I intend to keep using FinTech services for my main finances.", False),
    "q12": ("perceived_security", "I worry that my FinTech account could be hacked. (reverse-coded)", True),
}
SURVEY_DIMENSIONS = [
    "perceived_security", "privacy_assurance", "transparency", "reliability", "behavioural_intent",
]
SURVEY_DEMOGRAPHICS = ["age_band", "education", "usage_frequency"]
SURVEY_BEHAVIOURS = ["uses_mfa", "experienced_fraud", "digital_literacy"]
