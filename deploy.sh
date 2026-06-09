#!/bin/bash
# ============================================
# 🦞 deploy.sh — Despliega ClawTrader
# ============================================
# Uso: bash deploy.sh [es|en]
# Copia tools y skills al workspace de OpenClaw
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$HOME/.openclaw/workspace"

# Banner
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║      🦞 ClawTrader — Deploy               ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# Idioma
LANG="${1:-es}"
if [ "$LANG" != "es" ] && [ "$LANG" != "en" ]; then
    echo "⚠️  Idioma no válido: $LANG"
    echo "   Usa: bash deploy.sh es  (español, por defecto)"
    echo "   Usa: bash deploy.sh en  (inglés)"
    exit 1
fi

echo "🌐 Idioma: $([ "$LANG" = "es" ] && echo "Español" || echo "English")"
echo ""

# ─── Copiar tools ───
echo "📁 Copiando tools..."
TOOLS_SRC="$SCRIPT_DIR/tools"
TOOLS_DST="$WORKSPACE/tools"

mkdir -p "$TOOLS_DST"
cp -v "$TOOLS_SRC"/*.py "$TOOLS_DST/" 2>/dev/null || true
echo "   ✅ Tools copiadas a $TOOLS_DST"
echo ""

# ─── Copiar skills según idioma ───
echo "📁 Copiando skills ($LANG)..."
SKILLS_SRC="$SCRIPT_DIR/skills/$LANG"
SKILLS_DST="$HOME/.openclaw/skills"

mkdir -p "$SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
    skill_name=$(basename "$skill_dir")
    if [ -d "$skill_dir" ]; then
        mkdir -p "$SKILLS_DST/$skill_name"
        cp -rv "$skill_dir"/* "$SKILLS_DST/$skill_name/"
        echo "   ✅ Skill copiada: $skill_name"
    fi
done

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║   ✅ Despliegue completo ($LANG)             ║"
echo "╚═══════════════════════════════════════════╝"
echo ""
echo "📌 Próximo paso: Ejecuta 'openclaw' para iniciar"
exit 0
