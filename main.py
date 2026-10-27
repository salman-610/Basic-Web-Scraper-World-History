
import re
from datetime import datetime
from collections import Counter, defaultdict
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup


START_YEAR = 1865
END_YEAR = 1890
PREVIEW_ONLY = True

BASE_URL = "https://en.wikipedia.org/wiki/"

HEADERS = {
    "User-Agent": "WorldHistoryWebScraper/1.0 (educational project)"
}

MIN_TITLE_LENGTH = 25
SIMILARITY_THRESHOLD = 0.92


MONTHS = (
    r"January|February|March|April|May|June|July|August|"
    r"September|October|November|December"
)

DATE_PATTERN = re.compile(
    rf"\b({MONTHS})\s+(\d{{1,2}})(?:,\s*(\d{{4}}))?\b",
    re.IGNORECASE,
)

LEADING_DATE_PATTERN = re.compile(
    rf"^\s*({MONTHS})\s+(\d{{1,2}})"
    rf"(?:,\s*(\d{{4}}))?\s*[–—-]\s*",
    re.IGNORECASE,
)

DATE_CONTEXT_PATTERN = re.compile(
    rf"\b(?:occurred on|happened on|took place on|"
    rf"made landfall on|struck on|hit on|"
    rf"was signed on|was held on|began on|"
    rf"started on|was launched on|"
    rf"was conducted on|was carried out on|"
    rf"was announced on|was released on|"
    rf"was destroyed on|was attacked on|"
    rf"was killed on|was born on|was declared on|"
    rf"was captured on|was elected on|"
    rf"on)\s+"
    rf"({MONTHS})\s+(\d{{1,2}})(?:,\s*(\d{{4}}))?\b",
    re.IGNORECASE,
)

LATER_EVENT_PATTERN = re.compile(
    r"\b(?:months later|weeks later|days later|"
    r"the following day|the next day|"
    r"later that year|later that month|"
    r"subsequently|in a later development)\b",
    re.IGNORECASE,
)


CATEGORIES = {
    "War": [
        r"\bwar\b",
        r"\barmed conflict\b",
        r"\bairstrike\b",
        r"\bair strike\b",
        r"\bmissile attack\b",
        r"\bdrone strike\b",
        r"\bceasefire\b",
        r"\binvasion\b",
        r"\bmilitary offensive\b",
        r"\bmilitary forces\b",
        r"\bclashes\b",
        r"\bfighting\b",
        r"\bcombat\b",
        r"\bbombing\b",
        r"\bmilitary operation\b",
        r"\bwar crime\b",
        r"\bcivil war\b",
        r"\bwithdraw(?:s|al|ing)? troops\b",
    ],
    "Terrorism / Attack": [
        r"\bterrorist attack\b",
        r"\bsuicide bombing\b",
        r"\bmass shooting\b",
        r"\bshooting attack\b",
        r"\bterrorist shooting spree\b",
        r"\bterrorist\b",
        r"\battack on\b",
        r"\battacks on\b",
        r"\bhostage\b",
        r"\bcapitol attack\b",
        r"\bgunmen storm\b",
        r"\bshooting spree\b",
        r"\bsuicide bomber\b",
        r"\bgunmen\b",
        r"\bmilitants attack\b",
    ],
    "Natural Disaster": [
        r"\bearthquake\b",
        r"\btsunami\b",
        r"\bhurricane\b",
        r"\btyphoon\b",
        r"\bcyclone\b",
        r"\btornado\b",
        r"\bflood\b",
        r"\bflooding\b",
        r"\bwildfire\b",
        r"\bforest fire\b",
        r"\blandslide\b",
        r"\bvolcanic eruption\b",
        r"\beruption\b",
        r"\bdrought\b",
        r"\bheatwave\b",
        r"\bheat wave\b",
        r"\bblizzard\b",
        r"\bstorm\b",
        r"\bavalanche\b",
        r"\bnatural disaster\b",
        r"\bflash floods?\b",
    ],
    "Human-Caused Disaster": [
        r"\bindustrial accident\b",
        r"\bnuclear accident\b",
        r"\bchemical leak\b",
        r"\bgas leak\b",
        r"\bexplosion\b",
        r"\bbuilding collapse\b",
        r"\bbridge collapse\b",
        r"\bshipwreck\b",
        r"\btrain derailment\b",
        r"\bplane crash\b",
        r"\baircraft crash\b",
        r"\baviation accident\b",
        r"\bstructural collapse\b",
        r"\bdeadly accident\b",
        r"\bindustrial disaster\b",
        r"\baccidental detonation\b",
    ],
}


