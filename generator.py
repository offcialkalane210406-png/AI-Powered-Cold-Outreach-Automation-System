import random

PERSONALIZED_SUBJECTS = [
    "Wanted to learn from your experience at {company}",
    "AI/ML student seeking career guidance",
    "Quick question about growing as a software engineer",
    "Learning from experienced professionals at {company}",
]

GENERIC_SUBJECTS = [
    "Seeking career guidance",
    "Wanted to connect with an experienced professional",
    "AI/ML student looking for advice",
]


def _first_name(full_name):
    return full_name.strip().split()[0] if full_name.strip() else "there"


def generate_email(profile_info):
    name = profile_info.get("name", "").strip()
    company = profile_info.get("company", "").strip()
    role = profile_info.get("role", "").strip()
    greeting = _first_name(name)

    if company and role:
        subject = random.choice(PERSONALIZED_SUBJECTS).format(company=company)
        body = f"""Hi {greeting},

I came across your profile while learning about professionals working at {company}. Your experience as {role} stood out to me.

I am a third-year Computer Engineering student from SPPU, currently focused on AI/ML, backend development, Generative AI, and practical software engineering. I am trying to understand which skills matter most for internships and early software engineering roles.

If you have a few minutes, I would be grateful for any advice on what to focus on, how to prepare for internships, or what students should understand before entering the industry.

Thank you for your time.

Best regards,
Jagdish"""
    else:
        subject = random.choice(GENERIC_SUBJECTS)
        body = f"""Hi {greeting},

I came across your profile while exploring professionals in software engineering and technology.

I am a third-year Computer Engineering student from SPPU with an interest in AI/ML, backend development, Generative AI, and modern software systems. I am currently improving my technical skills and learning how engineers grow in the industry.

If possible, I would appreciate any advice or suggestions that could help me prepare better for internship opportunities and early software engineering roles.

Thank you for your time.

Best regards,
Jagdish"""

    return {"subject": subject, "body": body}
