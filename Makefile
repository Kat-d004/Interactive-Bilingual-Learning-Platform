# ============================================================
#  IBLP - Makefile
#  Ubuntu + Apache + MySQL  |  Deploy target: /var/www/html/iblp
#
#  Place this Makefile in the parent folder of iblp/:
#
#    iblp_everything_working/
#    +-- Makefile
#    +-- iblp/
#        +-- *.php, *.py, *.html, api/, config/, models/, ...
#
#  Full setup with one command:
#    sudo make install
# ============================================================

# -- Configurable paths & credentials ------------------------
SRC_DIR      := iblp
DEPLOY_DIR   := /var/www/html/iblp
VENV_DIR     := /opt/iblp/ml_env
PYTHON_BIN   := $(VENV_DIR)/bin/python3.12
PIP_BIN      := $(VENV_DIR)/bin/pip
WEB_USER     := www-data
WEB_GROUP    := www-data

DB_NAME      := iblp_database
DB_APP_USER  := iblp_user
DB_APP_PASS  := iblp_pass

# -- Derived paths (do not edit) -----------------------------
TMP_DIR      := $(DEPLOY_DIR)/tmp
MODELS_DIR   := $(DEPLOY_DIR)/models
RECORDINGS   := $(DEPLOY_DIR)/recordings
IMAGES_DIR   := $(DEPLOY_DIR)/images
API_DIR      := $(DEPLOY_DIR)/api
CONFIG_DIR   := $(DEPLOY_DIR)/config
CSS_DIR      := $(DEPLOY_DIR)/css
JS_DIR       := $(DEPLOY_DIR)/js
WHISPER_DIR  := $(DEPLOY_DIR)/whisper_cache
MYSQL_ROOT   := mysql -u root
MYSQL_APP    := mysql -u iblp_user -piblp_pass

# -- Progress display helper ---------------------------------
STEP  = @echo "" && echo "[STEP] $(1)" && echo "----------------------------------------------------"
OK    = @echo "[DONE] $(1)"

.DEFAULT_GOAL := help

# -------------------------------------------------------------
#  HELP
# -------------------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "  IBLP Makefile - Ubuntu / Apache / MySQL"
	@echo ""
	@echo "  Setup:"
	@echo "    sudo make install        Full install - system deps, venv, files, db, permissions"
	@echo ""
	@echo "  Individual targets:"
	@echo "    sudo make deps           Install Apache, MySQL, PHP, Python 3.12"
	@echo "    sudo make venv           Create Python virtual environment in $(VENV_DIR)"
	@echo "    sudo make deploy         Sync source files to $(DEPLOY_DIR)"
	@echo "    sudo make permissions    Fix ownership and file permissions"
	@echo "    sudo make db-init        Create database and tables"
	@echo "    sudo make db-reset       Drop and recreate the database"
	@echo "    sudo make pip-deps       Install Python dependencies into $(VENV_DIR)"
	@echo "    make check               Smoke-test Python, PHP, Apache, MySQL"
	@echo "    sudo make clean-tmp      Remove leftover wav/jpg/nbc files from tmp/"
	@echo "    sudo make reload         Reload Apache (no downtime)"
	@echo "    sudo make restart        Full Apache restart"
	@echo "    make logs                Tail Apache error log"
	@echo "    make logs-access         Tail Apache access log"
	@echo "    sudo make uninstall      Remove $(DEPLOY_DIR) entirely"
	@echo ""

# -------------------------------------------------------------
#  FULL INSTALL  (single entry point)
# -------------------------------------------------------------
.PHONY: install
install: _require-root _check-src
	@echo ""
	@echo "===================================================="
	@echo "  IBLP - Full Installation"
	@echo "===================================================="
	@$(MAKE) --no-print-directory _step_deps
	@$(MAKE) --no-print-directory _step_venv
	@$(MAKE) --no-print-directory _step_dirs
	@$(MAKE) --no-print-directory _step_deploy
	@$(MAKE) --no-print-directory _step_pip
	@$(MAKE) --no-print-directory _step_db
	@$(MAKE) --no-print-directory _step_permissions
	@$(MAKE) --no-print-directory _step_apache
	@echo ""
	@echo "===================================================="
	@echo "  Installation complete."
	@echo "  Visit: http://localhost/iblp/"
	@echo "===================================================="
	@echo ""

