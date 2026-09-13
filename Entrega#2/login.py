import mysql.connector
from mysql.connector import Error
import random
import string


usuario = ""
password = ""


def generarSalt():
    longitud = 15
    salt = "".join(random.choices(string.ascii_letters + string.digits, k=15))
    return salt


def hashing(password):
    password = input()
    salt = generarSalt()
    mitadSalt = len(salt) // 2
    primeraMitadSalt = salt[: mitadSalt + 1]
    segundaMitadSalt = salt[mitadSalt + 1 :]

    mitadPass = len(password) // 2
    primeraMitadPass = password[: mitadPass + 1]
    segundaMitadPass = password[mitadPass + 1 :]
    passwordcomplete = (
        primeraMitadPass + primeraMitadSalt + segundaMitadPass + segundaMitadSalt
    )
    passwordHashed = hash(passwordcomplete)
    return passwordHashed
