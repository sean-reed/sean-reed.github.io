AUTHOR = 'Sean Reed'
SITENAME = 'Sean Reed'
SITEURL = ""

PATH = "content"

TIMEZONE = 'Europe/Stockholm'

DEFAULT_LANG = 'en'

SITESUBTITLE = "On the simulation of complex systems and processes"
HIDE_AUTHORS = True

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

LINKS = ()  # Pairs of (name, url)

# Social widget
SOCIAL = (
    ("LinkedIn", "https://www.linkedin.com/in/seanreeds/"),
    ("Google Scholar", "https://scholar.google.com/citations?user=42ukSDsAAAAJ"),
)

DEFAULT_PAGINATION = 10

STATIC_PATHS = ['static']

THEME = '../themes/alchemy'

USE_FOLDER_AS_CATEGORY = True
DEFAULT_CATEGORY = 'misc'
DISPLAY_PAGES_ON_MENU = True
DELETE_OUTPUT_DIRECTORY = True
