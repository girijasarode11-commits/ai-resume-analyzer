import spacy
nlp = spacy.load("en_core_web_sm")

skills_db = [
    "python",
    "sql",
    "machine learning",
    "deep learning",
    "aws",
    "docker",
    "flask",
    "django",
    "react",
    "java",
    "c++",
    "html",
    "css",
    "javascript",
    "mongodb",
    "mysql"
]


def extract_skills(text):
    doc = nlp(text.lower())
    found = set()

    for token in doc:
        for skill in skills_db:
            if token.text == skill:
                found.add(skill)

    # handle multi-word skills
    lowered = text.lower()
    for skill in skills_db:
        if skill in lowered:
            found.add(skill)

    return list(found)


def match_skills(resume_text, job_desc):
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_desc))

    matched = list(resume_skills.intersection(job_skills))
    missing = list(job_skills - resume_skills)

    return matched, missing