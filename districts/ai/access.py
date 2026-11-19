# coding=utf-8
"""Access of the AI assistant (OpenSpec change ai-chat-panel, D1-D3): the anthropic SDK, the API key and the
per-project permission (table public.ai_settings, shared by everyone working on the project database)."""
import getpass
import importlib.util
import os
import sys

# tools that read only the public wiki: allowed in every project
ALWAYS_ALLOWED = ('search_help', 'read_help_page')
AI_SETTINGS_SQL = """CREATE TABLE IF NOT EXISTS public.ai_settings
(
    id integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    allowed boolean NOT NULL DEFAULT false,
    disabled_tools text[] NOT NULL DEFAULT '{}',
    changed_by text,
    changed_at timestamp
);"""
AUTH_KEY_USER = 'anthropic'


# ---------------- SDK ----------------
def sdkVersion():
    """version of the installed anthropic package, None when it cannot be imported"""
    if importlib.util.find_spec('anthropic') is None:
        return None
    try:
        import anthropic
        return anthropic.__version__
    except Exception:
        return None


def pythonExecutable():
    from ..mcp.bridge import mcpPython
    return mcpPython()


def installArguments():
    """pip arguments of 'Install AI support' (the user site of the QGIS Python: no administrator rights needed)"""
    return ['-m', 'pip', 'install', '--user', '--upgrade', 'anthropic']


def installCommandText():
    return '"{}" {}'.format(pythonExecutable(), ' '.join(installArguments()))


def refreshImportPath():
    """a package installed into the user site while QGIS runs: make the user site importable without a restart"""
    import site
    path = site.getusersitepackages()
    if os.path.isdir(path) and path not in sys.path:
        sys.path.append(path)
    importlib.invalidate_caches()


# ---------------- API key ----------------
def storedApiKey(config):
    """the key stored in the QGIS authentication database (setting ai_auth_id), None without one"""
    auth_id = config.get('ai_auth_id') or ''
    if not auth_id:
        return None
    from qgis.core import QgsApplication, QgsAuthMethodConfig
    cfg = QgsAuthMethodConfig()
    if not QgsApplication.authManager().loadAuthenticationConfig(auth_id, cfg, True):
        return None
    return cfg.config('password') or None


def storeApiKey(config, key):
    """stores the key in the QGIS authentication database and returns its auth_id ('' removes it)"""
    from qgis.core import QgsApplication, QgsAuthMethodConfig
    manager = QgsApplication.authManager()
    auth_id = config.get('ai_auth_id') or ''
    if not key:
        if auth_id:
            manager.removeAuthenticationConfig(auth_id)
        return ''
    cfg = QgsAuthMethodConfig('Basic')
    if auth_id:
        manager.loadAuthenticationConfig(auth_id, cfg, True)
    cfg.setName('Districts Modeler: Anthropic API key')
    cfg.setConfig('username', AUTH_KEY_USER)
    cfg.setConfig('password', key)
    if cfg.id():
        manager.updateAuthenticationConfig(cfg)
    else:
        manager.storeAuthenticationConfig(cfg)
    return cfg.id()


def keySource(config):
    """('settings' | 'environment' | None, key or None): the key of the settings first, else what the SDK finds"""
    key = storedApiKey(config)
    if key:
        return 'settings', key
    if os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN') or os.environ.get('ANTHROPIC_PROFILE'):
        return 'environment', None
    profile = os.path.join(os.path.expanduser('~'), '.config', 'anthropic')
    if os.path.isdir(profile):
        return 'profile', None
    return None, None


def createClient(config):
    import anthropic
    source, key = keySource(config)
    return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()


# ---------------- per-project permission ----------------
def ensureAiSettingsTable(cur):
    """the table in projects created before (upgradeProjectDB): the assistant stays off until allowed"""
    cur.execute(AI_SETTINGS_SQL)


def loadAiSettings(cur):
    """{'allowed', 'disabled_tools', 'changed_by', 'changed_at'}; not allowed without the table or its row"""
    cur.execute("SELECT to_regclass('public.ai_settings') IS NOT NULL AS ok;")
    if not cur.fetchone()['ok']:
        return {'allowed': False, 'disabled_tools': [], 'changed_by': None, 'changed_at': None}
    cur.execute('SELECT allowed, disabled_tools, changed_by, changed_at FROM public.ai_settings WHERE id = 1;')
    row = cur.fetchone()
    if not row:
        return {'allowed': False, 'disabled_tools': [], 'changed_by': None, 'changed_at': None}
    return {'allowed': bool(row['allowed']), 'disabled_tools': list(row['disabled_tools'] or []),
            'changed_by': row['changed_by'], 'changed_at': row['changed_at']}


def saveAiSettings(cur, allowed, disabled_tools):
    ensureAiSettingsTable(cur)
    cur.execute("""INSERT INTO public.ai_settings (id, allowed, disabled_tools, changed_by, changed_at) VALUES (1, %s, %s, %s, now())
        ON CONFLICT (id) DO UPDATE SET allowed = EXCLUDED.allowed, disabled_tools = EXCLUDED.disabled_tools,
        changed_by = EXCLUDED.changed_by, changed_at = EXCLUDED.changed_at;""",
                (bool(allowed), sorted(set(disabled_tools)), currentUser()))


def currentUser():
    try:
        return getpass.getuser()
    except Exception:
        return None


def toolAllowed(settings, name):
    if name in ALWAYS_ALLOWED:
        return True
    return settings['allowed'] and name not in settings['disabled_tools']
