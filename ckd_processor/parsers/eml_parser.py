"""
Email Document Parser (.eml, .msg) extracting headers and body text.
"""

import email
from email import policy
import os
from typing import List

from ckd_processor.parsers.base import BaseParser, ParsedDocument, PageContent
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("EMLParser")


class EMLParser(BaseParser):
    def supported_extensions(self) -> List[str]:
        return ["eml", "msg"]

    def parse(self, filepath: str) -> ParsedDocument:
        filename = os.path.basename(filepath)
        headers = {}
        body = ""

        try:
            with open(filepath, "rb") as f:
                msg = email.message_from_binary_file(f, policy=policy.default)

            headers = {
                "Subject": msg.get("Subject", ""),
                "From": msg.get("From", ""),
                "To": msg.get("To", ""),
                "Date": msg.get("Date", "")
            }

            body_parts = []
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body_parts.append(part.get_content())
                    elif content_type == "text/html" and not body_parts:
                        # Fallback html body if no plain text
                        body_parts.append(part.get_content())
            else:
                body_parts.append(msg.get_content())

            body = "\n\n".join(body_parts)

        except Exception as e:
            logger.error(f"Error parsing EML file {filename}: {e}")
            body = f"[EML Parse Error: {e}]"

        formatted_text = f"""# Email: {headers.get('Subject', filename)}

- **From:** {headers.get('From', 'N/A')}
- **To:** {headers.get('To', 'N/A')}
- **Date:** {headers.get('Date', 'N/A')}

---

{body}
"""
        page = PageContent(page_number=1, text=formatted_text)
        return ParsedDocument(
            filepath=filepath,
            filename=filename,
            extension=filepath.split(".")[-1].lower(),
            pages=[page],
            full_raw_text=formatted_text,
            raw_metadata=headers
        )
