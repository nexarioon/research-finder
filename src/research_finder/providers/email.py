from __future__ import annotations

from abc import ABC, abstractmethod

logger = __import__("logging").getname(__name__)


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
    ) -> bool:
        """Send an email. Returns True if successful."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the email provider is configured."""
        ...


class SMTPProvider(EmailProvider):
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        from_email: str | None = None,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_email = from_email or username

    async def is_available(self) -> bool:
        return bool(self.smtp_host and self.username and self.password)

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
    ) -> bool:
        import smtplib
        from email.mime.text import MIMEText

        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = from_email or self.from_email
            msg["To"] = to

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info("Email sent to %s", to)
            return True
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)
            return False


class ConsoleEmailProvider(EmailProvider):
    """Prints emails to console for testing. Does not actually send."""

    async def is_available(self) -> bool:
        return True

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
    ) -> bool:
        print(f"\n{'='*60}")
        print(f"TO: {to}")
        print(f"FROM: {from_email or 'research-finder@local'}")
        print(f"SUBJECT: {subject}")
        print(f"{'='*60}")
        print(body)
        print(f"{'='*60}\n")
        return True
