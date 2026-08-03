# SMTP Settings for e-mail notification
import os

smtp_username = os.environ.get("SMTP_USERNAME")
smtp_psw = os.environ.get("SMTP_PSW")
smtp_server =  os.environ.get("SMTP_SERVER")
smtp_port =  os.environ.get("SMTP_PORT")
smtp_toaddrs = [os.environ.get("SMTP_TO")]
smtp_from = os.environ.get("SMTP_FROM_ADDRESS")

slack_webhook_url = None
telegram_bot_token = None
telegram_chat_id = None
discord_webhook_url = None

# Vinted URL: change the TLD according to your country (.fr, .es, etc.)
vinted_url = "https://www.vinted.fr"

# Vinted queries for research
# "page", "per_page" and "order" you may not edit them
# "search_text" is the free search field, this field may be empty if you wish to search for the entire brand.
# "catalog_ids" is the category in which to eventually search, if the field is empty it will search in all categories. Vinted assigns a numeric ID to each category, e.g. 2996 is the ID for e-Book Reader
# "brand_ids" if you want to search by brand. Vinted assigns a numeric ID to each brand, e.g. 417 is the ID for Louis Vuitton
# "order" you can change it to relevance, newest_first, price_high_to_low, price_low_to_high

queries = [
        {
        'page': '1',
        'per_page': '96',
        'search_text': 'odaje',
        'catalog_ids': '1242',
        'size_ids': '784,785,786',
        'brand_ids': '18361610',
        'status_ids': '1,2,6',
        'required_keywords': ['odaje'],
        'order': 'newest_first',
    },
    {
        'page': '1',
        'per_page': '96',
        'search_text': 'maillot gardien équipe de France',
        'catalog_ids': '1204',
        'size_ids': '628,629',
        'brand_ids': '53',
        'status_ids': '1,2,6',
        'required_keywords': ['gardien', 'France'],
        'order': 'newest_first',
    },
    {
        'page': '1',
        'per_page': '96',
        'search_text': 'maillot équipe de France 1984',
        'catalog_ids': '30',
        'size_ids': '208',
        'brand_ids': '14,194976',
        'status_ids': '1,2,6',
        'required_keywords': ['1984'],
        'order': 'newest_first',
    },
        {
        'page': '1',
        'per_page': '96',
        'search_text': 'karhu',
        'catalog_ids': '1242',
        'size_ids': '784,785,786',
        'brand_ids': '304297',
        'status_ids': '1,2,6',
        'required_keywords': ['karhu'],
        'order': 'newest_first',
    }
]
