"""Email delivery via Resend. Both the client-facing report and the
practitioner-only confidential report are sent ONLY to the therapist's own
inbox - never to the client - regardless of what is entered in the form."""

import base64
import resend

THERAPIST_EMAIL = "Wijdan.psyc@gmail.com"


def _send(api_key, from_address, subject, html, attachments):
    resend.api_key = api_key
    params = {
        "from": from_address,
        "to": [THERAPIST_EMAIL],
        "subject": subject,
        "html": html,
        "attachments": attachments,
    }
    return resend.Emails.send(params)


def send_ybocs_reports(api_key, from_address, client_pdf_bytes, therapist_pdf_bytes,
                        client_name, band_label, total_score):
    safe_name = (client_name or "client").strip().replace(" ", "_") or "client"
    client_filename = f"YBOCS_Client_Report_{safe_name}.pdf"
    therapist_filename = f"YBOCS_Therapist_Confidential_{safe_name}.pdf"

    client_encoded = base64.b64encode(client_pdf_bytes).decode("utf-8")
    therapist_encoded = base64.b64encode(therapist_pdf_bytes).decode("utf-8")

    html = (
        f"<p>A new Y-BOCS assessment has been submitted"
        f"{f' for <b>{client_name}</b>' if client_name else ''}.</p>"
        f"<p><b>Total severity score:</b> {total_score}/40 — <b>{band_label}</b></p>"
        f"<p>Two PDFs are attached:</p>"
        f"<ul>"
        f"<li><b>Client Report</b> — the summary suitable to review with or hand to the client.</li>"
        f"<li><b>Therapist Confidential Report</b> — full item-level data, clinical formulation, "
        f"differential considerations, and session planning material. Not for the client.</li>"
        f"</ul>"
        f"<p style='color:#8A94A6;font-size:12px;'>Sent automatically by the Y-BOCS Clinical Assessment tool.</p>"
    )

    return _send(
        api_key, from_address,
        subject=f"[Y-BOCS] {client_name or 'Confidential Client'} — {total_score}/40 ({band_label})",
        html=html,
        attachments=[
            {"filename": client_filename, "content": client_encoded},
            {"filename": therapist_filename, "content": therapist_encoded},
        ],
    )
