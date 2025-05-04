import os
import json
import shutil
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, Listbox, StringVar, IntVar
from PIL import Image, ImageTk

LICENSE_FILE = "license.json"
VALID_KEY = "VBNE7-RTYUI-KLZXC-MQAS1"
MAX_USES = 50

def load_license():
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            return json.load(f)
    return {"key": "", "uses": 0}

def save_license(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f)

def check_license_key(root, callback):
    data = load_license()

    if data.get("key") == VALID_KEY:
        callback()
        return

    if data.get("uses", 0) < MAX_USES:
        data["uses"] += 1
        save_license(data)
        callback()
        return

    def on_submit():
        entered_key = entry.get().strip().upper()
        if entered_key == VALID_KEY:
            data["key"] = entered_key
            save_license(data)
            for widget in dialog.winfo_children():
                widget.destroy()
            ttk.Label(dialog, text="Đang vào phần mềm...", font=("Arial", 12)).pack(pady=10)
            progress = ttk.Progressbar(dialog, length=250, mode='determinate')
            progress.pack(pady=20)

            def update_progress(i=0):
                if i <= 100:
                    progress['value'] = i
                    dialog.update_idletasks()
                    dialog.after(30, lambda: update_progress(i + 5))
                else:
                    for widget in dialog.winfo_children():
                        widget.destroy()
                    ttk.Label(dialog, text="✅ Kích hoạt thành công!", font=("Arial", 12), foreground="green").pack(pady=10)
                    ttk.Button(dialog, text="Vào phần mềm", command=lambda: [dialog.destroy(), callback()]).pack(pady=5)
                    ttk.Button(dialog, text="Thoát phần mềm", command=lambda: os._exit(0)).pack(pady=5)

            update_progress()
        else:
            error_label.config(text="❌ Mã kích hoạt không đúng!", foreground="red")

    def on_close():
        os._exit(0)

    dialog = ttk.Toplevel(root)
    dialog.title("Nhập key kích hoạt")
    dialog.geometry("400x220")
    dialog.protocol("WM_DELETE_WINDOW", on_close)

    ttk.Label(dialog, text="Nhập key kích hoạt (ví dụ: XXXX-YYYY-ZZZZ-WWWW)").pack(pady=5)
    entry = ttk.Entry(dialog, width=30, justify="center")
    entry.pack(pady=5)

    error_label = ttk.Label(dialog, text="", foreground="red", font=("Arial", 9))
    error_label.pack()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Kích hoạt", command=on_submit).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Thoát", command=on_close).pack(side="left", padx=10)

    ttk.Label(dialog, text="Phần mềm làm bởi ChatGPT Prompt code: Triết Võ Phiên bản: V.3.0 beta").pack(pady=5)

