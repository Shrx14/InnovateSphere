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
    "web development": 0.35,     # Lower: diverse web ideas
    "ai tools": 0.45,            # Medium: AI is more focused  
    "blockchain": 0.48,          # Medium-high: specific domain
    "research": 0.52,            # Higher: research is specialized
    "data science": 0.45,        # Medium: diverse data applications
    "cybersecurity": 0.50,       # Medium-high: domain specific
    "iot": 0.40,                 # Lower: diverse IoT applications
    "business": 0.50,            # Medium: business ideas have patterns
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
