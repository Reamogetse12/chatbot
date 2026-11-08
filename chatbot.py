from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import tkinter as tk
import tkinter.font as tkfont

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.7,
    max_tokens=512,
    timeout=None,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a study mate you never give me direct answers to a task or homework,rather explain and give an exercise to test if I understand the concept.
    
    Your job:
    1.first explain the idea behind the task in simple English,step by step.
    2.Then give me a similar practice exercise to test if I understand the concept.
    3.Stop and wait for my answer to the practice exercise before giving me the correct answer.
    4.When I show you my answer, check it.If it is correct, congratulate me and give me a more challenging exercise to test my understanding of the concept.If it is wrong, give me hints and let me try again until I get it right.
    5.If I beg you for the answer, you will not give it to me, rather you will give me hints and let me try again until I get it right.
    6.Your answers should be in simple English and easy to understand.
    7.Your answers should be in a friendly and encouraging tone."""),
    ("user", "{text}")
])
chain = prompt | llm

# Colors
user_bubble = "#d1fae5"
bot_bubble = "#ffffff"
header = "#172554"
chat = "#f1f5f9"
input = "#ffffff"
accent = "#0f9f83"
text_color = "#1e293b"
muted_color = "#64748b"


window = tk.Tk()
window.title("MyChatbot")
window.geometry("720x720")
window.minsize(480, 520)
window.configure(bg=chat)

header_frame = tk.Frame(window, bg=header, height=76)
header_frame.pack(fill=tk.X)
header_frame.pack_propagate(False)

avatar = tk.Label(
    header_frame,
    text="✦",
    font=("Segoe UI", 18, "bold"),
    bg="#243b70",
    fg="#a7f3d0",
    width=3,
    height=1,
)
avatar.pack(side=tk.LEFT, padx=(18, 12), pady=15)
title_frame = tk.Frame(header_frame, bg=header)
title_frame.pack(side=tk.LEFT, pady=14)
tk.Label(
    title_frame, text="MyChatbot", font=("Segoe UI", 15, "bold"),
    bg=header, fg="#f8fafc",
).pack(anchor=tk.W)
tk.Label(
    title_frame, text="Your friendly study mate", font=("Segoe UI", 9),
    bg=header, fg="#bfdbfe",
).pack(anchor=tk.W, pady=(2, 0))
tk.Label(
    header_frame, text="●  ONLINE", font=("Segoe UI", 8, "bold"),
    bg=header, fg="#6ee7b7",
).pack(side=tk.RIGHT, padx=18)

chat_area = tk.Frame(window, bg=chat)
chat_area.pack(fill=tk.BOTH, expand=True)

chat_canvas = tk.Canvas(chat_area, bg=chat, highlightthickness=0)
chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(
    chat_area,
    orient=tk.VERTICAL,
    command=chat_canvas.yview,
    bg="#e2e8f0",
    troughcolor=chat,
    activebackground="#94a3b8",
    relief=tk.FLAT,
    borderwidth=0,
    width=10,
)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_canvas.configure(yscrollcommand=scrollbar.set)


def scroll_chat(event):
    if event.delta:
        steps = int(-event.delta / 120)
        if steps == 0:
            steps = -1 if event.delta > 0 else 1
        chat_canvas.yview_scroll(steps, "units")
    return "break"


def scroll_chat_linux(event):
    chat_canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
    return "break"


chat_canvas.bind("<MouseWheel>", scroll_chat)
chat_canvas.bind("<Button-4>", scroll_chat_linux)
chat_canvas.bind("<Button-5>", scroll_chat_linux)

messages = [("bot", "Hello! How can I assist you today?")]
message_font = tkfont.Font(family="Segoe UI", size=11)
label_font = tkfont.Font(family="Segoe UI", size=8, weight="bold")


def rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


def wrap_message(text, max_width):
    lines = []
    for paragraph in text.splitlines() or [""]:
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and message_font.measure(candidate) <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
            line = ""
            while message_font.measure(word) > max_width:
                chunk = ""
                for character in word:
                    if chunk and message_font.measure(chunk + character) > max_width:
                        lines.append(chunk)
                        chunk = ""
                    chunk += character
                line = chunk
                word = ""
            if word:
                line = word
        lines.append(line)
    return "\n".join(lines)


def render_messages():
    chat_canvas.delete("all")
    canvas_width = chat_canvas.winfo_width()
    if canvas_width <= 1:
        return

    y = 20
    margin = 18
    padding_x = 14
    padding_y = 10
    max_text_width = max(1, int((canvas_width - 2 * margin) * 0.76) - 2 * padding_x)

    for role, message in messages:
        wrapped = wrap_message(message, max_text_width)
        text = chat_canvas.create_text(
            0,
            0,
            text=wrapped,
            anchor="nw",
            font=message_font,
            fill=text_color,
        )
        text_bounds = chat_canvas.bbox(text)
        if text_bounds is None:
            continue

        sender = "STUDY MATE" if role == "bot" else "YOU"
        bubble_width = max(
            text_bounds[2] - text_bounds[0],
            label_font.measure(sender),
        ) + 2 * padding_x
        bubble_height = (
            text_bounds[3] - text_bounds[1]
            + label_font.metrics("linespace")
            + 3 * padding_y
            + 4
        )
        x1 = margin if role == "bot" else canvas_width - margin - bubble_width
        x2 = x1 + bubble_width
        y2 = y + bubble_height

        chat_canvas.coords(
            text,
            x1 + padding_x - text_bounds[0],
            y + 2 * padding_y + label_font.metrics("linespace") + 4 - text_bounds[1],
        )
        bubble = rounded_rectangle(
            chat_canvas,
            x1,
            y,
            x2,
            y2,
            radius=16,
            fill=bot_bubble if role == "bot" else user_bubble,
            outline="#e2e8f0" if role == "bot" else "",
        )
        chat_canvas.tag_lower(bubble)
        chat_canvas.create_text(
            x1 + padding_x,
            y + padding_y,
            text=sender,
            anchor="nw",
            font=label_font,
            fill=muted_color if role == "bot" else accent,
        )
        y = y2 + 12

    chat_canvas.configure(scrollregion=(0, 0, canvas_width, y))
    chat_canvas.yview_moveto(1)


chat_canvas.bind("<Configure>", lambda _: render_messages())

input_frame = tk.Frame(window, bg="#e2e8f0", padx=12, pady=10)
input_frame.pack(fill=tk.X)
input_box = tk.Entry(
    input_frame,
    width=50,
    font=("Segoe UI", 11),
    bg=input,
    fg=text_color,
    insertbackground=text_color,
    relief=tk.FLAT,
    highlightthickness=1,
    highlightbackground="#cbd5e1",
    highlightcolor=accent,
)
input_box.pack(padx=(0, 10), ipady=11, side=tk.LEFT, fill=tk.X, expand=True)

def send():
    question = input_box.get()
    if not question.strip():
        return
    input_box.delete(0, tk.END)
    messages.extend([("user", question), ("bot", "...")])
    render_messages()
    window.update()

    try:
        answer = chain.invoke({"text": question}).content
    except Exception as e:
        answer = f"Error: {e}"

    messages[-1] = ("bot", str(answer))
    render_messages()

def on_enter(event):
    send()
    return "break"

input_box.bind("<Return>", on_enter)
btn = tk.Button(
    input_frame,
    text="Send  ➤",
    command=send,
    bg=accent,
    fg="white",
    activebackground="#0b806d",
    activeforeground="white",
    font=("Segoe UI", 10, "bold"),
    relief=tk.FLAT,
    padx=18,
    pady=9,
    cursor="hand2",
)
btn.pack(side=tk.RIGHT)

window.mainloop()


    