IRRELEVANT_PATTERNS = [
    r"\btrade war\b",
    r"\bwar on poverty\b",
    r"\bwar on drugs\b",
    r"\bwar of words\b",
    r"\bpolitical battle\b",
    r"\blandslide victory\b",
    r"\bwins?\s+a\s+landslide\b",
    r"\blandslide\s+(?:victory|win|second\s+term)\b",
    r"\bstock market\b",
    r"\bcombat climate change\b",
    r"\boil price war\b",
    r"\bprice war\b",
    r"\btrade dispute\b",
    r"\bpolitical dispute\b",
]


def clean_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\[\d+\]", "", text)
    return text


def normalize_text(text):
    return clean_text(text).casefold()


def normalize_event_title(title):
    """Normalize titles for duplicate comparison."""
    title = normalize_text(title)
    title = re.sub(
        r"^[a-z]+\s+\d{1,2}(?:,\s*\d{4})?\s*[–—-]\s*",
        "",
        title,
    )
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def get_heading_text(heading):
    text = heading.get_text(" ", strip=True)
    text = re.sub(r"\[edit\]", "", text, flags=re.IGNORECASE)
    return normalize_text(text)


def parse_date_match(match, year):
    """Convert a matched date into YYYY-MM-DD and validate it."""
    month, day, explicit_year = match.groups()
    date_year = int(explicit_year) if explicit_year else year

    if date_year != year:
        return None

    try:
        parsed_date = datetime.strptime(
            f"{month} {day} {date_year}",
            "%B %d %Y",
        ).date()

        return parsed_date.isoformat()

    except ValueError:
        return None


def get_date_from_title(title, year):
    """
    Date priority:
    1. Explicit date at the beginning of an entry.
    2. One unambiguous date linked to the main event.
    3. Otherwise, return None.
    """
    leading_match = LEADING_DATE_PATTERN.match(title)

    if leading_match:
        date_match = DATE_PATTERN.search(leading_match.group(0))

        if date_match:
            return parse_date_match(date_match, year)

    sentences = re.split(
        r"(?<=[.!?])\s+",
        title.strip(),
        maxsplit=1,
    )

    first_sentence = sentences[0] if sentences else title.strip()

    if LATER_EVENT_PATTERN.search(first_sentence):
        return None

    matches = list(DATE_CONTEXT_PATTERN.finditer(first_sentence))
    valid_dates = set()

    for match in matches:
        parsed_date = parse_date_match(match, year)

        if parsed_date:
            valid_dates.add(parsed_date)

    if len(valid_dates) == 1:
        return next(iter(valid_dates))

    return None


def get_events_section(soup):
    for heading in soup.find_all(["h2", "h3"]):
        if get_heading_text(heading) == "events":
            return heading

    return None


def get_event_lists(events_heading):
    event_lists = []

    for element in events_heading.find_all_next():
        if element.name == "h2":
            break

        if element.name == "ul" and element.find_parent("ul") is None:
            event_lists.append(element)

    return event_lists


