import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def validate_assignment(notes_text, student_text):

    prompt = f"""
    Compare the student assignment with the teacher notes.

    Give:
    Score out of 10
    Short feedback

    TEACHER NOTES:
    {notes_text[:1500]}

    STUDENT ASSIGNMENT:
    {student_text[:1500]}
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()

    return result["response"]