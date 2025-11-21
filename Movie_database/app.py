#!/usr/bin/env python3
import csv
import itertools
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time
from datetime import datetime

l = [
    {
        "id": 1,
        "title": "Silent Horizon",
        "year": "2012",
        "description": "An emotional journey of unlikely heroes who must confront their pasts.",
        "runtime": "120",
        "rating": "7.8",
        "director": "Alex Turner",
        "actor1": "Jamie Hale",
        "actor2": "Taylor Brooks",
        "actor3": "Morgan Foster",
        "actor4": "Riley Hayes",
        "actor5": "Casey Griffin",
        "genres": "Drama, Adventure"
    },
    {
        "id": 2,
        "title": "Hidden City",
        "year": "2005",
        "description": "A suspenseful thriller where nothing is as it seems and every secret costs dearly.",
        "runtime": "105",
        "rating": "8.2",
        "director": "Morgan Reed",
        "actor1": "Alex Miller",
        "actor2": "Chris Bell",
        "actor3": "Jordan Scott",
        "actor4": "Drew Wright",
        "actor5": "Peyton Shaw",
        "genres": "Thriller, Mystery"
    },
    {
        "id": 3,
        "title": "Final Memory",
        "year": "2019",
        "description": "A clever sci-fi odyssey that questions reality and what it means to be human.",
        "runtime": "140",
        "rating": "8.6",
        "director": "Taylor Morgan",
        "actor1": "Alex Quinn",
        "actor2": "Harper Blake",
        "actor3": "Rowan Pierce",
        "actor4": "Reese Knight",
        "actor5": "Blake Powell",
        "genres": "Sci-Fi, Drama"
    },
]
f=open("movies_real.csv","w",newline="",encoding="utf-8")
l=f.readlines()

