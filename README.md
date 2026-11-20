# TCU Seat Watcher

Sends a phone notification when a seat opens in a full class on
[TCU Class Search](https://classes.tcu.edu).

It runs on GitHub Actions, so it keeps working when your computer is closed or turned off.

Right now it watches **ACCT 20653 (Introduction to Accounting), sections 080 and 081, Spring 2027**.

## How it works

1. About every 5 minutes, GitHub runs [`cloud_check.py`](cloud_check.py). GitHub sometimes runs it late.
2. The script searches TCU Class Search for the course. It reads each section's status and enrollment (for example `Closed 40/40`).
3. When a section goes from full to open, it sends an urgent push to your phone through [ntfy](https://ntfy.sh). The push includes the class number, so you can register right away.
4. [`state.json`](state.json) keeps track of which sections are already open. That way you get **one alert per opening**, not one every 5 minutes. If a section fills up and opens again, you get another alert.

## Setup

1. Install the free **ntfy** app on your phone and subscribe to a topic name that's hard to guess.
2. In this repo, go to **Settings → Secrets and variables → Actions**. Add a secret named `NTFY_TOPIC` with that topic name as its value. Because it's a secret, the topic stays private even though the repo is public.
3. The workflow in [`.github/workflows/watch.yml`](.github/workflows/watch.yml) starts running on its own.

## Watching a different class

Edit the settings at the top of `cloud_check.py`:

```python
TERM_CODE = "4273"          # "27 Spring" (value from the Term dropdown on classes.tcu.edu)
SUBJECT = "ACCT"
COURSE = "20653"
SECTIONS = {"080", "081"}
```

## Useful commands

```bash
# Run a check right now, and also send a test push to your phone
gh workflow run watch.yml -f test_push=true

# See recent checks
gh run list -L 5

# Turn it off once you're registered
gh workflow disable watch.yml

# Turn it back on
gh workflow enable watch.yml
```

You can do the same things from the **Actions** tab on GitHub.

## Notes

- The repo is public because GitHub Actions minutes are free and unlimited for public repos. Checking every 5 minutes would use up a private repo's free minutes.
- GitHub pauses scheduled workflows after 60 days with no activity in the repo. To start it again, click **Enable workflow** in the Actions tab.
- Please keep the interval at 5 minutes or longer so you don't put extra load on TCU's site.
