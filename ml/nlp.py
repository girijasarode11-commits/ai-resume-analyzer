import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_sm")

skills_db = [
    "python", "java", "sql", "machine learning", "deep learning",
    "docker", "aws", "flask", "django", "react", "javascript",
    "html", "css", "mongodb", "mysql", "c++"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(skill) for skill in skills_db]
matcher.add("SKILLS", patterns)


def extract_skills(text):
    doc = nlp(text.lower())
    matches = matcher(doc)

    found_skills = set()

    for match_id, start, end in matches:
        skill = doc[start:end].text
        found_skills.add(skill)

    return list(found_skills)


def extract_entities(text):
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append((ent.text, ent.label_))

    return entities

