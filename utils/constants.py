from utils.utils import generate_fe_url_path

# Static paths
INQUIRY_CONTACT_PATH = "/kontakty"
TRANSFER_MARKET_PATH = "/rynek-transferowy"
INQUIRY_LIMIT_INCREASE_PATH = "/limity"

# Dynamic URL properties
INQUIRY_CONTACT_URL = generate_fe_url_path(INQUIRY_CONTACT_PATH)
TRANSFER_MARKET_URL = generate_fe_url_path(TRANSFER_MARKET_PATH)
INQUIRY_LIMIT_INCREASE_URL = generate_fe_url_path(INQUIRY_LIMIT_INCREASE_PATH)
