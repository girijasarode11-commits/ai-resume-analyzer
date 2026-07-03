def calculate_ats(matched, total_job_skills):
    if total_job_skills == 0:
        return 0

    score = (len(matched) / total_job_skills) * 100
    return round(score, 2)