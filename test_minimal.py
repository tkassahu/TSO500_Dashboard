from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.h1("Test - If you see this, Shiny works!")
)

def server(input, output, session):
    pass

app = App(app_ui, server)
