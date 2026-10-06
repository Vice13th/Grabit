"""GUI confirmation/progress window for installing missing *required*
packages — used instead of a console prompt.

Why tkinter and not PySide6: this step can run *before* PySide6 itself is
confirmed installed (it's one of the required packages), so it can't
depend on Qt. tkinter ships with the standard Python installer on
Windows/macOS, so this keeps "no terminal window" true without adding a
dependency. If tkinter genuinely isn't available (some minimal Linux
installs), :func:`grabit.app._ensure_dependencies` falls back to the
original console prompt rather than failing outright.
"""
from __future__ import annotations

from typing import Callable, Optional

BG = "#0a0a0c"
PANEL = "#111114"
BORDER = "#232327"
RED = "#ff3b3b"
TEXT = "#e8e8ea"
TEXT_DIM = "#8a8a90"
GREEN = "#3ddc84"


def confirm_and_install(
    package_names: list[str],
    install_fn: Callable[[Callable[[str], None]], dict],
) -> Optional[dict]:
    """Show a small dark/red window asking to install ``package_names``.

    Returns the ``{package: ok}`` dict from ``install_fn`` if the user
    accepted and installation ran, or ``None`` if the user declined (in
    which case the caller should fall back to printing the manual command).
    ``install_fn`` receives a ``log(line: str)`` callback to stream progress.
    """
    import tkinter as tk
    from tkinter import font as tkfont

    root = tk.Tk()
    root.title("GrabIt — First-time setup")
    root.configure(bg=BG)
    root.resizable(False, False)
    w, h = 480, 360
    root.geometry(f"{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 2}")
    root.overrideredirect(False)  # keep a minimal native titlebar/close button

    mono = tkfont.Font(family="Consolas", size=10)
    if mono.actual("family") not in ("Consolas",):
        mono = tkfont.Font(family="Courier", size=10)

    title_frame = tk.Frame(root, bg=BG)
    title_frame.pack(pady=(22, 4))
    tk.Label(title_frame, text="Grab", fg=TEXT, bg=BG, font=("Segoe UI", 20, "bold")).pack(side="left")
    tk.Label(title_frame, text="It", fg=RED, bg=BG, font=("Segoe UI", 20, "bold")).pack(side="left")

    subtitle = tk.Label(
        root, text=f"{len(package_names)} required package(s) are missing:",
        fg=TEXT_DIM, bg=BG, font=("Segoe UI", 10),
    )
    subtitle.pack(pady=(0, 8))

    pkg_box = tk.Label(
        root, text=", ".join(package_names), fg=TEXT, bg=PANEL, font=mono,
        wraplength=420, justify="left", padx=12, pady=10, relief="solid",
        bd=1, highlightbackground=BORDER,
    )
    pkg_box.pack(padx=24, fill="x")

    note = tk.Label(
        root, text="Installed from the official PyPI index only, unless you've\nopted into mirror fallback in Settings.",
        fg=TEXT_DIM, bg=BG, font=("Segoe UI", 9), justify="center",
    )
    note.pack(pady=(10, 6))

    log_box = tk.Text(
        root, height=6, bg="#16161a", fg=TEXT_DIM, font=mono, bd=1,
        relief="solid", highlightbackground=BORDER, state="disabled",
    )
    log_box.pack(padx=24, pady=(4, 10), fill="both")
    log_box.pack_forget()  # hidden until install starts

    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(pady=(4, 20))

    result: dict = {"accepted": False, "install_result": None}

    def _log(line: str):
        log_box.configure(state="normal")
        log_box.insert("end", line + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")
        root.update_idletasks()

    def _on_install():
        result["accepted"] = True
        install_btn.configure(state="disabled", text="Installing...")
        skip_btn.configure(state="disabled")
        pkg_box.pack_forget()
        note.pack_forget()
        log_box.pack(padx=24, pady=(4, 10), fill="both")
        root.update_idletasks()
        outcome = install_fn(_log)
        result["install_result"] = outcome
        failed = [p for p, ok in outcome.items() if not ok]
        if failed:
            install_btn.configure(text="Some failed — close and check log", bg="#3a1414")
        else:
            install_btn.configure(text="✓ Done — starting GrabIt...", bg="#123a1f")
            root.after(700, root.destroy)
            return
        skip_btn.configure(text="Close", state="normal")

    def _on_skip():
        result["accepted"] = False
        root.destroy()

    install_btn = tk.Button(
        btn_frame, text="Install Now", command=_on_install,
        bg="#241010", fg=RED, activebackground="#331616", activeforeground=RED,
        font=("Segoe UI", 10, "bold"), relief="flat", padx=18, pady=8, cursor="hand2",
    )
    install_btn.pack(side="left", padx=8)

    skip_btn = tk.Button(
        btn_frame, text="Not Now", command=_on_skip,
        bg="#16161a", fg=TEXT_DIM, activebackground="#1a1a1f", activeforeground=TEXT,
        font=("Segoe UI", 10), relief="flat", padx=18, pady=8, cursor="hand2",
    )
    skip_btn.pack(side="left", padx=8)

    root.protocol("WM_DELETE_WINDOW", _on_skip)
    root.mainloop()

    if not result["accepted"]:
        return None
    return result["install_result"]
