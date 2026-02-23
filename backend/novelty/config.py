TECH_TERMS = {
    "react", "flask", "django", "api", "web", "app",
    "backend", "frontend", "system", "platform",
    "database", "server", "client", "framework"
}

GENERIC_IDEAS = [
    "todo", "crud", "management system", "dashboard",
    "expense tracker", "chat app", "blog", "portfolio"
]

COMMODITY_PATTERNS = GENERIC_IDEAS + [
    "ecommerce", "inventory system", "cms",
    "landing page", "admin panel", "authentication"
]

# Per-domain similarity thresholds for novelty comparison.
# Used by compute_similarity_distribution() to calibrate domain-specific
# thresholds for counting "high-similarity" sources.
SIMILARITY_THRESHOLDS = {
    "AI & Machine Learning": 0.45,
    "Web & Mobile Development": 0.35,
    "Data Science & Analytics": 0.42,
    "Cybersecurity & Privacy": 0.50,
    "Cloud & DevOps": 0.48,
    "Blockchain & Web3": 0.52,
    "IoT & Hardware": 0.40,
    "Healthcare & Biotech": 0.55,
    "Education & E-Learning": 0.45,
    "Business & Productivity Tools": 0.50,
}

DOMAIN_NOVELTY_WEIGHT = {
    "AI & Machine Learning": 1.2,
    "Web & Mobile Development": 0.95,
    "Data Science & Analytics": 1.1,
    "Cybersecurity & Privacy": 1.15,
    "Cloud & DevOps": 1.05,
    "Blockchain & Web3": 1.25,
    "IoT & Hardware": 1.1,
    "Healthcare & Biotech": 1.3,
    "Education & E-Learning": 1.05,
    "Business & Productivity Tools": 0.9,
}

DOMAIN_MATURITY = {
    "AI & Machine Learning": "emerging",
    "Web & Mobile Development": "mature",
    "Data Science & Analytics": "mature",
    "Cybersecurity & Privacy": "mature",
    "Cloud & DevOps": "mature",
    "Blockchain & Web3": "emerging",
    "IoT & Hardware": "growing",
    "Healthcare & Biotech": "growing",
    "Education & E-Learning": "growing",
    "Business & Productivity Tools": "mature",
}
