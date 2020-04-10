from enum import Enum
from utils import get_db

class Permissions(Enum):
    admin = 0
    member = 1

def bit_on(perm, i):
    return perm & (1 << i) != 0

def has(user, permission):
    return bit_on(user.permissions, permission.value)

def can_say(user):
    return has(user, Permissions.member)

def can_play(user):
    return has(user, Permissions.admin)

def can_create_category(user):
    return has(user, Permissions.admin)

def can_transact(user):
    return has(user, Permissions.member)

def can_edit_protected_category(user):
    return has(user, Permissions.admin)

def get_members():
    return [{"id": x["id"], "displayname": x["displayname"]} for x in get_db()["users"].find(permissions={">": 0})]
