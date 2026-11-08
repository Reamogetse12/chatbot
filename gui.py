import os
import sys
import threading
import textwrap
import tkinter as tk
from tkinter import font as tkfont

# Import chat logic from chatbot.py
from chatbot import AgentMemory, chat

# ── Colours & sizing ────────────────────────────────────────────────
BG_COLOR        = "#1e1e2e"   # dark window background
USER_BUBBLE     = "#5865f2"   # indigo  – user bubbles (right)
BOT_BUBBLE      = "#2d2d3f"   # dark slate – bot bubbles (left)
USER_TEXT       = "#ffffff"
BOT_TEXT        = "#e0e0f0"
INPUT_BG        = "#2d2d3f"
INPUT_FG        = "#ffffff"
SEND_BTN_BG     = "#5865f2"
SEND_BTN_FG     = "#ffffff"
SCROLLBAR_COLOR = "#3d3d5c"
TIMESTAMP_COLOR = "#888899"

BUBBLE_RADIUS   = 18          # corner radius for rounded rectangles
H_PAD           = 14          # horizontal padding inside bubble
V_PAD           = 10          # vertical padding inside bubble
BUBBLE_MAX_W    = 0.65        # max fraction of canvas width
WRAP_CHARS      = 55          # approx chars before wrapping text
AVATAR_SIZE     = 32          # diameter of avatar circle
AVATAR_GAP      = 10          # gap between avatar and bubble


# ── Rounded-rectangle helper ────────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """Draw a rounded rectangle on *canvas* and return all item ids."""
    ids = []
    ids.append(canvas.create_arc(x1,       y1,       x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kwargs))
    ids.append(canvas.create_arc(x2-2*r,   y1,       x2,     y1+2*r, start=0,   extent=90,  style="pieslice", **kwargs))
    ids.append(canvas.create_arc(x1,       y2-2*r,   x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kwargs))
    ids.append(canvas.create_arc(x2-2*r,   y2-2*r,   x2,     y2,     start=270, extent=90,  style="pieslice", **kwargs))
    ids.append(canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs))
    ids.append(canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs))
    return ids


