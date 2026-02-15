"""
Common utility functions used across the backend.
"""


def map_domain_to_external_category(domain):
    """
    Map internal domain names to external API category keywords.
    Returns a list of relevant keywords for the domain that can be used
    in GitHub/Arxiv API searches.
    
    Args:
        domain: Internal domain name (matches the 10 primary domains)
        
    Returns:
        String of space-separated keywords for API queries.
    """
    # Domain-specific keyword mappings for better external API search results
    domain_keywords = {
        'AI & Machine Learning': ['ai', 'machine-learning', 'neural-network', 'nlp', 'deep-learning', 'llm'],
        'Web & Mobile Development': ['web', 'frontend', 'backend', 'react', 'mobile', 'pwa'],
        'Data Science & Analytics': ['data', 'analytics', 'data-science', 'visualization', 'pandas'],
        'Cybersecurity & Privacy': ['security', 'privacy', 'encryption', 'cybersecurity', 'oauth'],
        'Cloud & DevOps': ['cloud', 'devops', 'docker', 'kubernetes', 'aws', 'azure'],
        'Blockchain & Web3': ['blockchain', 'cryptocurrency', 'smart-contract', 'ethereum', 'defi'],
        'IoT & Hardware': ['iot', 'hardware', 'sensor', 'embedded', 'robotics', 'device'],
        'Healthcare & Biotech': ['healthcare', 'health', 'medical', 'biotech', 'genomics'],
        'Education & E-Learning': ['education', 'learning', 'elearning', 'course', 'training'],
        'Business & Productivity Tools': ['business', 'crm', 'saas', 'productivity', 'automation'],
        
        # Legacy mappings for backward compatibility
        'accessibility': ['accessibility', 'a11y'],
        'cognitive_accessibility': ['accessibility', 'cognitive'],
        'web_accessibility': ['accessibility'],
        'security': ['security'],
        'privacy': ['privacy'],
        'education': ['education', 'learning'],
        'healthcare': ['healthcare', 'health'],
        'ecommerce': ['ecommerce', 'shopping'],
        'ai': ['ai', 'machine-learning'],
        'web_development': ['web', 'development'],
        'mobile': ['mobile', 'app'],
        'devops': ['devops', 'deployment'],
        'data': ['data', 'analytics'],
    }
    
    # If domain has a custom mapping, return it
    if domain in domain_keywords:
        keywords = domain_keywords[domain]
        # Return as string to maintain backward compatibility
        return ' '.join(keywords)
    
    # Default: return domain as-is if no mapping exists
    return domain
