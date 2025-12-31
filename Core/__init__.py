from datetime import datetime

from fastapi import Request

from Core.security import Password,AccessToken
from Core.file import Files
from Model import Loans


def flash_context(request: Request):
    msg = request.session.pop("flush", None)
    request.session["flush"] = None
    return {
        "flush": msg
    }

def remin_day(loan:Loans)-> int:
    return (loan.deadline_date -  datetime.now()).days