# -- Individual install steps (called by install) -------------

.PHONY: _step_deps
_step_deps:
	@echo ""
	@echo "[1/8] Installing system packages (Apache, MySQL, PHP, Python 3.12) ..."
	@echo "      This may take a few minutes on a fresh system."
	@echo "----------------------------------------------------"
	@apt-get update -qq || true
	@DEBIAN_FRONTEND=noninteractive apt-get install -y \
		apache2 \
		mysql-server \
		php \
		php-mysql \
		php-json \
		php-mbstring \
		libapache2-mod-php \
		python3.12 \
		python3.12-venv \
		python3.12-dev \
		python3-pip \
		ffmpeg \
		libsndfile1 \
		build-essential \
		2>&1 | grep -E "^(Get|Unpacking|Setting up|Processing)" || true
	@a2enmod rewrite headers -q
	@systemctl enable apache2 mysql --quiet
	@systemctl start  apache2 mysql
	@echo "      System packages installed."

.PHONY: _step_venv
_step_venv:
	@echo ""
	@echo "[2/8] Creating Python virtual environment at $(VENV_DIR) ..."
	@echo "----------------------------------------------------"
	@mkdir -p /opt/iblp
	@if [ ! -f $(PYTHON_BIN) ]; then \
		python3.12 -m venv $(VENV_DIR); \
		echo "      Virtual environment created."; \
	else \
		echo "      Virtual environment already exists, skipping."; \
	fi
	@chown -R root:$(WEB_GROUP) $(VENV_DIR)
	@chmod -R 775 $(VENV_DIR)

.PHONY: _step_dirs
_step_dirs:
	@echo ""
	@echo "[3/8] Creating deployment directories ..."
	@echo "----------------------------------------------------"
	@mkdir -p \
		$(DEPLOY_DIR)         \
		$(TMP_DIR)            \
		$(MODELS_DIR)         \
		$(RECORDINGS)         \
		$(IMAGES_DIR)/animals \
		$(API_DIR)            \
		$(CONFIG_DIR)         \
		$(CSS_DIR)            \
		$(JS_DIR)             \
		$(WHISPER_DIR)
	@echo "      $(DEPLOY_DIR)"
	@echo "      $(TMP_DIR)"
	@echo "      $(MODELS_DIR)"
	@echo "      $(RECORDINGS)"
	@echo "      $(IMAGES_DIR)/animals"
	@echo "      $(WHISPER_DIR)"
	@echo "      Directories ready."

