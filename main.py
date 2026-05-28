import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import time
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import sys

# Đảm bảo import đúng khi chạy từ thư mục gốc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageTk
from config.settings import APP_TITLE, APP_WIDTH, APP_HEIGHT, IMAGE_DIR, HASH_DIR
from modules.face.capture import get_frame_generator, capture_face
from modules.face.embedding import add_user, delete_user, list_users, build_embeddings
from modules.face.logger import log_login, get_logs
from modules.image.hash import hash_image
from modules.image.watermark import add_watermark
from modules.blockchain.contract import verify_on_chain, register_on_chain
from modules.blockchain.nft_contract import mint_nft
from modules.database.db import save_user, save_image, get_images_by_user, init_db
def recognize_face_lazy(path):
    from modules.face.recognition import recognize_face
    return recognize_face(path)


# ═══════════════════════════════════════════════
#  THEME / PALETTE
# ═══════════════════════════════════════════════
BG        = "#0D0F1A"   # nền tối chính
BG2       = "#161929"   # card / sidebar
ACCENT    = "#4F8EF7"   # xanh dương chính
ACCENT2   = "#7B5EF8"   # tím phụ
SUCCESS   = "#34D399"   # xanh lá
DANGER    = "#F87171"   # đỏ
TEXT      = "#E8EAF6"   # chữ chính
TEXT_DIM  = "#6B7280"   # chữ phụ
BORDER    = "#2A2D45"   # viền


class FaceLoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.current_user = None

        # Căn giữa màn hình
        self.update_idletasks()
        x = (self.winfo_screenwidth() - APP_WIDTH) // 2
        y = (self.winfo_screenheight() - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

        self._cam_gen = None
        self._cam_running = False
        self._capture_result = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ──────────────────────────────────────────
    # BUILD UI
    # ──────────────────────────────────────────

    def _build_ui(self):
        # ── Sidebar ──
        sidebar = tk.Frame(self, bg=BG2, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(sidebar, bg=BG2)
        logo_frame.pack(pady=30)
        tk.Label(logo_frame, text="◉", font=("Helvetica", 28), fg=ACCENT, bg=BG2).pack()
        tk.Label(logo_frame, text="FaceID", font=("Helvetica", 16, "bold"), fg=TEXT, bg=BG2).pack()
        tk.Label(logo_frame, text="Nhận diện khuôn mặt", font=("Helvetica", 8),
                 fg=TEXT_DIM, bg=BG2).pack()

        # Divider
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=5)

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("🔐", "Đăng nhập",    "login"),
            ("👤", "Đăng ký",      "register"),
            ("👥", "Người dùng",   "users"),
            ("📋", "Lịch sử",      "logs"),
            ("🖼️", "Bản quyền ảnh", "images"),
        ]
        for icon, label, key in nav_items:
            btn = self._make_nav_btn(sidebar, icon, label, key)
            self.nav_buttons[key] = btn

        # ── Main content area ──
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        # Frames
        self.frames = {}
        for F, key in [
            (LoginFrame,    "login"),
            (RegisterFrame, "register"),
            (UsersFrame,    "users"),
            (LogsFrame,     "logs"),
            (ImageFrame,    "images"),
        ]:
            frame = F(self.content, self)
            self.frames[key] = frame
            frame.place(relwidth=1, relheight=1)

        self._show_frame("login")

    def _make_nav_btn(self, parent, icon, label, key):
        frame = tk.Frame(parent, bg=BG2, cursor="hand2")
        frame.pack(fill="x", padx=12, pady=3)

        indicator = tk.Frame(frame, bg=BG2, width=3)
        indicator.pack(side="left", fill="y", pady=4)

        inner = tk.Frame(frame, bg=BG2)
        inner.pack(side="left", padx=8, pady=10)

        tk.Label(inner, text=icon, font=("Helvetica", 14), fg=TEXT_DIM, bg=BG2).pack(side="left")
        tk.Label(inner, text=f"  {label}", font=("Helvetica", 11), fg=TEXT_DIM, bg=BG2).pack(side="left")

        frame._indicator = indicator
        frame._icon_lbl = inner.winfo_children()[0]
        frame._text_lbl = inner.winfo_children()[1]

        frame.bind("<Button-1>", lambda e, k=key: self._show_frame(k))
        for child in frame.winfo_children():
            child.bind("<Button-1>", lambda e, k=key: self._show_frame(k))
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, k=key: self._show_frame(k))

        return frame

    def _show_frame(self, key):
        # Reset nav style
        for k, btn in self.nav_buttons.items():
            btn._indicator.configure(bg=BG2)
            btn._icon_lbl.configure(fg=TEXT_DIM, bg=BG2)
            btn._text_lbl.configure(fg=TEXT_DIM, bg=BG2)
            btn.configure(bg=BG2)

        # Active nav style
        btn = self.nav_buttons[key]
        btn._indicator.configure(bg=ACCENT)
        btn._icon_lbl.configure(fg=TEXT, bg=BG2)
        btn._text_lbl.configure(fg=TEXT, bg=BG2)

        # Raise frame
        self.frames[key].tkraise()
        self.frames[key].on_show()

    def _on_close(self):
        self._cam_running = False
        self.destroy()


