import wx
import csv
import os
from theAlgorithm import main


class MovieFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Movie Database", size=(750, 500))
        panel = wx.Panel(self)

        # Buttons
        wx.Button(panel, label="Check Database", pos=(20, 20)).Bind(wx.EVT_BUTTON, self.show_all)
        wx.Button(panel, label="Filter by Rating", pos=(160, 20)).Bind(wx.EVT_BUTTON, self.filter_rating)
        wx.Button(panel, label="Filter by Runtime", pos=(300, 20)).Bind(wx.EVT_BUTTON, self.filter_runtime)
        wx.Button(panel, label="Filter by Genre", pos=(460, 20)).Bind(wx.EVT_BUTTON, self.filter_genre)
        wx.Button(panel, label="Filter by Year", pos=(600, 20)).Bind(wx.EVT_BUTTON, self.filter_year)
        wx.Button(panel, label="Get Recommendations", pos=(285, 50)).Bind(wx.EVT_BUTTON, self.get_recommendations)

        # Output box
        self.output = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            pos=(20, 90),
            size=(700, 360)
        )

        # CSV path (absolute, safe)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.csv_path = os.path.join(self.base_dir, "movies_backup.csv")

    # =====================================================
    # HELPER FUNCTIONS
    # =====================================================
    def clear(self):
        self.output.Clear()

    def read_csv(self):
        if not os.path.isfile(self.csv_path):
            self.output.AppendText("❌ movies_backup.csv NOT FOUND\n")
            return None, None

        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            return header, rows

#FUNCTIONS FOR THE BUTTONS
    def show_all(self, event):
        self.clear()
        header, rows = self.read_csv()
        if not rows:
            return

        title_idx = header.index("title")
        for i, row in enumerate(rows, 1):
            self.output.AppendText(f"{i} - {row[title_idx]}\n")

    def filter_rating(self, event):
        dlg = wx.TextEntryDialog(self, "Enter rating range (e.g. 6-8)", "Rating Filter")
        if dlg.ShowModal() != wx.ID_OK:
            return

        try:
            low, high = map(float, dlg.GetValue().split("-"))
        except:
            self.output.AppendText("❌ Invalid rating format\n")
            return

        self.clear()
        header, rows = self.read_csv()
        if not rows:
            return

        rate_idx = header.index("rating")
        title_idx = header.index("title")

        c = 1
        for row in rows:
            try:
                r = float(row[rate_idx])
                if low <= r <= high:
                    self.output.AppendText(f"{c} - {row[title_idx]} ({r})\n")
                    c += 1
            except:
                continue

    def filter_runtime(self, event):
        dlg = wx.TextEntryDialog(self, "Enter runtime range (e.g. 90-120)", "Runtime Filter")
        if dlg.ShowModal() != wx.ID_OK:
            return

        try:
            low, high = map(int, dlg.GetValue().split("-"))
        except:
            self.output.AppendText("❌ Invalid runtime format\n")
            return

        self.clear()
        header, rows = self.read_csv()
        if not rows:
            return

        run_idx = header.index("runtime")
        title_idx = header.index("title")

        c = 1
        for row in rows:
            try:
                rt = int(row[run_idx])
                if low <= rt <= high:
                    self.output.AppendText(f"{c} - {row[title_idx]} ({rt} min)\n")
                    c += 1
            except:
                continue

    def filter_genre(self, event):
        dlg = wx.TextEntryDialog(self, "Enter genre (e.g. Action)", "Genre Filter")
        if dlg.ShowModal() != wx.ID_OK:
            return

        genre = dlg.GetValue().lower()
        self.clear()

        header, rows = self.read_csv()
        if not rows:
            return

        genre_idx = header.index("genres")
        title_idx = header.index("title")

        c = 1
        for row in rows:
            if genre in row[genre_idx].lower():
                self.output.AppendText(f"{c} - {row[title_idx]} ({row[genre_idx]})\n")
                c += 1

    def filter_year(self, event):
        dlg = wx.TextEntryDialog(self, "Enter year range (e.g. 2000-2010)", "Year Filter")
        if dlg.ShowModal() != wx.ID_OK:
            return

        try:
            low, high = map(int, dlg.GetValue().split("-"))
        except:
            self.output.AppendText("❌ Invalid year format\n")
            return

        self.clear()
        header, rows = self.read_csv()
        if not rows:
            return

        year_idx = header.index("year")
        title_idx = header.index("title")

        c = 1
        for row in rows:
            try:
                y = int(row[year_idx])
                if low <= y <= high:
                    self.output.AppendText(f"{c} - {row[title_idx]} ({y})\n")
                    c += 1
            except:
                continue

    def get_recommendations(self, event):
        dlg = wx.TextEntryDialog(
            self,
            "Enter movie titles you like (comma separated)",
            "Recommendations"
        )
        if dlg.ShowModal() != wx.ID_OK:
            return

        liked_titles = [t.strip() for t in dlg.GetValue().split(",") if t.strip()]
        self.clear()

        recommendations = main(self.csv_path, liked_titles)

        if not recommendations:
            self.output.AppendText("No recommendations found.\n")
            return

        self.output.AppendText(f"Recommendations based on {liked_titles}:\n\n")
        for i, rec in enumerate(recommendations, 1):
            self.output.AppendText(
                f"{i} - {rec['title']} (Score: {rec['score']:.2f})\n"
            )


# =====================================================
# RUN APP
# =====================================================
app = wx.App(False)
frame = MovieFrame()
frame.Show()
app.MainLoop()


