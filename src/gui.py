import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from . import processor
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # We want path relative to main bundle, so go up if needed
        base_path = sys._MEIPASS
    except Exception:
        # Not bundled, running in development structure
        # Path relative to the script file's directory's PARENT (project root)
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))

    # Assuming assets folder is directly inside the base_path (project root)
    return os.path.join(base_path, 'assets', relative_path)


# -- Icon Paths (Use the helper function) --
# Assumes your 'assets' folder is directly inside 'watermarker_project'
try:
    ICON_WATERMARK = resource_path('watermark_icn.png')
    ICON_FILE = resource_path('file_icn.png')
    ICON_EXPORT = resource_path('download_icn.png')
    ICON_ARROW = resource_path('arrow_icn.png')
    # You also need an application icon file for macOS (.icns)
    # << CREATE/RENAME this file
    APP_ICON_MACOS = resource_path('marktrix_logo_1024.icns')
except Exception as e:
    print(f"Error defining icon paths: {e}")
    # Define fallbacks if resource_path fails (shouldn't normally)
    ICON_WATERMARK = ICON_FILE = ICON_EXPORT = ICON_ARROW = APP_ICON_MACOS = None


try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: Pillow library not found. Icons may not display correctly.")

    class ImageTk:
        @staticmethod
        def PhotoImage(img): return None

# -- Color Definitions --
COLOR_BACKGROUND = '#2A2B2E'
# COLOR_PANE = '#F6F7EB' # No longer needed for pane background
COLOR_COMBO_BG = '#3D52D5'
COLOR_TEXT_ON_PANE = '#000000'
COLOR_TEXT_ON_DARK = '#FFFFFF'
COLOR_BUTTON_FG = '#FFFFFF'
COLOR_BUTTON_BG = '#5C5C5C'
COLOR_HIGHLIGHT_BG = '#3D52D5'
COLOR_CLEAR_BUTTON_FG = '#A0A0A0'
COLOR_LISTBOX_BG = '#DDDDDD'
COLOR_LISTBOX_FG = '#000000'
COLOR_LISTBOX_SELECT_BG = COLOR_COMBO_BG
COLOR_LISTBOX_SELECT_FG = COLOR_TEXT_ON_DARK
COLOR_ENTRY_BG = '#FFFFFF'


icons = {}


def load_icon(path, size=None):
    if not PIL_AVAILABLE:
        return None
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        photo_img = ImageTk.PhotoImage(img)
        icons[path] = photo_img
        return photo_img
    except Exception as e:
        print(f"Error loading icon {path}: {e}")
        return None


class AppWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Marktrix Watermarker")
        self.root.config(bg=COLOR_BACKGROUND)
        self.root.resizable(False, False)

        window_width = 750
        window_height = 600  # Adjusted height slightly, may need tuning
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(
            f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.input_files = []
        self.watermark_file = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.icon_watermark_img = load_icon(ICON_WATERMARK, (64, 64))
        # Slightly smaller icon for top row
        self.icon_file_img = load_icon(ICON_FILE, (48, 48))
        # Slightly smaller icon for top row
        self.icon_export_img = load_icon(ICON_EXPORT, (48, 48))
        self.icon_arrow_img = load_icon(ICON_ARROW, (48, 48))

        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            print("Warning: 'clam' theme not available.")

        COLOR_DISABLED_BG = '#888888'  # Medium grey background for disabled state
        COLOR_DISABLED_FG = '#BBBBBB'  # Light grey text for disabled state

        self.style.configure("TButton", padding=6, relief="flat", font=(
            "Helvetica", 10), foreground=COLOR_BUTTON_FG, background=COLOR_BUTTON_BG)
        self.style.map("TButton", background=[
                       ('active', '#777777'), ('disabled', COLOR_DISABLED_BG)], foreground=[('disabled', COLOR_DISABLED_FG)])
        self.style.configure(
            "Highlight.TButton", background=COLOR_HIGHLIGHT_BG, foreground=COLOR_BUTTON_FG)
        self.style.map("Highlight.TButton", background=[
                       ('active', '#5568da'), ('disabled', COLOR_DISABLED_BG)], foreground=[('disabled', COLOR_DISABLED_FG)])
        self.style.configure("TCombobox", fieldbackground=COLOR_ENTRY_BG, background=COLOR_BUTTON_BG, foreground=COLOR_TEXT_ON_PANE,
                             arrowcolor=COLOR_TEXT_ON_DARK, selectbackground=COLOR_LISTBOX_SELECT_BG, selectforeground=COLOR_LISTBOX_SELECT_FG,
                             highlightthickness=0)
        self.root.option_add('*TCombobox*Listbox.background', COLOR_LISTBOX_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', COLOR_LISTBOX_FG)
        self.root.option_add(
            '*TCombobox*Listbox.selectBackground', COLOR_LISTBOX_SELECT_BG)
        self.root.option_add(
            '*TCombobox*Listbox.selectForeground', COLOR_LISTBOX_SELECT_FG)

        container = tk.Frame(root, bg=COLOR_BACKGROUND)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (WatermarkPage, MainPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("WatermarkPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if page_name == "MainPage":
            self.update_export_button_state()
            if self.watermark_file.get():
                self.frames["MainPage"].update_status(
                    f"Using watermark: {os.path.basename(self.watermark_file.get())}")
            else:
                self.frames["MainPage"].update_status(
                    "Watermark not set!", warning=True)

    # --- Callbacks and Helpers (mostly unchanged) ---
    def select_watermark_file(self):
        filepath = filedialog.askopenfilename(title="Select Watermark File (PNG)", filetypes=(
            ("PNG files", "*.png"), ("All files", "*.*")))
        if filepath and filepath.lower().endswith(".png") and os.path.exists(filepath):
            self.watermark_file.set(filepath)
        elif filepath:
            messagebox.showerror(
                "Invalid File", "Please select a valid PNG file.")
            self.watermark_file.set("")
        self.frames["WatermarkPage"].update_display()

    def clear_watermark(self):
        self.watermark_file.set("")
        self.frames["WatermarkPage"].update_display()

    def select_image_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Image Files", filetypes=(
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")))
        if filepaths:
            new_files_added = 0
            current_full_paths = set(self.input_files)
            valid_selection = []
            for f_path in filepaths:
                if f_path and os.path.exists(f_path):
                    valid_selection.append(f_path)
                    if f_path not in current_full_paths:
                        self.input_files.append(f_path)
                        new_files_added += 1
            if valid_selection:
                self.update_file_listbox()
                if new_files_added > 0:
                    self.frames["MainPage"].update_status(
                        f"Added {new_files_added} image(s). Total: {len(self.input_files)}.")
                else:
                    self.frames["MainPage"].update_status(
                        f"Selected image(s) already in list. Total: {len(self.input_files)}.", warning=True)
            elif not self.input_files:
                self.frames["MainPage"].update_status(
                    "Image selection cancelled or no valid files chosen.", warning=True)
        self.update_export_button_state()

    def remove_selected_file(self):
        selected_indices = self.frames["MainPage"].file_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning(
                "No Selection", "Please select a file from the list to remove.")
            return
        selected_index = selected_indices[0]
        selected_filename = self.frames["MainPage"].file_listbox.get(
            selected_index)
        full_path_to_remove = next(
            (f for f in self.input_files if os.path.basename(f) == selected_filename), None)
        if full_path_to_remove:
            try:
                self.input_files.remove(full_path_to_remove)
                self.update_file_listbox()
                self.frames["MainPage"].update_status(
                    f"Removed: {selected_filename}. Remaining: {len(self.input_files)}.")
                self.update_export_button_state()
            except ValueError:
                self.frames["MainPage"].update_status(
                    f"Error removing {selected_filename}.", error=True)
        else:
            self.frames["MainPage"].update_status(
                f"Error finding {selected_filename} to remove.", error=True)

    def select_output_folder(self):
        directory = filedialog.askdirectory(title="Select Output Folder")
        if directory and os.path.isdir(directory):
            self.output_folder.set(directory)
            self.frames["MainPage"].update_status(
                f"Output folder set: {directory}")
        elif directory:
            self.output_folder.set("")
            self.frames["MainPage"].update_status(
                "Output folder selection invalid or cancelled.", warning=True)
        self.update_export_button_state()

    def start_export(self):
        position = self.frames["MainPage"].position_combo.get()
        self.frames["MainPage"].set_ui_state('disabled')
        self.frames["MainPage"].update_status("Processing... Please wait.")
        self.root.update()
        try:
            count = processor.batch_watermark(list(
                self.input_files), self.watermark_file.get(), self.output_folder.get(), position)
            messagebox.showinfo(
                "Success", f"Processing Complete!\n{count} images successfully watermarked in:\n{self.output_folder.get()}")
            self.frames["MainPage"].update_status(
                f"Processing complete. {count} images watermarked.", success=True)
        except FileNotFoundError as e:
            messagebox.showerror("Processing Error",
                                 f"File Not Found Error:\n{e}")
            self.frames["MainPage"].update_status(
                f"File not found error: {e}", error=True)
            print(f"Error: {e}")
        # except processor.WatermarkError as e: messagebox.showerror("Processing Error", f"Watermarking Error:\n{e}"); self.frames["MainPage"].update_status(f"Watermarking error: {e}", error=True); print(f"Error: {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Processing Error",
                                 f"An unexpected error occurred:\n{e}")
            self.frames["MainPage"].update_status(
                f"Unexpected error: {e}", error=True)
        finally:
            self.frames["MainPage"].set_ui_state('normal')
            self.update_export_button_state()

    def update_file_listbox(self):
        listbox = self.frames["MainPage"].file_listbox
        listbox.delete(0, tk.END)
        display_names = sorted([os.path.basename(f) for f in self.input_files])
        for name in display_names:
            listbox.insert(tk.END, name)

    def update_export_button_state(self):
        if "MainPage" not in self.frames:
            return
        wm_file = self.watermark_file.get()
        out_folder = self.output_folder.get()
        ready = bool(self.input_files and wm_file and os.path.exists(
            wm_file) and out_folder and os.path.isdir(out_folder))
        export_button = self.frames["MainPage"].export_button
        if export_button:
            export_button['state'] = 'normal' if ready else 'disabled'

# --- === Page 1 Frame Definition === ---
# (No changes needed in WatermarkPage structure)


class WatermarkPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=COLOR_BACKGROUND)
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        title_label = tk.Label(self, text="Marktrix", font=(
            "Helvetica", 64, "bold"), bg=COLOR_BACKGROUND, fg=COLOR_TEXT_ON_DARK)
        title_label.grid(row=0, column=0, pady=(20, 30))
        pane_area = tk.Frame(self, bg=COLOR_BACKGROUND)
        pane_area.grid(row=1, column=0, sticky="nsew")
        pane_area.grid_columnconfigure(0, weight=1)
        pane_area.grid_rowconfigure(0, weight=1)
        pane_area.grid_rowconfigure(1, weight=0)
        pane_area.grid_rowconfigure(2, weight=0)
        pane_area.grid_rowconfigure(3, weight=1)
        self.icon_label = tk.Label(
            pane_area, image=self.controller.icon_watermark_img, bg=COLOR_BACKGROUND)
        if self.controller.icon_watermark_img:
            self.icon_label.grid(row=0, column=0, sticky="s", pady=(0, 5))
        else:
            tk.Label(pane_area, text="💧", font=("Helvetica", 30), bg=COLOR_BACKGROUND,
                     fg=COLOR_TEXT_ON_DARK).grid(row=0, column=0, sticky="s", pady=(0, 5))
        select_btn = ttk.Button(pane_area, text="Select Watermark File",
                                style="Std.TButton", command=self.controller.select_watermark_file)
        select_btn.grid(row=1, column=0, pady=5)
        self.filename_area = tk.Frame(pane_area, bg=COLOR_BACKGROUND)
        self.filename_area.grid_columnconfigure(0, weight=0)  # No expansion
        self.filename_area.grid_columnconfigure(1, weight=0)
        self.filename_label = tk.Label(self.filename_area, textvariable=self.controller.watermark_file,
                                       width=35, anchor="w", bg=COLOR_BACKGROUND, fg=COLOR_TEXT_ON_DARK, wraplength=300, justify="left")
        self.filename_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.clear_btn = tk.Button(self.filename_area, text="X", font=("Helvetica", 8, "bold"), relief="flat", borderwidth=0,
                                   bg=COLOR_BACKGROUND, fg=COLOR_CLEAR_BUTTON_FG, activebackground=COLOR_BACKGROUND, command=self.controller.clear_watermark)
        self.clear_btn.grid(row=0, column=1, sticky="w")
        self.filename_area.grid(row=2, column=0, pady=5)
        self.filename_area.grid_remove()
        nav_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        nav_frame.grid(row=2, column=0, sticky="se", padx=15, pady=15)
        self.next_button = ttk.Button(nav_frame, text="Next", style="Highlight.TButton",
                                      state='disabled', command=lambda: self.controller.show_frame("MainPage"))
        self.next_button.pack()
        self.update_display()

    def update_display(self):
        wm_file = self.controller.watermark_file.get()
        if wm_file and os.path.exists(wm_file):
            self.filename_label.config(text=os.path.basename(wm_file))
            self.filename_area.grid()
            self.next_button['state'] = 'normal'
        else:
            self.filename_label.config(text="")
            self.filename_area.grid_remove()
            self.next_button['state'] = 'disabled'


# --- === Page 2 Frame Definition (REVISED ALIGNMENT + CENTERING) === ---
class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg=COLOR_BACKGROUND)
        self.controller = controller
        self.widgets_to_disable = []

        # Configure main grid rows/columns for this page frame
        # Main content row expands vertically
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Bottom controls fixed height
        self.grid_columnconfigure(0, weight=1)

        # --- Main content frame holds the 3 areas ---
        content_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        # Configure internal grid columns
        content_frame.grid_columnconfigure(
            0, weight=1, uniform="pane", minsize=200)
        content_frame.grid_columnconfigure(1, weight=0)
        content_frame.grid_columnconfigure(
            2, weight=1, uniform="pane", minsize=200)
        # Configure the single content row to expand vertically
        content_frame.grid_rowconfigure(0, weight=1)

        # --- Left Area (Col 0, Row 0 - Top Aligned using Pack) ---
        # (No changes needed in this area's internal layout)
        left_area = tk.Frame(
            content_frame, bg=COLOR_BACKGROUND, padx=5, pady=5)
        # Fill the cell, align top implicitly via pack
        left_area.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        icon_label_left = tk.Label(
            left_area, image=self.controller.icon_file_img, bg=COLOR_BACKGROUND)
        if self.controller.icon_file_img:
            icon_label_left.pack(pady=(10, 5))
        else:
            tk.Label(left_area, text="📄", font=("Helvetica", 24),
                     bg=COLOR_BACKGROUND, fg=COLOR_TEXT_ON_DARK).pack(pady=(10, 5))

        select_images_btn = ttk.Button(
            left_area, text="Select Images", style="Std.TButton", command=self.controller.select_image_files)
        select_images_btn.pack(pady=5)
        self.widgets_to_disable.append(select_images_btn)

        listbox_frame = tk.Frame(left_area, bg=COLOR_LISTBOX_BG)
        listbox_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        self.file_listbox = tk.Listbox(listbox_frame, height=6,
                                       bg=COLOR_LISTBOX_BG, fg=COLOR_LISTBOX_FG, selectbackground=COLOR_LISTBOX_SELECT_BG,
                                       selectforeground=COLOR_LISTBOX_SELECT_FG, borderwidth=0, relief="flat", exportselection=False)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar_y = ttk.Scrollbar(
            listbox_frame, orient="vertical", command=self.file_listbox.yview)
        list_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=list_scrollbar_y.set)

        remove_btn = ttk.Button(left_area, text="Remove Selected",
                                style="Std.TButton", command=self.controller.remove_selected_file)
        remove_btn.pack(pady=(5, 10))
        self.widgets_to_disable.append(remove_btn)

        # --- Middle Area (Col 1, Row 0 - Centered Vertically using Grid Weights) ---
        middle_area = tk.Frame(
            content_frame, bg=COLOR_BACKGROUND, padx=10, pady=10)
        middle_area.grid(row=0, column=1, padx=5, pady=5,
                         sticky="nsew")  # Fill the cell
        # Use grid row weights to center content vertically
        middle_area.grid_rowconfigure(0, weight=1)  # Space above, expands
        # Position Group, fixed size <<-- CONTENT ROW 1
        middle_area.grid_rowconfigure(1, weight=0)
        # Arrow, fixed size          <<-- CONTENT ROW 2
        middle_area.grid_rowconfigure(2, weight=0)
        middle_area.grid_rowconfigure(3, weight=1)  # Space below, expands
        middle_area.grid_columnconfigure(
            0, weight=1)  # Allows horizontal centering

        # Position Group centered horizontally in its row
        position_group = tk.Frame(middle_area, bg=COLOR_BACKGROUND)
        position_group.grid(row=1, column=0, pady=5)  # Place in grid row 1
        pos_label = tk.Label(position_group, text="Position",
                             bg=COLOR_BACKGROUND, fg=COLOR_TEXT_ON_DARK)
        pos_label.pack()  # Pack inside group
        self.position_combo = ttk.Combobox(position_group, values=[
            'Bottom-Left', 'Bottom-Right', 'Top-Right', 'Top-Left', 'Center'], state="readonly", width=15)
        self.position_combo.set('Bottom-Left')
        self.position_combo.pack(pady=(2, 0))  # Pack inside group
        self.widgets_to_disable.append(self.position_combo)
        self.position_combo.bind(
            '<<ComboboxSelected>>', self.on_position_selected)

        # Arrow centered horizontally in its row
        icon_label_arrow = tk.Label(
            middle_area, image=self.controller.icon_arrow_img, bg=COLOR_BACKGROUND)
        if self.controller.icon_arrow_img:
            # Place in grid row 2
            icon_label_arrow.grid(row=2, column=0, pady=10)
        else:
            tk.Label(middle_area, text="➡", font=("Helvetica", 30), bg=COLOR_BACKGROUND,
                     # Place in grid row 2
                     fg=COLOR_TEXT_ON_DARK).grid(row=2, column=0, pady=10)

        # --- Right Area (Col 2, Row 0 - Centered Vertically using Grid Weights) ---
        right_area = tk.Frame(
            content_frame, bg=COLOR_BACKGROUND, padx=5, pady=5)
        right_area.grid(row=0, column=2, padx=5, pady=5,
                        sticky="nsew")  # Fill the cell
        # Use grid row weights to center content vertically
        right_area.grid_rowconfigure(0, weight=1)  # Space above, expands
        # Icon, fixed size       <<-- CONTENT ROW 1
        right_area.grid_rowconfigure(1, weight=0)
        # Button, fixed size     <<-- CONTENT ROW 2
        right_area.grid_rowconfigure(2, weight=0)
        right_area.grid_rowconfigure(3, weight=1)  # Space below, expands
        # Allows horizontal centering
        right_area.grid_columnconfigure(0, weight=1)

        # Export Icon centered horizontally in its row
        icon_label_export = tk.Label(
            right_area, image=self.controller.icon_export_img, bg=COLOR_BACKGROUND)
        # Place in grid row 1, use default sticky (center)
        if self.controller.icon_export_img:
            icon_label_export.grid(row=1, column=0, pady=5)
        else:
            tk.Label(right_area, text="⬇", font=("Helvetica", 30), bg=COLOR_BACKGROUND,
                     fg=COLOR_TEXT_ON_DARK).grid(row=1, column=0, pady=5)

        # Export Button centered horizontally in its row
        self.export_button = ttk.Button(
            right_area, text="Export", style="Highlight.TButton", state='disabled', command=self.controller.start_export)
        # Place in grid row 2, use default sticky (center)
        self.export_button.grid(row=2, column=0, pady=5)

        # --- Bottom Controls Frame (Unchanged placement relative to page) ---
        bottom_controls_frame = tk.Frame(self, bg=COLOR_BACKGROUND)
        bottom_controls_frame.grid(
            # Use grid row 1
            row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # --- Output Row, Status Row, Nav Row remain unchanged inside bottom_controls_frame ---
        output_frame = tk.Frame(bottom_controls_frame, bg=COLOR_BACKGROUND)
        output_frame.pack(fill=tk.X, pady=(5, 5))
        output_label = tk.Label(
            output_frame, text="Output Folder:", bg=COLOR_BACKGROUND, fg=COLOR_TEXT_ON_DARK)
        output_label.pack(side=tk.LEFT, padx=(0, 5))
        self.output_entry = tk.Entry(output_frame, textvariable=self.controller.output_folder, width=50,
                                     relief="solid", borderwidth=1, state='readonly', bg=COLOR_ENTRY_BG, fg=COLOR_TEXT_ON_PANE)
        self.output_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        output_browse_btn = ttk.Button(
            output_frame, text="Browse", style="Std.TButton", command=self.controller.select_output_folder)
        output_browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.widgets_to_disable.append(output_browse_btn)

        self.status_label_var = tk.StringVar()
        self.status_label = tk.Label(bottom_controls_frame, textvariable=self.status_label_var,
                                     height=2, anchor='center', justify='center', bg=COLOR_BACKGROUND, fg=COLOR_TEXT_ON_DARK)
        self.status_label.pack(fill=tk.X, pady=(5, 5))

        nav_frame = tk.Frame(bottom_controls_frame, bg=COLOR_BACKGROUND)
        nav_frame.pack(fill=tk.X, pady=(5, 5))
        back_button = ttk.Button(nav_frame, text="Back", style="Std.TButton",
                                 command=lambda: self.controller.show_frame("WatermarkPage"))
        back_button.pack(side=tk.LEFT)
        self.widgets_to_disable.append(back_button)

    # --- Methods update_status and set_ui_state remain unchanged ---
    def update_status(self, message, error=False, warning=False, success=False):
        color = COLOR_TEXT_ON_DARK
        fm = self.controller.frames.get("MainPage")
        if error:
            color = '#FF6347'
        elif warning:
            color = '#FFA500'
        elif success:
            color = '#90EE90'
        if fm and hasattr(fm, 'status_label_var'):
            fm.status_label_var.set(message)
        if fm and hasattr(fm, 'status_label'):
            fm.status_label.config(fg=color)

    def set_ui_state(self, state='normal'):
        combobox_state = state if state == 'normal' else 'disabled'
        entry_state = 'readonly'
        output_browse_btn = None
        for w in self.widgets_to_disable:
            # Find browse button better
            if isinstance(w, ttk.Button) and 'Browse' in w.cget('text'):
                output_browse_btn = w
                break
        for widget in self.widgets_to_disable:
            widget_type = widget.winfo_class()
            try:
                if widget is self.position_combo:
                    widget['state'] = combobox_state
                elif widget_type == 'Entry':
                    pass  # Keep readonly
                elif widget_type in ('TButton', 'Button'):
                    widget['state'] = state
            except tk.TclError:
                pass
            except Exception as e:
                print(f"Error setting state for {widget}: {e}")

    def on_position_selected(self, event=None):
        """Forces focus away from combobox after selection."""
        # Set focus to the main page frame itself
        self.focus_set()
        # Alternatively, could try setting focus to the root window:
        # self.controller.root.focus_set()


# --- Main execution ---
if __name__ == '__main__':
    class MockProcessor:
        class WatermarkError(Exception):
            pass

        def batch_watermark(self, *args): print("\n--- Mock Processing ---"); import time; time.sleep(
            1); print(f"Args: {args[:]}"); print("--- Mock Processing Complete ---"); return len(args[0])
    processor = MockProcessor()
    root = tk.Tk()
    app = AppWindow(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application closed.")
