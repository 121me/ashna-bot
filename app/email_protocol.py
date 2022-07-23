import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ashna_secrets import SENDER, PASSWORD


# send emails to users
# the receiver is the email address of the user, take it as a parameter
# the subject is "Ashna Bot - Verification code"
# the body is a message with the verification code


def send_email(receiver: str, code: str):
	msg = MIMEMultipart()
	msg['From'] = "Ashna Bot"
	msg['Subject'] = "Verification code"
	msg['To'] = receiver
	body = f"Your verification code is: {code}"
	msg.attach(MIMEText(body, 'plain'))
	with smtplib.SMTP('smtp.gmail.com', 587) as server:
		server.starttls()
		server.login(SENDER, PASSWORD)
		text = msg.as_string()
		server.sendmail(SENDER, receiver, text)


def main():
	for i in range(5):
		send_email("testme@domain.com", ''.join(random.choices(string.digits, k=6)))


if __name__ == "__main__":
	main()

pass