# ═══════════════════════════════════════════════
#  BASE FRAME
# ═══════════════════════════════════════════════

class BaseFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

    def on_show(self):
        pass

    def _title(self, text, sub=""):
        tk.Label(self, text=text, font=("Helvetica", 20, "bold"),
                 fg=TEXT, bg=BG).pack(anchor="w", padx=36, pady=(30, 2))
        if sub:
            tk.Label(self, text=sub, font=("Helvetica", 10),
                     fg=TEXT_DIM, bg=BG).pack(anchor="w", padx=36, pady=(0, 16))

    def _card(self, parent=None, **kwargs):
        if parent is None:
            parent = self
        f = tk.Frame(parent, bg=BG2, bd=0, relief="flat", **kwargs)
        return f

    def _btn(self, parent, text, command, color=ACCENT, width=180):
        b = tk.Button(parent, text=text, command=command,
                      bg=color, fg="white", font=("Helvetica", 10, "bold"),
                      relief="flat", bd=0, padx=16, pady=10,
                      cursor="hand2", width=width // 10,
                      activebackground=color, activeforeground="white")
        b.bind("<Enter>", lambda e: b.config(bg=self._lighten(color)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    @staticmethod
    def _lighten(hex_color):
        """Làm sáng màu hex thêm 15%."""
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r, g, b = min(r + 30, 255), min(g + 30, 255), min(b + 30, 255)
        return f"#{r:02x}{g:02x}{b:02x}"


# ═══════════════════════════════════════════════
#  LOGIN FRAME
# ═══════════════════════════════════════════════

class LoginFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._cam_running = False
        self._cam_thread = None
        self.current_frame = None
        self._build()

    def _build(self):
        self._title("Đăng nhập", "Nhìn thẳng vào camera để đăng nhập")

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=36)

        main.columnconfigure(0, weight=3)  # camera
        main.columnconfigure(1, weight=1)  # panel phải

        # ── Camera card ──
        cam_card = self._card(main)
        cam_card.grid(row=0, column=0, sticky="nsew")

        self.cam_label = tk.Label(cam_card, bg="#0A0C14",
                                   text="Camera chưa bật",
                                   fg=TEXT_DIM, font=("Helvetica", 11))
        self.cam_label.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Right panel ──
        right = tk.Frame(main, bg=BG, width=220)
        right.grid(row=0, column=1, sticky="ns", padx=(16, 0))
        right.grid_propagate(False)

        # Status card
        status_card = self._card(right)
        status_card.pack(fill="x", pady=(0, 12))

        tk.Label(status_card, text="Trạng thái", font=("Helvetica", 9),
                 fg=TEXT_DIM, bg=BG2).pack(anchor="w", padx=14, pady=(12, 4))

        self.status_icon = tk.Label(status_card, text="⬤", font=("Helvetica", 14),
                                     fg=TEXT_DIM, bg=BG2)
        self.status_icon.pack(pady=(0, 4))

        self.status_label = tk.Label(status_card, text="Chờ nhận diện",
                                      font=("Helvetica", 11, "bold"),
                                      fg=TEXT_DIM, bg=BG2, wraplength=180)
        self.status_label.pack(pady=(0, 4), padx=8)

        self.user_label = tk.Label(status_card, text="",
                                    font=("Helvetica", 18, "bold"),
                                    fg=ACCENT, bg=BG2)
        self.user_label.pack(pady=(0, 4))

        self.conf_label = tk.Label(status_card, text="",
                                    font=("Helvetica", 9), fg=TEXT_DIM, bg=BG2)
        self.conf_label.pack(pady=(0, 14))

        # Buttons
        btn_frame = tk.Frame(right, bg=BG)
        btn_frame.pack(side="bottom", fill="x")

        self._btn(btn_frame, "▶  Bật camera", self._start_camera, ACCENT).pack(fill="x", pady=4)
        self._btn(btn_frame, "📷  Nhận diện", self._do_recognize, ACCENT2).pack(fill="x", pady=4)
        self._btn(btn_frame, "⏹  Tắt camera", self._stop_camera, "#374151").pack(fill="x", pady=4)

    def on_show(self):
        if not self._cam_running:
            self.after(200, self._start_camera)

    def _start_camera(self):
        if self._cam_running:
            return
        self._cam_running = True
        self._cam_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self._cam_thread.start()

    def _stop_camera(self):
        self._cam_running = False
        self.cam_label.configure(image="", text="Camera đã tắt", fg=TEXT_DIM)

    def _camera_loop(self):
        gen = get_frame_generator()
        for frame in gen:
            if not self._cam_running:
                break
            if frame is None:
                continue

            self.current_frame = frame.copy()

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img).resize((480, 340))
            
            if not getattr(self, '_ui_update_pending', False):
                self._ui_update_pending = True
                def update_cam(image=img):
                    self._ui_update_pending = False
                    if not self._cam_running:
                        return
                    imgtk = ImageTk.PhotoImage(image)
                    self.cam_label.configure(image=imgtk, text="")
                    self.cam_label._img = imgtk
                self.after(0, update_cam)

            time.sleep(0.03)

    def _do_recognize(self):
        if not self._cam_running:
            messagebox.showwarning("Thông báo", "Hãy bật camera trước!")
            return  

        self.status_label.configure(text="Đang nhận diện...", fg=TEXT_DIM)
        self.status_icon.configure(fg=TEXT_DIM)
        self.user_label.configure(text="")
        self.conf_label.configure(text="")
        self.update()

        if self.current_frame is None:
            self._set_status(False, "Không có frame", "", 0)
            return

        import cv2, os, time
        from config.settings import TEMP_DIR

        path = os.path.join(TEMP_DIR, f"capture_{int(time.time())}.jpg")
        cv2.imwrite(path, self.current_frame)

        if path is None:
            self._set_status(False, "Không thấy khuôn mặt", "", 0)
            return

        result = recognize_face_lazy(path)
        log_login(result.get("username"), result["success"], result.get("confidence", 0))

        if result["success"]:
            self.app.current_user = result["username"] 
            self._set_status(True, "Đăng nhập thành công!", result["username"], result["confidence"])
        else:
            self.app.current_user = None 
            self._set_status(False, result["message"], "", 0)

    def _set_status(self, ok, msg, username, conf):
        color = SUCCESS if ok else DANGER
        icon  = "✔" if ok else "✘"
        self.status_icon.configure(text=icon, fg=color)
        self.status_label.configure(text=msg, fg=color)
        self.user_label.configure(text=username)
        self.conf_label.configure(
            text=f"Độ chính xác: {int(conf*100)}%" if conf else ""
        )


