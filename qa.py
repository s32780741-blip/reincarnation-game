"""QA — self-check untuk memastikan game state konsisten."""
import database as db


def check_character_integrity(character_id):
    """Return list of issues."""
    issues = []
    char = db.get_character(character_id)
    if not char:
        return ["Karakter tidak ditemukan"]

    # Negative checks
    if char["silver"] < 0: issues.append("Silver negatif")
    if char["gold"] < 0: issues.append("Gold negatif")
    if char["zambrut"] < 0: issues.append("Zambrut negatif")
    if char["level"] < 0: issues.append("Level negatif")
    if char["hp_current"] < 0: issues.append("HP negatif")
    if char["mp_current"] < 0: issues.append("MP negatif")
    if char["attr_points"] < 0: issues.append("Attribute points negatif")

    stats = db.get_stats(character_id)
    if stats:
        for k, v in stats.items():
            if k == "character_id": continue
            if isinstance(v, int) and v < 0:
                issues.append(f"Stat {k} negatif ({v})")

    # Orphan checks
    inv = db.get_inventory(character_id)
    if len(inv) > 500:
        issues.append(f"Inventory terlalu banyak ({len(inv)})")

    return issues


def check_database_integrity():
    """Cek konsistensi database level global."""
    issues = []
    c = db.conn()
    # Foreign key check
    try:
        fk = c.execute("PRAGMA foreign_key_check").fetchall()
        for row in fk:
            issues.append(f"FK violation: {dict(row)}")
    except Exception:
        pass
    return issues


def full_check(character_id):
    issues = []
    issues += check_character_integrity(character_id)
    issues += check_database_integrity()
    return issues


def report(character_id):
    """Tampilkan report."""
    from ui import C, color, box, pause, clear
    clear()
    issues = full_check(character_id)
    if not issues:
        print(box("QA REPORT", [
            color(" ✓ Tidak ada masalah ditemukan.", C.GREEN),
            "",
            " Karakter & database konsisten.",
        ]))
    else:
        lines = [color(f" {len(issues)} masalah ditemukan:", C.RED + C.BOLD), ""]
        for i in issues[:20]:
            lines.append(f"  • {i}")
        print(box("QA REPORT", lines))
    pause()


def quick_heal(character_id):
    """Perbaiki nilai negatif."""
    char = db.get_character(character_id)
    if not char:
        return
    fixes = {}
    if char["silver"] < 0: fixes["silver"] = 0
    if char["gold"] < 0: fixes["gold"] = 0
    if char["zambrut"] < 0: fixes["zambrut"] = 0
    if char["level"] < 1: fixes["level"] = 1
    if char["hp_current"] < 0: fixes["hp_current"] = 1
    if char["mp_current"] < 0: fixes["mp_current"] = 0
    if char["attr_points"] < 0: fixes["attr_points"] = 0
    if fixes:
        db.update_character(character_id, **fixes)

    stats = db.get_stats(character_id)
    if stats:
        sfix = {}
        for k, v in stats.items():
            if k == "character_id": continue
            if isinstance(v, int) and v < 0:
                sfix[k] = 0
        if sfix:
            db.update_stats(character_id, **sfix)

    return fixes
