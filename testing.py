import os
import openai
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext


openai.api_key = open("./__secrets/openai", "r").read()


class GradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grading Automation App")

        # Variables
        self.task_description = tk.StringVar()
        self.key_points = []
        self.student_submissions = {}
        self.current_submission_index = 0

        # Start with the first page
        self.show_task_input_page()

    def show_task_input_page(self):
        # Create widgets for task description and key points input
        label1 = tk.Label(self.root, text="Enter the task description:")
        label1.pack(pady=10)

        self.task_entry = tk.Entry(self.root, textvariable=self.task_description, width=50)
        self.task_entry.pack(pady=10)

        label2 = tk.Label(self.root, text="Enter key points (comma-separated):")
        label2.pack(pady=10)

        self.key_points_entry = tk.Entry(self.root, width=50)
        self.key_points_entry.pack(pady=10)

        next_button = tk.Button(self.root, text="Next", command=self.load_submissions_page)
        next_button.pack(pady=20)

    def load_submissions_page(self):
        # Get values from input page
        self.task_description = self.task_entry.get()
        self.key_points = self.key_points_entry.get().split(',')

        # Clear the current page
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create submission upload widgets
        label = tk.Label(self.root, text="Upload Student Submissions:")
        label.pack(pady=10)

        upload_button = tk.Button(self.root, text="Upload Files", command=self.upload_files)
        upload_button.pack(pady=10)

    def upload_files(self):
        # Get files using file dialog
        file_paths = filedialog.askopenfilenames(title="Select Student Submissions",
                                                 filetypes=[("Text Files", "*.txt")])
        for path in file_paths:
            with open(path, 'r') as f:
                file_name = os.path.basename(path)
                self.student_submissions[file_name] = f.read()

        # Proceed to the graded submissions display page
        self.show_graded_submissions_page()

    def show_graded_submissions_page(self):
        # Clear the current page
        for widget in self.root.winfo_children():
            widget.destroy()

        # Check if there are submissions
        if not self.student_submissions:
            messagebox.showinfo("Info", "No submissions to grade.")
            return

        # Get the current submission
        submission_name = list(self.student_submissions.keys())[self.current_submission_index]
        submission_code = self.student_submissions[submission_name]

        # Grade the current submission
        feedback, improvement_points = self.grade_gpt(self.task_description,
                                                      self.key_points,
                                                      submission_code)

        # Create widgets to display the graded submission
        label = tk.Label(self.root, text=f"Grading: {submission_name}")
        label.pack(pady=10)

        original_code_text = scrolledtext.ScrolledText(self.root, width=50, height=20)
        original_code_text.insert(tk.END, submission_code)
        original_code_text.pack(pady=10, padx=10, side=tk.LEFT)

        feedback_text = scrolledtext.ScrolledText(self.root, width=50, height=20)
        feedback_text.insert(tk.END, feedback + "\n\n" + improvement_points)
        feedback_text.pack(pady=10, padx=10, side=tk.RIGHT)

        next_button = tk.Button(self.root, text="Next Submission", command=self.next_submission)
        next_button.pack(pady=20)

    def next_submission(self):
        self.current_submission_index += 1
        if self.current_submission_index < len(self.student_submissions):
            self.show_graded_submissions_page()
        else:
            messagebox.showinfo("Info", "All submissions graded.")
            self.root.quit()

    @staticmethod
    def grade_gpt(task_description, key_points, student_code):
        prompt = f"Evaluate the following student submission based on the task: '{task_description}' and key points: {', '.join(key_points)}.\n\n---\n\n{student_code}\n\n---\n\nFeedback: "

        response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=150)
        feedback = response.choices[0].text.strip()

        improvement_prompt = f"Suggest improvements for the following student submission based on the task: '{task_description}' and key points: {', '.join(key_points)}.\n\n---\n\n{student_code}\n\n---\n\nImprovements: "
        improvement_response = openai.Completion.create(engine="davinci", prompt=improvement_prompt,
                                                        max_tokens=150)
        improvement_points = improvement_response.choices[0].text.strip()

        return feedback, improvement_points


if __name__ == "__main__":
    root = tk.Tk()
    app = GradingApp(root)
    root.mainloop()