# ── Main application ─────────────────────────────────────────────────
class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🤖 Smart Chatbot")
        self.geometry("520x680")
        self.minsize(400, 500)
        self.configure(bg=BG_COLOR)
        self.resizable(True, True)

        self.memory = AgentMemory()
        self._build_fonts()
        self._build_ui()
        self._add_welcome_message()

    # ── Fonts ────────────────────────────────────────────────────────
    def _build_fonts(self):
        self.msg_font  = tkfont.Font(family="Segoe UI", size=11)
        self.time_font = tkfont.Font(family="Segoe UI", size=8)
        self.name_font = tkfont.Font(family="Segoe UI", size=9, weight="bold")

    # ── UI layout ────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header bar
        header = tk.Frame(self, bg="#12121f", height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Label(header, text="🤖  Smart Chatbot", bg="#12121f",
                 fg="#ffffff", font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(header, text="● online", bg="#12121f",
                 fg="#43b581", font=("Segoe UI", 9)).pack(side="right", padx=16)

        # ── Scrollable canvas for messages
        canvas_frame = tk.Frame(self, bg=BG_COLOR)
        canvas_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(canvas_frame, bg=BG_COLOR,
                                highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical",
                                 command=self.canvas.yview,
                                 bg=SCROLLBAR_COLOR, troughcolor=BG_COLOR,
                                 activebackground=SCROLLBAR_COLOR)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Inner frame that holds all bubble widgets
        self.msg_frame = tk.Frame(self.canvas, bg=BG_COLOR)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.msg_frame, anchor="nw"
        )

        self.msg_frame.bind("<Configure>", self._on_frame_resize)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ── Input area
        input_frame = tk.Frame(self, bg="#12121f", pady=10)
        input_frame.pack(fill="x", side="bottom")

        self.input_var = tk.StringVar()
        self.input_box = tk.Entry(
            input_frame, textvariable=self.input_var,
            bg=INPUT_BG, fg=INPUT_FG, insertbackground=INPUT_FG,
            relief="flat", font=("Segoe UI", 11), bd=0
        )
        self.input_box.pack(side="left", fill="x", expand=True,
                            padx=(14, 8), ipady=8)
        self.input_box.bind("<Return>", lambda e: self._send())

        self.send_btn = tk.Button(
            input_frame, text="Send ➤",
            bg=SEND_BTN_BG, fg=SEND_BTN_FG,
            activebackground="#4752c4", activeforeground="#ffffff",
            relief="flat", font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2",
            command=self._send
        )
        self.send_btn.pack(side="right", padx=(0, 14))

    # ── Canvas / frame resize handlers ───────────────────────────────
    def _on_frame_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _scroll_bottom(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # ── Welcome message ───────────────────────────────────────────────
    def _add_welcome_message(self):
        self._add_bubble(
            "Hi! I'm your smart assistant 👋\n"
            "Ask me anything, or try:\n"
            "• \"What's the weather in London?\"\n"
            "• \"Remember my name is Alex\"\n"
            "• \"What's my name?\"",
            sender="bot"
        )

    # ── Bubble drawing ────────────────────────────────────────────────
    def _add_bubble(self, text: str, sender: str):
        """Add a chat bubble to the message frame."""
        is_user = sender == "user"
        bubble_color = USER_BUBBLE if is_user else BOT_BUBBLE
        text_color   = USER_TEXT   if is_user else BOT_TEXT
        avatar_label = "You" if is_user else "AI"
        avatar_color = "#5865f2" if is_user else "#43b581"

        # Outer row frame
        row = tk.Frame(self.msg_frame, bg=BG_COLOR)
        row.pack(fill="x", padx=12, pady=(6, 2),
                 anchor="e" if is_user else "w")

        # Avatar circle (drawn on a small canvas)
        av_canvas = tk.Canvas(row, width=AVATAR_SIZE, height=AVATAR_SIZE,
                              bg=BG_COLOR, highlightthickness=0, bd=0)
        av_canvas.create_oval(2, 2, AVATAR_SIZE-2, AVATAR_SIZE-2,
                              fill=avatar_color, outline="")
        av_canvas.create_text(AVATAR_SIZE//2, AVATAR_SIZE//2,
                              text=avatar_label[0],
                              fill="white",
                              font=("Segoe UI", 9, "bold"))

        # Bubble canvas
        cw = int(self.winfo_width() * BUBBLE_MAX_W) or 300
        wrapped = textwrap.fill(text, width=WRAP_CHARS)

        # Measure text size using a temporary label
        tmp = tk.Label(self, text=wrapped, font=self.msg_font,
                       wraplength=cw - H_PAD*2)
        tmp.update_idletasks()
        tw = min(tmp.winfo_reqwidth(), cw - H_PAD*2)
        th = tmp.winfo_reqheight()
        tmp.destroy()

        bw = tw + H_PAD * 2
        bh = th + V_PAD * 2

        bub = tk.Canvas(row, width=bw, height=bh,
                        bg=BG_COLOR, highlightthickness=0, bd=0)

        # Draw rounded rect
        rounded_rect(bub, 0, 0, bw, bh, BUBBLE_RADIUS,
                     fill=bubble_color, outline="")

        # Draw text
        bub.create_text(
            H_PAD, V_PAD,
            text=wrapped,
            fill=text_color,
            font=self.msg_font,
            anchor="nw",
            width=tw
        )

        # Pack avatar and bubble in the correct order
        if is_user:
            bub.pack(side="right", padx=(0, AVATAR_GAP))
            av_canvas.pack(side="right")
        else:
            av_canvas.pack(side="left")
            bub.pack(side="left", padx=(AVATAR_GAP, 0))

        self._scroll_bottom()

    # ── Typing indicator ──────────────────────────────────────────────
    def _show_typing(self):
        self._typing_row = tk.Frame(self.msg_frame, bg=BG_COLOR)
        self._typing_row.pack(fill="x", padx=12, pady=(4, 2), anchor="w")

        av = tk.Canvas(self._typing_row, width=AVATAR_SIZE, height=AVATAR_SIZE,
                       bg=BG_COLOR, highlightthickness=0, bd=0)
        av.create_oval(2, 2, AVATAR_SIZE-2, AVATAR_SIZE-2,
                       fill="#43b581", outline="")
        av.create_text(AVATAR_SIZE//2, AVATAR_SIZE//2, text="A",
                       fill="white", font=("Segoe UI", 9, "bold"))
        av.pack(side="left")

        bub = tk.Canvas(self._typing_row, width=72, height=36,
                        bg=BG_COLOR, highlightthickness=0, bd=0)
        rounded_rect(bub, 0, 0, 72, 36, BUBBLE_RADIUS,
                     fill=BOT_BUBBLE, outline="")
        bub.create_text(36, 18, text="● ● ●", fill="#888899",
                        font=("Segoe UI", 10))
        bub.pack(side="left", padx=(AVATAR_GAP, 0))

        self._scroll_bottom()

    def _hide_typing(self):
        if hasattr(self, "_typing_row"):
            self._typing_row.destroy()
            del self._typing_row

    # ── Send logic ────────────────────────────────────────────────────
    def _send(self):
        text = self.input_var.get().strip()
        if not text:
            return

        self.input_var.set("")
        self.input_box.config(state="disabled")
        self.send_btn.config(state="disabled")

        self._add_bubble(text, sender="user")
        self._show_typing()

        # Run the API call in a background thread so the UI stays responsive
        threading.Thread(target=self._get_reply, args=(text,),
                         daemon=True).start()

    def _get_reply(self, text: str):
        try:
            reply = chat(text, self.memory)
        except Exception as e:
            reply = f"⚠️ Error: {e}"
        # Schedule UI update back on the main thread
        self.after(0, self._show_reply, reply)

    def _show_reply(self, reply: str):
        self._hide_typing()
        self._add_bubble(reply, sender="bot")
        self.input_box.config(state="normal")
        self.send_btn.config(state="normal")
        self.input_box.focus_set()


# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY environment variable is not set.")
        print("   Set it before running:  $env:OPENAI_API_KEY = 'sk-...'")
        sys.exit(1)

    app = ChatApp()
    app.mainloop()
