#!/bin/bash
set -e

echo "🧠 Mendeteksi sistem operasi..."
OS=""
PKG=""
SUDO="sudo"

# 🧩 Deteksi WSL terlebih dahulu
if grep -qi microsoft /proc/version 2>/dev/null; then
    OS="WSL (Windows Subsystem for Linux)"
    if command -v apt >/dev/null 2>&1; then
        PKG="apt"
    elif command -v pacman >/dev/null 2>&1; then
        PKG="pacman"
    fi
fi

# 🧩 Deteksi OS umum jika bukan WSL
if [ -z "$OS" ]; then
    if command -v apt >/dev/null 2>&1; then
        OS="Debian/Ubuntu/Kali"
        PKG="apt"
    elif command -v pacman >/dev/null 2>&1; then
        OS="Arch/BlackArch/Manjaro"
        PKG="pacman"
    elif command -v dnf >/dev/null 2>&1; then
        OS="Fedora/RHEL"
        PKG="dnf"
    elif command -v apk >/dev/null 2>&1; then
        OS="Alpine"
        PKG="apk"
    elif command -v pkg >/dev/null 2>&1 && [ -d "/data/data/com.termux/files/usr" ]; then
        OS="Termux"
        PKG="pkg"
    elif command -v brew >/dev/null 2>&1; then
        OS="macOS"
        PKG="brew"
    else
        OS="Unknown"
    fi
fi

echo "📀 Sistem terdeteksi: $OS"

# 🧩 Jika OS tidak dikenali, coba cek PHP dulu
if [ "$OS" = "Unknown" ]; then
    if command -v php >/dev/null 2>&1; then
        echo "✅ PHP sudah terinstal di sistem."
        php -v
        exit 0
    else
        echo "❌ Tidak dapat mendeteksi OS dan PHP belum terinstal."
        exit 1
    fi
fi

# 🧩 Nonaktifkan sudo di Termux
if [ "$PKG" = "pkg" ]; then
    SUDO=""
fi

echo "⚙️ Menginstal PHP..."

case "$PKG" in
    apt)
        $SUDO apt update -y
        $SUDO apt install -y php php-cli php-common
        ;;
    pacman)
        $SUDO pacman -Sy --noconfirm php
        ;;
    dnf)
        $SUDO dnf install -y php php-cli php-common
        ;;
    apk)
        $SUDO apk add php php-cli
        ;;
    pkg)
        pkg update -y
        pkg install -y php
        ;;
    brew)
        brew update
        brew install php
        ;;
    *)
        echo "❌ Tidak ada package manager yang cocok."
        exit 1
        ;;
esac

echo "✅ PHP berhasil diinstal!"
php -v || echo "⚠️ PHP terinstal, tapi tidak bisa dijalankan otomatis."
