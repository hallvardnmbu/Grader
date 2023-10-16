import os
import openai

openai.api_key = 'YOUR_OPENAI_API_KEY'


def get_input():
    task_description = input("Enter the task description: ")
    key_points = input("Enter the key points for grading (comma-separated): ").split(',')
    return task_description, key_points


def load_student_submissions(directory_path):
    student_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
    student_submissions = {}
    for file in student_files:
        with open(os.path.join(directory_path, file), 'r') as f:
            student_submissions[file] = f.read()
    return student_submissions


def grade_with_chatgpt(task_description, key_points, student_code):
    prompt = f"Evaluate the following student submission based on the task: '{task_description}' and key points: {', '.join(key_points)}.\n\n---\n\n{student_code}\n\n---\n\nFeedback: "

    response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=150)
    feedback = response.choices[0].text.strip()

    improvement_prompt = f"Suggest improvements for the following student submission based on the task: '{task_description}' and key points: {', '.join(key_points)}.\n\n---\n\n{student_code}\n\n---\n\nImprovements: "
    improvement_response = openai.Completion.create(engine="davinci", prompt=improvement_prompt,
                                                    max_tokens=150)
    improvement_points = improvement_response.choices[0].text.strip()

    return feedback, improvement_points



def main():
    task_description, key_points = get_input()
    directory_path = input("Enter the directory path containing student submissions: ")
    student_submissions = load_student_submissions(directory_path)

    for student_file, code in student_submissions.items():
        feedback, improvement_points = grade_with_chatgpt(task_description, key_points, code)
        print(f"\nFeedback for {student_file}:")
        print(feedback)
        print("\nImprovement Points:")
        print(improvement_points)