# ----------------- Main application -----------------
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Movie DB")
        self.geometry("1000x600")
        self.minsize(800, 500)

        # in-memory dataset (replace with load_movies())
        self.all_movies = [m.copy() for m in l]
        self.displayed_movies = list(self.all_movies)  # currently shown after search/filter/sort

        # UI state
        self.search_var = tk.StringVar()
        self.genre_var = tk.StringVar(value="All")
        self.sort_var = tk.StringVar(value="Year ↓")
        self.selected_item_id = None
        self._id_counter = itertools.count(start=max((m["id"] for m in self.all_movies), default=0) + 1)

        # Build UI
        self._create_menu()
        self._create_main_frame()
        self._create_toolbar()
        self._create_list_area()
        self._create_status_bar()
        self._bind_shortcuts()

        # initial render
        self.render_movie_list(self.all_movies)

    # ----------------- UI creation -----------------
    def _create_menu(self):
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=False)
        filem.add_command(label="Import CSV...", command=self.on_import_csv)
        filem.add_command(label="Export CSV...", command=self.on_export_csv)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filem)

        editm = tk.Menu(menubar, tearoff=False)
        editm.add_command(label="Add", command=self.open_add_window, accelerator="Ctrl+N")
        editm.add_command(label="Refresh", command=self.on_refresh, accelerator="Ctrl+R")
        menubar.add_cascade(label="Edit", menu=editm)

        helpm = tk.Menu(menubar, tearoff=False)
        helpm.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=helpm)

        self.config(menu=menubar)

    def _create_main_frame(self):
        self.main_frame = ttk.Frame(self, padding=(12, 8))
        self.main_frame.pack(fill="both", expand=True)

    def _create_toolbar(self):
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(side="top", fill="x")

        ttk.Label(toolbar, text="Search Title:").pack(side="left", padx=(0, 4))
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=40)
        search_entry.pack(side="left")
        search_entry.bind("<Return>", lambda e: self.on_search())

        ttk.Button(toolbar, text="Search", command=self.on_search).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Clear", command=self.on_clear_search).pack(side="left")

        ttk.Frame(toolbar, width=12).pack(side="left")  # spacer

        ttk.Label(toolbar, text="Filter:").pack(side="left", padx=(6, 4))
        self.genre_cb = ttk.Combobox(toolbar, textvariable=self.genre_var, state="readonly", width=20)
        self.genre_cb.pack(side="left")
        self._refresh_genre_options()
        self.genre_cb.bind("<<ComboboxSelected>>", lambda e: self.on_filter_change())

        ttk.Label(toolbar, text="Sort:").pack(side="left", padx=(6, 4))
        self.sort_cb = ttk.Combobox(toolbar, textvariable=self.sort_var, state="readonly", width=18,
                                    values=["Year ↓","Year ↑","Rating ↓","Rating ↑","Title A→Z","Title Z→A"])
        self.sort_cb.pack(side="left")
        self.sort_cb.bind("<<ComboboxSelected>>", lambda e: self.on_sort_change())

        # right-aligned action buttons
        action_frame = ttk.Frame(toolbar)
        action_frame.pack(side="right")
        ttk.Button(action_frame, text="Add", command=self.open_add_window).pack(side="right", padx=4)
        self.refresh_btn = ttk.Button(action_frame, text="Refresh", command=self.on_refresh)
        self.refresh_btn.pack(side="right", padx=4)
        self.delete_btn = ttk.Button(action_frame, text="Delete", command=self.on_delete_click, state="disabled")
        self.delete_btn.pack(side="right", padx=4)
        self.edit_btn = ttk.Button(action_frame, text="Edit", command=self.open_edit_window, state="disabled")
        self.edit_btn.pack(side="right", padx=4)
        self.view_btn = ttk.Button(action_frame, text="View", command=self.open_view_window, state="disabled")
        self.view_btn.pack(side="right", padx=4)

    def _create_list_area(self):
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill="both", expand=True, pady=(8, 6))

        columns = ("id", "title", "year", "rating", "director", "genres")
        self.movie_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.movie_tree.heading("id", text="ID", command=lambda: self.on_heading_click("id"))
        self.movie_tree.heading("title", text="Title", command=lambda: self.on_heading_click("title"))
        self.movie_tree.heading("year", text="Year", command=lambda: self.on_heading_click("year"))
        self.movie_tree.heading("rating", text="Rating", command=lambda: self.on_heading_click("rating"))
        self.movie_tree.heading("director", text="Director", command=lambda: self.on_heading_click("director"))
        self.movie_tree.heading("genres", text="Genres", command=lambda: self.on_heading_click("genres"))

        self.movie_tree.column("id", width=60, anchor="center")
        self.movie_tree.column("title", width=440, anchor="w")
        self.movie_tree.column("year", width=80, anchor="center")
        self.movie_tree.column("rating", width=80, anchor="center")
        self.movie_tree.column("director", width=180, anchor="w")
        self.movie_tree.column("genres", width=140, anchor="w")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.movie_tree.yview)
        self.movie_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.movie_tree.pack(side="left", fill="both", expand=True)

        # Bindings
        self.movie_tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        self.movie_tree.bind("<Double-1>", self.on_row_double_click)

        # alternating row tags
        self.movie_tree.tag_configure("odd", background="#f9f9f9")
        self.movie_tree.tag_configure("even", background="#ffffff")

    def _create_status_bar(self):
        status = ttk.Frame(self.main_frame)
        status.pack(side="bottom", fill="x")

        self.count_label = ttk.Label(status, text="")
        self.count_label.pack(side="left", padx=(4, 10))

        self.filter_label = ttk.Label(status, text="")
        self.filter_label.pack(side="left")

        self.progress = ttk.Progressbar(status, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side="right", padx=4)
        self.last_refreshed_label = ttk.Label(status, text="")
        self.last_refreshed_label.pack(side="right", padx=6)

    # ----------------- Rendering & data functions -----------------
    def render_movie_list(self, movies):
        """Clear and render given movies list into the treeview."""
        # clear
        for iid in self.movie_tree.get_children():
            self.movie_tree.delete(iid)

        # sort according to sort_var (basic implementation)
        movies_to_show = list(movies)
        sort_val = self.sort_var.get()
        reverse = False
        key = None
        if sort_val == "Year ↓":
            key = lambda m: int(m.get("year") or 0)
            reverse = True
        elif sort_val == "Year ↑":
            key = lambda m: int(m.get("year") or 0)
            reverse = False
        elif sort_val == "Rating ↓":
            key = lambda m: float(m.get("rating") or 0.0)
            reverse = True
        elif sort_val == "Rating ↑":
            key = lambda m: float(m.get("rating") or 0.0)
            reverse = False
        elif sort_val == "Title A→Z":
            key = lambda m: m.get("title","").lower()
            reverse = False
        elif sort_val == "Title Z→A":
            key = lambda m: m.get("title","").lower()
            reverse = True
        if key:
            movies_to_show.sort(key=key, reverse=reverse)

        # insert
        for idx, m in enumerate(movies_to_show):
            tag = "odd" if idx % 2 else "even"
            values = (m.get("id"), m.get("title"), m.get("year") or "", m.get("rating") or "", m.get("director") or "", m.get("genres") or "")
            self.movie_tree.insert("", "end", iid=str(m["id"]), values=values, tags=(tag,))

        # update counts & labels
        self.displayed_movies = movies_to_show
        self.count_label.config(text=f"Showing {len(self.displayed_movies)} of {len(self.all_movies)} movies")
        self.filter_label.config(text=f"Filter: {self.genre_var.get()} | Sort: {self.sort_var.get()}")
        self.last_refreshed_label.config(text=f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # reset selection state buttons
        self._set_action_buttons_state(0)

    def _refresh_genre_options(self):
        # compute unique genres from all_movies
        genres = set()
        for m in self.all_movies:
            g = m.get("genres", "")
            for part in [x.strip() for x in g.split(",") if x.strip()]:
                genres.add(part)
        values = ["All"] + sorted(genres)
        self.genre_cb['values'] = values
        if self.genre_var.get() not in values:
            self.genre_var.set("All")

    # ----------------- Event handlers -----------------
    def on_search(self):
        q = self.search_var.get().strip().lower()
        if not q:
            self.render_movie_list(self.all_movies if self.genre_var.get() == "All" else self._filter_by_genre(self.all_movies, self.genre_var.get()))
            return
        filtered = [m for m in self.all_movies if q in (m.get("title","").lower())]
        if self.genre_var.get() != "All":
            filtered = self._filter_by_genre(filtered, self.genre_var.get())
        self.render_movie_list(filtered)

    def on_clear_search(self):
        self.search_var.set("")
        self.genre_var.set("All")
        self.render_movie_list(self.all_movies)

    def on_filter_change(self):
        genre = self.genre_var.get()
        if genre == "All":
            base = self.all_movies
        else:
            base = self._filter_by_genre(self.all_movies, genre)
        # also respect search if present
        q = self.search_var.get().strip().lower()
        if q:
            base = [m for m in base if q in (m.get("title","").lower())]
        self.render_movie_list(base)

    def on_sort_change(self):
        # re-render uses sort_var; just call render on current displayed list
        self.render_movie_list(self.displayed_movies)

    def on_heading_click(self, col):
        # quick toggle through a small mapping or just show a message
        messagebox.showinfo("Sort", f"Column heading clicked: {col}\nUse the Sort combobox for sorting in this skeleton.")

    def on_selection_change(self, event):
        sel = self.movie_tree.selection()
        self._set_action_buttons_state(len(sel))
        # update preview if desired (not implemented)
        if len(sel) == 1:
            self.selected_item_id = int(sel[0])
        else:
            self.selected_item_id = None

    def _set_action_buttons_state(self, n_selected):
        if n_selected == 0:
            self.view_btn.config(state="disabled")
            self.edit_btn.config(state="disabled")
            self.delete_btn.config(state="disabled")
        elif n_selected == 1:
            self.view_btn.config(state="normal")
            self.edit_btn.config(state="normal")
            self.delete_btn.config(state="normal")
        else:
            self.view_btn.config(state="disabled")
            self.edit_btn.config(state="disabled")
            self.delete_btn.config(state="normal")

    def on_row_double_click(self, event):
        sel = self.movie_tree.selection()
        if sel:
            movie_id = int(sel[0])
            self.open_view_window(movie_id)

    # ----------------- CRUD-ish UI actions (in-memory) -----------------
    def open_view_window(self, movie_id=None):
        if movie_id is None:
            sel = self.movie_tree.selection()
            if not sel:
                return
            movie_id = int(sel[0])
        movie = self._get_movie_by_id(movie_id)
        if not movie:
            messagebox.showerror("Not found", "Movie not found.")
            return
        win = tk.Toplevel(self)
        win.title(f"View — {movie.get('title')}")
        win.geometry("600x420")
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=movie.get("title"), font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(frm, text=f"Year: {movie.get('year') or '—'}    Runtime: {movie.get('runtime') or '—'} mins    Rating: {movie.get('rating') or '—'}").pack(anchor="w", pady=(4,8))
        ttk.Label(frm, text=f"Director: {movie.get('director') or '—'}").pack(anchor="w")
        ttk.Label(frm, text="Top Actors:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(8,0))
        for i in range(1,6):
            a = movie.get(f"actor{i}") or ""
            ttk.Label(frm, text=f"  {i}. {a}").pack(anchor="w")

        ttk.Label(frm, text="Genres:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(8,0))
        ttk.Label(frm, text=movie.get("genres") or "").pack(anchor="w")

        ttk.Label(frm, text="Description:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(8,0))
        txt = tk.Text(frm, height=8, wrap="word")
        txt.insert("1.0", movie.get("description") or "")
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True, pady=(4,4))

        btnf = ttk.Frame(frm)
        btnf.pack(fill="x", pady=(6,0))
        ttk.Button(btnf, text="Edit", command=lambda mid=movie_id: (win.destroy(), self.open_edit_window(mid))).pack(side="left")
        ttk.Button(btnf, text="Delete", command=lambda mid=movie_id: (win.destroy(), self._confirm_and_delete(mid))).pack(side="left", padx=6)
        ttk.Button(btnf, text="Close", command=win.destroy).pack(side="right")

    def open_add_window(self):
        win = tk.Toplevel(self)
        win.title("Add Movie")
        win.geometry("520x520")
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        # simple form fields (title, year, rating, director, actor1, genres, description)
        labels = [
            ("Title", "title"), ("Year", "year"), ("Runtime (mins)", "runtime"),
            ("Rating", "rating"), ("Director", "director"),
            ("Actor 1", "actor1"), ("Actor 2", "actor2"), ("Actor 3", "actor3"),
            ("Actor 4", "actor4"), ("Actor 5", "actor5"), ("Genres (comma-separated)", "genres")
        ]
        entries = {}
        for lbl, key in labels:
            ttk.Label(frm, text=lbl).pack(anchor="w", pady=(6,0))
            ent = ttk.Entry(frm)
            ent.pack(fill="x")
            entries[key] = ent

        ttk.Label(frm, text="Description").pack(anchor="w", pady=(6,0))
        desc = tk.Text(frm, height=6, wrap="word")
        desc.pack(fill="both", expand=True)

        def on_save():
            title = entries["title"].get().strip()
            if not title:
                messagebox.showerror("Validation", "Title is required.")
                return
            new_id = next(self._id_counter)
            movie = {
                "id": new_id,
                "title": title,
                "year": entries["year"].get().strip(),
                "description": desc.get("1.0", "end").strip(),
                "runtime": entries["runtime"].get().strip(),
                "rating": entries["rating"].get().strip(),
                "director": entries["director"].get().strip(),
                "actor1": entries["actor1"].get().strip(),
                "actor2": entries["actor2"].get().strip(),
                "actor3": entries["actor3"].get().strip(),
                "actor4": entries["actor4"].get().strip(),
                "actor5": entries["actor5"].get().strip(),
                "genres": entries["genres"].get().strip(),
            }
            # append to in-memory list; replace with append_movie(csv_path, movie) later
            self.all_movies.append(movie)
            self._refresh_genre_options()
            self.render_movie_list(self.all_movies)
            win.destroy()
            messagebox.showinfo("Added", f"Movie '{title}' added (in-memory).")

        btnf = ttk.Frame(frm)
        btnf.pack(fill="x", pady=(8,0))
        ttk.Button(btnf, text="Save", command=on_save).pack(side="right", padx=4)
        ttk.Button(btnf, text="Cancel", command=win.destroy).pack(side="right")

    def open_edit_window(self, movie_id=None):
        if movie_id is None:
            sel = self.movie_tree.selection()
            if not sel:
                return
            movie_id = int(sel[0])
        movie = self._get_movie_by_id(movie_id)
        if not movie:
            messagebox.showerror("Not found", "Movie not found.")
            return

        win = tk.Toplevel(self)
        win.title(f"Edit — {movie.get('title')}")
        win.geometry("520x520")
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        labels = [
            ("Title", "title"), ("Year", "year"), ("Runtime (mins)", "runtime"),
            ("Rating", "rating"), ("Director", "director"),
            ("Actor 1", "actor1"), ("Actor 2", "actor2"), ("Actor 3", "actor3"),
            ("Actor 4", "actor4"), ("Actor 5", "actor5"), ("Genres (comma-separated)", "genres")
        ]
        entries = {}
        for lbl, key in labels:
            ttk.Label(frm, text=lbl).pack(anchor="w", pady=(6,0))
            ent = ttk.Entry(frm)
            ent.insert(0, movie.get(key, ""))
            ent.pack(fill="x")
            entries[key] = ent

        ttk.Label(frm, text="Description").pack(anchor="w", pady=(6,0))
        desc = tk.Text(frm, height=6, wrap="word")
        desc.insert("1.0", movie.get("description",""))
        desc.pack(fill="both", expand=True)

        def on_save():
            title = entries["title"].get().strip()
            if not title:
                messagebox.showerror("Validation", "Title is required.")
                return
            # update in-memory (replace with update_movie in real version)
            movie.update({
                "title": title,
                "year": entries["year"].get().strip(),
                "description": desc.get("1.0", "end").strip(),
                "runtime": entries["runtime"].get().strip(),
                "rating": entries["rating"].get().strip(),
                "director": entries["director"].get().strip(),
                "actor1": entries["actor1"].get().strip(),
                "actor2": entries["actor2"].get().strip(),
                "actor3": entries["actor3"].get().strip(),
                "actor4": entries["actor4"].get().strip(),
                "actor5": entries["actor5"].get().strip(),
                "genres": entries["genres"].get().strip(),
            })
            self._refresh_genre_options()
            self.render_movie_list(self.all_movies)
            win.destroy()
            messagebox.showinfo("Saved", f"Movie '{title}' updated (in-memory).")

        btnf = ttk.Frame(frm)
        btnf.pack(fill="x", pady=(8,0))
        ttk.Button(btnf, text="Save", command=on_save).pack(side="right", padx=4)
        ttk.Button(btnf, text="Cancel", command=win.destroy).pack(side="right")

    def on_delete_click(self):
        sel = self.movie_tree.selection()
        if not sel:
            return
        ids = [int(s) for s in sel]
        if len(ids) == 1:
            self._confirm_and_delete(ids[0])
        else:
            if messagebox.askyesno("Confirm Delete", f"Delete {len(ids)} movies?"):
                # delete multiple
                for mid in ids:
                    self._delete_movie_by_id(mid)
                self.render_movie_list(self.all_movies)

    def _confirm_and_delete(self, movie_id):
        movie = self._get_movie_by_id(movie_id)
        if not movie:
            messagebox.showerror("Not found", "Movie not found.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete '{movie.get('title')}'?"):
            self._delete_movie_by_id(movie_id)
            self.render_movie_list(self.all_movies)

    def _delete_movie_by_id(self, movie_id):
        # replace this with delete_movie(csv_path, movie_id) in real version
        self.all_movies = [m for m in self.all_movies if m["id"] != movie_id]
        # update id counter not necessary; we maintain increasing IDs
        self._refresh_genre_options()

    # ----------------- Helpers -----------------
    def _get_movie_by_id(self, movie_id):
        for m in self.all_movies:
            if int(m["id"]) == int(movie_id):
                return m
        return None

    def _filter_by_genre(self, movies, genre):
        g = genre.strip().lower()
        return [m for m in movies if any(part.strip().lower() == g for part in (m.get("genres","") or "").split(",") if part.strip())]

    def on_refresh(self):
        # placeholder: in a full app, reload CSV here (load_movies)
        messagebox.showinfo("Refresh", "Reloaded in-memory data (placeholder).")
        self._refresh_genre_options()
        self.render_movie_list(self.all_movies)

    def on_import_csv(self):
        messagebox.showinfo("Import CSV", "Import CSV not implemented in skeleton.")

    def on_export_csv(self):
        messagebox.showinfo("Export CSV", "Export CSV not implemented in skeleton.")

    def show_about(self):
        messagebox.showinfo("About", "Movie DB — UI skeleton\nBuild your data_manager and wire it in.")

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.open_add_window())
        self.bind_all("<Control-r>", lambda e: self.on_refresh())
        self.bind_all("<Control-f>", lambda e: self._focus_search())
        self.bind_all("<Delete>", lambda e: self.on_delete_click())
        self.bind_all("<Return>", self._enter_key_handler)

    def _focus_search(self):
        # focus the search entry widget
        # we find it by walking widgets (a simple approach)
        for child in self.main_frame.winfo_children():
            for sub in child.winfo_children():
                if isinstance(sub, ttk.Entry) and sub.cget("width") == 40:
                    sub.focus_set()
                    return

    def _enter_key_handler(self, event):
        # Only open view if tree has focus
        widget = self.focus_get()
        if widget and str(widget).startswith(str(self.movie_tree)):
            sel = self.movie_tree.selection()
            if sel:
                self.open_view_window(int(sel[0]))

# ----------------- Run -----------------
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
