"""Controlled regression switch used ONLY for the faculty CI demonstration.

Change SEARCH_BUG_ENABLED from False to True, commit and push, then watch
GitHub Actions detect the broken search functionality. Restore False afterward.
"""
SEARCH_BUG_ENABLED = False
