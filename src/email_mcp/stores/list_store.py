"""Step 2: search and read mock emails kept in a plain Python list."""

import re

# Each email is a dictionary with the fields get_email returns. The data is
# synthetic; ids, addresses and text are made up for the project.
MOCK_EMAILS = [
    {
        "id": 1,
        "date": "2026-10-01 16:00:00",
        "sender": "alice@example.com",
        "to": ["bob@example.com"],
        "cc": [],
        "subject": "AI Club project meeting",
        "body": "Let's meet on Friday to work on the MCP project.",
    },
    {
        "id": 2,
        "date": "2026-10-01 18:30:00",
        "sender": "bob@example.com",
        "to": ["alice@example.com"],
        "cc": ["carol@example.com"],
        "subject": "Re: AI Club project meeting",
        "body": "Friday works. I'll bring a sample email for the demo.",
    },
    {
        "id": 3,
        "date": "2026-10-02 09:15:00",
        "sender": "carol@example.com",
        "to": ["alice@example.com", "bob@example.com"],
        "cc": [],
        "subject": "",
        "body": "The dataset link is ready. Ask me before sharing it outside the club.",
    },
]


class ListStore:
    """Find emails by looping over MOCK_EMAILS."""

    description = f"{len(MOCK_EMAILS)} synthetic emails from a Python list"

    def search(self, query, limit):
        # An email matches when every word of the query appears in its
        # subject or body, ignoring upper/lower case.
        words = re.findall(r"\w+", query.lower())
        if not words:
            return []
        results = []
        for email in MOCK_EMAILS:
            text = f"{email['subject']} {email['body']}".lower()
            if all(word in text for word in words):
                results.append(
                    {
                        "id": email["id"],
                        "date": email["date"],
                        "sender": email["sender"],
                        "subject": email["subject"] or "(no subject)",
                        "snippet": email["body"][:200],
                    }
                )
        return results[:limit]

    def get(self, email_id):
        for email in MOCK_EMAILS:
            if email["id"] == email_id:
                # Return a copy so the placeholder does not change MOCK_EMAILS.
                return email | {"subject": email["subject"] or "(no subject)"}
        return None
