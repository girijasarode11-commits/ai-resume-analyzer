from ml.nlp import extract_skills, extract_entities

sample = """
I am a Python developer with Machine Learning and SQL experience.
Worked at Infosys in Pune.
"""

print("Skills:", extract_skills(sample))
print("Entities:", extract_entities(sample))