def get_item_text(list_item):
    """Extract an item's text without nested events or references."""
    item_copy = BeautifulSoup(str(list_item), "html.parser")

    selectors = [
        "figure",
        ".thumb",
        ".thumbcaption",
        ".gallery",
        ".gallerybox",
        ".gallerytext",
        ".mw-file-element",
        "sup.reference",
        ".reference",
        ".mw-editsection",
    ]

    for selector in selectors:
        for element in item_copy.select(selector):
            element.decompose()

    for element in item_copy.find_all(["ul", "ol"]):
        element.decompose()

    return clean_text(item_copy.get_text(" ", strip=True))


def is_irrelevant(title):
    return any(
        re.search(pattern, title, re.IGNORECASE)
        for pattern in IRRELEVANT_PATTERNS
    )


def is_political_landslide(title):
    return bool(
        re.search(r"\blandslide\b", title, re.IGNORECASE)
        and re.search(
            r"\b(election|electoral|vote|votes|victory|"
            r"president|prime minister|parliament|second term)\b",
            title,
            re.IGNORECASE,
        )
    )


def classify_event(title):
    if is_irrelevant(title) or is_political_landslide(title):
        return "Ignore", []

    legislative_context = re.search(
        r"\b(legislation|law|bill|criminalizes|criminalises|"
        r"sanctions|designates|national security legislation)\b",
        title,
        re.IGNORECASE,
    )

    explicit_attack = re.search(
        r"\b(terrorist attack|suicide bombing|suicide bomber|"
        r"mass shooting|shooting spree|gunmen storm|"
        r"militants attack|attack on civilians)\b",
        title,
        re.IGNORECASE,
    )

    if legislative_context and not explicit_attack:
        title_for_attack_check = re.sub(
            r"\b(terrorism|terrorist|attack|attacks)\b",
            "",
            title,
            flags=re.IGNORECASE,
        )
    else:
        title_for_attack_check = title

    if re.search(
        r"\b(covid-19|coronavirus|pandemic)\b",
        title,
        re.IGNORECASE,
    ) and not re.search(
        r"\b(airstrike|bombing|invasion|military attack|"
        r"terrorist attack|armed conflict|war crime)\b",
        title,
        re.IGNORECASE,
    ):
        return "Ignore", []

    if re.search(
        r"\b(shooting|gunmen|suicide bomber|terrorist attack|"
        r"terrorist shooting spree|militants attack)\b",
        title,
        re.IGNORECASE,
    ):
        return "Terrorism / Attack", ["Terrorism / Attack"]

    matching = []

    for category, patterns in CATEGORIES.items():
        check_title = (
            title_for_attack_check
            if category == "Terrorism / Attack"
            else title
        )

        if any(
            re.search(pattern, check_title, re.IGNORECASE)
            for pattern in patterns
        ):
            matching.append(category)

    if not matching:
        return "Ignore", []

    if len(matching) > 1:
        return "Needs Review", matching

    return matching[0], matching


def is_valid_event_title(title):
    if not title or len(title) < MIN_TITLE_LENGTH:
        return False

    normalized = normalize_text(title)

    if normalized in ("events", "references", "see also"):
        return False

    if re.fullmatch(r"\d{1,4}", title):
        return False

    if "citation needed" in normalized:
        return False

    return True


def get_review_reason(title, category, matching_categories, event_date):
    reasons = []

    if category == "Needs Review":
        reasons.append("Multiple matching categories")
        reasons.append(
            "Matched categories: " + ", ".join(matching_categories)
        )

    dates = DATE_PATTERN.findall(title)

    if len(dates) > 1:
        reasons.append("Multiple dates found; verify event date")

    if re.search(
        r"\b(in a separate incident|meanwhile|separately|"
        r"another attack|a second attack|in another incident|"
        r"two separate incidents|multiple incidents)\b",
        title,
        re.IGNORECASE,
    ):
        reasons.append("Possible multiple incidents in one entry")

    if event_date is None:
        reasons.append("Event date not identified")

    if re.search(
        r"\b(unrelated incident|at the same time|"
        r"as well as another incident)\b",
        title,
        re.IGNORECASE,
    ):
        reasons.append("Possible unrelated events in one description")

    if re.search(
        r"\b(election|elected|parliamentary vote)\b",
        title,
        re.IGNORECASE,
    ) and category in (
        "Natural Disaster",
        "Human-Caused Disaster",
    ):
        reasons.append("Possible unrelated election reference")

    if len(title) < 45:
        reasons.append("Short description; check completeness")

    if title.count("(") != title.count(")"):
        reasons.append("Unbalanced parentheses; check entry formatting")

    if re.search(r"\b(?:etc|e\.g|i\.e)\.$", title, re.IGNORECASE):
        reasons.append("Description may be incomplete")

    return "; ".join(dict.fromkeys(reasons))


