set -e

echo "🧠 Mendeteksi sistem operasi..."
OS=""
PKG=""
SUDO="sudo"

if grep -qi microsoft /proc/version 2>/dev/null; then
    OS="WSL (Windows Subsystem for Linux)"
    if command -v apt >/dev/null 2>&1; then
        PKG="apt"
    elif command -v pacman >/dev/null 2>&1; then
        PKG="pacman"
    fi
fi

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

if [ "$OS" = "Unknown" ]; then
    if command -v php >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1; then
        echo "✅ PHP atau Python sudah terinstal di sistem."
        php -v 2>/dev/null || true
        python3 --version 2>/dev/null || true
        exit 0
    else
        echo "❌ Tidak dapat mendeteksi OS dan tidak ada PHP/Python terinstal."
        exit 1
    fi
fi

if [ "$PKG" = "pkg" ]; then
    SUDO=""
fi

echo ""
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
esac

echo ""
echo "⚙️ Menginstal Python..."
case "$PKG" in
    apt)
        $SUDO apt install -y python3 python3-pip
        ;;
    pacman)
        $SUDO pacman -Sy --noconfirm python python-pip
        ;;
    dnf)
        $SUDO dnf install -y python3 python3-pip
        ;;
    apk)
        $SUDO apk add python3 py3-pip
        ;;
    pkg)
        pkg install -y python
        ;;
    brew)
        brew install python
        ;;
esac

echo ""
echo "✅ Instalasi selesai!"
echo "📜 Versi terinstal:"
php -v || echo "⚠️ PHP gagal dijalankan."
python3 --version || echo "⚠️ Python gagal dijalankan."