# ═══════════════════════════════════════════════
#  REGISTER FRAME
# ═══════════════════════════════════════════════

class RegisterFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._cam_running = False
        self._build()

    def _build(self):
        self._title("Đăng ký người dùng", "Chụp ảnh hoặc chọn ảnh từ máy tính")

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=36)

        main.columnconfigure(0, weight=3)  # camera
        main.columnconfigure(1, weight=1)  # panel phai

        # ── Camera ──
        cam_card = self._card(main)
        cam_card.grid(row=0, column=0, sticky="nsew")
        self.cam_label = tk.Label(cam_card, bg="#0A0C14",
                                   text="Camera chưa bật",
                                   fg=TEXT_DIM, font=("Helvetica", 11))
        self.cam_label.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Right panel ──
        right = tk.Frame(main, bg=BG, width=220)
        right.grid(row=0, column=1, sticky="ns", padx=(16, 0))
        right.grid_propagate(False)

        # Form card
        form = self._card(right)
        form.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Tên người dùng", font=("Helvetica", 9),
                 fg=TEXT_DIM, bg=BG2).pack(anchor="w", padx=14, pady=(14, 4))

        self.name_var = tk.StringVar()
        entry = tk.Entry(form, textvariable=self.name_var,
                         font=("Helvetica", 12), bg="#1E2235",
                         fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0)
        entry.pack(fill="x", padx=14, pady=(0, 14), ipady=8)

        # Status
        self.reg_status = tk.Label(right, text="", font=("Helvetica", 10),
                                    fg=TEXT_DIM, bg=BG, wraplength=200)
        self.reg_status.pack(pady=8)

        # Buttons
        btn_frame = tk.Frame(right, bg=BG)
        btn_frame.pack(fill="x")

        self._btn(btn_frame, "▶  Bật camera", self._start_camera, ACCENT).pack(fill="x", pady=4)
        self._btn(btn_frame, "📷  Chụp & Đăng ký", self._register_webcam, ACCENT2).pack(fill="x", pady=4)
        self._btn(btn_frame, "🖼  Chọn ảnh từ máy", self._register_file, "#374151").pack(fill="x", pady=4)
        self._btn(btn_frame, "⏹  Tắt camera", self._stop_camera, "#374151").pack(fill="x", pady=4)

    def on_show(self):
        pass

    def _start_camera(self):
        if self._cam_running:
            return
        self._cam_running = True
        threading.Thread(target=self._camera_loop, daemon=True).start()

    def _stop_camera(self):
        self._cam_running = False
        self.cam_label.configure(image="", text="Camera đã tắt", fg=TEXT_DIM)

    def _camera_loop(self):
        for frame in get_frame_generator():
            if not self._cam_running:
                break
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img).resize((480, 340))
            
            if not getattr(self, '_ui_update_pending', False):
                self._ui_update_pending = True
                def update_cam(image=img):
                    self._ui_update_pending = False
                    if not self._cam_running:
                        return
                    imgtk = ImageTk.PhotoImage(image)
                    self.cam_label.configure(image=imgtk, text="")
                    self.cam_label._img = imgtk
                self.after(0, update_cam)
            time.sleep(0.03)

    def _get_username(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Thông báo", "Vui lòng nhập tên người dùng!")
            return None
        return name

    def _register_webcam(self):
        username = self._get_username()
        if not username:
            return
        if not self._cam_running:
            messagebox.showwarning("Thông báo", "Hãy bật camera trước!")
            return

        self.reg_status.configure(text="Đang chụp ảnh...", fg=TEXT_DIM)
        self.update()

        path = capture_face()
        if path is None:
            self.reg_status.configure(text="❌ Không thấy khuôn mặt", fg=DANGER)
            return

        ok = add_user(username, path)
        if ok:
            self.reg_status.configure(text=f"✅ Đã đăng ký '{username}'", fg=SUCCESS)
            self.name_var.set("")
            # Refresh users frame
            self.app.frames["users"].refresh()
        else:
            self.reg_status.configure(text="❌ Không thể trích xuất khuôn mặt", fg=DANGER)

    def _register_file(self):
        username = self._get_username()
        if not username:
            return

        path = filedialog.askopenfilename(
            title="Chọn ảnh khuôn mặt",
            filetypes=[("Ảnh", "*.jpg *.jpeg *.png")]
        )
        if not path:
            return

        self.reg_status.configure(text="Đang xử lý...", fg=TEXT_DIM)
        self.update()

        ok = add_user(username, path)
        if ok:
            self.reg_status.configure(text=f"✅ Đã đăng ký '{username}'", fg=SUCCESS)
            self.name_var.set("")
            self.app.frames["users"].refresh()
        else:
            self.reg_status.configure(text="❌ Không tìm thấy khuôn mặt trong ảnh", fg=DANGER)


# ═══════════════════════════════════════════════
#  USERS FRAME
# ═══════════════════════════════════════════════

class UsersFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self._title("Quản lý người dùng", "Danh sách người dùng đã đăng ký")

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=36, pady=8)

        # Toolbar
        toolbar = tk.Frame(content, bg=BG)
        toolbar.pack(fill="x", pady=(0, 12))

        self._btn(toolbar, "🔄  Làm mới", self.refresh, ACCENT).pack(side="left")
        self._btn(toolbar, "🗑  Xóa đã chọn", self._delete_selected, DANGER).pack(side="left", padx=8)
        self._btn(toolbar, "🔨  Rebuild Embeddings", self._rebuild, "#374151").pack(side="left")

        self.rebuild_label = tk.Label(toolbar, text="", font=("Helvetica", 9),
                                       fg=TEXT_DIM, bg=BG)
        self.rebuild_label.pack(side="left", padx=12)

        # Table
        table_frame = self._card(content)
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                         background=BG2, foreground=TEXT,
                         fieldbackground=BG2, rowheight=36,
                         font=("Helvetica", 10))
        style.configure("Custom.Treeview.Heading",
                         background=BG, foreground=TEXT_DIM,
                         font=("Helvetica", 9, "bold"), relief="flat")
        style.map("Custom.Treeview", background=[("selected", ACCENT2)])

        self.tree = ttk.Treeview(table_frame,
                                  columns=("name", "img"),
                                  show="headings",
                                  style="Custom.Treeview",
                                  selectmode="browse")
        self.tree.heading("name", text="Tên người dùng")
        self.tree.heading("img", text="Ảnh đăng ký")
        self.tree.column("name", width=200)
        self.tree.column("img", width=400)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def on_show(self):
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name in list_users():
            from modules.face.embedding import get_embeddings_db
            db = get_embeddings_db()
            img = db.get(name, {}).get("img_path", "—")
            self.tree.insert("", "end", values=(name, img))

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Chưa chọn người dùng nào!")
            return
        name = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Xác nhận", f"Xóa người dùng '{name}'?"):
            delete_user(name)
            self.refresh()

    def _rebuild(self):
        self.rebuild_label.configure(text="Đang rebuild...", fg=TEXT_DIM)
        self.update()
        count = build_embeddings()
        self.rebuild_label.configure(text=f"✅ Đã rebuild {count} người", fg=SUCCESS)
        self.refresh()


