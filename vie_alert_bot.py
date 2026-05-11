import argparse
import json
import os
import smtplib
import ssl
from datetime import date, datetime
from email.message import EmailMessage
from urllib.parse import parse_qs, urljoin, urlparse
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

DEFAULT_URL = "https://mon-vie-via.businessfrance.fr/offres/recherche?query=data&missionsTypesIds=VIE&geographicZones=2&countriesIds=CA&countriesIds=US&teletravail=0&porteEnv=0"
DEFAULT_STATE_PATH = os.path.join("data", "state.json")
DEFAULT_SITE_URL = "https://mon-vie-via.businessfrance.fr"
DEFAULT_OFFERS_API_ENDPOINT = "https://civiweb-api-prd.azurewebsites.net/api/Offers/search"


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def extract_offers(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    offers = {}
    for link in soup.select("a[href]"):
        href = link.get("href", "").strip()
        if not href:
            continue
        if "/offres/" not in href:
            continue
        if "offres/recherche" in href:
            continue
        full_url = urljoin(base_url, href)
        title = " ".join(link.get_text(" ", strip=True).split())
        if not title:
            title = "Offre V.I.E"
        offer_id = full_url.rsplit("/", 1)[-1]
        offers[full_url] = {
            "id": str(offer_id),
            "title": title,
            "url": full_url,
        }
    return list(offers.values())


def parse_search_url(url: str) -> dict:
    query_params = parse_qs(urlparse(url).query)

    def list_param(name: str) -> Optional[list[str]]:
        values = query_params.get(name, [])
        return values or None

    payload = {
        "query": (query_params.get("query") or [None])[0],
        "missionsTypesIds": list_param("missionsTypesIds"),
        "missionsDurations": list_param("missionsDurations"),
        "geographicZones": list_param("geographicZones"),
        "countriesIds": list_param("countriesIds"),
        "citiesName": list_param("citiesName"),
        "studiesLevelId": list_param("studiesLevelId"),
        "companiesSizes": list_param("companiesSizes"),
        "specializationsIds": list_param("specializationsIds"),
        "missionStartDate": (query_params.get("missionStartDate") or [None])[0],
        "teletravail": list_param("teletravail"),
        "porteEnv": list_param("porteEnv"),
    }

    return {key: value for key, value in payload.items() if value is not None}


def fetch_offers_from_api(url: str) -> list[dict]:
    endpoint = os.getenv("OFFERS_API_ENDPOINT", DEFAULT_OFFERS_API_ENDPOINT)
    payload = parse_search_url(url)
    limit = 100
    skip = 0
    offers = []

    while True:
        body = dict(payload)
        body.update({"skip": skip, "limit": limit})
        response = requests.post(endpoint, json=body, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("result", [])
        count = data.get("count", len(items))
        offers.extend(items)

        if skip + limit >= count or not items:
            break
        skip += limit

    normalized = []
    for item in offers:
        offer_id = str(item.get("id"))
        title = item.get("missionTitle") or "Offre V.I.E"
        organization = item.get("organizationName")
        if organization:
            title = f"{title} — {organization}"
        normalized.append(
            {
                "id": offer_id,
                "title": title,
                "url": f"{DEFAULT_SITE_URL}/offres/{offer_id}",
            }
        )

    return normalized


def load_state(state_path: str) -> dict:
    if not os.path.exists(state_path):
        return {"offers": {}, "last_checked": None, "last_daily_sent": None}
    with open(state_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "offers" in data and isinstance(data["offers"], dict):
        return {
            "offers": data["offers"],
            "last_checked": data.get("last_checked"),
            "last_daily_sent": data.get("last_daily_sent"),
        }
    seen_ids = data.get("seen_ids", [])
    offers = {str(offer_id): {"id": str(offer_id), "title": "", "url": ""} for offer_id in seen_ids}
    return {
        "offers": offers,
        "last_checked": data.get("last_checked"),
        "last_daily_sent": data.get("last_daily_sent"),
    }


def save_state(state_path: str, offers: dict, checked_at: str, last_daily_sent: Optional[str]) -> None:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(
            {"offers": offers, "last_checked": checked_at, "last_daily_sent": last_daily_sent},
            handle,
            ensure_ascii=False,
            indent=2,
        )


def build_alert_email_body(added_offers: list[dict]) -> str:
    lines = ["Nouvelles offres V.I.E :", ""]
    for offer in added_offers:
        lines.append(f"- {offer['title']}")
        lines.append(f"  {offer['url']}")
    lines.append("")
    lines.append(f"Vérifié le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


def build_daily_email_body(added_offers: list[dict], current_offers: list[dict]) -> str:
    lines = ["Récapitulatif des offres V.I.E", ""]
    if added_offers:
        lines.append("Nouvelles offres depuis le dernier récap :")
        lines.append("")
        for offer in added_offers:
            lines.append(f"- {offer['title']}")
            lines.append(f"  {offer['url']}")
        lines.append("")

    lines.append("Toutes les offres actuelles :")
    lines.append("")
    for offer in current_offers:
        lines.append(f"- {offer['title']}")
        lines.append(f"  {offer['url']}")
    lines.append("")
    lines.append(f"Vérifié le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


def send_email(subject: str, body: str, to_email: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "")
    use_starttls = os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes"}
    smtp_debug = os.getenv("SMTP_DEBUG", "false").lower() in {"1", "true", "yes"}

    if not smtp_host or not smtp_user or not smtp_pass or not smtp_from:
        raise RuntimeError("SMTP configuration is incomplete. Check SMTP_HOST/SMTP_USER/SMTP_PASS/SMTP_FROM.")

    message = EmailMessage()
    message["From"] = smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        if smtp_debug:
            server.set_debuglevel(1)
        if use_starttls:
            server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(message)


def run_check(url: str, state_path: str, to_email: str, dry_run: bool, force_send: bool, daily: bool) -> int:
    try:
        offers = fetch_offers_from_api(url)
    except Exception:
        html = fetch_html(url)
        offers = extract_offers(html, base_url=url)

    state = load_state(state_path)
    previous_offers = state.get("offers", {})
    current_offers = {offer["id"]: offer for offer in offers}

    previous_ids = set(previous_offers.keys())
    current_ids = set(current_offers.keys())

    added_ids = sorted(current_ids - previous_ids)
    added_offers = [current_offers[offer_id] for offer_id in added_ids]
    checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_daily_sent = state.get("last_daily_sent")
    today = date.today().isoformat()

    if daily:
        if last_daily_sent == today and not force_send:
            save_state(state_path, current_offers, checked_at, last_daily_sent)
            return 0

        subject = f"Récap V.I.E {today}"
        body = build_daily_email_body(added_offers, list(current_offers.values()))
        last_daily_sent = today
    else:
        if not added_offers and not force_send:
            save_state(state_path, current_offers, checked_at, last_daily_sent)
            return 0

        subject = f"{len(added_offers)} nouvelle(s) offre(s) V.I.E"
        body = build_alert_email_body(added_offers)

    save_state(state_path, current_offers, checked_at, last_daily_sent)

    if dry_run:
        print(body)
    else:
        send_email(subject, body, to_email)

    return len(added_offers)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alerte email pour nouvelles offres V.I.E sur Civiweb")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--state", default=DEFAULT_STATE_PATH)
    parser.add_argument("--to", default=os.getenv("SMTP_TO", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-send", action="store_true")
    parser.add_argument("--daily", action="store_true")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    if not args.to:
        raise RuntimeError("Aucune adresse destinataire. Renseigne SMTP_TO ou --to.")
    return run_check(args.url, args.state, args.to, args.dry_run, args.force_send, args.daily)


if __name__ == "__main__":
    raise SystemExit(main())
