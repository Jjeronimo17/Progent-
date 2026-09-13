import mysql.connector
from mysql.connector import Error
import random
import string


def generarSalt():
    longitud = 15
    salt = "".join(random.choices(string.ascii_letters + string.digits, k=15))
    print(salt)
