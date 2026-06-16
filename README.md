# Email Sender

A small laptop-friendly tool that finds LinkedIn profile URLs through SerpAPI, enriches contacts from public search results, discovers verified emails with Hunter.io, and saves only verified contacts to `queue.json`.

## Architecture

1. `search.py` searches Google through SerpAPI for LinkedIn profile URLs.
2. It extracts the contact name, role, company, snippet, and LinkedIn URL from search results only.
3. `sources.py` searches public web results for company/domain evidence without scraping LinkedIn pages.
4. `hunter.py` calls Hunter Email Finder and Email Verifier.
5. `main.py` queues only contacts with verified Hunter emails and a confidence score above your threshold.
6. `sender.py` sends only queued contacts where `email_verified` is `true`.

## First-time setup

1. Double-click `run.bat` or run it from PowerShell.
2. Copy `.env.example` to `.env`.
3. Add your own `SERPAPI_API_KEY`, `HUNTER_API_KEY`, `GMAIL_ADDRESS`, and `GMAIL_APP_PASSWORD` in `.env`.

## Generate email drafts

```powershell
python main.py "software engineer Mastercard Pune" --limit 5 --min-confidence 80
```

This creates or replaces:

- `queue.json`: verified contacts only
- `rejected_contacts.json`: contacts skipped because no verified email was found

## Queue fields

Each queued contact includes:

- `receiver_email`
- `email_verified`
- `email_confidence_score`
- `email_verification_status`
- `email_source`
- `hunter_sources`
- `public_sources`
- `contact`
- `subject`
- `body`

The app no longer guesses email addresses. If Hunter cannot verify an email, the contact is not added to the send queue.

## Test sender without sending

```powershell
python sender.py
```

## Actually send reviewed emails

```powershell
python sender.py --send
```

## Notes

- Credentials are loaded from `.env`; they are no longer stored in Python files.
- `sender.py` runs in dry-run mode unless you pass `--send`.
- LinkedIn pages are not scraped. The tool uses LinkedIn URLs and metadata from SerpAPI search results.
- Hunter Email Finder returns confidence scores and verification details. The default queue threshold is 80.
