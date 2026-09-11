from __future__ import annotations

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


DEFAULT_RECIPIENTS = ["felipe@nex.work", "bruna@nexcoworking.com.br"]


def send_report_email(html_content: str, period_label: str) -> None:
    sender = os.environ["GMAIL_SENDER_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipients_env = os.environ.get("REPORT_RECIPIENTS")
    recipients = [r.strip() for r in recipients_env.split(",")] if recipients_env else DEFAULT_RECIPIENTS

    msg = MIMEMultipart()
    msg["Subject"] = f"Relatório Semanal Nex — {period_label}"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText("Segue em anexo o relatório semanal de performance comercial.", "plain"))

    attachment = MIMEApplication(html_content.encode("utf-8"), _subtype="html")
    attachment.add_header("Content-Disposition", "attachment", filename="relatorio-semanal-nex.html")
    msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, recipients, msg.as_string())
