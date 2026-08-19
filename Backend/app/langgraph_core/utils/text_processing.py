def preprocess_user_input(user_input: str) -> str:
    """Correct common misspellings and typos in the user's input.

    This simple utility performs word-level replacements based on a small
    dictionary of frequent mistakes. Extend the mapping as you notice new
    patterns in real usage.
    """
    corrections = {
        "comman": "common",
        "prject": "project",
        "resme": "resume",
    }

    words = user_input.split()
    corrected_words = [corrections.get(word.lower(), word) for word in words]
    return " ".join(corrected_words)


