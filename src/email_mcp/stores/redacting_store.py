"""Step 5: hide email addresses and phone numbers in the text of emails.

RedactingStore wraps any other store. The server asks it for emails as
before, and it passes each result through redact() on the way out, so no
tool can return text that skipped redaction.

The people stay named: sender, to and cc are left as they are, so the model
can still say who wrote to whom. Only the subject, body and snippet are
redacted.
"""

import re

# A regular expression describes a pattern of text. These two match the
# personal details this step hides.
# An email address: letters, digits, dots, plus signs or hyphens, then @,
# then a domain with at least one dot, such as jeff.skilling@enron.com.
EMAIL_ADDRESS = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A North American phone number: 713-853-6161, 713.853.6161 or
# (713) 853-6161.
PHONE_NUMBER = re.compile(r"\(?\b\d{3}\)?[-. ]?\d{3}[-.]\d{4}\b")


def redact(text):
    """Return text with every email address and phone number replaced."""
    # TODO 4, part 1: replace each email address with [email] and each
    # phone number with [phone].
    # Hint: EMAIL_ADDRESS.sub("[email]", text) returns a copy of text with
    #       every email address replaced by [email]. Do the same with
    #       PHONE_NUMBER, then return the result.
    raise NotImplementedError("TODO 4: fill in redact in redacting_store.py")


class RedactingStore:
    """A store that redacts everything another store returns."""

    def __init__(self, store):
        self._store = store
        self.description = f"{store.description}, with personal details redacted"

    def search(self, query, limit):
        results = []
        for summary in self._store.search(query, limit):
            # Copy the dictionary so the wrapped store's own data is not
            # changed, then redact the text fields.
            summary = dict(summary)
            summary["subject"] = redact(summary["subject"])
            summary["snippet"] = redact(summary["snippet"])
            results.append(summary)
        return results

    def get(self, email_id):
        # TODO 4, part 2: return the wrapped store's email with its subject
        # and body redacted.
        # search() above is your model.
        # Hint 1: self._store.get(email_id) returns the email, or None when
        #         no email has that id. Return None in that case.
        # Hint 2: copy the email with dict(...) before changing it, then
        #         pass its subject and body through redact().
        raise NotImplementedError("TODO 4: fill in RedactingStore.get in redacting_store.py")
