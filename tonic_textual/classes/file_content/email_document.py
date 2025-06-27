from typing import Dict, List
from tonic_textual.classes.file_content.base_document import BaseDocument
from tonic_textual.classes.file_content.content import Content
from tonic_textual.classes.httpclient import HttpClient
from datetime import datetime

class EmailDocument(BaseDocument):
    def __init__(self, client: HttpClient, json_def):
        super().__init__(client, json_def)
        self.sent_date: datetime | None = json_def.get("sentDate", None)        
        self.message_id: str | None = json_def.get("messageId", None)
        self.in_reply_to_message_id: str | None = json_def.get("in_reply_to_message_id", None)
        self.message_id_references: List[str] = json_def.get("message_id_references", [])
        self.sender_address: EmailAddress = EmailAddress(json_def.get("senderAddress"))
        self.to_addresses: List[EmailAddress] = [EmailAddress(json_add) for json_add in json_def.get("toAddresses", [])]
        self.cc_addresses: List[EmailAddress] = [EmailAddress(json_add) for json_add in json_def.get("ccAddresses", [])]
        self.bcc_addresses: List[EmailAddress] = [EmailAddress(json_add) for json_add in json_def.get("bccAddresses", [])]
        self.subject = Content(client, json_def.get("subject", ""))

        self.plain_text_body_content: Content = Content(client, json_def.get("plainTextBodyContent", ""))

class EmailAddress:
    def __init__(self, json_email_address: Dict):
        self.address: str = json_email_address.get("address")
        self.display_name: str | None = json_email_address.get("displayName", None)
        self.group_name: str | None = json_email_address.get("group_name", None)