def extract_list_entries(event_lists, year):
    entries = []
    seen_entries = set()

    def process_item(list_item):
        title = get_item_text(list_item)

        if is_valid_event_title(title):
            category, matching_categories = classify_event(title)

            if category != "Ignore":
                event_date = get_date_from_title(title, year)

                unique_key = (
                    normalize_text(title),
                    event_date,
                )

                if unique_key not in seen_entries:
                    seen_entries.add(unique_key)

                    entries.append({
                        "event_date": event_date,
                        "event_year": year,
                        "event_title": title,
                        "category": category,
                        "source_url": f"{BASE_URL}{year}",
                        "source_name": "Wikipedia",
                        "review_reason": get_review_reason(
                            title,
                            category,
                            matching_categories,
                            event_date,
                        ),
                    })

        for child_list in list_item.find_all(
            ["ul", "ol"],
            recursive=False,
        ):
            for child_item in child_list.find_all(
                "li",
                recursive=False,
            ):
                process_item(child_item)

    for event_list in event_lists:
        for list_item in event_list.find_all(
            "li",
            recursive=False,
        ):
            process_item(list_item)

    return entries


def scrape_year(year):
    url = f"{BASE_URL}{year}"

    print(f"\nScraping {year}...")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Could not retrieve {year}: {error}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    events_heading = get_events_section(soup)

    if events_heading is None:
        print("Events heading was not found.")
        return []

    event_lists = get_event_lists(events_heading)

    print(f"Raw Events lists found: {len(event_lists)}")

    entries = extract_list_entries(event_lists, year)

    print(f"Relevant candidates: {len(entries)}")

    return entries


def add_review_reason(event, reason):
    existing = event.get("review_reason", "")

    reasons = [
        item.strip()
        for item in existing.split(";")
        if item.strip()
    ]

    if reason not in reasons:
        reasons.append(reason)

    event["review_reason"] = "; ".join(reasons)


def run_global_quality_checks(events):
    """
    Flag potential duplicates across scraped entries.
    Does not delete or merge records automatically.
    """
    exact_groups = defaultdict(list)
    title_groups = defaultdict(list)
    date_category_groups = defaultdict(list)

    for index, event in enumerate(events):
        title_key = normalize_event_title(event["event_title"])
        date = event["event_date"]
        category = event["category"]

        if title_key:
            exact_groups[(title_key, date)].append(index)
            title_groups[title_key].append(index)

        if date:
            date_category_groups[(date, category)].append(index)

    duplicate_indices = set()
    similar_indices = set()
    same_date_category_indices = set()

    for indices in exact_groups.values():
        if len(indices) > 1:
            duplicate_indices.update(indices)

    for indices in title_groups.values():
        if len(indices) > 1:
            for index in indices:
                if index not in duplicate_indices:
                    similar_indices.add(index)

    for indices in date_category_groups.values():
        if len(indices) > 1:
            same_date_category_indices.update(indices)

    for index in duplicate_indices:
        add_review_reason(
            events[index],
            "Possible duplicate title and date",
        )

    for index in similar_indices:
        add_review_reason(
            events[index],
            "Repeated normalized title; verify whether duplicate",
        )

    for index in same_date_category_indices:
        add_review_reason(
            events[index],
            "Another event shares this date and category; verify",
        )

    year_groups = defaultdict(list)

    for index, event in enumerate(events):
        year_groups[event["event_year"]].append(index)

    for year, indices in year_groups.items():
        for position, first_index in enumerate(indices):
            first_title = normalize_event_title(
                events[first_index]["event_title"]
            )

            if len(first_title) < 35:
                continue

            for second_index in indices[position + 1:]:
                second_title = normalize_event_title(
                    events[second_index]["event_title"]
                )

                if len(second_title) < 35:
                    continue

                if first_title == second_title:
                    continue

                similarity = SequenceMatcher(
                    None,
                    first_title,
                    second_title,
                ).ratio()

                if similarity >= SIMILARITY_THRESHOLD:
                    add_review_reason(
                        events[first_index],
                        f"Similar title in {year}; verify possible duplicate",
                    )
                    add_review_reason(
                        events[second_index],
                        f"Similar title in {year}; verify possible duplicate",
                    )


