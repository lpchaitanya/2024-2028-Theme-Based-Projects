"""
ImageShield Frontend: Secure PNG/JPG Image Encryption Tool GUI
BE CSE(IOT-CS-BCT) – Sem IV 2025 – 2026 Batch-No: 1

This module provides the complete Tkinter GUI for the ImageShield application
with integration to the backend encryption/decryption system.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import io
import os
import threading
from datetime import datetime
from backend import ImageShieldBackend

try:
    from livecam import LiveCameraWindow
except Exception:
    LiveCameraWindow = None


# ==================== COLOR SCHEME ====================

COLORS = {
    'bg_primary': '#0A0C10',      # Dark Space Obsidian
    'bg_secondary': '#141822',    # Carbon dark slate
    'bg_input': '#0F121C',        # Dark obsidian input field
    'accent_blue': '#00F0FF',     # Holographic Neon Cyan
    'accent_hover': '#00C2CF',    # Holographic hover cyan
    'accent_purple': '#8A2BE2',   # Neon electric purple
    'accent_red': '#FF4655',      # Coral red warning
    'accent_green': '#10F499',    # Neon success green
    'text_primary': '#F5F7FA',    # Crisp pearl white
    'text_secondary': '#7E889B',  # Slate gray secondary text
    'border': '#1F2536'           # Boundary border line
}


# ==================== MAIN APPLICATION WINDOW ====================

class ImageShieldApp:
    """Main application window for ImageShield."""
    
    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("ImageShield - Secure Image Encryption Tool")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Initialize backend
        self.backend = ImageShieldBackend()
        
        # Application state
        self.selected_image_path = None
        self.selected_file_id = None
        self.selected_enc_file_path = None
        self.current_operation = tk.StringVar(value="encrypt")
        self.lockout_remaining = tk.StringVar(value="0")
        self.lockout_timer_running = False
        
        # Create GUI
        self.create_ui()
        
    def setup_styles(self):
        """Set up modern, flat dark theme styles for Ttk widgets."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Frame styles
        self.style.configure('TFrame', background=COLORS['bg_secondary'], borderwidth=0)
        self.style.configure('AppFrame.TFrame', background=COLORS['bg_primary'], borderwidth=0)
        
        # Label styles
        self.style.configure('TLabel', background=COLORS['bg_secondary'], foreground=COLORS['text_primary'], font=("Segoe UI", 10))
        self.style.configure('Header.TLabel', background=COLORS['bg_primary'], foreground=COLORS['text_primary'], font=("Segoe UI", 16, "bold"))
        
        # Separator style
        self.style.configure('TSeparator', background=COLORS['border'])
        
        # Scrollbar style
        self.style.configure('TScrollbar',
            background=COLORS['border'],
            troughcolor=COLORS['bg_primary'],
            borderwidth=0,
            arrowsize=10
        )
        self.style.map('TScrollbar',
            background=[('active', COLORS['accent_blue'])]
        )
        
        # Notebook (Tab container) style
        self.style.configure('TNotebook', background=COLORS['bg_primary'], borderwidth=0, padding=0)
        self.style.configure('TNotebook.Tab',
            background=COLORS['bg_secondary'],
            foreground=COLORS['text_secondary'],
            font=("Segoe UI", 10, "bold"),
            padding=[20, 8],
            borderwidth=0
        )
        self.style.map('TNotebook.Tab',
            background=[('selected', COLORS['bg_primary']), ('active', COLORS['bg_primary'])],
            foreground=[('selected', COLORS['accent_blue']), ('active', COLORS['accent_blue'])],
            focuscolor=[('selected', COLORS['bg_primary'])]
        )

    def style_entry(self, entry):
        """Apply sleek obsidian entry styling with active border highlight."""
        entry.config(
            font=("Segoe UI", 10),
            bg=COLORS['bg_input'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent_blue']
        )

    def style_text_widget(self, text_widget):
        """Apply sleek text box styling."""
        text_widget.config(
            font=("Segoe UI", 10),
            bg=COLORS['bg_input'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent_blue']
        )

    def create_styled_button(self, parent, text, command, button_type="blue", **kwargs):
        """
        Create a flat, modern button with instant hover micro-animations.
        
        button_type: "blue", "green", "red", "purple"
        """
        type_colors = {
            'blue': (COLORS['accent_blue'], COLORS['bg_primary'], COLORS['accent_hover']),
            'green': (COLORS['accent_green'], COLORS['bg_primary'], '#0ee58e'),
            'red': (COLORS['accent_red'], COLORS['text_primary'], '#ff3546'),
            'purple': (COLORS['accent_purple'], COLORS['text_primary'], '#791dcf')
        }
        
        bg_color, fg_color, hover_color = type_colors.get(button_type, type_colors['blue'])
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=kwargs.get('padx', 15),
            pady=kwargs.get('pady', 8)
        )
        
        def on_enter(e):
            if btn['state'] != tk.DISABLED:
                btn.config(bg=hover_color)
                
        def on_leave(e):
            if btn['state'] != tk.DISABLED:
                btn.config(bg=bg_color)
                
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
        
    def create_ui(self):
        """Create the user interface."""
        # Apply custom style configuration
        self.setup_styles()
        
        # Main container
        main_container = ttk.Frame(self.root, style='AppFrame.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_container)
        
        # Separator
        sep = ttk.Separator(main_container, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, pady=(15, 20))
        
        # Content area with tabs
        self.create_tabbed_interface(main_container)
        
        # Footer
        self.create_footer(main_container)
    
    def create_header(self, parent):
        """Create application header."""
        header_frame = ttk.Frame(parent, style='AppFrame.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="ImageShield - Secure Image Encryption",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS['bg_primary'],
            fg=COLORS['accent_blue']
        )
        title_label.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Protect your images with AES-256 encryption",
            font=("Segoe UI", 10),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary']
        )
        subtitle_label.pack(side=tk.LEFT, padx=(20, 0), pady=(8, 0))
    
    def create_tabbed_interface(self, parent):
        """Create tabbed interface for different operations."""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Encryption Tab
        encrypt_frame = ttk.Frame(notebook)
        notebook.add(encrypt_frame, text="Encryption")
        self.create_encryption_tab(encrypt_frame)
        
        # Decryption Tab
        decrypt_frame = ttk.Frame(notebook)
        notebook.add(decrypt_frame, text="Decryption")
        self.create_decryption_tab(decrypt_frame)
        
        # Gallery Tab
        gallery_frame = ttk.Frame(notebook)
        notebook.add(gallery_frame, text="File Gallery")
        self.create_gallery_tab(gallery_frame)

        # String Encrypter Tab
        string_frame = ttk.Frame(notebook)
        notebook.add(string_frame, text="String Encrypter")
        self.create_string_encryption_tab(string_frame)
    
    def create_encryption_tab(self, parent):
        """Create encryption tab."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel - Image selection and preview
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Image selection section
        selection_label = tk.Label(
            left_panel,
            text="Step 1: Select Image",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        selection_label.pack(anchor=tk.W, pady=(0, 10))
        
        # File selector
        file_frame = ttk.Frame(left_panel)
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.encrypt_file_label = tk.Label(
            file_frame,
            text="No file selected",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            wraplength=300,
            height=2
        )
        self.encrypt_file_label.pack(fill=tk.X, pady=(0, 8))
        
        browse_btn = self.create_styled_button(
            file_frame,
            "Browse Image File",
            self.browse_image_for_encryption,
            "blue"
        )
        browse_btn.pack(fill=tk.X)
 
        camera_btn = self.create_styled_button(
            file_frame,
            "Capture From Camera",
            self.open_live_camera,
            "purple"
        )
        camera_btn.pack(fill=tk.X, pady=(8, 0))
        
        # Image preview
        preview_label = tk.Label(
            left_panel,
            text="Image Preview",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        preview_label.pack(anchor=tk.W, pady=(20, 10))
        
        self.encrypt_preview = tk.Label(
            left_panel,
            bg=COLORS['bg_primary'],
            width=250,
            height=200,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS['border']
        )
        self.encrypt_preview.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Image info
        self.encrypt_info_label = tk.Label(
            left_panel,
            text="Image info will appear here",
            font=("Segoe UI", 9),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT
        )
        self.encrypt_info_label.pack(anchor=tk.W)
        
        # Right panel - Encryption options
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # Password section
        password_label = tk.Label(
            right_panel,
            text="Step 2: Set Password",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        password_label.pack(anchor=tk.W, pady=(0, 15))
        
        tk.Label(
            right_panel,
            text="Password:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W)
        
        self.encrypt_password = tk.Entry(right_panel, show="*")
        self.style_entry(self.encrypt_password)
        self.encrypt_password.pack(fill=tk.X, pady=(5, 15))
        
        tk.Label(
            right_panel,
            text="Confirm Password:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W)
        
        self.encrypt_password_confirm = tk.Entry(right_panel, show="*")
        self.style_entry(self.encrypt_password_confirm)
        self.encrypt_password_confirm.pack(fill=tk.X, pady=(5, 20))
        
        # Custom filename section
        tk.Label(
            right_panel,
            text="Display Name (Optional):",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W)
        
        self.encrypt_display_name = tk.Entry(right_panel)
        self.style_entry(self.encrypt_display_name)
        self.encrypt_display_name.pack(fill=tk.X, pady=(5, 15))
        
        # Tags section
        tk.Label(
            right_panel,
            text="Tags (Optional):",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W)
        
        self.encrypt_tags = tk.Entry(right_panel)
        self.style_entry(self.encrypt_tags)
        self.encrypt_tags.pack(fill=tk.X, pady=(5, 25))
        
        # Encrypt button
        encrypt_btn = self.create_styled_button(
            right_panel,
            "Encrypt Image",
            self.encrypt_image,
            "green",
            pady=12
        )
        encrypt_btn.pack(fill=tk.X, pady=(0, 20))
        
        # Status area
        status_label = tk.Label(
            right_panel,
            text="Status",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        status_label.pack(anchor=tk.W, pady=(20, 10))
        
        self.encrypt_status = tk.Label(
            right_panel,
            text="Ready to encrypt",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT,
            wraplength=250,
            height=2
        )
        self.encrypt_status.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    def create_decryption_tab(self, parent):
        """Create decryption tab."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel - File selection
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        selection_label = tk.Label(
            left_panel,
            text="Step 1: Select Encrypted File",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        selection_label.pack(anchor=tk.W, pady=(0, 15))

        # Local .enc file selector
        enc_frame = ttk.Frame(left_panel)
        enc_frame.pack(fill=tk.X, pady=(0, 15))

        self.decrypt_enc_file_label = tk.Label(
            enc_frame,
            text="No .enc file selected",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            wraplength=300,
            height=2
        )
        self.decrypt_enc_file_label.pack(fill=tk.X, pady=(0, 8))

        browse_enc_btn = self.create_styled_button(
            enc_frame,
            "Browse .enc File",
            self.browse_enc_file_for_decryption,
            "blue"
        )
        browse_enc_btn.pack(fill=tk.X, pady=(0, 10))
        
        # File list
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.decrypt_file_list = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            bg=COLORS['bg_input'],
            fg=COLORS['text_primary'],
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent_blue'],
            selectbackground=COLORS['accent_blue'],
            selectforeground=COLORS['bg_primary']
        )
        self.decrypt_file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.decrypt_file_list.yview)
        self.decrypt_file_list.bind('<<ListboxSelect>>', self.on_file_selected)
        
        # Refresh button
        refresh_btn = self.create_styled_button(
            left_panel,
            "Refresh File List",
            self.refresh_file_list,
            "blue"
        )
        refresh_btn.pack(fill=tk.X)
        
        # Right panel - Decryption options
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        # File info
        info_label = tk.Label(
            right_panel,
            text="File Information",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        info_label.pack(anchor=tk.W, pady=(0, 15))
        
        self.decrypt_info = tk.Label(
            right_panel,
            text="Select a file to view details",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT,
            wraplength=280,
            height=3
        )
        self.decrypt_info.pack(fill=tk.X, pady=(0, 20))
        
        # Password section
        password_label = tk.Label(
            right_panel,
            text="Step 2: Enter Password",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        password_label.pack(anchor=tk.W, pady=(20, 15))
        
        tk.Label(
            right_panel,
            text="Password:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W)
        
        self.decrypt_password = tk.Entry(right_panel, show="*")
        self.style_entry(self.decrypt_password)
        self.decrypt_password.pack(fill=tk.X, pady=(5, 15))
        
        # Lockout warning
        self.decrypt_lockout_label = tk.Label(
            right_panel,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_red']
        )
        self.decrypt_lockout_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons frame
        buttons_frame = ttk.Frame(right_panel)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Preview button
        preview_btn = self.create_styled_button(
            buttons_frame,
            "Preview",
            self.preview_decrypted_image,
            "blue"
        )
        preview_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Decrypt button
        decrypt_btn = self.create_styled_button(
            buttons_frame,
            "Decrypt & Save",
            self.decrypt_image,
            "green"
        )
        decrypt_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Decrypted image preview section
        preview_label = tk.Label(
            right_panel,
            text="Decrypted Image Preview",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        preview_label.pack(anchor=tk.W, pady=(15, 10))
        
        self.decrypt_preview = tk.Label(
            right_panel,
            bg=COLORS['bg_primary'],
            width=250,
            height=180,
            relief=tk.FLAT,
            text="Preview will appear here",
            highlightthickness=1,
            highlightbackground=COLORS['border']
        )
        self.decrypt_preview.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Status area
        status_label = tk.Label(
            right_panel,
            text="Status",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        status_label.pack(anchor=tk.W, pady=(15, 10))
        
        self.decrypt_status = tk.Label(
            right_panel,
            text="Ready to decrypt",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT,
            wraplength=250,
            height=2
        )
        self.decrypt_status.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    def create_gallery_tab(self, parent):
        """Create file gallery tab."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_label = tk.Label(
            main_frame,
            text="Encrypted Files Gallery",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        header_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Gallery frame with scrollbar
        gallery_container = ttk.Frame(main_frame)
        gallery_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(gallery_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas = tk.Canvas(
            gallery_container,
            bg=COLORS['bg_primary'],
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)
        
        self.gallery_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.gallery_frame, anchor='nw')
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        
        self.gallery_frame.bind('<Configure>', on_frame_configure)
        
        # Refresh button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        refresh_btn = self.create_styled_button(
            button_frame,
            "Refresh Gallery",
            self.refresh_gallery,
            "blue"
        )
        refresh_btn.pack(side=tk.LEFT)
        
        # Initial gallery load
        self.refresh_gallery()
    
    def create_footer(self, parent):
        """Create application footer."""
        footer_frame = ttk.Frame(parent, style='AppFrame.TFrame')
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        footer_label = tk.Label(
            footer_frame,
            text="ImageShield v1.0 | Secure Encryption Tool | © 2026 MVSR Engineering College",
            font=("Segoe UI", 8),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary']
        )
        footer_label.pack(side=tk.LEFT)
    
    # ==================== ENCRYPTION FUNCTIONS ====================
    
    def browse_image_for_encryption(self):
        """Browse and select image file for encryption."""
        file_path = filedialog.askopenfilename(
            title="Select Image to Encrypt",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.set_encryption_image(file_path, source_label="Selected")

    def set_encryption_image(self, file_path, source_label="Selected"):
        """Set the image used for encryption and refresh the preview/info panel."""
        self.selected_image_path = file_path
        filename = os.path.basename(file_path)
        try:
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            info_text = f"File: {filename}\nSize: {file_size:.2f} MB"
        except OSError:
            info_text = f"File: {filename}\nSize: Unknown"

        self.encrypt_file_label.config(text=f"{source_label}: {filename}")
        self.encrypt_info_label.config(text=info_text)

        # Show preview
        self.show_image_preview(file_path, self.encrypt_preview)

    def open_live_camera(self):
        """Open a live camera window to capture an image for encryption."""
        if LiveCameraWindow is None:
            messagebox.showerror(
                "Camera Unavailable",
                "The live camera feature is unavailable because the camera module could not be loaded."
            )
            return
        LiveCameraWindow(self.root, on_capture=self.set_encryption_image)

    def browse_enc_file_for_decryption(self):
        """Browse and select a standalone .enc file for decryption."""
        file_path = filedialog.askopenfilename(
            title="Select .enc File",
            filetypes=[("Encrypted Files", "*.enc"), ("All Files", "*.*")]
        )

        if file_path:
            self.selected_enc_file_path = file_path
            self.selected_file_id = None
            self.decrypt_enc_file_label.config(text=f"Selected: {os.path.basename(file_path)}")
            self.update_enc_file_info(file_path)
            self.decrypt_preview.config(image="", text="Preview will appear here")

    def update_enc_file_info(self, enc_file_path):
        """Update file information display for a local .enc file."""
        package = self.backend.image_io.load_encrypted_package(enc_file_path)
        if package:
            info_text = f"Encrypted File: {os.path.basename(enc_file_path)}\n"
            info_text += f"Original Name: {package.get('original_filename', 'Unknown')}\n"
            info_text += f"Display Name: {package.get('display_name', 'Unknown')}\n"
            info_text += f"Format: {package.get('file_format', 'Unknown')}\n"
            info_text += f"Created: {package.get('created_at', 'Unknown')}"
            self.decrypt_info.config(text=info_text, fg=COLORS['text_primary'])
        else:
            info_text = (
                f"Encrypted File: {os.path.basename(enc_file_path)}\n"
                "This .enc file is not in the current package format.\n"
                "Re-encrypt the image with this version of ImageShield."
            )
            self.decrypt_info.config(
                text=info_text,
                fg=COLORS['accent_red']
            )
    
    def show_image_preview(self, image_path, preview_label):
        """Display image preview."""
        try:
            img = Image.open(image_path)
            img.thumbnail((250, 200))
            photo = ImageTk.PhotoImage(img)
            preview_label.config(image=photo)
            preview_label.image = photo
        except Exception as e:
            preview_label.config(text=f"Error loading preview: {str(e)}")
    
    def encrypt_image(self):
        """Encrypt selected image."""
        if not self.selected_image_path:
            messagebox.showerror("Error", "Please select an image file first")
            return
        
        password = self.encrypt_password.get()
        confirm_password = self.encrypt_password_confirm.get()
        display_name = self.encrypt_display_name.get() or None
        tags = self.encrypt_tags.get() or None
        
        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return

        default_name = self.encrypt_display_name.get().strip() or os.path.splitext(
            os.path.basename(self.selected_image_path)
        )[0]
        save_path = filedialog.asksaveasfilename(
            title="Save Encrypted .enc File As",
            defaultextension=".enc",
            initialfile=f"{default_name}.enc",
            filetypes=[("Encrypted Files", "*.enc"), ("All Files", "*.*")]
        )

        if not save_path:
            self.encrypt_status.config(
                text="Encryption canceled",
                fg=COLORS['text_secondary']
            )
            return
        
        # Run encryption in background thread
        threading.Thread(
            target=self._encrypt_image_thread,
            args=(self.selected_image_path, password, tags, display_name, save_path),
            daemon=True
        ).start()
    
    def _encrypt_image_thread(self, image_path, password, tags, display_name, save_path):
        """Encryption worker thread."""
        self.encrypt_status.config(
            text="Encrypting...",
            fg=COLORS['text_secondary']
        )
        self.root.update()
        
        try:
            result = self.backend.encrypt_image_file(
                image_path,
                password,
                tags,
                display_name,
                output_path=save_path
            )
            
            if result['success']:
                encrypted_file_path = result.get('encrypted_file_path', '')
                success_message = result['message']
                if encrypted_file_path:
                    success_message += f"\nSaved: {encrypted_file_path}"
                self.encrypt_status.config(
                    text=f"✓ {success_message}",
                    fg=COLORS['accent_green']
                )
                messagebox.showinfo("Success", success_message)
                
                # Clear inputs
                self.encrypt_password.delete(0, tk.END)
                self.encrypt_password_confirm.delete(0, tk.END)
                self.encrypt_display_name.delete(0, tk.END)
                self.encrypt_tags.delete(0, tk.END)
                self.selected_image_path = None
                self.encrypt_file_label.config(text="No file selected")
                self.encrypt_info_label.config(text="Image info will appear here")
            else:
                self.encrypt_status.config(
                    text=f"✗ {result['message']}",
                    fg=COLORS['accent_red']
                )
                messagebox.showerror("Error", result['message'])
        
        except Exception as e:
            self.encrypt_status.config(
                text=f"✗ Error: {str(e)}",
                fg=COLORS['accent_red']
            )
            messagebox.showerror("Error", f"Encryption failed: {str(e)}")
    
    # ==================== DECRYPTION FUNCTIONS ====================
    
    def refresh_file_list(self):
        """Refresh list of encrypted files."""
        self.decrypt_file_list.delete(0, tk.END)
        files = self.backend.get_gallery_files()
        
        for file in files:
            # Use display_name if available, otherwise use original filename
            file_name = file.get('display_name') or file['filename']
            display_text = f"{file_name} ({file['format']}) - {file['size'] / 1024:.1f} KB"
            self.decrypt_file_list.insert(tk.END, display_text)
            self.decrypt_file_list._file_ids = getattr(
                self.decrypt_file_list, '_file_ids', []
            ) + [file['file_id']]
    
    def on_file_selected(self, event):
        """Handle file selection in decryption tab."""
        selection = self.decrypt_file_list.curselection()
        if selection:
            idx = selection[0]
            file_ids = getattr(self.decrypt_file_list, '_file_ids', [])
            if idx < len(file_ids):
                self.selected_file_id = file_ids[idx]
                self.selected_enc_file_path = None
                self.decrypt_enc_file_label.config(text="No .enc file selected")
                self.update_file_info(self.selected_file_id)
    
    def update_file_info(self, file_id):
        """Update file information display."""
        files = self.backend.get_gallery_files()
        for file in files:
            if file['file_id'] == file_id:
                info_text = f"Filename: {file['filename']}\n"
                info_text += f"Format: {file['format']}\n"
                info_text += f"Size: {file['size'] / 1024:.1f} KB\n"
                info_text += f"Date: {file['date']}"
                self.decrypt_info.config(text=info_text, fg=COLORS['text_primary'])
                # Clear previous preview when selecting a new file
                self.decrypt_preview.config(image="", text="Preview will appear here")
                break
    
    def preview_decrypted_image(self):
        """Preview decrypted image without saving."""
        if not self.selected_file_id and not self.selected_enc_file_path:
            messagebox.showerror("Error", "Please select an encrypted file first")
            return
        
        password = self.decrypt_password.get()
        if not password:
            messagebox.showerror("Error", "Please enter the password")
            return
        
        # Run preview in background thread
        threading.Thread(
            target=self._preview_decrypted_image_thread,
            args=(self.selected_file_id, self.selected_enc_file_path, password),
            daemon=True
        ).start()
    
    def _preview_decrypted_image_thread(self, file_id, enc_path, password):
        """Preview decrypted image worker thread."""
        self.decrypt_status.config(
            text="Generating preview...",
            fg=COLORS['text_secondary']
        )
        self.root.update()
        
        try:
            if enc_path:
                result = self.backend.decrypt_encrypted_package_file(enc_path, password, preview_only=True)
            else:
                result = self.backend.decrypt_image_file(file_id, password, preview_only=True)
            
            if result['success']:
                # Display preview
                image_bytes = result.get('image_bytes')
                if image_bytes:
                    img = Image.open(io.BytesIO(image_bytes))
                    img.thumbnail((250, 180))
                    photo = ImageTk.PhotoImage(img)
                    self.decrypt_preview.config(image=photo, text="")
                    self.decrypt_preview.image = photo
                    
                    self.decrypt_status.config(
                        text="✓ Preview loaded successfully",
                        fg=COLORS['accent_green']
                    )
                else:
                    self.decrypt_status.config(
                        text="✗ Could not generate preview",
                        fg=COLORS['accent_red']
                    )
            else:
                if result.get('locked_out'):
                    self.decrypt_status.config(
                        text=f"✗ Locked out for {result['remaining_time']}s",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Locked Out", result['message'])
                else:
                    self.decrypt_status.config(
                        text=f"✗ {result['message']}",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Error", result['message'])
        
        except Exception as e:
            self.decrypt_status.config(
                text=f"✗ Error: {str(e)}",
                fg=COLORS['accent_red']
            )
            messagebox.showerror("Error", f"Preview failed: {str(e)}")
    
    def decrypt_image(self):
        """Decrypt selected encrypted file."""
        if not self.selected_file_id and not self.selected_enc_file_path:
            messagebox.showerror("Error", "Please select an encrypted file first")
            return
        
        password = self.decrypt_password.get()
        if not password:
            messagebox.showerror("Error", "Please enter the password")
            return

        if self.selected_enc_file_path:
            self.decrypt_status.config(
                text="Decrypting...",
                fg=COLORS['text_secondary']
            )
            self.root.update()

            validation = self.backend.decrypt_encrypted_package_file(
                self.selected_enc_file_path,
                password,
                preview_only=True
            )

            if not validation['success']:
                if validation.get('locked_out'):
                    self.decrypt_status.config(
                        text=f"✗ Locked out for {validation['remaining_time']}s",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Locked Out", validation['message'])
                else:
                    self.decrypt_status.config(
                        text=f"✗ {validation['message']}",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Error", validation['message'])
                return

            package = self.backend.image_io.load_encrypted_package(self.selected_enc_file_path)
            if package is None:
                messagebox.showerror("Error", "Unable to read the selected .enc file")
                return

            default_name = package.get('original_filename') or 'decrypted_image'
            file_ext = package.get('file_format', 'png').lower()
            save_path = filedialog.asksaveasfilename(
                defaultextension=f".{file_ext}",
                initialfile=default_name,
                filetypes=[(f"{file_ext.upper()} Files", f"*.{file_ext}"), ("All Files", "*.*")]
            )

            if not save_path:
                self.decrypt_status.config(
                    text="Decryption canceled",
                    fg=COLORS['text_secondary']
                )
                return

            saved = self.backend.image_io.save_image(
                validation['image_bytes'],
                validation.get('image_format') or package.get('file_format', 'png'),
                save_path
            )
            if saved:
                self.decrypt_status.config(
                    text="✓ Image decrypted successfully",
                    fg=COLORS['accent_green']
                )
                messagebox.showinfo(
                    "Success",
                    f"Image decrypted successfully!\nSaved to: {save_path}"
                )
                self.decrypt_password.delete(0, tk.END)
            else:
                self.decrypt_status.config(
                    text="✗ Failed to save decrypted image",
                    fg=COLORS['accent_red']
                )
                messagebox.showerror("Error", "Failed to save decrypted image")
            return

        # Ask where to save for gallery-backed decryptions
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All Files", "*.*")]
        )

        if not save_path:
            return

        # Run decryption in background thread
        threading.Thread(
            target=self._decrypt_image_thread,
            args=(self.selected_file_id, self.selected_enc_file_path, password, save_path),
            daemon=True
        ).start()
    
    def _decrypt_image_thread(self, file_id, enc_path, password, save_path):
        """Decryption worker thread."""
        self.decrypt_status.config(
            text="Decrypting...",
            fg=COLORS['text_secondary']
        )
        self.root.update()
        
        try:
            if enc_path:
                result = self.backend.decrypt_encrypted_package_file(enc_path, password, save_path)
            else:
                result = self.backend.decrypt_image_file(file_id, password, save_path)
            
            if result['success']:
                self.decrypt_status.config(
                    text=f"✓ {result['message']}",
                    fg=COLORS['accent_green']
                )
                messagebox.showinfo(
                    "Success",
                    f"Image decrypted successfully!\nSaved to: {save_path}"
                )
                self.decrypt_password.delete(0, tk.END)
            else:
                if result.get('locked_out'):
                    self.decrypt_status.config(
                        text=f"✗ Locked out for {result['remaining_time']}s",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Locked Out", result['message'])
                else:
                    self.decrypt_status.config(
                        text=f"✗ {result['message']}",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Error", result['message'])
        
        except Exception as e:
            self.decrypt_status.config(
                text=f"✗ Error: {str(e)}",
                fg=COLORS['accent_red']
            )
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")
    
    # ==================== GALLERY FUNCTIONS ====================
    
    def refresh_gallery(self):
        """Refresh file gallery display."""
        # Clear existing widgets
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()
        
        files = self.backend.get_gallery_files()
        
        if not files:
            no_files_label = tk.Label(
                self.gallery_frame,
                text="No encrypted files yet",
                font=("Segoe UI", 11),
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_secondary']
            )
            no_files_label.pack(pady=20)
            return
        
        for file in files:
            self.create_gallery_item(file)
    
    def create_gallery_item(self, file):
        """Create gallery item widget."""
        item_frame = tk.Frame(
            self.gallery_frame,
            bg=COLORS['bg_secondary'],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS['border']
        )
        item_frame.pack(fill=tk.X, pady=6, padx=10)
        
        # Content frame
        content_frame = ttk.Frame(item_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # File info - use display_name if available
        file_name = file.get('display_name') or file['filename']
        info_text = f"{file_name} ({file['format']}) - {file['size'] / 1024:.1f} KB"
        info_label = tk.Label(
            content_frame,
            text=info_text,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        )
        info_label.pack(anchor=tk.W)
        
        date_label = tk.Label(
            content_frame,
            text=f"Date: {file['date']}",
            font=("Segoe UI", 8),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary']
        )
        date_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Action buttons
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        decrypt_btn = self.create_styled_button(
            button_frame,
            "Decrypt",
            lambda fid=file['file_id']: self.quick_decrypt(fid),
            "blue"
        )
        decrypt_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = self.create_styled_button(
            button_frame,
            "Delete",
            lambda fid=file['file_id']: self.delete_file(fid),
            "red"
        )
        delete_btn.pack(side=tk.LEFT)
    
    def quick_decrypt(self, file_id):
        """Quick decrypt from gallery."""
        messagebox.showinfo(
            "Info",
            f"Go to Decryption tab and select this file to decrypt it"
        )
    
    def delete_file(self, file_id):
        """Delete encrypted file."""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this file?"):
            result = self.backend.delete_file(file_id)
            if result['success']:
                messagebox.showinfo("Success", "File deleted successfully")
                self.refresh_gallery()
            else:
                messagebox.showerror("Error", result['message'])
    
    # ==================== STRING ENCRYPTER FUNCTIONS ====================

    def create_string_encryption_tab(self, parent):
        """Create a dedicated tab for encrypting and decrypting strings/text."""
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Dual-pane layout: Left for Encryption, Right for Decryption
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # ==================== LEFT PANEL: ENCRYPTION ====================
        enc_title = tk.Label(
            left_panel,
            text="String Encryption",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        enc_title.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Label(
            left_panel,
            text="Enter text to encrypt:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Scrollable Text Input Area
        enc_text_frame = ttk.Frame(left_panel)
        enc_text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        enc_scroll = ttk.Scrollbar(enc_text_frame)
        enc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.str_encrypt_input = tk.Text(
            enc_text_frame,
            height=10
        )
        self.style_text_widget(self.str_encrypt_input)
        self.str_encrypt_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        enc_scroll.config(command=self.str_encrypt_input.yview)
        
        # Password options inside left panel
        pwd_frame = ttk.Frame(left_panel)
        pwd_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            pwd_frame,
            text="Password:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.str_encrypt_password = tk.Entry(pwd_frame, show="*")
        self.style_entry(self.str_encrypt_password)
        self.str_encrypt_password.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        tk.Label(
            pwd_frame,
            text="Confirm Password:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.str_encrypt_confirm_password = tk.Entry(pwd_frame, show="*")
        self.style_entry(self.str_encrypt_confirm_password)
        self.str_encrypt_confirm_password.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        pwd_frame.columnconfigure(1, weight=1)
        
        # Display Name (Optional)
        meta_frame = ttk.Frame(left_panel)
        meta_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            meta_frame,
            text="Display Name (Opt):",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.str_encrypt_display_name = tk.Entry(meta_frame)
        self.style_entry(self.str_encrypt_display_name)
        self.str_encrypt_display_name.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        meta_frame.columnconfigure(1, weight=1)
        
        # Encrypt & Save Button
        str_encrypt_btn = self.create_styled_button(
            left_panel,
            "Encrypt & Save String",
            self.encrypt_string,
            "green"
        )
        str_encrypt_btn.pack(fill=tk.X, pady=(0, 10))
        
        self.str_encrypt_status = tk.Label(
            left_panel,
            text="Ready to encrypt text",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT,
            wraplength=350,
            height=2
        )
        self.str_encrypt_status.pack(fill=tk.X)
        
        # ==================== RIGHT PANEL: DECRYPTION ====================
        dec_title = tk.Label(
            right_panel,
            text="String Decryption",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent_blue']
        )
        dec_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Select .enc file button
        browse_file_btn = self.create_styled_button(
            right_panel,
            "Browse & Load Encrypted Text File (.enc)",
            self.browse_str_enc_file,
            "blue"
        )
        browse_file_btn.pack(fill=tk.X, pady=(0, 10))
        
        self.selected_str_enc_path = None
        self.str_decrypt_file_label = tk.Label(
            right_panel,
            text="No text file selected",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            wraplength=350,
            height=2
        )
        self.str_decrypt_file_label.pack(fill=tk.X, pady=(0, 10))
        
        # Password entry for decryption
        pwd_dec_frame = ttk.Frame(right_panel)
        pwd_dec_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            pwd_dec_frame,
            text="Password:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.str_decrypt_password = tk.Entry(pwd_dec_frame, show="*")
        self.style_entry(self.str_decrypt_password)
        self.str_decrypt_password.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        pwd_dec_frame.columnconfigure(1, weight=1)
        
        # Decrypt Button
        str_decrypt_btn = self.create_styled_button(
            right_panel,
            "Decrypt Text",
            self.decrypt_string,
            "green"
        )
        str_decrypt_btn.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            right_panel,
            text="Decrypted Output Text:",
            font=("Segoe UI", 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary']
        ).pack(anchor=tk.W, pady=(5, 5))
        
        # Scrollable Output Text Area
        dec_text_frame = ttk.Frame(right_panel)
        dec_text_frame.pack(fill=tk.BOTH, expand=True)
        
        dec_scroll = ttk.Scrollbar(dec_text_frame)
        dec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.str_decrypt_output = tk.Text(
            dec_text_frame,
            height=8
        )
        self.style_text_widget(self.str_decrypt_output)
        self.str_decrypt_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dec_scroll.config(command=self.str_decrypt_output.yview)
        
        self.str_decrypt_status = tk.Label(
            right_panel,
            text="Ready to decrypt text",
            font=("Segoe UI", 9),
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            justify=tk.LEFT,
            wraplength=350,
            height=2
        )
        self.str_decrypt_status.pack(fill=tk.X, pady=(10, 0))

    def browse_str_enc_file(self):
        """Browse and select a standalone .enc file for string decryption."""
        file_path = filedialog.askopenfilename(
            title="Select Encrypted Text .enc File",
            filetypes=[("Encrypted Files", "*.enc"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.selected_str_enc_path = file_path
            filename = os.path.basename(file_path)
            self.str_decrypt_file_label.config(text=f"Selected: {filename}")
            
            # Let's quickly peek at the package metadata to verify it is indeed TXT format
            package = self.backend.image_io.load_encrypted_package(file_path)
            if package:
                fmt = package.get('file_format', 'Unknown')
                disp_name = package.get('display_name') or package.get('original_filename', 'Unknown')
                created = package.get('created_at', 'Unknown')
                info = f"File: {filename}\nName: {disp_name} | Format: {fmt} | Created: {created}"
                self.str_decrypt_status.config(text=info, fg=COLORS['text_primary'])
            else:
                self.str_decrypt_status.config(text="Warning: Invalid or legacy .enc file", fg=COLORS['accent_red'])
            
            # Clear decrypted text
            self.str_decrypt_output.config(state=tk.NORMAL)
            self.str_decrypt_output.delete('1.0', tk.END)
            self.str_decrypt_output.config(state=tk.DISABLED)

    def encrypt_string(self):
        """Action handler to encrypt input text."""
        text = self.str_encrypt_input.get('1.0', tk.END).strip()
        password = self.str_encrypt_password.get()
        confirm_password = self.str_encrypt_confirm_password.get()
        display_name = self.str_encrypt_display_name.get().strip() or None
        
        if not text:
            messagebox.showerror("Error", "Please enter some text to encrypt")
            return
        
        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return
        
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
            
        default_name = display_name or "encrypted_text"
        save_path = filedialog.asksaveasfilename(
            title="Save Encrypted Text As",
            defaultextension=".enc",
            initialfile=f"{default_name}.enc",
            filetypes=[("Encrypted Files", "*.enc"), ("All Files", "*.*")]
        )
        
        if not save_path:
            self.str_encrypt_status.config(text="Encryption canceled", fg=COLORS['text_secondary'])
            return
            
        # Run encryption in background thread
        threading.Thread(
            target=self._encrypt_string_thread,
            args=(text, password, display_name, save_path),
            daemon=True
        ).start()

    def _encrypt_string_thread(self, text, password, display_name, save_path):
        """Thread worker to run text encryption in the background."""
        self.str_encrypt_status.config(text="Encrypting...", fg=COLORS['text_secondary'])
        self.root.update()
        
        try:
            result = self.backend.encrypt_text_to_file(
                text=text,
                password=password,
                output_path=save_path,
                display_name=display_name
            )
            
            if result['success']:
                msg = result['message']
                self.str_encrypt_status.config(
                    text=f"✓ Saved successfully to {os.path.basename(save_path)}",
                    fg=COLORS['accent_green']
                )
                messagebox.showinfo("Success", f"{msg}\nSaved to:\n{save_path}")
                
                # Clear encryption inputs
                self.str_encrypt_input.delete('1.0', tk.END)
                self.str_encrypt_password.delete(0, tk.END)
                self.str_encrypt_confirm_password.delete(0, tk.END)
                self.str_encrypt_display_name.delete(0, tk.END)
            else:
                self.str_encrypt_status.config(
                    text=f"✗ {result['message']}",
                    fg=COLORS['accent_red']
                )
                messagebox.showerror("Error", result['message'])
        except Exception as e:
            self.str_encrypt_status.config(
                text=f"✗ Error: {str(e)}",
                fg=COLORS['accent_red']
            )
            messagebox.showerror("Error", f"Text encryption failed: {str(e)}")

    def decrypt_string(self):
        """Action handler to decrypt loaded text file."""
        if not self.selected_str_enc_path:
            messagebox.showerror("Error", "Please load an encrypted text file (.enc) first")
            return
            
        password = self.str_decrypt_password.get()
        if not password:
            messagebox.showerror("Error", "Please enter the password")
            return
            
        # Run decryption in background thread
        threading.Thread(
            target=self._decrypt_string_thread,
            args=(self.selected_str_enc_path, password),
            daemon=True
        ).start()

    def _decrypt_string_thread(self, enc_path, password):
        """Thread worker to run text decryption in the background."""
        self.str_decrypt_status.config(text="Decrypting...", fg=COLORS['text_secondary'])
        self.root.update()
        
        try:
            result = self.backend.decrypt_text_from_file(enc_path, password)
            
            if result['success']:
                decrypted_text = result['text']
                
                # Render decrypted text
                self.str_decrypt_output.config(state=tk.NORMAL)
                self.str_decrypt_output.delete('1.0', tk.END)
                self.str_decrypt_output.insert(tk.END, decrypted_text)
                self.str_decrypt_output.config(state=tk.DISABLED)
                
                self.str_decrypt_status.config(
                    text="✓ Text decrypted successfully",
                    fg=COLORS['accent_green']
                )
                messagebox.showinfo("Success", "Text decrypted successfully!")
                self.str_decrypt_password.delete(0, tk.END)
            else:
                if result.get('locked_out'):
                    self.str_decrypt_status.config(
                        text=f"✗ Locked out for {result['remaining_time']}s",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Locked Out", result['message'])
                else:
                    self.str_decrypt_status.config(
                        text=f"✗ {result['message']}",
                        fg=COLORS['accent_red']
                    )
                    messagebox.showerror("Error", result['message'])
        except Exception as e:
            self.str_decrypt_status.config(
                text=f"✗ Error: {str(e)}",
                fg=COLORS['accent_red']
            )
            messagebox.showerror("Error", f"Text decryption failed: {str(e)}")

    # ==================== TIMER FUNCTION ====================
    
    def update_lockout_timer(self):
        """Update lockout timer display."""
        remaining = self.backend.security.get_remaining_lockout_time()
        
        if remaining > 0:
            self.decrypt_lockout_label.config(
                text=f"System locked out. Try again in {remaining} seconds.",
                fg=COLORS['accent_red']
            )
            if hasattr(self, 'str_decrypt_status'):
                self.str_decrypt_status.config(
                    text=f"System locked out. Try again in {remaining} seconds.",
                    fg=COLORS['accent_red']
                )
        else:
            self.decrypt_lockout_label.config(text="")
            if hasattr(self, 'str_decrypt_status') and "locked out" in self.str_decrypt_status.cget('text').lower():
                self.str_decrypt_status.config(text="Ready to decrypt text", fg=COLORS['text_secondary'])
        
        # Schedule next update
        self.root.after(1000, self.update_lockout_timer)


# ==================== APPLICATION ENTRY POINT ====================

def main():
    """Main application entry point."""
    root = tk.Tk()
    app = ImageShieldApp(root)
    root.mainloop()
    app.backend.close()


def main_with_camera():
    """Start the application and open the camera window after launch."""
    root = tk.Tk()
    app = ImageShieldApp(root)
    root.after(250, app.open_live_camera)
    root.mainloop()
    app.backend.close()


if __name__ == "__main__":
    main()
