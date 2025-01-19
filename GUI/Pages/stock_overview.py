import customtkinter


def stock_overview(app):

    tabView = customtkinter.CTkTabview(app)
    tabView.pack(padx=20, pady=20)
    tabView.add("Overview")
    tabView.add("Financials")
    tabView.add("Options")
    tabView.set("News")
