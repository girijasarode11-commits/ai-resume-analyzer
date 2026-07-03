def generate_local_feedback(ats, similarity, matched, missing):
    feedback = ""

    # ATS analysis
    if ats >= 80:
        feedback += "Your resume is highly ATS-optimized and aligns well with the job requirements. "
    elif ats >= 50:
        feedback += "Your resume has moderate ATS compatibility but still has room for improvement. "
    else:
        feedback += "Your resume currently has low ATS compatibility for this role. "

    # Similarity analysis
    if similarity >= 75:
        feedback += "The resume content strongly matches the provided job description. "
    elif similarity >= 50:
        feedback += "The resume partially matches the job description. "
    else:
        feedback += "The resume lacks several important keywords from the job description. "

    # Matched skills
    if matched:
        top_skills = ", ".join(matched[:4])
        feedback += f"Your strongest matching skills include {top_skills}. "

    # Missing skills
    if missing:
        missing_skills = ", ".join(missing[:4])
        feedback += (
            f"However, important skills such as {missing_skills} are missing. "
            "Adding projects, certifications, or experience in these areas could improve your ranking significantly. "
        )

    feedback += "Focus on tailoring your resume to each job description for better hiring success."

    return feedback