import json, requests, logging
from datetime import datetime

class MailgunApi(object):
    """
    Allows to send emails via the mailgun API.
    """

    def __init__(self, mailgun_domain, mailgun_key):
        self.mailgun_domain = mailgun_domain
        self.mailgun_key = mailgun_key


    def send_simple_message(self, recipients, subject, text):

        return requests.post(
            f"https://api.eu.mailgun.net/v3/{mailgun_domain}/messages",
            auth=("api", mailgun_key),
            data={"from": f"Notfallseelsorge Schichtplan Sipgate Adapter <schichtsystem@{mailgun_domain}>",
                "to": f"schichtsystem@{mailgun_domain}",
                "bcc": recipients,
                "subject": subject,
                "text": text})


    def send_confirmation_mail(self, recipients, text):
        time_string = datetime.strftime(datetime.now(), "%H:%M %d.%m.%y")
        return self.send_simple_message(recipients, f"Bestätigung Umstellung Telefonsystem {time_string} Uhr", text)


if __name__ == "__main__":

    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)
    mailgun_domain = config_data["mailgun"]["domain"]
    mailgun_key = config_data["mailgun"]["api_key"]
    recipients = config_data["mailgun"]["recipients"]

    mail_handler = MailgunApi(mailgun_domain, mailgun_key)

    text = "Die Telefonummern wurden erfolgreich umgestellt."
    print(mail_handler.send_confirmation_mail(recipients, text).content)
