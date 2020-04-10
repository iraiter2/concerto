from flask import Blueprint, Response, abort, redirect, render_template, request
from flask_login import login_required, login_user, logout_user
from urllib.parse import urlparse, urljoin
from utils import get_db, get_user
import hashlib
import os
import base64

app = Blueprint('dashboard', __name__, template_folder='templates', static_folder='assets')
