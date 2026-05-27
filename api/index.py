"""
Vercel serverless entry point for FerrePro API.
This file is the entry point that Vercel uses to serve the Flask app.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.server import app

# Vercel expects a variable named 'app' that is a WSGI application
# The Flask application is already named 'app' in server.py