.PHONY: _step_deploy
_step_deploy:
	@echo ""
	@echo "[4/8] Deploying source files to $(DEPLOY_DIR) ..."
	@echo "----------------------------------------------------"
	@echo "      Copying PHP files ..."
	@cp -r $(SRC_DIR)/*.php          $(DEPLOY_DIR)/
	@echo "      Copying Python scripts ..."
	@cp -r $(SRC_DIR)/*.py           $(DEPLOY_DIR)/
	@echo "      Copying HTML pages ..."
	@for f in $(SRC_DIR)/*.html; do [ -f "$$f" ] && cp -v "$$f" $(DEPLOY_DIR)/ || true; done
	@echo "      Copying API layer ..."
	@cp -r $(SRC_DIR)/api/           $(DEPLOY_DIR)/
	@echo "      Copying config ..."
	@cp -r $(SRC_DIR)/config/        $(DEPLOY_DIR)/
	@echo "      Copying CSS ..."
	@cp -r $(SRC_DIR)/css/           $(DEPLOY_DIR)/
	@echo "      Copying JS ..."
	@cp -r $(SRC_DIR)/js/            $(DEPLOY_DIR)/
	@echo "      Copying images ..."
	@cp -r $(SRC_DIR)/images/        $(DEPLOY_DIR)/
	@echo "      Copying recordings ..."
	@cp -r $(SRC_DIR)/recordings/    $(DEPLOY_DIR)/
	@echo "      Copying ML models ..."
	@cp -r $(SRC_DIR)/models/        $(DEPLOY_DIR)/
	@echo "      Copying Whisper cache ..."
	@[ -d $(SRC_DIR)/whisper_cache ] && cp -r $(SRC_DIR)/whisper_cache/ $(DEPLOY_DIR)/ || true
	@echo "      All files deployed."

.PHONY: _step_pip
_step_pip:
	@echo ""
	@echo "[5/8] Installing Python packages into $(VENV_DIR) ..."
	@echo "      (librosa, numpy, tensorflow, whisper, soundfile, matplotlib)"
	@echo "----------------------------------------------------"
	@$(PIP_BIN) install --timeout 120 --retries 5 \
		librosa \
		matplotlib \
		numpy \
		tensorflow \
		openai-whisper \
		soundfile
	@echo "      Downloading Whisper base model (~145MB) ..."
	@$(PYTHON_BIN) -c "import whisper; whisper.load_model('base', download_root='/var/www/html/iblp/whisper_cache')"
	@echo "      Whisper model ready."

.PHONY: _step_db
_step_db:
	@echo ""
	@echo "[6/8] Setting up database '$(DB_NAME)' ..."
	@echo "----------------------------------------------------"
	@echo "      Creating database ..."
	@$(MYSQL_ROOT) -e \
		"CREATE DATABASE IF NOT EXISTS \`$(DB_NAME)\` \
		 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
	@echo "      Creating application user '$(DB_APP_USER)' ..."
	@$(MYSQL_ROOT) -e \
		"CREATE USER IF NOT EXISTS '$(DB_APP_USER)'@'localhost' IDENTIFIED BY '$(DB_APP_PASS)';"
	@$(MYSQL_ROOT) -e \
		"GRANT ALL PRIVILEGES ON \`$(DB_NAME)\`.* TO '$(DB_APP_USER)'@'localhost';"
	@$(MYSQL_ROOT) -e "FLUSH PRIVILEGES;"
	@echo "      Running schema ..."
	@$(MYSQL_ROOT) $(DB_NAME) < $(SRC_DIR)/config/schema.sql
	@echo "      Patching db.php credentials ..."
	@sed -i "s/define('DB_USER', .*)/define('DB_USER', '$(DB_APP_USER)');/" \
		$(DEPLOY_DIR)/config/db.php
	@sed -i "s/define('DB_PASS', .*)/define('DB_PASS', '$(DB_APP_PASS)');/" \
		$(DEPLOY_DIR)/config/db.php
	@echo "      Database ready. User: $(DB_APP_USER) | DB: $(DB_NAME)"

.PHONY: _step_permissions
_step_permissions:
	@echo ""
	@echo "[7/8] Setting file permissions ..."
	@echo "----------------------------------------------------"
	@chown -R $(WEB_USER):$(WEB_GROUP) $(DEPLOY_DIR)
	@find $(DEPLOY_DIR) -type d -exec chmod 755 {} \;
	@find $(DEPLOY_DIR) -type f -exec chmod 644 {} \;
	@chmod 755 $(DEPLOY_DIR)/asr_predict.py \
	           $(DEPLOY_DIR)/asr_predict_animals.py \
	           $(DEPLOY_DIR)/asr_predict_colours.py \
	           $(DEPLOY_DIR)/asr_predict_english.py
	@chmod 775 $(TMP_DIR)
	@chmod -R 755 $(RECORDINGS)
	@chmod -R 644 $(MODELS_DIR)
	@chmod 755 $(MODELS_DIR)
	@chmod -R 775 $(WHISPER_DIR)
	@echo "      Ownership: $(WEB_USER):$(WEB_GROUP)"
	@echo "      Directories: 755, Files: 644"
	@echo "      Python scripts: 755, tmp/: 775"

.PHONY: _step_apache
_step_apache:
	@echo ""
	@echo "[8/8] Reloading Apache ..."
	@echo "----------------------------------------------------"
	@systemctl reload apache2
	@echo "      Apache reloaded."

# -------------------------------------------------------------
#  STANDALONE TARGETS (for day-to-day use)
# -------------------------------------------------------------

.PHONY: deps
deps: _require-root
	@$(MAKE) --no-print-directory _step_deps

.PHONY: venv
venv: _require-root
	@$(MAKE) --no-print-directory _step_venv

.PHONY: deploy
deploy: _require-root _check-src _make-dirs
	@$(MAKE) --no-print-directory _step_deploy

.PHONY: pip-deps
pip-deps: _check-venv
	@$(MAKE) --no-print-directory _step_pip

.PHONY: db-init
db-init:
	@$(MAKE) --no-print-directory _step_db

.PHONY: permissions
permissions: _require-root
	@$(MAKE) --no-print-directory _step_permissions

.PHONY: _make-dirs
_make-dirs:
	@$(MAKE) --no-print-directory _step_dirs

# -------------------------------------------------------------
#  DATABASE RESET
# -------------------------------------------------------------
.PHONY: db-reset
db-reset: _require-root
	@echo "WARNING: This will DROP and recreate '$(DB_NAME)'. Press Ctrl-C to cancel ..."
	@sleep 4
	@$(MYSQL_ROOT) -e "DROP DATABASE IF EXISTS \`$(DB_NAME)\`;"
	@$(MAKE) --no-print-directory _step_db
	@echo "Database reset complete."

# -------------------------------------------------------------
#  SMOKE TESTS
# -------------------------------------------------------------
.PHONY: check
check:
	@echo ""
	@echo "===================================================="
	@echo "  IBLP - System Check"
	@echo "===================================================="

	@echo ""
	@echo "-- System packages ---------------------------------"
	@apache2 -v 2>/dev/null | head -1 \
		|| echo "  MISSING: Apache - run: sudo make deps"
	@mysql --version 2>/dev/null \
		|| echo "  MISSING: MySQL - run: sudo make deps"
	@php --version 2>/dev/null | head -1 \
		|| echo "  MISSING: PHP - run: sudo make deps"
	@python3.12 --version 2>/dev/null \
		|| echo "  MISSING: Python 3.12 - run: sudo make deps"
	@ffmpeg -version 2>/dev/null | head -1 \
		|| echo "  MISSING: ffmpeg - run: sudo make deps"

	@echo ""
	@echo "-- Virtual environment -----------------------------"
	@[ -d $(VENV_DIR) ] \
		&& echo "  $(VENV_DIR) ... exists" \
		|| echo "  MISSING: venv - run: sudo make install"

	@echo ""
	@echo "-- Python packages ---------------------------------"
	@$(PYTHON_BIN) -c "\
		import librosa, matplotlib, numpy, tensorflow; \
		print('  librosa, matplotlib, numpy, tensorflow ... OK')" 2>/dev/null \
		|| echo "  MISSING: packages - run: sudo make pip-deps"
	@$(PYTHON_BIN) -c "\
		import whisper; print('  whisper ... OK')" 2>/dev/null \
		|| echo "  MISSING: whisper - run: sudo make pip-deps"

	@echo ""
	@echo "-- PHP syntax --------------------------------------"
	@for f in $(DEPLOY_DIR)/*.php $(DEPLOY_DIR)/api/*.php $(DEPLOY_DIR)/config/*.php; do \
		[ -f $$f ] && php -l $$f | grep -v "^No syntax errors" || true; \
	done
	@echo "  PHP syntax OK"

	@echo ""
	@echo "-- Apache ------------------------------------------"
	@apachectl configtest 2>&1 | grep -E "Syntax|Error"

	@echo ""
	@echo "-- MySQL -------------------------------------------"
	@$(MYSQL_APP) -e "SELECT 'MySQL connection OK' AS status;" 2>/dev/null \
		|| echo "  FAILED: Cannot connect to MySQL - check DB_APP_USER/DB_APP_PASS in Makefile"

	@echo ""
	@echo "-- Deploy directory --------------------------------"
	@[ -d $(DEPLOY_DIR) ]  && echo "  $(DEPLOY_DIR) ... OK"  || echo "  MISSING: $(DEPLOY_DIR)"
	@[ -d $(TMP_DIR) ]     && echo "  tmp/ ... OK"           || echo "  MISSING: tmp/"
	@[ -d $(MODELS_DIR) ]  && echo "  models/ ... OK"        || echo "  MISSING: models/"
	@[ -d $(RECORDINGS) ]  && echo "  recordings/ ... OK"    || echo "  MISSING: recordings/"
	@[ -d $(WHISPER_DIR) ] && echo "  whisper_cache/ ... OK" || echo "  MISSING: whisper_cache/"

	@echo ""
	@echo "===================================================="
	@echo "  Check complete."
	@echo "===================================================="
	@echo ""

# -------------------------------------------------------------
#  CLEAN TMP
# -------------------------------------------------------------
.PHONY: clean-tmp
clean-tmp: _require-root
	@echo "-> Removing leftover tmp files ..."
	@find $(TMP_DIR) -type f \
		\( -name "*.wav" -o -name "*.jpg" -o -name "*.nbc" -o -name "*.nbi" \) \
		-delete
	@echo "   tmp/ cleaned."

# -------------------------------------------------------------
#  APACHE
# -------------------------------------------------------------
.PHONY: reload
reload: _require-root
	@echo "-> Reloading Apache ..."
	@systemctl reload apache2
	@echo "   Apache reloaded."

.PHONY: restart
restart: _require-root
	@echo "-> Restarting Apache ..."
	@systemctl restart apache2
	@echo "   Apache restarted."

# -------------------------------------------------------------
#  LOGS
# -------------------------------------------------------------
.PHONY: logs
logs:
	@tail -f /var/log/apache2/error.log

.PHONY: logs-access
logs-access:
	@tail -f /var/log/apache2/access.log

# -------------------------------------------------------------
#  UNINSTALL
# -------------------------------------------------------------
.PHONY: uninstall
uninstall: _require-root
	@echo "WARNING: This will remove $(DEPLOY_DIR) and $(VENV_DIR). Press Ctrl-C to cancel ..."
	@sleep 4
	@rm -rf $(DEPLOY_DIR)
	@rm -rf /opt/iblp
	@echo "Removed $(DEPLOY_DIR) and /opt/iblp."

# -------------------------------------------------------------
#  INTERNAL GUARDS
# -------------------------------------------------------------
.PHONY: _require-root
_require-root:
	@[ "$$(id -u)" -eq 0 ] || \
		{ echo "ERROR: Run with sudo: sudo make $(MAKECMDGOALS)"; exit 1; }

.PHONY: _check-src
_check-src:
	@[ -d $(SRC_DIR) ] || \
		{ echo "ERROR: Source folder '$(SRC_DIR)/' not found."; \
		  echo "       Run make from the folder that contains the iblp/ directory."; \
		  exit 1; }

.PHONY: _check-venv
_check-venv:
	@[ -f $(PYTHON_BIN) ] || \
		{ echo "ERROR: Virtual environment not found at $(VENV_DIR)."; \
		  echo "       Run: sudo make install"; \
		  exit 1; }
