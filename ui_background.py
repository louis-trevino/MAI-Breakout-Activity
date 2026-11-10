"""Full-page landscape background for the Streamlit UI.

Images live in ./static/backgrounds and are served by Streamlit's static file
serving (`[server] enableStaticServing = true` in .streamlit/config.toml).
Photos: Unsplash (free to use under the Unsplash License).
"""
from __future__ import annotations

import streamlit as st

# label -> (file name, focal point used for background-position)
BACKGROUNDS: dict[str, tuple[str, str]] = {
    "Alpine sunrise": ("alpine_sunrise.jpg", "center 35%"),
    "Forest trail": ("forest_trail.jpg", "center"),
    "Tropical shore": ("tropical_shore.jpg", "center 40%"),
}
DEFAULT_BACKGROUND = "Alpine sunrise"

# Key of the st.container that holds the main content; styled as a frosted panel.
CONTENT_KEY = "content_panel"


def apply_background(name: str) -> None:
    """Inject CSS that paints `name` behind the app and keeps content readable."""
    file_name, position = BACKGROUNDS.get(name, BACKGROUNDS[DEFAULT_BACKGROUND])
    dark = st.context.theme.type == "dark"
    # Panel tint follows the active light/dark theme so text contrast stays high.
    panel = "rgba(14, 17, 23, 0.80)" if dark else "rgba(255, 255, 255, 0.84)"
    veil = "rgba(0, 0, 0, 0.25)" if dark else "rgba(255, 255, 255, 0.10)"

    st.html(
        f"""
        <style>
        .stApp {{
            background:
                linear-gradient({veil}, {veil}),
                url("app/static/backgrounds/{file_name}") {position} / cover no-repeat fixed;
        }}
        /* Let the image show through the top bar and the chat-input dock. */
        [data-testid="stHeader"], [data-testid="stBottom"] > div {{
            background: transparent;
        }}
        .st-key-{CONTENT_KEY} {{
            background: {panel};
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
            border-radius: 1rem;
            padding: 1.5rem 1.75rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
        }}
        [data-testid="stChatInput"] {{
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
            border-radius: 1.25rem;
        }}
        </style>
        """
    )
