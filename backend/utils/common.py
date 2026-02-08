"""
Common utility functions used across the backend.
"""


def map_domain_to_external_category(domain):
    """
    Map internal domain names to external API category names.
    Currently returns domain as-is, but can be extended for custom mappings.
    
    Args:
        domain: Internal domain name
        
    Returns:
        External category name for API queries
    """
    return domain
