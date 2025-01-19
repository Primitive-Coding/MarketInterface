import customtkinter

# Tkinter settings
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")


# Custom pages
from GUI.Pages.stock_overview import stock_overview


class StockApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stock App")
        self.geometry("500x500")
        self.ticker = ""
        self.home_search()

    """
    ==================================================================================================================================
    Home
    ==================================================================================================================================
    """

    def home_search(self):
        # Search bar (CTkEntry)
        self.search_entry = customtkinter.CTkEntry(
            self, placeholder_text="Search here...", width=300
        )
        self.search_entry.pack(pady=10)

        # Search button
        search_button = customtkinter.CTkButton(
            self,
            text="Search",
            command=lambda: self.get_search_value(True, stock_overview),
        )
        search_button.pack(pady=10)

    """
    ==================================================================================================================================
    Utilities
    ==================================================================================================================================
    """

    def get_search_value(self, redirect: bool = False, page_to_redirect=None):
        # Get the value from the search bar
        self.ticker = self.search_entry.get()
        self.clear_screen()
        if redirect:
            page_to_redirect(self)
        print(f"TICKER: {self.ticker}")

    def clear_screen(self):
        # Destroy all widgets on the screen
        for widget in self.winfo_children():
            widget.destroy()


def main():

    app = StockApp()
    app.mainloop()
