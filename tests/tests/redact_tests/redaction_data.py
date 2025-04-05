# Test data
INVOICE_TEXT = """
Invoice To:
Joe Ferrara
1234 Main St.
San Francisco CA 94107
Invoice Number: 001256
Invoice Date: March 27, 2024
Due Date: May 15, 2024
Amount Due: $12,000
"""

NAMES_TEXT = """The IP 192.168.123.132 has breached our firewall. The machine is registered to a man named Luke McFee, a US Citizen in Japan. This is a clear violation of The Computer Fraud and Abuse Act."""

SPELLING_TEXT = """Agent:
Yeah. Could you spell your first and last name for me again you say it.

Customer:
Sure. Last name is L-O-U-N-G-A-N-I-L-O-U-N-L for Larry. L for Larry, o for Orange. U for Umbrella. N for Nancy. G for God. A for Andy. N for Nancy and I for Indiana. Longani.
"""

XML_SAMPLE = [
    """<person age="22">Jim Doe</person>""",
    """<?xml version="1.0" encoding="UTF-8"?>
    <!-- This XML document contains sample PII with namespaces and attributes -->
    <PersonInfo xmlns="http://www.example.com/default" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:contact="http://www.example.com/contact">
        <!-- Personal Information with an attribute containing PII -->
        <Name preferred="true" contact:userID="uid123">
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>
        </Name>

        <contact:Details>
            <!-- Email stored in an attribute for demonstration -->
            <contact:Email address="john.doe@example.com"/>
            <contact:Phone type="mobile" number="555-6789"/>
        </contact:Details>

        <!-- SSN stored as an attribute -->
        <SSN value="187-65-4321" xsi:nil="false"/>
        <data>his name was John Doe</data>
    </PersonInfo>""",
]

HTML_SAMPLE = """<html>
 <head>
     <title>John Doe</title>
 </head>
 <body>
     <h1>Personal Information</h1>
     <p>My name is Jo<span>hn</span> Doe and I am 22 years old.</p>
     <p>My email address is <a href="mailto:johndoe@example.com">johndoe@example.com</a>.</p>
     <p>My phone number is (123) 456-7890.</p>
 </body>
</html>"""

DICT_SAMPLE = {
    "person": {"first": "John", "last": "Johnson"},
    "address": {
        "city": "Memphis",
        "state": "TN",
        "street": "847 Rocky Top",
        "zip": 1234,
    },
    "description": (
        "John is a man that lives in Memphis. He is 37 years old and is married to Cynthia"
    ),
}
