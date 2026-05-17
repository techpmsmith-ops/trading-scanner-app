import argparse
import sys

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test a deployed private trading scanner stack")
    parser.add_argument("--backend-url", required=True, help="Backend base URL, for example https://api.example.com")
    parser.add_argument("--frontend-url", required=True, help="Frontend base URL, for example https://scanner.example.com")
    parser.add_argument("--email", required=True, help="Admin login email")
    parser.add_argument("--password", required=True, help="Admin login password")
    args = parser.parse_args()

    backend = args.backend_url.rstrip("/")
    frontend = args.frontend_url.rstrip("/")

    checks = [
        ("backend health", lambda: expect_ok(requests.get(f"{backend}/health", timeout=15))),
        ("protected route rejects anonymous", lambda: expect_status(requests.get(f"{backend}/scan/latest", timeout=15), 401)),
        ("auth login", lambda: login(backend, args.email, args.password)),
        ("frontend returns 200", lambda: expect_ok(requests.get(frontend, timeout=20, allow_redirects=True))),
    ]

    token = ""
    for name, check in checks:
        try:
            result = check()
            if name == "auth login":
                token = result
            print(f"PASS: {name}")
        except Exception as exc:
            print(f"FAIL: {name}: {exc}")
            return 1

    try:
        response = requests.get(f"{backend}/scan/latest", headers={"Authorization": f"Bearer {token}"}, timeout=20)
        if response.status_code == 404:
            print("PASS: authenticated scan latest reachable; no scan results yet")
        else:
            expect_ok(response)
            print("PASS: authenticated scan latest reachable")
    except Exception as exc:
        print(f"FAIL: authenticated scan latest: {exc}")
        return 1

    return 0


def expect_ok(response: requests.Response) -> requests.Response:
    if not 200 <= response.status_code < 300:
        raise RuntimeError(f"expected 2xx, got {response.status_code}: {response.text[:300]}")
    return response


def expect_status(response: requests.Response, status_code: int) -> requests.Response:
    if response.status_code != status_code:
        raise RuntimeError(f"expected {status_code}, got {response.status_code}: {response.text[:300]}")
    return response


def login(backend: str, email: str, password: str) -> str:
    response = requests.post(f"{backend}/auth/login", json={"email": email, "password": password}, timeout=20)
    expect_ok(response)
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("login response did not include access_token")
    return token


if __name__ == "__main__":
    sys.exit(main())