# ═══════════════════════════════════════════════
#  LOGS FRAME
# ═══════════════════════════════════════════════

class LogsFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self._title("Lịch sử đăng nhập", "50 lần gần nhất")

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=36, pady=8)

        toolbar = tk.Frame(content, bg=BG)
        toolbar.pack(fill="x", pady=(0, 12))
        self._btn(toolbar, "🔄  Làm mới", self.refresh, ACCENT).pack(side="left")   

        table_frame = self._card(content)
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Log.Treeview",
                         background=BG2, foreground=TEXT,
                         fieldbackground=BG2, rowheight=32,
                         font=("Helvetica", 10))
        style.configure("Log.Treeview.Heading",
                         background=BG, foreground=TEXT_DIM,
                         font=("Helvetica", 9, "bold"), relief="flat")
        style.map("Log.Treeview", background=[("selected", ACCENT2)])

        self.tree = ttk.Treeview(table_frame,
                                  columns=("time", "user", "result", "conf"),
                                  show="headings",
                                  style="Log.Treeview")
        self.tree.heading("time",   text="Thời gian")
        self.tree.heading("user",   text="Người dùng")
        self.tree.heading("result", text="Kết quả")
        self.tree.heading("conf",   text="Độ chính xác")
        self.tree.column("time",   width=160)
        self.tree.column("user",   width=160)
        self.tree.column("result", width=120)
        self.tree.column("conf",   width=120)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def on_show(self):
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for log in get_logs():
            result_text = "✅ Thành công" if log["success"] else "❌ Thất bại"
            conf_text = f"{int(log['confidence'] * 100)}%" if log["success"] else "—"
            self.tree.insert("", "end", values=(
                log["time"], log["username"], result_text, conf_text
            ))


