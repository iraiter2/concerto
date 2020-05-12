from enum import Enum
from utils import get_db

class Permissions(Enum):
    admin = 0
    member = 1

def bit_on(perm, i):
    return perm & (1 << i) != 0

def has(user, permission):
    return bit_on(user.permissions, permission.value)

def get_members():
    return [{"id": x["id"], "displayname": x["displayname"]} for x in get_db()["users"].find(permissions={">": 0})]
