# skills/fees.py — Feature 3: clear fee & dues summary.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def fees_summary(data, message):
    fees = data.get("fees", [])
    if not fees:
        return "No fee records found on your account."

    total = sum(f["total"] for f in fees)
    paid = sum(f["paid"] for f in fees)
    pending = total - paid

    lines = [f"**Fee & Dues Summary — {data['name']}**", ""]
    lines.append("| Term | Total | Paid | Pending |")
    lines.append("|---|---|---|---|")
    for f in fees:
        due = f["total"] - f["paid"]
        status = "Cleared" if due == 0 else f"Rs {due:,}"
        lines.append(f"| {f['term']} | Rs {f['total']:,} | Rs {f['paid']:,} | {status} |")

    lines.append("")
    lines.append(f"**Total billed:** Rs {total:,}")
    lines.append(f"**Total paid:** Rs {paid:,}")
    if pending > 0:
        lines.append(f"**Pending dues:** Rs {pending:,}")
        lines.append(f"\nYou have an outstanding balance of **Rs {pending:,}**. Please clear it before the deadline to avoid late fees.")
    else:
        lines.append(f"**Pending dues:** Rs 0")
        lines.append("\nAll your fees are cleared. You're all set.")

    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(fees_summary(data, "how much fees do I owe"))