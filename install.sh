set -e

echo "🧠 Deteksi sistem operasi..."
OS=""
PKG=""

if [ -n "$(command -v apt)" ]; then
    OS="Debian/Ubuntu/Kali"
    PKG="apt"
elif [ -n "$(command -v pacman)" ]; then
    OS="Arch/BlackArch/Manjaro"
    PKG="pacman"
elif [ -n "$(command -v dnf)" ]; then
    OS="Fedora/RHEL"
    PKG="dnf"
elif [ -n "$(command -v apk)" ]; then
    OS="Alpine"
    PKG="apk"
elif [ -n "$(command -v pkg)" ]; then
    OS="Termux"
    PKG="pkg"
elif [ -n "$(command -v brew)" ]; then
    OS="macOS"
    PKG="brew"
else
    if grep -qi microsoft /proc/version 2>/dev/null; then
        OS="WSL (Windows Subsystem for Linux)"
        if [ -n "$(command -v apt)" ]; then
            PKG="apt"
        elif [ -n "$(command -v pacman)" ]; then
            PKG="pacman"
        fi
    else
        OS="Unknown"
    fi
fi

echo "📀 Sistem terdeteksi: $OS"

if [ "$OS" = "Unknown" ]; then
    echo "❌ Tidak dapat mendeteksi OS. Instalasi PHP gagal."
    exit 1
fi

echo "⚙️ Menginstal PHP..."

case "$PKG" in
    apt)
        sudo apt update -y
        sudo apt install php php-cli php-common -y
        ;;
    pacman)
        sudo pacman -Sy --noconfirm php
        ;;
    dnf)
        sudo dnf install php php-cli php-common -y
        ;;
    apk)
        sudo apk add php php-cli
        ;;
    pkg)
        pkg update -y
        pkg install php -y
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
php -v || echo "⚠️ PHP sudah diinstal tapi tidak bisa dijalankan otomatis."