def validate_event_records(events):
    """Check date structure, year consistency, and required fields."""
    valid_categories = set(CATEGORIES) | {"Needs Review"}

    for event in events:
        event_date = event.get("event_date")
        event_year = event.get("event_year")
        title = event.get("event_title", "")

        if not title.strip():
            add_review_reason(event, "Missing event title")

        if event_year not in range(START_YEAR, END_YEAR + 1):
            add_review_reason(event, "Event year outside configured range")

        if event_date:
            try:
                parsed_date = datetime.strptime(
                    event_date,
                    "%Y-%m-%d",
                ).date()

                if parsed_date.isoformat() != event_date:
                    add_review_reason(event, "Invalid date format")

                if parsed_date.year != event_year:
                    add_review_reason(
                        event,
                        "Date year does not match target year",
                    )

            except (ValueError, TypeError):
                add_review_reason(event, "Invalid calendar date")

        if not event.get("source_url"):
            add_review_reason(event, "Missing source URL")

        if not event.get("source_name"):
            add_review_reason(event, "Missing source name")

        if event.get("category") not in valid_categories:
            add_review_reason(
                event,
                "Unrecognized category; verify classification",
            )


def print_data_quality_report(events):
    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    total = len(events)
    flagged = [
        event for event in events
        if event.get("review_reason")
    ]
    unflagged = total - len(flagged)

    print(f"Total candidate events: {total}")
    print(f"Entries requiring review: {len(flagged)}")
    print(f"Entries without review flags: {unflagged}")

    print("\nReview reason counts:")

    reason_counts = Counter()

    for event in events:
        for reason in event.get("review_reason", "").split(";"):
            reason = reason.strip()

            if reason:
                reason_counts[reason] += 1

    if reason_counts:
        for reason, count in reason_counts.most_common():
            print(f"{reason}: {count}")
    else:
        print("No review flags found.")

    print("\nDATE VALIDATION SUMMARY")

    known_dates = sum(
        1 for event in events
        if event.get("event_date")
    )

    unknown_dates = total - known_dates

    print(f"Known dates: {known_dates}")
    print(f"Unknown dates: {unknown_dates}")

    if total:
        print(f"Known-date percentage: {known_dates / total * 100:.1f}%")
        print(f"Unknown-date percentage: {unknown_dates / total * 100:.1f}%")

    print("\nEVENT COUNTS BY YEAR")

    yearly_counts = defaultdict(Counter)

    for event in events:
        year = event["event_year"]
        yearly_counts[year]["total"] += 1

        if event.get("event_date"):
            yearly_counts[year]["known"] += 1
        else:
            yearly_counts[year]["unknown"] += 1

    for year in range(START_YEAR, END_YEAR + 1):
        counts = yearly_counts[year]

        print(
            f"{year}: total={counts['total']}, "
            f"known={counts['known']}, "
            f"unknown={counts['unknown']}"
        )

    print("\nCATEGORY COUNTS")

    category_counts = Counter(
        event["category"]
        for event in events
    )

    for category, count in sorted(category_counts.items()):
        print(f"{category}: {count}")


