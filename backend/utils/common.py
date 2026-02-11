"""
Common utility functions used across the backend.
"""


def map_domain_to_external_category(domain):
    """
    Map internal domain names to external API category keywords.
    Returns a list of relevant keywords for the domain that can be used
    in GitHub API searches.
    
    Args:
        domain: Internal domain name
        
    Returns:
        String of space-separated keywords or list of keyword strings
        for API queries. Can be extended with custom mappings.
    """
    # Domain-specific keyword mappings for better GitHub search results
    domain_keywords = {
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
