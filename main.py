import re
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup


START_YEAR = 2020
END_YEAR = 2026

BASE_URL = "https://en.wikipedia.org/wiki/"
HEADERS = {
    "User-Agent": "HistoryEventResearchTool/1.0 (student learning project)"
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
    rf"was captured on|was elected on|on)\s+"
    rf"({MONTHS})\s+(\d{{1,2}})(?:,\s*(\d{{4}}))?\b",
    re.IGNORECASE,
)

LATER_EVENT_PATTERN = re.compile(
    r"\b(?:months later|weeks later|days later|"
    r"the following day|the next day|later that year|"
    r"later that month|subsequently|in a later development)\b",
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


def history_scraper_clean_page_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return re.sub(r"\[\d+\]", "", text)


def history_scraper_normalize_text(text):
    return history_scraper_clean_page_text(text).casefold()


def history_scraper_prepare_title_key(title):
    title = history_scraper_normalize_text(title)

    title = re.sub(
        r"^[a-z]+\s+\d{1,2}(?:,\s*\d{4})?\s*[–—-]\s*",
        "",
        title,
    )

    title = re.sub(r"[^a-z0-9\s]", " ", title)

    return re.sub(r"\s+", " ", title).strip()


def history_scraper_read_heading(heading):
    text = heading.get_text(" ", strip=True)

    text = re.sub(
        r"\[edit\]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return history_scraper_normalize_text(text)


def history_scraper_validate_date_match(match, year):
    month, day, explicit_year = match.groups()

    date_year = int(explicit_year) if explicit_year else year

    if date_year != year:
        return None

    try:
        return datetime.strptime(
            f"{month} {day} {date_year}",
            "%B %d %Y",
        ).date().isoformat()

    except ValueError:
        return None


def history_scraper_find_event_date(title, year):
    leading_match = LEADING_DATE_PATTERN.match(title)

    if leading_match:
        date_match = DATE_PATTERN.search(leading_match.group(0))

        if date_match:
            return history_scraper_validate_date_match(
                date_match,
                year,
            )

    sentences = re.split(
        r"(?<=[.!?])\s+",
        title.strip(),
        maxsplit=1,
    )

    first_sentence = sentences[0] if sentences else title.strip()

    if LATER_EVENT_PATTERN.search(first_sentence):
        return None

    valid_dates = {
        parsed
        for match in DATE_CONTEXT_PATTERN.finditer(first_sentence)
        if (
            parsed := history_scraper_validate_date_match(
                match,
                year,
            )
        )
    }

    return next(iter(valid_dates)) if len(valid_dates) == 1 else None


def history_scraper_locate_events_section(soup):
    for heading in soup.find_all(["h2", "h3"]):
        if history_scraper_read_heading(heading) == "events":
            return heading

    return None


def history_scraper_collect_event_lists(events_heading):
    event_lists = []

    for element in events_heading.find_all_next():

        if element.name == "h2":
            break

        if element.name == "ul" and element.find_parent("ul") is None:
            event_lists.append(element)

    return event_lists


def history_scraper_extract_list_item_text(list_item):
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

    return history_scraper_clean_page_text(
        item_copy.get_text(" ", strip=True)
    )


def history_scraper_is_out_of_scope(title):
    return any(
        re.search(pattern, title, re.IGNORECASE)
        for pattern in IRRELEVANT_PATTERNS
    )


def history_scraper_detect_election_landslide(title):
    return bool(
        re.search(r"\blandslide\b", title, re.IGNORECASE)
        and re.search(
            r"\b(election|electoral|vote|votes|victory|president|"
            r"prime minister|parliament|second term)\b",
            title,
            re.IGNORECASE,
        )
    )


def history_scraper_assign_event_category(title):

    if (
        history_scraper_is_out_of_scope(title)
        or history_scraper_detect_election_landslide(title)
    ):
        return "Ignore", []

    legislative_context = re.search(
        r"\b(legislation|law|bill|criminalizes|criminalises|sanctions|"
        r"designates|national security legislation)\b",
        title,
        re.IGNORECASE,
    )

    explicit_attack = re.search(
        r"\b(terrorist attack|suicide bombing|suicide bomber|mass shooting|"
        r"shooting spree|gunmen storm|militants attack|attack on civilians)\b",
        title,
        re.IGNORECASE,
    )

    if legislative_context and not explicit_attack:
        attack_check_title = re.sub(
            r"\b(terrorism|terrorist|attack|attacks)\b",
            "",
            title,
            flags=re.IGNORECASE,
        )
    else:
        attack_check_title = title

    if (
        re.search(
            r"\b(covid-19|coronavirus|pandemic)\b",
            title,
            re.IGNORECASE,
        )
        and not re.search(
            r"\b(airstrike|bombing|invasion|military attack|"
            r"terrorist attack|armed conflict|war crime)\b",
            title,
            re.IGNORECASE,
        )
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
            attack_check_title
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


def history_scraper_check_title_quality(title):

    if not title or len(title) < MIN_TITLE_LENGTH:
        return False

    normalized = history_scraper_normalize_text(title)

    if normalized in ("events", "references", "see also"):
        return False

    if re.fullmatch(r"\d{1,4}", title):
        return False

    if "citation needed" in normalized:
        return False

    return True


def history_scraper_build_review_notes(
    title,
    category,
    matching_categories,
    event_date,
):
    reasons = []

    if category == "Needs Review":
        reasons.append("Multiple matching categories")

        reasons.append(
            "Matched categories: " + ", ".join(matching_categories)
        )

    if len(DATE_PATTERN.findall(title)) > 1:
        reasons.append("Multiple dates found; verify event date")

    if re.search(
        r"\b(in a separate incident|meanwhile|separately|another attack|"
        r"a second attack|in another incident|two separate incidents|multiple incidents)\b",
        title,
        re.IGNORECASE,
    ):
        reasons.append("Possible multiple incidents in one entry")

    if event_date is None:
        reasons.append("Event date not identified")

    if re.search(
        r"\b(unrelated incident|at the same time|as well as another incident)\b",
        title,
        re.IGNORECASE,
    ):
        reasons.append("Possible unrelated events in one description")

    if (
        re.search(
            r"\b(election|elected|parliamentary vote)\b",
            title,
            re.IGNORECASE,
        )
        and category in (
            "Natural Disaster",
            "Human-Caused Disaster",
        )
    ):
        reasons.append("Possible unrelated election reference")

    if len(title) < 45:
        reasons.append("Short description; check completeness")

    if title.count("(") != title.count(")"):
        reasons.append("Unbalanced parentheses; check entry formatting")

    if re.search(r"\b(?:etc|e\.g|i\.e)\.$", title, re.IGNORECASE):
        reasons.append("Description may be incomplete")

    return "; ".join(dict.fromkeys(reasons))


def history_scraper_parse_event_entries(event_lists, year):
    entries = []
    seen_entries = set()

    def history_scraper_process_list_item(list_item):

        title = history_scraper_extract_list_item_text(list_item)

        if history_scraper_check_title_quality(title):

            category, matching_categories = (
                history_scraper_assign_event_category(title)
            )

            if category != "Ignore":

                event_date = history_scraper_find_event_date(
                    title,
                    year,
                )

                unique_key = (
                    history_scraper_normalize_text(title),
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
                        "review_reason": (
                            history_scraper_build_review_notes(
                                title,
                                category,
                                matching_categories,
                                event_date,
                            )
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
                history_scraper_process_list_item(child_item)

    for event_list in event_lists:

        for list_item in event_list.find_all("li", recursive=False):
            history_scraper_process_list_item(list_item)

    return entries


def history_scraper_fetch_year_events(year):

    try:
        response = requests.get(
            f"{BASE_URL}{year}",
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Could not retrieve {year}: {error}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    events_heading = history_scraper_locate_events_section(soup)

    if events_heading is None:
        print(f"Events section not found for {year}.")
        return []

    event_lists = history_scraper_collect_event_lists(events_heading)

    return history_scraper_parse_event_entries(
        event_lists,
        year,
    )


def history_scraper_append_review_note(event, reason):

    reasons = [
        item.strip()
        for item in event.get("review_reason", "").split(";")
        if item.strip()
    ]

    if reason not in reasons:
        reasons.append(reason)

    event["review_reason"] = "; ".join(reasons)


def history_scraper_check_collection_duplicates(events):

    exact_groups = defaultdict(list)
    title_groups = defaultdict(list)
    date_category_groups = defaultdict(list)

    for index, event in enumerate(events):

        title_key = history_scraper_prepare_title_key(
            event["event_title"]
        )

        event_date = event["event_date"]
        category = event["category"]

        if title_key:
            exact_groups[(title_key, event_date)].append(index)
            title_groups[title_key].append(index)

        if event_date:
            date_category_groups[(event_date, category)].append(index)

    duplicate_indices = set()
    similar_indices = set()
    same_date_category_indices = set()

    for indices in exact_groups.values():

        if len(indices) > 1:
            duplicate_indices.update(indices)

    for indices in title_groups.values():

        if len(indices) > 1:
            similar_indices.update(
                index
                for index in indices
                if index not in duplicate_indices
            )

    for indices in date_category_groups.values():

        if len(indices) > 1:
            same_date_category_indices.update(indices)

    for index in duplicate_indices:

        history_scraper_append_review_note(
            events[index],
            "Possible duplicate title and date",
        )

    for index in similar_indices:

        history_scraper_append_review_note(
            events[index],
            "Repeated normalized title; verify whether duplicate",
        )

    for index in same_date_category_indices:

        history_scraper_append_review_note(
            events[index],
            "Another event shares this date and category; verify",
        )

    year_groups = defaultdict(list)

    for index, event in enumerate(events):
        year_groups[event["event_year"]].append(index)

    for year, indices in year_groups.items():

        for position, first_index in enumerate(indices):

            first_title = history_scraper_prepare_title_key(
                events[first_index]["event_title"]
            )

            if len(first_title) < 35:
                continue

            for second_index in indices[position + 1:]:

                second_title = history_scraper_prepare_title_key(
                    events[second_index]["event_title"]
                )

                if len(second_title) < 35 or first_title == second_title:
                    continue

                similarity = SequenceMatcher(
                    None,
                    first_title,
                    second_title,
                ).ratio()

                if similarity >= SIMILARITY_THRESHOLD:

                    reason = (
                        f"Similar title in {year}; verify possible duplicate"
                    )

                    history_scraper_append_review_note(
                        events[first_index],
                        reason,
                    )

                    history_scraper_append_review_note(
                        events[second_index],
                        reason,
                    )


def history_scraper_validate_event_collection(events):

    valid_categories = set(CATEGORIES) | {"Needs Review"}

    for event in events:

        event_date = event.get("event_date")
        event_year = event.get("event_year")
        title = event.get("event_title", "")

        if not title.strip():

            history_scraper_append_review_note(
                event,
                "Missing event title",
            )

        if event_year not in range(START_YEAR, END_YEAR + 1):

            history_scraper_append_review_note(
                event,
                "Event year outside configured range",
            )

        if event_date:

            try:
                parsed_date = datetime.strptime(
                    event_date,
                    "%Y-%m-%d",
                ).date()

                if parsed_date.isoformat() != event_date:

                    history_scraper_append_review_note(
                        event,
                        "Invalid date format",
                    )

                if parsed_date.year != event_year:

                    history_scraper_append_review_note(
                        event,
                        "Date year does not match target year",
                    )

            except (ValueError, TypeError):

                history_scraper_append_review_note(
                    event,
                    "Invalid calendar date",
                )

        if not event.get("source_url"):

            history_scraper_append_review_note(
                event,
                "Missing source URL",
            )

        if not event.get("source_name"):

            history_scraper_append_review_note(
                event,
                "Missing source name",
            )

        if event.get("category") not in valid_categories:

            history_scraper_append_review_note(
                event,
                "Unrecognized category; verify classification",
            )


def history_scraper_display_collection_summary(events):

    total = len(events)

    known_dates = sum(
        bool(event.get("event_date"))
        for event in events
    )

    flagged = sum(
        bool(event.get("review_reason"))
        for event in events
    )

    print("\n===== Scraping Summary =====")
    print(f"Events collected: {total}")
    print(f"Dates identified: {known_dates}/{total}")
    print(f"Entries needing review: {flagged}")

    if total:
        print(f"Date coverage: {known_dates / total:.1%}")
    else:
        print("Date coverage: 0.0%")


def history_scraper_display_category_events(
    events,
    selected_category,
):

    matching_events = [
        event
        for event in events
        if event["category"] == selected_category
    ]

    print(f"\n===== {selected_category} Events =====")
    print(f"Total events: {len(matching_events)}")

    if not matching_events:
        print("No events found in this category.")
        return

    for index, event in enumerate(matching_events, start=1):

        print(f"\n{index}. {event['event_title']}")
        print(f"   Date: {event['event_date'] or 'Unknown'}")
        print(f"   Year: {event['event_year']}")
        print(f"   Source: {event['source_url']}")

        if event.get("review_reason"):
            print(f"   Review note: {event['review_reason']}")


def history_scraper_run_year_menu():

    while True:

        year_input = input(
            f"\nEnter a year ({START_YEAR}-{END_YEAR}) or Q to quit: "
        ).strip()

        if year_input.lower() == "q":

            print("Exiting the History Scraper.")
            break

        if not year_input.isdigit():

            print("Please enter a valid year.")
            continue

        selected_year = int(year_input)

        if not START_YEAR <= selected_year <= END_YEAR:

            print(
                f"Please enter a year between "
                f"{START_YEAR} and {END_YEAR}."
            )

            continue

        print(f"\nScraping events for {selected_year}...")

        yearly_events = history_scraper_fetch_year_events(
            selected_year
        )

        history_scraper_validate_event_collection(yearly_events)

        history_scraper_check_collection_duplicates(yearly_events)

        history_scraper_display_collection_summary(yearly_events)

        categories = sorted({
            event["category"]
            for event in yearly_events
        })

        while True:

            print("\n===== Event Categories =====")

            for index, category in enumerate(categories, start=1):

                count = sum(
                    event["category"] == category
                    for event in yearly_events
                )

                print(f"{index}. {category}: {count}")

            print("0. Choose another year")

            category_choice = input(
                "Select a category: "
            ).strip()

            if category_choice == "0":
                break

            if not category_choice.isdigit():

                print("Please enter a valid option.")
                continue

            category_index = int(category_choice) - 1

            if not 0 <= category_index < len(categories):

                print("Invalid category selection.")
                continue

            selected_category = categories[category_index]

            history_scraper_display_category_events(
                yearly_events,
                selected_category,
            )


def run_world_history_scraping_session():
    history_scraper_run_year_menu()


if __name__ == "__main__":
    run_world_history_scraping_session()