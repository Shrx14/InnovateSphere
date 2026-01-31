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

SIMILARITY_THRESHOLDS = {
    "web development": 0.30,
    "ai tools": 0.45,
    "blockchain": 0.50,
    "research": 0.55,
}

DOMAIN_NOVELTY_WEIGHT = {
    "web development": 1.0,
    "ai tools": 1.15,
    "blockchain": 1.1,
    "research": 1.2,
}

DOMAIN_MATURITY = {
    "web development": "mature",
    "ai tools": "emerging",
    "blockchain": "emerging",
    "quantum computing": "nascent",
}
