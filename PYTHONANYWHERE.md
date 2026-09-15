# PythonAnywhere deployment

This guide is for the existing PythonAnywhere deployment of WeatherTomBot.

## Important
Do not overwrite a working production project until a backup exists. If the existing bot has additional modules, databases, JSON files, WSGI configuration, or payment settings, merge the changes into that project rather than blindly replacing the whole directory.

## 1. Backup the current project
Open a PythonAnywhere Bash console:

```bash
cd /home/YOUR_USERNAME
mkdir -p backups
tar -czf backups/WeatherTomBot_before_update_$(date +%Y%m%d_%H%M%S).tar.gz \
  bot.py bot.py.backup bot_texts.json weather.py database.py utils.py \
  config.py settings.json subscriptions.json b2b_users.json \
  notifications.json users_city.json requirements.txt weather_bot.db .env 2>/dev/null || true
```

Also save the current package list:

```bash
python3 -m pip freeze > backups/requirements_before_update.txt
```

## 2. Upload the package
In **Files**, upload `WeatherTomBot_fixed.zip` to `/home/YOUR_USERNAME`.

Then in Bash:

```bash
cd /home/YOUR_USERNAME
mkdir -p WeatherTomBot_new
unzip -o WeatherTomBot_fixed.zip -d WeatherTomBot_new
find WeatherTomBot_new -maxdepth 3 -type f -print
```

## 3. Do not immediately replace production
First check the current deployment:

```bash
ps aux | grep -E 'python|bot.py' | grep -v grep
python3 --version
which python3
```

If the bot is a Web App, check **Web → WSGI configuration file**, **Source code**, **Working directory**, and **Virtualenv**. If it is an Always-on task, check **Tasks**.

## 4. Environment variables
Create a real `.env` from `.env.example` only if the deployment uses environment variables:

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Never commit or upload real secrets into a public repository. Rotate any token that has previously been exposed in source code.

## 5. Dependencies
Use the same Python/virtualenv that the working bot currently uses. Install only after comparing `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

If the current deployment uses a virtualenv, activate/use that environment instead.

## 6. Syntax test
Before switching production:

```bash
python3 -m py_compile bot.py
```

## 7. Smoke test
Test, in order:

1. `/start`
2. language selection: RU / EN / ES / ZH
3. city selection
4. current weather
5. forecast
6. rain check
7. moon/sunrise features
8. subscription screen
9. B2B tariff screen
10. invoice creation
11. successful payment flow
12. notifications
13. admin panel (if enabled)

For each language, verify that user-facing text does not unexpectedly fall back to Russian.

## 8. Reload
For a PythonAnywhere Web App, use **Web → Reload** after the code is ready. Do not restart a different process by mistake.

## 9. Rollback
If the new version fails, restore the backup:

```bash
cd /home/YOUR_USERNAME
mkdir -p rollback
# inspect the archive first
 tar -tzf backups/WeatherTomBot_before_update_YYYYMMDD_HHMMSS.tar.gz | head
# restore only after confirming the correct archive
```

Then reload the Web App or restart the relevant task.

## PythonAnywhere-specific note
The included `deploy/weathertombot.service` is for a normal Linux/systemd server. **Do not install it on PythonAnywhere.** PythonAnywhere manages Web Apps and scheduled/always-on processes through its own interface.
