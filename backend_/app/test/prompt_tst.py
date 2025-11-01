from ..services.imap_service import classify_application_email
import mailparser

raw_email = {
        b'RFC822': b'Return-Path: <john.doe@example.com>\r\n'
                   b'Received: from laptop (192.0.2.15)\r\n'
                   b'        by smtp.example.com with ESMTPSA id ABC123\r\n'
                   b'        for <hr@company.org>; Sat, 18 Oct 2025 09:46:53 +0000 (UTC)\r\n'
                   b'Subject: Internship Application \xe2\x80\x93 Software Developer\r\n'
                   b'From: John Doe <john.doe@example.com>\r\n'
                   b'To: HR Department <hr@company.org>\r\n'
                   b'Date: Sat, 18 Oct 2025 09:46:53 +0000\r\n'
                   b'Message-ID: <internship-2025@example.com>\r\n'
                   b'MIME-Version: 1.0\r\n'
                   b'Content-Type: multipart/mixed; boundary="000000000000a2b3cd05"\r\n'
                   b'\r\n'
                   b'--000000000000a2b3cd05\r\n'
                   b'Content-Type: text/plain; charset="UTF-8"\r\n'
                   b'Content-Transfer-Encoding: 7bit\r\n'
                   b'\r\n'
                   b'Dear HR Team,\r\n'
                   b'\r\n'
                   b'I am writing to apply for the Software Development Internship at your company.\r\n'
                   b'I am a third-year Computer Science student with experience in Python, Java,\r\n'
                   b'and web technologies. I am particularly interested in your recent projects\r\n'
                   b'involving AI-driven analytics.\r\n'
                   b'\r\n'
                   b'Please find attached my resume for your consideration.\r\n'
                   b'I would be delighted to discuss how I can contribute to your team.\r\n'
                   b'\r\n'
                   b'Thank you for your time and consideration.\r\n'
                   b'\r\n'
                   b'Best regards,\r\n'
                   b'John Doe\r\n'
                   b'john.doe@example.com\r\n'
                   b'+1 555-123-4567\r\n'
                   b'\r\n'
                   b'--000000000000a2b3cd05\r\n'
                   b'Content-Type: application/pdf; name="John_Doe_Resume.pdf"\r\n'
                   b'Content-Transfer-Encoding: base64\r\n'
                   b'Content-Disposition: attachment; filename="John_Doe_Resume.pdf"\r\n'
                   b'\r\n'
                   b'JVBERi0xLjQKJcfsj6IKMSAwIG9iago8PC9UeXBlIC9DYXRhbG9nIC9QYWdlcyAyIDAgUgo+PgplbmRvYmoK...\r\n'
                   b'--000000000000a2b3cd05--\r\n'
    }

parsed_mail = mailparser.parse_from_bytes(raw_email[b'RFC822'])

print(parsed_mail, flush=True)



async def prmpt_test():
    res = await classify_application_email(parsed_mail)
    return res