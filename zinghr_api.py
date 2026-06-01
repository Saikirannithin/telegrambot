import requests
from config import ZINGHR_SUBSCRIPTION, ZINGHR_API_TOKEN

BASE_URL = "https://portal.zinghr.com/2015/route/"

def zinghr_headers():
    return {
        "Content-Type": "application/json",
        "SubscriptionName": ZINGHR_SUBSCRIPTION,
        "Token": ZINGHR_API_TOKEN
    }

def punch_in_out(employee_code, in_out="IN", location=""):
    """Punch In or Out"""
    url = f"{BASE_URL}SwipePushAPI"
    payload = {
        "SubscriptionName": ZINGHR_SUBSCRIPTION,
        "Token": ZINGHR_API_TOKEN,
        "EmployeeCode": employee_code,
        "SwipeDate": datetime.now().strftime("%Y-%m-%d"),
        "SwipeTime": datetime.now().strftime("%H:%M:%S"),
        "InOut": in_out,
        "Location": location
    }
    
    try:
        response = requests.post(url, json=payload, headers=zinghr_headers())
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_employee_details(employee_code):
    """Get employee basic details"""
    url = f"{BASE_URL}EmployeeBasicDetailsAPI"
    payload = {
        "SubscriptionName": ZINGHR_SUBSCRIPTION,
        "Token": ZINGHR_API_TOKEN,
        "EmployeeCode": employee_code
    }
    
    try:
        response = requests.post(url, json=payload, headers=zinghr_headers())
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def apply_leave(employee_code, from_date, to_date, leave_type, reason=""):
    """Apply for leave"""
    url = f"{BASE_URL}LeaveApplicationAPI"
    payload = {
        "SubscriptionName": ZINGHR_SUBSCRIPTION,
        "Token": ZINGHR_API_TOKEN,
        "EmployeeCode": employee_code,
        "FromDate": from_date,
        "ToDate": to_date,
        "LeaveType": leave_type,
        "Reason": reason
    }
    
    try:
        response = requests.post(url, json=payload, headers=zinghr_headers())
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_attendance(employee_code, month, year):
    """Get attendance data"""
    url = f"{BASE_URL}AttendanceAPI"
    payload = {
        "SubscriptionName": ZINGHR_SUBSCRIPTION,
        "Token": ZINGHR_API_TOKEN,
        "EmployeeCode": employee_code,
        "Month": month,
        "Year": year
    }
    
    try:
        response = requests.post(url, json=payload, headers=zinghr_headers())
        return response.json()
    except Exception as e:
        return {"error": str(e)}