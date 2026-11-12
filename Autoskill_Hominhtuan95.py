import ctypes
import hashlib
import json
import os
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

APP = 'Autoskill Hominhtuan95 - 4 cua so'
PUBLIC_KEY_HEX = '75268130aebcfc32ca24e39141e0863d18ede2fdb280c73db47b0c19d874c4e4'
USER32 = ctypes.windll.user32
WM_KEYDOWN, WM_KEYUP = 0x100, 0x101
VK = [0x09, 0x20] + list(range(0x31, 0x3A)) + [0x30]
NAMES = ['Tab (chon quai)', 'Space (nhat do)'] + [f'Skill {i}' for i in range(1, 11)]
DEFAULT_DELAYS = [1500, 1000] + [1000] * 10
LICENSE_FILE = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'AutoskillHominhtuan95' / 'license.txt'


def hwid():
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography') as key:
        guid, _ = winreg.QueryValueEx(key, 'MachineGuid')
    return hashlib.sha256(('Autoskill-Hominhtuan95|' + guid).encode()).hexdigest()[:32].upper()


def verify_license(token, machine):
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        if PUBLIC_KEY_HEX == 'REPLACE_WITH_PUBLIC_KEY':
            return False
        payload_hex, sig_hex = token.strip().split('.', 1)
        payload = bytes.fromhex(payload_hex)
        signature = bytes.fromhex(sig_hex)
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX)).verify(signature, payload)
        data = json.loads(payload.decode('utf-8'))
        return data.get('hwid') == machine and data.get('app') == 'Autoskill-Hominhtuan95'
    except Exception:
        return False


def ensure_license(root):
    machine = hwid()
    try:
        if verify_license(LICENSE_FILE.read_text(encoding='utf-8'), machine):
            return True
    except OSError:
        pass
    result = {'ok': False}
    dlg = tk.Toplevel(root)
    dlg.title('Kich hoat ban quyen - HWID')
    dlg.geometry('650x310')
    dlg.transient(root)
    dlg.grab_set()
    ttk.Label(dlg, text='Ma may (HWID) - gui ma nay cho nguoi cap phep:').pack(anchor='w', padx=15, pady=(15, 4))
    machine_var = tk.StringVar(master=dlg, value=machine)
    ttk.Entry(dlg, textvariable=machine_var, state='readonly', width=52).pack(fill='x', padx=15)
    ttk.Button(dlg, text='Sao chep HWID', command=lambda: (dlg.clipboard_clear(), dlg.clipboard_append(machine))).pack(pady=7)
    ttk.Label(dlg, text='Dan ma kich hoat duoc cap:').pack(anchor='w', padx=15)
    token_box = tk.Text(dlg, height=5, wrap='word')
    token_box.pack(fill='both', expand=True, padx=15, pady=5)
    def activate():
        token = token_box.get('1.0', 'end').strip()
        if not verify_license(token, machine):
            messagebox.showerror('Khong hop le', 'Ma kich hoat khong dung voi may nay.', parent=dlg)
            return
        LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LICENSE_FILE.write_text(token, encoding='utf-8')
        result['ok'] = True
        dlg.destroy()
    ttk.Button(dlg, text='KICH HOAT', command=activate).pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW', dlg.destroy)
    root.wait_window(dlg)
    return result['ok']


