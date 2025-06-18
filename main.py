# main.py
import tkinter as tk
from tkinter import ttk, messagebox
from learner import Learner
from database import LearnerDatabase
from fpdf import FPDF

# Initialize DB
db = LearnerDatabase()

# Functions
def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    for row in db.get_all_learners():
        tree.insert("", tk.END, values=row)

def add_learner():
    learner = Learner(entry_id.get(), entry_name.get(), entry_course.get())
    if db.add_learner(learner):
        messagebox.showinfo("Success", "Learner added successfully")
        refresh_table()
    else:
        messagebox.showerror("Error", "Learner ID already exists")

def update_learner():
    db.update_learner(entry_id.get(), entry_name.get(), entry_course.get())
    messagebox.showinfo("Updated", "Learner updated successfully")
    refresh_table()

def delete_learner():
    db.delete_learner(entry_id.get())
    messagebox.showinfo("Deleted", "Learner deleted")
    refresh_table()

def on_select(event):
    selected = tree.item(tree.selection()[0])['values']
    entry_id.delete(0, tk.END)
    entry_name.delete(0, tk.END)
    entry_course.delete(0, tk.END)

    entry_id.insert(0, selected[0])
    entry_name.insert(0, selected[1])
    entry_course.insert(0, selected[2])

def export_to_pdf():
    learners = db.get_all_learners()
    if not learners:
        messagebox.showinfo("No Data", "No learners to export.")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Learner Report", ln=True, align='C')

    for learner in learners:
        pdf.cell(200, 10, txt=f"ID: {learner[0]}, Name: {learner[1]}, Course: {learner[2]}", ln=True)

    pdf.output("learner_report.pdf")
    messagebox.showinfo("Success", "Exported to learner_report.pdf")

# GUI Setup
root = tk.Tk()
root.title("Learner Management System")
root.geometry("650x550")
root.configure(bg="#2e2e2e")  # Dark background

style = {
    "bg": "#2e2e2e",
    "fg": "#ffffff",
    "font": ("Arial", 11),
}

tk.Label(root, text="Learner ID", **style).pack()
entry_id = tk.Entry(root, bg="#444", fg="#fff")
entry_id.pack()

tk.Label(root, text="Name", **style).pack()
entry_name = tk.Entry(root, bg="#444", fg="#fff")
entry_name.pack()

tk.Label(root, text="Course", **style).pack()
entry_course = tk.Entry(root, bg="#444", fg="#fff")
entry_course.pack()

tk.Button(root, text="Add Learner", command=add_learner, bg="#555", fg="#fff").pack(pady=4)
tk.Button(root, text="Update Learner", command=update_learner, bg="#555", fg="#fff").pack(pady=4)
tk.Button(root, text="Delete Learner", command=delete_learner, bg="#555", fg="#fff").pack(pady=4)
tk.Button(root, text="Export to PDF", command=export_to_pdf, bg="#555", fg="#fff").pack(pady=4)

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview",
                background="#2e2e2e",
                foreground="white",
                rowheight=25,
                fieldbackground="#2e2e2e")
style.map('Treeview', background=[('selected', '#6c6c6c')])

tree = ttk.Treeview(root, columns=("ID", "Name", "Course"), show='headings')
tree.heading("ID", text="ID")
tree.heading("Name", text="Name")
tree.heading("Course", text="Course")
tree.pack(fill="both", expand=True, padx=10, pady=10)
tree.bind("<Double-1>", on_select)

refresh_table()
root.mainloop()
