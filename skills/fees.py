# skills/fees.py — Feature 3: clear fee & dues summary (simple wording).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def fees_summary(data, message):
    fees = data.get("fees", [])
    if not fees:
        return "No fee records found on your account."

    total = sum(f["total"] for f in fees)
    paid = sum(f["paid"] for f in fees)
    pending = total - paid

    lines = [f"**Your Fees — {data['name']}**", ""]
    lines.append("| Term | Total | Paid | Still Due |")
    lines.append("|---|---|---|---|")
    for f in fees:
        due = f["total"] - f["paid"]
        status = "Paid" if due == 0 else f"Rs {due:,}"
        lines.append(f"| {f['term']} | Rs {f['total']:,} | Rs {f['paid']:,} | {status} |")

    lines.append("")
    lines.append(f"**Total fee:** Rs {total:,}")
    lines.append(f"**You have paid:** Rs {paid:,}")
    if pending > 0:
        lines.append(f"**Still to pay:** Rs {pending:,}")
        lines.append(f"\nYou still need to pay **Rs {pending:,}**. Please pay it before the due date so no late charge is added.")
    else:
        lines.append(f"**Still to pay:** Rs 0")
        lines.append("\nAll your fees are paid. Nothing is due.")

    return "\n".join(lines)