def print_flagged_events(events, limit=50):
    flagged_events = [
        event for event in events
        if event.get("review_reason")
    ]

    print("\n" + "=" * 60)
    print("EVENTS REQUIRING MANUAL REVIEW")
    print("=" * 60)

    print(f"Flagged entries: {len(flagged_events)}")
    print(f"Displaying up to: {limit}")

    for number, event in enumerate(flagged_events[:limit], start=1):
        print(f"\n{number}. {event['event_title']}")
        print(f"   Year: {event['event_year']}")
        print(f"   Date: {event['event_date'] or 'UNKNOWN'}")
        print(f"   Category: {event['category']}")
        print(f"   Review: {event['review_reason']}")
        print(f"   Source: {event['source_url']}")

    if len(flagged_events) > limit:
        print(
            f"\n{len(flagged_events) - limit} additional entries "
            "were not displayed."
        )


def print_date_quality_report(events):
    total = len(events)

    known = sum(
        1 for event in events
        if event.get("event_date") is not None
    )

    unknown = total - known

    print("\n" + "=" * 60)
    print("DATE QUALITY REPORT")
    print("=" * 60)

    print(f"Total candidate events: {total}")
    print(f"Known dates: {known}")
    print(f"Unknown dates: {unknown}")

    if total:
        print(f"Known-date percentage: {known / total * 100:.1f}%")
        print(f"Unknown-date percentage: {unknown / total * 100:.1f}%")

    yearly_totals = defaultdict(Counter)

    for event in events:
        year = event["event_year"]

        if event.get("event_date"):
            yearly_totals[year]["known"] += 1
        else:
            yearly_totals[year]["unknown"] += 1

    print("\nDate counts by year:")

    for year in range(START_YEAR, END_YEAR + 1):
        counts = yearly_totals[year]

        print(
            f"{year}: total={counts['known'] + counts['unknown']}, "
            f"known={counts['known']}, "
            f"unknown={counts['unknown']}"
        )


def print_review_summary(events):
    category_totals = Counter()
    flagged_events = []
    unflagged_events = []

    for event in events:
        category_totals[event["category"]] += 1

        if event.get("review_reason"):
            flagged_events.append(event)
        else:
            unflagged_events.append(event)

    print("\n" + "=" * 60)
    print("SCRAPING SUMMARY")
    print("=" * 60)

    print(f"Total candidate events: {len(events)}")

    print("\nCategory totals:")

    for category in sorted(category_totals):
        print(f"{category}: {category_totals[category]}")

    print(f"\nEntries flagged for review: {len(flagged_events)}")
    print(f"Entries without review flags: {len(unflagged_events)}")

    print("\nSAMPLE EVENTS")
    print("-" * 60)

    for number, event in enumerate(events[:20], start=1):
        print(
            f"{number}. [{event['category']}] "
            f"{event['event_date'] or 'UNKNOWN DATE'} - "
            f"{event['event_title']}"
        )

        if event.get("review_reason"):
            print(f"   REVIEW: {event['review_reason']}")


def main():
    print("=" * 60)
    print("WORLD HISTORY WEB SCRAPER")
    print("=" * 60)

    print(f"Year range: {START_YEAR}-{END_YEAR}")
    print(f"Preview only: {PREVIEW_ONLY}")
    print("Database writes: DISABLED")

    all_events = []

    for year in range(START_YEAR, END_YEAR + 1):
        all_events.extend(scrape_year(year))

    print("\nRunning data quality checks...")

    validate_event_records(all_events)
    run_global_quality_checks(all_events)

    print_review_summary(all_events)
    print_date_quality_report(all_events)
    print_data_quality_report(all_events)
    print_flagged_events(all_events)

    print("\nPREVIEW COMPLETE")
    print("No database records were changed.")
    print("Duplicate and similarity flags require manual confirmation.")


if __name__ == "__main__":
    main()
