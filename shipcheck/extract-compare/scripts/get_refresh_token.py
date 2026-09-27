#!/usr/bin/env python3
"""
One-time script to generate a permanent Google OAuth 2.0 Refresh Token.
Usage:
    python scripts/get_refresh_token.py
"""
import os
import sys
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import httpx
from dotenv import load_dotenv

# Load root .env
load_dotenv()

CLIENT_ID = (
    os.environ.get("GMAIL_CLIENT_ID")
    or os.environ.get("GOOGLE_CLIENT_ID")
    or os.environ.get("VITE_GOOGLE_CLIENT_ID")
)
CLIENT_SECRET = (
    os.environ.get("GMAIL_CLIENT_SECRET")
    or os.environ.get("GOOGLE_CLIENT_SECRET")
    or os.environ.get("VITE_GOOGLE_CLIENT_SECRET")
)

if not CLIENT_ID or not CLIENT_SECRET:
    print("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in backend/.env")
    print("(rotate the client secret in Google Cloud Console first if it was ever committed to source control)")
    sys.exit(1)

PORT = 8088
REDIRECT_URI = f"http://localhost:{PORT}/callback"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email"

captured_code = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global captured_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            captured_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
            <html>
                <body style="font-family:sans-serif; text-align:center; padding:50px;">
                    <h2 style="color:#166534;">&#10003; Authorization Code Received!</h2>
                    <p>You can close this browser tab and check your terminal.</p>
                </body>
            </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received.")

    def log_message(self, format, *args):
        pass  # Quiet HTTP logs


def main():
    global captured_code
    print("=" * 65)
    print("ShipCheck — Google OAuth 2.0 Refresh Token Generator")
    print("=" * 65)
    print(f"Client ID: {CLIENT_ID[:20]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    print()

    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"

    print("Opening browser for authorization...")
    print(url)
    print()
    webbrowser.open(url)

    server = HTTPServer(("localhost", PORT), OAuthCallbackHandler)
    print(f"Waiting for authorization callback on port {PORT}...")
    while not captured_code:
        server.handle_request()

    print("Exchanging code for Refresh Token...")
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": captured_code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
        )
        if not resp.is_success:
            print(f"Error during token exchange ({resp.status_code}): {resp.text}")
            sys.exit(1)

        data = resp.json()
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            print("Warning: Google did not return a refresh_token.")
            print("Response:", data)
            sys.exit(1)

        print()
        print("=" * 65)
        print("SUCCESS! Your GMAIL_REFRESH_TOKEN is:")
        print("=" * 65)
        print(refresh_token)
        print("=" * 65)
        print()
        print("Add this to your email-extract-compare/.env and Cloud Run env vars:")
        print(f"GMAIL_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
