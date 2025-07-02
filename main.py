import os
import json # Vẫn giữ lại json nếu bạn muốn lưu cài đặt theme, nếu không có thể loại bỏ
import shutil
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, Listbox, StringVar, IntVar
from PIL import Image, ImageTk


class ImageCutterApp:
    def __init__(self, master):
        self.master = master
        master.title("Phần mềm lọc ảnh và video đơn giản")
        master.state('zoomed')
        master.bind("<Configure>", self.check_fullscreen)

        self.source_folder = StringVar()
        self.filtered_folders = [StringVar() for _ in range(10)]
        self.selected_folder_index = IntVar(value=0)

        self.image_list = []
        self.current_index = 0

        self.supported_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp",
                                     ".mp4", ".avi", ".mov", ".mkv", ".webm")

        self.create_widgets()

    def check_fullscreen(self, event=None):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        current_width = self.master.winfo_width()
        current_height = self.master.winfo_height()
        if current_width < screen_width or current_height < screen_height:
            self.master.after(500, lambda: self.master.state('zoomed'))

    def create_widgets(self):
        frm = ttk.Frame(self.master, padding=10)
        frm.pack(fill=BOTH, expand=True)

        folder_selection_frame = ttk.Labelframe(frm, text="📁 Chọn thư mục", padding=10)
        folder_selection_frame.pack(fill=X, pady=5)

        folder_selection_frame.grid_columnconfigure(1, weight=1)
        folder_selection_frame.grid_columnconfigure(5, weight=1)
        folder_selection_frame.grid_columnconfigure(3, weight=0, minsize=50)

        ttk.Label(folder_selection_frame, text="Thư mục gốc:").grid(row=0, column=0, sticky=W, pady=2, padx=5)
        ttk.Entry(folder_selection_frame, textvariable=self.source_folder, width=60).grid(row=0, column=1, pady=2, padx=5, columnspan=5, sticky="ew")
        ttk.Button(folder_selection_frame, text="Chọn", command=self.select_source_folder).grid(row=0, column=6, padx=5, pady=2)

        num_folders = len(self.filtered_folders)
        rows_per_column = 5

        for i in range(num_folders):
            if i < rows_per_column:
                col_offset = 0
                current_row = i + 1
            else:
                col_offset = 4
                current_row = (i % rows_per_column) + 1

            ttk.Label(folder_selection_frame, text=f"Thư mục lọc {i+1}:").grid(row=current_row, column=0 + col_offset, sticky=W, pady=2, padx=5)
            ttk.Entry(folder_selection_frame, textvariable=self.filtered_folders[i], width=40).grid(row=current_row, column=1 + col_offset, pady=2, padx=5, sticky="ew")
            ttk.Button(folder_selection_frame, text="Chọn", command=lambda idx=i: self.select_filtered_folder(idx)).grid(row=current_row, column=2 + col_offset, padx=5, pady=2)


        radio_select_frame = ttk.Labelframe(frm, text="🎯 Chọn thư mục đích:", padding=10)
        radio_select_frame.pack(fill=X, pady=5)

        radio_buttons_inner_frame = ttk.Frame(radio_select_frame)
        radio_buttons_inner_frame.pack(fill=X, expand=True)

        for i in range(num_folders):
            ttk.Radiobutton(radio_buttons_inner_frame, text=f"Lọc {i+1}", variable=self.selected_folder_index, value=i).pack(side=LEFT, padx=5, pady=2)


        self.image_label = ttk.Label(frm, text="Chưa có ảnh/video", anchor="center")
        self.image_label.pack(pady=10)

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="<< Trước", command=self.prev_image, bootstyle="secondary").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Di chuyển", command=self.cut_image, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Sao chép", command=self.copy_image, bootstyle="warning").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Sau >>", command=self.next_image, bootstyle="secondary").pack(side=LEFT, padx=5)

        self.listbox = Listbox(frm, height=7)
        self.listbox.pack(fill=X, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        bottom_frame = ttk.Frame(frm)
        bottom_frame.pack(fill=X, pady=10)

        ttk.Button(bottom_frame, text="🔃 Làm mới", command=self.load_images, bootstyle="info").pack(side=LEFT, padx=5)
        ttk.Button(bottom_frame, text="💖 Donate", command=self.open_donate, bootstyle="secondary").pack(side=LEFT, padx=5)
        self.dark_mode_button = ttk.Button(bottom_frame, text="🌙 Dark Mode", command=self.toggle_dark_mode, bootstyle="info")
        self.dark_mode_button.pack(side=LEFT, padx=5)
        ttk.Button(bottom_frame, text="❌ Thoát", command=self.master.destroy, bootstyle="danger").pack(side=RIGHT, padx=5)

    def select_source_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_folder.set(folder)
            self.load_images()

    def select_filtered_folder(self, index):
        folder = filedialog.askdirectory()
        if folder:
            self.filtered_folders[index].set(folder)

    def load_images(self):
        folder = self.source_folder.get()
        if os.path.isdir(folder):
            self.image_list = [f for f in os.listdir(folder) if f.lower().endswith(self.supported_extensions)]
            self.image_list.sort()
            self.listbox.delete(0, END)
            for img in self.image_list:
                self.listbox.insert(END, img)
            self.current_index = 0
            self.show_file()

    def show_file(self):
        if not self.image_list:
            self.image_label.configure(image='', text="Không có ảnh/video")
            return

        current_file_name = self.image_list[self.current_index]
        file_path = os.path.join(self.source_folder.get(), current_file_name)
        file_extension = os.path.splitext(current_file_name)[1].lower()

        if file_extension in (".png", ".jpg", ".jpeg", ".gif", ".bmp"):
            try:
                img = Image.open(file_path)
                img.thumbnail((200, 200))
                self.tk_img = ImageTk.PhotoImage(img)
                self.image_label.configure(image=self.tk_img, text="")
            except Exception as e:
                self.image_label.configure(image='', text=f"Lỗi hiển thị ảnh: {e}\n{current_file_name}")
                self.tk_img = None
        elif file_extension in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
            self.image_label.configure(image='', text=f"Tệp video: {current_file_name}")
            self.tk_img = None
        else:
            self.image_label.configure(image='', text=f"Tệp không hỗ trợ: {current_file_name}")
            self.tk_img = None

        self.listbox.select_clear(0, END)
        self.listbox.select_set(self.current_index)
        self.listbox.see(self.current_index)

    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_file()

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_file()

    def cut_image(self):
        if not self.image_list:
            return
        idx = self.selected_folder_index.get()
        target_folder = self.filtered_folders[idx].get()
        if not target_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đích!")
            return
        src = os.path.join(self.source_folder.get(), self.image_list[self.current_index])
        dst = os.path.join(target_folder, self.image_list[self.current_index])
        try:
            shutil.move(src, dst)
            del self.image_list[self.current_index]
            self.listbox.delete(self.current_index)
            if self.current_index >= len(self.image_list):
                self.current_index = len(self.image_list) - 1
            self.show_file()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi di chuyển tệp: {e}")

    def copy_image(self):
        if not self.image_list:
            return
        idx = self.selected_folder_index.get()
        target_folder = self.filtered_folders[idx].get()
        if not target_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đích!")
            return
        src = os.path.join(self.source_folder.get(), self.image_list[self.current_index])
        file_name = self.image_list[self.current_index]
        base, ext = os.path.splitext(file_name)

        unique_name = f"{base}_{os.urandom(4).hex()}{ext}"
        dst = os.path.join(target_folder, unique_name)

        try:
            shutil.copy2(src, dst)
            messagebox.showinfo("Thành công", f"Đã sao chép tệp: {dst}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi sao chép tệp: {e}")

    def on_listbox_select(self, event):
        if not self.listbox.curselection():
            return
        self.current_index = self.listbox.curselection()[0]
        self.show_file()

    def open_donate(self):
        import webbrowser
        webbrowser.open("https://raw.githubusercontent.com/trietpko2002/trietpko2002.github.io/refs/heads/main/donate_qr.png")

    def toggle_dark_mode(self):
        # Không cần load/save license file nữa, chỉ chuyển đổi theme trực tiếp
        current_theme = self.master.style.theme.name
        if current_theme == "flatly":
            self.master.style.theme_use("darkly")
            self.dark_mode_button.config(text="🔆 Light Mode")
        else:
            self.master.style.theme_use("flatly")
            self.dark_mode_button.config(text="🌙 Dark Mode")

if __name__ == "__main__":
    root = ttk.Window()
    # root.withdraw() # Không cần ẩn cửa sổ chính nữa, nó sẽ hiển thị ngay lập tức

    # Không cần load license data để lấy theme nữa
    # license_data = load_license()
    # initial_theme = license_data.get("theme", "flatly")
    # root.style.theme_use(initial_theme) # Sử dụng theme mặc định hoặc một theme cố định nếu muốn

    # Thiết lập theme mặc định (ví dụ: "flatly" hoặc "darkly")
    root.style.theme_use("flatly") # Bạn có thể thay đổi thành "darkly" nếu muốn theme tối mặc định

    # Không cần hàm start_app và màn hình chào mừng nữa
    global app
    app = ImageCutterApp(root)
    # Cập nhật trạng thái nút Dark Mode theo theme ban đầu
    if root.style.theme.name == "darkly":
        app.dark_mode_button.config(text="🔆 Light Mode")
    else:
        app.dark_mode_button.config(text="🌙 Dark Mode")

    root.mainloop()
