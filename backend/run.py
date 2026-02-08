#!/usr/bin/env python3
"""
Application entry point for InnovateSphere backend.

Usage:
    python run.py              # Run development server
    python run.py --production  # Run production server (gunicorn)
"""
import sys
import argparse
from backend.core.app import create_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InnovateSphere Backend")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run with gunicorn (production)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    if args.production:
        try:
            import gunicorn.app.wsgiapp as wsgi
            sys.argv = [
                "gunicorn",
                "-w", "4",
                "-b", f"{args.host}:{args.port}",
                "backend.run:app"
            ]
            wsgi.run()
        except ImportError:
            print("Error: gunicorn not installed. Install with: pip install gunicorn")
            sys.exit(1)
    else:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