def game_windows():
    found = []
    CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(hwnd, _):
        if USER32.IsWindowVisible(hwnd) and USER32.GetWindowTextLengthW(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            USER32.GetWindowTextW(hwnd, buf, 512)
            name = buf.value
            if name and ('chien quoc' in name.lower() or 'chiến quốc' in name.lower()):
                found.append((int(hwnd), name))
        return True
    callback = CALLBACK(cb)
    USER32.EnumWindows(callback, 0)
    return found


def post_key(hwnd, vk):
    if not USER32.IsWindow(hwnd):
        return
    USER32.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
    time.sleep(0.045)
    USER32.PostMessageW(hwnd, WM_KEYUP, vk, 0xC0000001)


class Slot:
    def __init__(self, parent, index):
        self.frame = ttk.LabelFrame(parent, text=f'Cua so game {index + 1}')
        self.frame.pack(fill='x', padx=8, pady=5)
        self.selected = tk.StringVar()
        self.enabled = tk.BooleanVar(value=True)
        self.rows = []
        head = ttk.Frame(self.frame)
        head.pack(fill='x', padx=6, pady=4)
        ttk.Checkbutton(head, text='Su dung', variable=self.enabled).pack(side='left')
        self.combo = ttk.Combobox(head, textvariable=self.selected, state='readonly', width=62)
        self.combo.pack(side='left', padx=8, fill='x', expand=True)
        grid = ttk.Frame(self.frame)
        grid.pack(fill='x', padx=5, pady=4)
        for i, name in enumerate(NAMES):
            active = tk.BooleanVar(value=(i < 2))
            delay = tk.StringVar(value=str(DEFAULT_DELAYS[i]))
            col, row = i // 6, i % 6
            area = ttk.Frame(grid)
            area.grid(row=row, column=col, sticky='w', padx=12, pady=2)
            ttk.Checkbutton(area, text=name, variable=active, width=19).pack(side='left')
            ttk.Entry(area, textvariable=delay, width=8).pack(side='left')
            ttk.Label(area, text='ms').pack(side='left')
            self.rows.append((active, delay))
        self.options = {}

    def update_windows(self, options):
        self.options = options
        self.combo['values'] = list(options)
        if self.selected.get() not in options:
            self.selected.set('')

    def snapshot(self):
        if not self.enabled.get() or not self.selected.get():
            return None
        hwnd = self.options.get(self.selected.get())
        if not hwnd:
            return None
        settings = []
        for i, (active, delay) in enumerate(self.rows):
            if active.get():
                try:
                    ms = int(delay.get())
                except ValueError:
                    raise ValueError(f'Cua so {self.frame.cget("text")}: thoi gian phai la so nguyen.')
                if not 50 <= ms <= 180000:
                    raise ValueError('Thoi gian phai tu 50 den 180000 ms.')
                settings.append((VK[i], ms / 1000))
        return (hwnd, settings)


class AutoApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP)
        self.root.geometry('860x900')
        self.running = False
        self.stop_event = threading.Event()
        self.workers = []
        ttk.Label(root, text='AUTOSKILL HOMINHTUAN95 - 4 CUA SO', font=('Segoe UI', 15, 'bold')).pack(pady=8)
        bar = ttk.Frame(root)
        bar.pack(fill='x', padx=10)
        ttk.Button(bar, text='Quet cua so game', command=self.refresh).pack(side='left', padx=4)
        self.button = ttk.Button(bar, text='BAT AUTO (F1)', command=self.toggle)
        self.button.pack(side='left', padx=4)
        self.status = tk.StringVar(value='Dang dung')
        ttk.Label(bar, textvariable=self.status).pack(side='left', padx=14)
        self.slots = [Slot(root, i) for i in range(4)]
        ttk.Label(root, text='Thoi gian: 50 - 180000 ms. F1 chi hoat dong khi cua so AutoSkill duoc chon.', foreground='#555').pack(pady=7)
        root.bind_all('<F1>', self.on_f1)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh()

    def refresh(self):
        options = {f'{name[:65]} | HWND {hwnd}': hwnd for hwnd, name in game_windows()}
        for slot in self.slots:
            slot.update_windows(options)
        self.status.set(f'Tim thay {len(options)} cua so game' if not self.running else 'DANG CHAY')

    def on_f1(self, event):
        self.toggle()
        return 'break'

    def toggle(self):
        if self.running:
            self.stop_event.set()
            self.running = False
            self.button.config(text='BAT AUTO (F1)')
            self.status.set('Da dung')
            return
        try:
            configs = [slot.snapshot() for slot in self.slots]
        except ValueError as exc:
            messagebox.showerror('Sai cau hinh', str(exc))
            return
        configs = [x for x in configs if x and x[1]]
        if not configs:
            messagebox.showwarning('Chua chon', 'Hay chon it nhat mot cua so game va bat mot thao tac.')
            return
        if len({hwnd for hwnd, _ in configs}) != len(configs):
            messagebox.showwarning('Trung cua so', 'Moi o phai chon mot cua so game khac nhau.')
            return
        self.stop_event = threading.Event()
        self.running = True
        self.button.config(text='TAT AUTO (F1)')
        self.status.set(f'DANG CHAY - {len(configs)} cua so')
        self.workers = []
        for hwnd, settings in configs:
            t = threading.Thread(target=self.worker, args=(hwnd, settings, self.stop_event), daemon=True)
            self.workers.append(t)
            t.start()

    @staticmethod
    def worker(hwnd, settings, stop):
        due = [time.monotonic()] * len(settings)
        while not stop.is_set() and USER32.IsWindow(hwnd):
            now = time.monotonic()
            for i, (vk, interval) in enumerate(settings):
                if now >= due[i]:
                    post_key(hwnd, vk)
                    due[i] = time.monotonic() + interval
            stop.wait(0.025)

    def close(self):
        self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        if not ensure_license(root):
            root.destroy()
            return
    except Exception as exc:
        messagebox.showerror('Loi kich hoat', str(exc), parent=root)
        root.destroy()
        return
    root.deiconify()
    AutoApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
