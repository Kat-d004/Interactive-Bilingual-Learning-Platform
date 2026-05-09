# IBLP — Interactive Bilingual Learning Platform

A web-based bilingual learning platform for young children, combining speech
recognition, machine learning, and interactive quizzes to teach colours,
animals, and numbers in both Sesotho and English.

---

## Table of Contents

- [Project Overview](#project-overview)
- [System Requirements](#system-requirements)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Makefile Reference](#makefile-reference)
- [Database](#database)
- [Troubleshooting](#troubleshooting)
- [Uninstalling](#uninstalling)

---

## Project Overview

IBLP allows parents to register children, track their learning progress, and
have children practise spoken words through a microphone. The platform uses 
TensorFlow models trained on Sesotho audio to recognise spoken numbers, 
colours and animals, OpenAI Whisper for English speech-to-text.

**Modules**

- Learn — flashcard-style lessons for colours, animals, and numbers
- Quiz — multiple choice questions per module
- Speech Practice — microphone-based pronunciation exercises
- Progress — parent dashboard showing scores and completed modules

**Tech Stack**

- Frontend: HTML, CSS, JavaScript
- Backend: PHP 8.3
- Database: MySQL 8.0
- Machine Learning: Python 3.12, TensorFlow, OpenAI Whisper, librosa
- Web Server: Apache 2.4
- OS: Ubuntu 24.04 LTS

---

## System Requirements
- Ubuntu (to run this makefile)
- Internet connection (required during install to download packages)

All other dependencies (Apache, MySQL, PHP, Python) are installed
automatically by the Makefile.

---

## Project Structure

```
complete_iblp/
+-- Makefile                  <- place here, in the parent folder
+-- README.md
+-- iblp/
    +-- *.php                 <- main PHP pages
    +-- *.html                <- frontend pages
    +-- *.py                  <- speech recognition scripts
    +-- api/                  <- PHP API endpoints
    |   +-- login.php
    |   +-- logout.php
    |   +-- register.php
    |   +-- auth-check.php
    |   +-- quiz.php
    |   +-- progress.php
    |   +-- activity.php
    |   +-- preferences.php
    +-- config/
    |   +-- db.php            <- database connection and helpers
    |   +-- schema.sql        <- table definitions
    +-- css/                  <- stylesheets
    +-- js/                   <- JavaScript files
    +-- images/
    |   +-- animals/          <- animal images used in lessons
    +-- recordings/           <- Sesotho audio samples (.wav)
    +-- models/               <- trained TensorFlow models (.h5)
```

After installation the Makefile deploys everything to `/var/www/html/iblp`

---

## Installation

### 1. Place the Makefile

Make sure the `Makefile` and `README.md` are in the parent folder of `iblp/`:

```
complete_iblp/
+-- Makefile
+-- README.md
+-- iblp/
```

### 2. Run the installer

```bash
cd complete_iblp
sudo make install
```

That single command runs all eight steps automatically:

```
[1/8] Installing system packages (Apache, MySQL, PHP, Python 3.12)
[2/8] Creating Python virtual environment at /opt/iblp/ml_env
[3/8] Creating deployment directories
[4/8] Deploying source files to /var/www/html/iblp
[5/8] Installing Python packages (librosa, numpy, tensorflow, whisper ...)
[6/8] Setting up database
[7/8] Setting file permissions
[8/8] Reloading Apache
```

Step 5 downloads large packages and progress is printed line
by line so you can see it is working.

### 3. Open the application

```
http://localhost/iblp/
```
---

## Makefile Reference

All targets that write to the system require `sudo`. Targets that only read
(check, logs) do not.

### Setup

| Command | Description |
|---|---|
| `sudo make install` | Full install — runs all steps from scratch |
| `sudo make deps` | Install system packages only (Apache, MySQL, PHP, Python, ffmpeg) |
| `sudo make venv` | Create Python virtual environment at `/opt/iblp/ml_env` |

### Day-to-day

| Command | Description |
|---|---|
| `sudo make deploy` | Re-copy source files to `/var/www/html/iblp` |
| `sudo make permissions` | Fix file ownership and permissions |
| `sudo make pip-deps` | Re-install Python packages into the venv |
| `sudo make db-init` | Create database and tables |
| `sudo make db-reset` | Drop and recreate the database (all data lost) |
| `sudo make clean-tmp` | Remove leftover `.wav`, `.jpg`, `.nbc` files from `tmp/` |
| `sudo make reload` | Reload Apache without downtime |
| `sudo make restart` | Full Apache restart |

### Diagnostics

| Command | Description |
|---|---|
| `make check` | Smoke-test all components — packages, Python, PHP, Apache, MySQL, directories |
| `make logs` | Tail the Apache error log |
| `make logs-access` | Tail the Apache access log |

### Removal

| Command | Description |
|---|---|
| `sudo make uninstall` | Remove all installed files, database, user, and system packages |

---

## Database

The Makefile creates a dedicated MySQL user so that the application never
runs as root.

| Setting | Value |
|---|---|
| Database | `iblp_database` |
| User | `iblp_user` |
| Password | `iblp_pass` |
| Host | `localhost` |

The deployed `config/db.php` is patched automatically during install to use
these credentials. The source file in `iblp/config/db.php` is not modified.

### Tables

| Table | Purpose |
|---|---|
| `parents` | Parent accounts (email, password hash) |
| `children` | Child profiles linked to a parent |
| `student_progress` | Stars and completion flags per child per module |
| `quiz_scores` | Individual quiz results with percentage |
| `user_preferences` | Language, theme, and sound settings per child |
| `sessions` | Login tokens with expiry |
| `activity_log` | Timestamped record of all child activity |

---

## Troubleshooting

**pip times out during step 5**

This is common on VMs with slow network. The Makefile already sets
`--timeout 120 --retries 5`. If it still fails, run:

```bash
sudo make pip-deps
```

This retries only the pip step without repeating the full install.
Switching VirtualBox from NAT to Bridged Adapter also helps significantly.

**apt-get update shows PPA errors**

Lines like `does not have a Release file` from third-party PPAs (wine, java,
codeblocks) are harmless. The Makefile uses `|| true` to ignore them and
continues normally.

**MySQL connection refused**

If `make check` reports a MySQL connection failure, verify the service is
running:

```bash
sudo systemctl status mysql
sudo systemctl start mysql
```

Then retry:

```bash
sudo make db-init
```

**Permission denied on tmp/ or whisper_cache/**

```bash
sudo make permissions
```

**Apache not serving the site**

```bash
make logs
sudo make restart
```

---

## Uninstalling

To completely remove IBLP and all installed components:

```bash
sudo make uninstall
```

This removes, in order:

1. Deployed files at `/var/www/html/iblp`
2. Python virtual environment at `/opt/iblp`
3. MySQL database `iblp_database` and user `iblp_user`
4. Apache and MySQL services (stopped and disabled)
5. All installed system packages (Apache, MySQL, PHP, Python 3.12, ffmpeg)

A 5-second cancellation window is shown before anything is deleted.
