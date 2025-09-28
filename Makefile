wuv=/mnt/c/Users/katao/.local/bin/uv.exe
project_name=sdvx_arena
target=$(project_name)/$(project_name).exe
target_zip=$(project_name).zip
srcs=$(subst update.py,,$(wildcard *.py)) $(wildcard *.pyw)
html_files=$(wildcard *.html)

# バージョンを自動取得（Gitタグから）
GIT_VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "0.0.0-dev")
# v. または v を除去して、リリース版かどうかを判定
VERSION_RAW := $(shell echo $(GIT_VERSION) | sed 's/^v\.//' | sed 's/^v//')

# リリース版（正確にタグと一致）かどうかを判定
IS_RELEASE := $(shell echo $(VERSION_RAW) | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null && echo "true" || echo "false")

# リリース版の場合はクリーンなバージョン、開発版の場合は詳細バージョン
ifeq ($(IS_RELEASE),true)
    VERSION_CLEAN := $(VERSION_RAW)
else
    VERSION_CLEAN := $(VERSION_RAW)
endif

all: $(target_zip)

$(target_zip): $(target) resources $(project_name)/update.exe
	@mkdir -p $(project_name)
	@rm -rf $(project_name)/log
	@cp -a resources $(project_name)
	@zip $(target_zip) $(project_name)/*

# バージョンファイルを自動生成
version.py: .git/refs/tags/* .git/HEAD
	@echo "# Auto-generated version file" > version.py
	@echo "__version__ = '$(VERSION_CLEAN)'" >> version.py
	@echo "Generated version.py with version: $(VERSION_CLEAN)"

$(project_name)/update.exe: update.py
	@$(wuv) run pyinstaller update.py --distpath="./$(project_name)" --clean --windowed --onefile --icon="assets/icon.ico" --add-data "assets/icon.ico;assets"

$(target): $(srcs) version.py
	@$(wuv) run pyinstaller $(project_name).pyw --distpath="./$(project_name)" --clean --windowed --onefile --icon="assets/icon.ico" --add-data "assets/icon.ico;assets"

clean:
	@rm -rf $(target)
	@rm -rf $(project_name)/update.exe
	@rm -rf __pycache__
	@rm -rf pyarmor*log
	@rm -rf .pyarmor
	@rm -f version.py

test: version.py
	@$(wuv) run python $(project_name).pyw

.PHONY: all clean test