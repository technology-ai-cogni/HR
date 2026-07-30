from llm_integration import extract_structured_data

def test():
    resume_text = "Experienced Data Scientist with 5 years of experience in Python, Machine Learning, and SQL. Education: Master in Computer Science."
    jd_text = "Seeking a Data Scientist with 3 years of experience. Required skills: Python, Machine Learning."
    
    print("Testing resume extraction...")
    resume_res = extract_structured_data(resume_text, "resume")
    print("Resume Result:", resume_res)
    
    print("\nTesting JD extraction...")
    jd_res = extract_structured_data(jd_text, "jd")
    print("JD Result:", jd_res)

if __name__ == "__main__":
    test()