class ImageCutterApp:
    def __init__(self, master):
        self.master = master
        master.title("Phần mềm lọc ảnh đơn giản")
        master.state('zoomed')  # Phóng to cửa sổ
        master.bind("<Configure>", self.check_fullscreen)

        self.source_folder = StringVar()
        self.filtered_folders = [StringVar() for _ in range(4)]
        self.selected_folder_index = IntVar(value=0)

        self.image_list = []
        self.current_index = 0

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

        folder_frame = ttk.Labelframe(frm, text="📁 Chọn thư mục", padding=10)
        folder_frame.pack(fill=X, pady=5)

        ttk.Label(folder_frame, text="Thư mục gốc:").grid(row=0, column=0, sticky=W)
        ttk.Entry(folder_frame, textvariable=self.source_folder, width=60).grid(row=0, column=1)
        ttk.Button(folder_frame, text="Chọn", command=self.select_source_folder).grid(row=0, column=2, padx=5)

        for i in range(4):
            ttk.Label(folder_frame, text=f"Thư mục lọc {i+1}:").grid(row=i+1, column=0, sticky=W)
            ttk.Entry(folder_frame, textvariable=self.filtered_folders[i], width=60).grid(row=i+1, column=1)
            ttk.Button(folder_frame, text="Chọn", command=lambda idx=i: self.select_filtered_folder(idx)).grid(row=i+1, column=2, padx=5)

        radio_frame = ttk.Frame(frm)
        radio_frame.pack(pady=5)
        ttk.Label(radio_frame, text="Chọn thư mục để lọc: ").pack(side=LEFT)
        for i in range(4):
            ttk.Radiobutton(radio_frame, text=f"Lọc {i+1}", variable=self.selected_folder_index, value=i).pack(side=LEFT, padx=5)

        self.image_label = ttk.Label(frm, text="Chưa có ảnh", anchor="center")
        self.image_label.pack(pady=10)

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="<< Trước", command=self.prev_image, bootstyle="secondary").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cắt ảnh", command=self.cut_image, bootstyle="success").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Copy ảnh", command=self.copy_image, bootstyle="warning").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Sau >>", command=self.next_image, bootstyle="secondary").pack(side=LEFT, padx=5)

        self.listbox = Listbox(frm, height=7)
        self.listbox.pack(fill=X, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        bottom_frame = ttk.Frame(frm)
        bottom_frame.pack(fill=X, pady=10)

        ttk.Button(bottom_frame, text="🔃 Làm mới", command=self.load_images, bootstyle="info").pack(side=LEFT, padx=5)
        ttk.Button(bottom_frame, text="💖 Donate", command=self.open_donate, bootstyle="secondary").pack(side=LEFT, padx=5)
        ttk.Button(bottom_frame, text="🔑 Đổi key kích hoạt", command=self.change_key, bootstyle="warning").pack(side=LEFT, padx=5)
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
            self.image_list = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
            self.image_list.sort()
            self.listbox.delete(0, END)
            for img in self.image_list:
                self.listbox.insert(END, img)
            self.current_index = 0
            self.show_image()

    def show_image(self):
        if not self.image_list:
            self.image_label.configure(image='', text="Không có ảnh")
            return
        img_path = os.path.join(self.source_folder.get(), self.image_list[self.current_index])
        try:
            img = Image.open(img_path)
            img.thumbnail((300, 300))
            self.tk_img = ImageTk.PhotoImage(img)
            self.image_label.configure(image=self.tk_img, text="")
            self.listbox.select_clear(0, END)
            self.listbox.select_set(self.current_index)
            self.listbox.see(self.current_index)
        except Exception as e:
            self.image_label.configure(text=f"Lỗi ảnh: {e}")

    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_image()

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def cut_image(self):
        if not self.image_list:
            return
        idx = self.selected_folder_index.get()
        target_folder = self.filtered_folders[idx].get()
        if not target_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lọc tương ứng!")
            return
        src = os.path.join(self.source_folder.get(), self.image_list[self.current_index])
        dst = os.path.join(target_folder, self.image_list[self.current_index])
        try:
            shutil.move(src, dst)
            del self.image_list[self.current_index]
            self.listbox.delete(self.current_index)
            if self.current_index >= len(self.image_list):
                self.current_index = len(self.image_list) - 1
            self.show_image()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi cắt ảnh: {e}")

    def copy_image(self):
        if not self.image_list:
            return
        idx = self.selected_folder_index.get()
        target_folder = self.filtered_folders[idx].get()
        if not target_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lọc tương ứng!")
            return
        src = os.path.join(self.source_folder.get(), self.image_list[self.current_index])
        dst = os.path.join(target_folder, f"copy_{self.image_list[self.current_index]}")
        try:
            shutil.copy2(src, dst)
            messagebox.showinfo("Thành công", f"Đã copy ảnh: {dst}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi copy: {e}")

    def on_listbox_select(self, event):
        if not self.listbox.curselection():
            return
        self.current_index = self.listbox.curselection()[0]
        self.show_image()

    def open_donate(self):
        import webbrowser
        webbrowser.open("https://raw.githubusercontent.com/trietpko2002/trietpko2002.github.io/refs/heads/main/donate_qr.png")

    def change_key(self):
        save_license({"key": "", "uses": MAX_USES})
        messagebox.showinfo("Đổi key", "Vui lòng khởi động lại phần mềm để nhập mã mới.")
        self.master.destroy()

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    root.withdraw()

    def start_app():
        root.deiconify()
        global app
        app = ImageCutterApp(root)

    check_license_key(root, start_app)
    root.mainloop()
