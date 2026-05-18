"""Script to fetch projects from ServiceNow API.

Usage:
    python scripts/fetch_servicenow_projects.py

This script:
1. Authenticates with ServiceNow using OAuth2 client credentials
2. Fetches projects from the sn_sales_common_u_project table
3. Prints the response JSON
"""

import json
import sys

import httpx

# ============================================================
# ServiceNow Configuration
# ============================================================

SN_BASE_URL = "https://myhelpdev.zeb.co"
SN_TOKEN_ENDPOINT = f"{SN_BASE_URL}/oauth_token.do"
SN_PROJECTS_ENDPOINT = f"{SN_BASE_URL}/api/now/table/sn_sales_common_u_project"

# OAuth2 Client Credentials
CLIENT_ID = "4959b6d6c00448fc92601897d4e78257"
CLIENT_SECRET = "H]<~,?mE-m0^~DC&zsEmXP3Ft5GYHL(@"

# Number of records to fetch
RECORD_LIMIT = 5


def get_access_token() -> str:
    """Authenticate with ServiceNow and get an access token."""
    print("=" * 60)
    print("Step 1: Getting OAuth2 Access Token...")
    print("=" * 60)

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = httpx.post(SN_TOKEN_ENDPOINT, data=data, timeout=30)

    print(f"Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: Token request failed!")
        print(f"Response: {response.text}")
        sys.exit(1)

    token_data = response.json()
    print(f"Token Type: {token_data.get('token_type')}")
    print(f"Expires In: {token_data.get('expires_in')} seconds")
    print(f"Access Token: {token_data.get('access_token', '')[:20]}...")
    print()

    return token_data["access_token"]


def fetch_projects(access_token: str) -> dict:
    """Fetch projects from ServiceNow Table API."""
    print("=" * 60)
    print(f"Step 2: Fetching Projects (limit={RECORD_LIMIT})...")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {
        "sysparm_limit": str(RECORD_LIMIT),
    }

    response = httpx.get(
        SN_PROJECTS_ENDPOINT,
        headers=headers,
        params=params,
        timeout=30,
    )

    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print()

    if response.status_code != 200:
        print(f"ERROR: Projects request failed!")
        print(f"Response: {response.text[:500]}")
        sys.exit(1)

    return response.json()


def main():
    """Main entry point."""
    print()
    print("ServiceNow Projects Fetcher")
    print("=" * 60)
    print()

    # Step 1: Get token
    access_token = get_access_token()

    # Step 2: Fetch projects
    result = fetch_projects(access_token)

    # Step 3: Display results
    print("=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    print(json.dumps(result, indent=2, default=str))
    print()

    # Summary
    records = result.get("result", [])
    print("=" * 60)
    print(f"Total Records Returned: {len(records)}")
    print("=" * 60)

    if records:
        print()
        print("Field Names in First Record:")
        print("-" * 40)
        for key in sorted(records[0].keys()):
            value = records[0][key]
            # Truncate long values
            display_value = str(value)[:80] if value else "(empty)"
            print(f"  {key}: {display_value}")


if __name__ == "__main__":
    main()
