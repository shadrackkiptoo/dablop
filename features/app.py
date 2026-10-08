from fastapi.staticfiles import StaticFiles
from .state import state
from . import models, auth, devices, messages, monitoring, telegram, screenshots
def create_app():
    state.app.router.lifespan_context=monitoring.lifespan(state.app)
    state.app.mount("/web",StaticFiles(directory=state.BASE_DIR/"web"),name="web")
    state.load_text_messages(); state.load_devices(); state.load_client_site_url()
    state.SUPPORT_METHODS=state.parse_support_methods(state.BUY_ME_A_COFFEE_URL)
    state.MONITORED_APP_PATTERNS=state.load_monitored_app_patterns()
    state.MONITORED_SITE_PATTERNS=state.load_monitored_site_patterns()
    return state.app
app=create_app()
__all__=["app","state","models","auth","messages","devices","monitoring","telegram","screenshots","create_app"]
