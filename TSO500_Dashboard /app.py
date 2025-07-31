# app.py
from shiny import App, ui

# 1) UI definition with our smoke-test inside the page_sidebar
app_ui = ui.page_sidebar(
    ui.panel_sidebar(
        ui.h2("🔥 Hello Shiny!"),
        ui.p("If you see this, Shiny is reloading correctly.")
    ),
    ui.panel_main(
        ui.h3("❗❗❗ THIS IS MY SHINY APP ❗❗❗")
    )
)

# 2) A no-op server
def server(input, output, session):
    pass

# 3) Launch the app
app = App(app_ui, server)
