import requests
import os
import sys
import argparse
from pathlib import Path


def get_checkers(base_url, api_key):
    url = f"{base_url}/api/checkers"
    headers = {"x-api-key": api_key}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def export_checker_csv(base_url, api_key, profile_id, checker_id, language=None):
    url = f"{base_url}/api/export/profiles/{profile_id}/checkers/{checker_id}"
    headers = {"x-api-key": api_key}
    params = {}
    if language:
        params["language"] = language
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.text


def main():
    parser = argparse.ArgumentParser(
        description="Export CSV for all checkers from Tenable Identity Exposure"
    )
    parser.add_argument("--base-url", required=True, help="Base URL, e.g. https://customer.tenable.ad")
    parser.add_argument("--api-key", default=os.environ.get("TENABLE_API_KEY"), help="API key (or set TENABLE_API_KEY env var)")
    parser.add_argument("--profile-id", required=True, help="Profile ID to export")
    parser.add_argument("--output-dir", default="exports", help="Directory to save CSV files (default: exports)")
    parser.add_argument("--language", default=None, help="Optional language parameter for export")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key required. Use --api-key or set TENABLE_API_KEY env var.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching available checkers...")
    checkers = get_checkers(args.base_url, args.api_key)

    if not checkers:
        print("No checkers found.")
        sys.exit(0)

    print(f"Found {len(checkers)} checkers.")

    for checker in checkers:
        checker_id = checker.get("id") or checker.get("codename") or checker.get("checkerId")
        checker_name = checker.get("name") or checker.get("codename") or str(checker_id)

        if not checker_id:
            print(f"  Skipping checker with no ID: {checker}")
            continue

        print(f"  Exporting checker: {checker_name} (ID: {checker_id})...")
        try:
            csv_data = export_checker_csv(
                args.base_url, args.api_key, args.profile_id, checker_id, args.language
            )
            safe_name = str(checker_name).replace("/", "_").replace(" ", "_")
            filename = output_dir / f"{safe_name}_{checker_id}.csv"
            filename.write_text(csv_data, encoding="utf-8")
            print(f"    Saved to {filename}")
        except requests.HTTPError as e:
            print(f"    Failed ({e.response.status_code}): {e}")
        except Exception as e:
            print(f"    Error: {e}")

    print(f"\nDone. Exports saved to {output_dir}/")


if __name__ == "__main__":
    main()