# ═══════════════════════════════════════════════
#  IMAGE FRAME
# ═══════════════════════════════════════════════

class ImageFrame(BaseFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.selected_path = None
        self._build()

    def _build(self):
        self._title("Bảo vệ bản quyền ảnh", "Watermark + Hash SHA-256")

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=36)

        # chọn ảnh
        self.path_label = tk.Label(container, text="Chưa chọn ảnh",
                                   fg=TEXT_DIM, bg=BG)
        self.path_label.pack(pady=10)

        self._btn(container, "📁 Chọn ảnh", self.choose_file).pack(pady=5)

        self._btn(container, "💧 Thêm watermark + Đăng ký", self.register_image, ACCENT).pack(pady=5)

        self._btn(container, "🪙 Mint NFT từ ảnh", self.mint_nft, "#10b981").pack(pady=5)

        self._btn(container, "🔍 Kiểm tra ảnh", self.verify_image, ACCENT2).pack(pady=5)

        self._btn(container, "📂 Xem ảnh của tôi", self.show_my_images, "#374151").pack(pady=5)

        self.result_label = tk.Label(container, text="",
                                     fg=TEXT, bg=BG, wraplength=400)
        self.result_label.pack(pady=20)

    def choose_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image", "*.jpg *.png *.jpeg")]
        )
        if path:
            self.selected_path = path
            self.path_label.config(text=path)

    def register_image(self):
        from modules.blockchain.contract import register_on_chain
        user = self.app.current_user
        if not user:
            messagebox.showwarning("Thông báo", "Bạn chưa đăng nhập!")
            return
            
        if not self.selected_path:
            messagebox.showwarning("Thông báo", "Chọn ảnh trước!")
            return

        dirs = self._get_user_dirs()
        if dirs is None:
            return

        img_dir, hash_dir = dirs

        filename = os.path.basename(self.selected_path)
        wm_path = os.path.join(img_dir, "wm_" + filename)
        hash_file = os.path.join(hash_dir, filename + ".txt")

        user = self.app.current_user

        # watermark theo user 👇
        add_watermark(self.selected_path, wm_path, user)

        img_hash = hash_image(wm_path)

        with open(hash_file, "w") as f:
            f.write(img_hash)

        self.result_label.config(
            text=f"✅ Ảnh đã thuộc về: {user}\nHash:\n{img_hash}",
            fg=SUCCESS
        )

        try:
            save_user(user)
            save_image(user, wm_path, img_hash)
            register_on_chain(img_hash, user)

            self.result_label.config(
                text=f"✅ Đã lưu + ghi blockchain\nHash: {img_hash[:10]}...",
                fg=SUCCESS
            )

        except Exception as e:
            print("Lỗi:", e)
            self.result_label.config(
                text=f"❌ Lỗi: {str(e)}",
                fg=DANGER
            )

    def mint_nft(self):
        user = self.app.current_user
        if not user:
            messagebox.showwarning("Thông báo", "Bạn chưa đăng nhập!")
            return

        if not self.selected_path:
            messagebox.showwarning("Thông báo", "Chọn ảnh trước!")
            return

        dirs = self._get_user_dirs()
        if dirs is None:
            return

        img_dir, hash_dir = dirs
        filename = os.path.basename(self.selected_path)
        wm_path = os.path.join(img_dir, "wm_" + filename)
        hash_file = os.path.join(hash_dir, filename + ".txt")

        self.result_label.config(text="Đang chuẩn bị mint NFT...", fg=TEXT_DIM)
        self.update()

        try:
            add_watermark(self.selected_path, wm_path, user)
            img_hash = hash_image(wm_path)

            save_user(user)
            save_image(user, wm_path, img_hash)
            register_on_chain(img_hash, user)

            token_uri = f"hash://{img_hash}"
            receipt = mint_nft(token_uri)

            self.result_label.config(
                text=(f"✅ NFT đã mint thành công!\n" \
                      f"Token URI: {token_uri}\n" \
                      f"TxHash: {receipt.transactionHash.hex()}"),
                fg=SUCCESS
            )
        except Exception as e:
            print("Lỗi mint NFT:", e)
            self.result_label.config(
                text=f"❌ Mint NFT thất bại: {str(e)}",
                fg=DANGER
            )

    def verify_image(self):
        if not self.selected_path:
            messagebox.showwarning("Thông báo", "Chọn ảnh trước!")
            return

        dirs = self._get_user_dirs()
        if dirs is None:
            return

        _, hash_dir = dirs

        filename = os.path.basename(self.selected_path)
        hash_file = os.path.join(hash_dir, filename + ".txt")

        if not os.path.exists(hash_file):
            self.result_label.config(
                text="❌ Ảnh này không thuộc về bạn!",
                fg=DANGER
            )
            return

        # 🔥 hash ảnh hiện tại
        current_hash = hash_image(self.selected_path)

        # 🔥 kiểm tra local trước
        with open(hash_file, "r") as f:
            original_hash = f.read()

        if current_hash != original_hash:
            self.result_label.config(
                text="❌ Ảnh đã bị chỉnh sửa!",
                fg=DANGER
            )
            return

        # 🔥 kiểm tra blockchain (GẮN Ở ĐÂY)
        try:
            result = verify_on_chain(current_hash)

            if result["valid"]:
                self.result_label.config(
                    text=f"✅ Blockchain xác nhận\nOwner: {result['owner']}",
                    fg=SUCCESS
                )
            else:
                self.result_label.config(
                    text="❌ Không tồn tại trên blockchain",
                    fg=DANGER
                )

        except Exception as e:
            self.result_label.config(
                text=f"⚠ Lỗi blockchain:\n{str(e)}",
                fg=DANGER
            )
    
    def _get_user_dirs(self):
        user = self.app.current_user
        if not user:
            messagebox.showwarning("Thông báo", "Bạn chưa đăng nhập!")
            return None

        img_dir = os.path.join(IMAGE_DIR, user)
        hash_dir = os.path.join(HASH_DIR, user)

        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(hash_dir, exist_ok=True)

        return img_dir, hash_dir

    def show_my_images(self):
        user = self.app.current_user
        if not user:
            messagebox.showwarning("Thông báo", "Bạn chưa đăng nhập!")
            return

        data = get_images_by_user(user)

        if not data:
            self.result_label.config(text="Bạn chưa có ảnh nào", fg=TEXT_DIM)
            return

        text = "📂 Ảnh của bạn:\n\n"

        for path, hash_val, time in data:
            text += f"📸 {path}\n🔑 {hash_val[:10]}...\n🕒 {time}\n\n"

        self.result_label.config(text=text, fg=TEXT)
# ═══════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════

def start_app():
    app = FaceLoginApp()
    app.mainloop()

if __name__ == "__main__":
    print("🚀 Starting app...")

    init_db()
    start_app()