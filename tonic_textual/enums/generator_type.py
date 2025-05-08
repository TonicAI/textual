from enum import Enum


class GeneratorType(str, Enum):
    Scramble = "Scramble"
    CompanyName = "CompanyName"
    Email = "Email"
    IpAddress = "IpAddress"
    Ssn = "Ssn"
    Url = "Url"
    Name = "Name"
    HipaaAddressGenerator = "HipaaAddressGenerator"
    DateTime = "DateTime"
    NumericValue = "NumericValue"
    PhoneNumber = "PhoneNumber"
    Money = "Money"
    CcExp = "CcExp"
    Cvv = "Cvv"
    CreditCard = "CreditCard"
    MicrCode = "MicrCode"
    PersonAge = "PersonAge"