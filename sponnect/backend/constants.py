"""
Constants used throughout the Sponnect application.
This file centralizes all constant values to ensure consistency.
"""

# Industry options for sponsors
INDUSTRIES = [
    'Technology',
    'Fashion',
    'Cosmetics',
    'Food & Beverage',
    'Travel',
    'Gaming',
    'Health & Fitness',
    'Automotive',
    'Finance',
    'Art',
    'Entertainment',
    'Education',
    'Home & Decor',
    'Sports',
    'Media',
    'Retail'
]

# Category options for campaigns
CATEGORIES = [
    'technology',
    'fashion',
    'beauty',
    'food',
    'travel',
    'gaming',
    'fitness',
    'automotive',
    'finance',
    'entertainment',
    'education',
    'lifestyle',
    'sports',
    'other'
]

# Category options for influencers
INFLUENCER_CATEGORIES = [
    'Fashion',
    'Beauty',
    'Fitness',
    'Travel',
    'Food',
    'Technology',
    'Gaming',
    'Lifestyle',
    'Business',
    'Education',
    'Entertainment',
    'Health',
    'Sports',
    'Parenting',
    'Other'
]

# Map industries to campaign categories
INDUSTRY_TO_CATEGORY = {
    'Technology': 'technology',
    'Fashion': 'fashion',
    'Cosmetics': 'beauty',
    'Food & Beverage': 'food',
    'Travel': 'travel',
    'Gaming': 'gaming',
    'Health & Fitness': 'fitness',
    'Automotive': 'automotive',
    'Finance': 'finance',
    'Art': 'entertainment',
    'Entertainment': 'entertainment',
    'Education': 'education',
    'Home & Decor': 'lifestyle',
    'Sports': 'sports',
    'Media': 'entertainment',
    'Retail': 'fashion'
}

# Default category if industry doesn't match
DEFAULT_CATEGORY = 'other'

def map_industry_to_category(industry):
    """Maps a sponsor's industry to a campaign category"""
    if not industry:
        return DEFAULT_CATEGORY
    return INDUSTRY_TO_CATEGORY.get(industry, DEFAULT_CATEGORY) 