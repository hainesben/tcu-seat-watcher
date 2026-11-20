# TCU Seat Watcher

Sends a phone notification when a seat opens in a full class on
[TCU Class Search](https://classes.tcu.edu).

It runs on GitHub Actions, so it keeps working when your computer is closed or turned off.

Right now it watches **ACCT 20653 (Introduction to Accounting), sections 080 and 081, Spring 2027**.

## How it works

1. Every 5 minutes, [cron-job.org](https://cron-job.org) tells GitHub to run [`cloud_check.py`](cloud_check.py). (The workflow also has GitHub's own 5-minute schedule as a backup, but GitHub's schedule is unreliable; see [Why cron-job.org](#why-cron-joborg).)
2. The script searches TCU Class Search for the course. It reads each section's status and enrollment (for example `Closed 40/40`).
3. When a section goes from full to open, it sends an urgent push to your phone through [ntfy](https://ntfy.sh). The push includes the class number, so you can register right away.
4. [`state.json`](state.json) keeps track of which sections are already open. That way you get **one alert per opening**, not one every 5 minutes. If a section fills up and opens again, you get another alert.

## Setup

1. Install the free **ntfy** app on your phone and subscribe to a topic name that's hard to guess.
2. In this repo, go to **Settings → Secrets and variables → Actions**. Add a secret named `NTFY_TOPIC` with that topic name as its value. Because it's a secret, the topic stays private even though the repo is public.
3. Set up cron-job.org to start the check every 5 minutes (below).

### cron-job.org trigger

**Step 1: Make a GitHub token** at <https://github.com/settings/personal-access-tokens/new> (fine-grained token):

- **Repository access:** *Only select repositories* → this repo
- **Permissions:** Repository permissions → **Actions: Read and write** (nothing else)
- Pick an expiration date after registration closes, then copy the token (starts with `github_pat_`). Never commit it to this repo.

**Step 2: Create a cronjob** on [cron-job.org](https://cron-job.org) (free account):

- **URL:** `https://api.github.com/repos/hainesben/tcu-seat-watcher/actions/workflows/watch.yml/dispatches`
- **Schedule:** every 5 minutes
- **Advanced → Request method:** `POST`
- **Advanced → Headers:**

  | Key | Value |
  |---|---|
  | `Accept` | `application/vnd.github+json` |
  | `Authorization` | `Bearer <your token>` |
  | `X-GitHub-Api-Version` | `2022-11-28` |
  | `Content-Type` | `application/json` |

- **Advanced → Request body:** `{"ref":"main"}`

Click **Test run**. A response of **204 No Content** means it worked, and a new run appears in this repo's **Actions** tab.

### Why cron-job.org

GitHub's built-in `schedule:` trigger can take hours to start on a new repo, and even after that it often runs late or skips runs. When this repo was set up, GitHub ran zero scheduled checks in the first hour. cron-job.org calls GitHub's API to start the workflow on time, every time.

If GitHub's own schedule also starts running, the extra checks are harmless. `state.json` makes sure you still get only one alert per opening.

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
# (also pause or delete the job on cron-job.org)
gh workflow disable watch.yml

# Turn it back on
gh workflow enable watch.yml
```

You can do the same things from the **Actions** tab on GitHub.

## Notes

- The repo is public because GitHub Actions minutes are free and unlimited for public repos. Checking every 5 minutes would use up a private repo's free minutes.
- The GitHub token expires on the date you picked. After that, cron-job.org gets an error and the checks stop. To keep going, make a new token and update the `Authorization` header on cron-job.org.
- GitHub pauses scheduled workflows after 60 days with no activity in the repo. To start it again, click **Enable workflow** in the Actions tab.
- Please keep the interval at 5 minutes or longer so you don't put extra load on TCU's site.
