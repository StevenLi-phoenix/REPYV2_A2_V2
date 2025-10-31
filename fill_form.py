from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import threading
import uvicorn

app = FastAPI(
    title="Google Forms Submission API",
    description="API for submitting Google Forms with manual login",
    version="1.0.0"
)

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdWKAlQPqcteypacqRFwS0DZEx-247xNVUYnIoigx7bjOHvLg/viewform"

# XPath selectors for form fields
CHECKBOX_XPATH = '//*[@id="i5"]'
NAME_XPATH = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/input'
NETID_XPATH = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[3]/div/div/div[2]/div/div[1]/div/div[1]/input'
ATTACK_CASE_XPATH = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[4]/div/div/div[2]/div/div[1]/div/div[1]/input'
REASON_XPATH = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[5]/div/div/div[2]/div/div[1]/div[2]/textarea'
SUBMIT_XPATH = '//*[@id="mG61Hd"]/div[2]/div/div[3]/div[2]/div[1]/div/span/span'
SUBMIT_ANOTHER_FORM_XPATH = '//*[@id="mG61Hd"]/div[2]/div/div[3]/div[2]/div[1]/div[2]/span'

# Global browser instance to persist login
browser_driver = None
browser_lock = threading.Lock()

class FormSubmission(BaseModel):
    name: str = Field(..., description="Student name")
    netid: str = Field(..., description="Student NetID")
    attack_case: str = Field(..., description="Attack case filename to flag")
    reason: str = Field(..., description="Reason for flagging")
    submit: bool = Field(False, description="Whether to actually submit the form")


class SubmissionResponse(BaseModel):
    status: str
    message: str
    data: dict


def initialize_browser():
    """Initialize browser and perform one-time login"""
    global browser_driver
    
    if browser_driver is None:
        print("Initializing browser for first time login...")
        browser_driver = webdriver.Chrome()
        
        # Navigate to Google login
        browser_driver.get("https://accounts.google.com/")
        input("Please log in to Google, then press Enter in the terminal to continue...")
        print("Login successful! Browser session will be reused for subsequent submissions.")
    
    return browser_driver


def fill_google_form(name: str, netid: str, attack_case: str, reason: str, submit: bool = False):
    """
    Fill out the Google Form with provided data.
    Uses persistent browser session to maintain login state.
    """
    global browser_driver
    
    with browser_lock:
        try:
            # Initialize browser if needed (first time only)
            driver = initialize_browser()
            
            # Navigate to form
            driver.get(FORM_URL)
            time.sleep(2)
            
            # Fill out fields
            checkbox = driver.find_element(By.XPATH, CHECKBOX_XPATH)
            checkbox.click()
            
            name_input = driver.find_element(By.XPATH, NAME_XPATH)
            name_input.send_keys(name)
            
            netid_input = driver.find_element(By.XPATH, NETID_XPATH)
            netid_input.send_keys(netid)
            
            attack_case_input = driver.find_element(By.XPATH, ATTACK_CASE_XPATH)
            attack_case_input.send_keys(attack_case)
            
            reason_input = driver.find_element(By.XPATH, REASON_XPATH)
            reason_input.send_keys(reason)
            
            if submit:
                submit_button = driver.find_element(By.XPATH, SUBMIT_XPATH)
                submit_button.click()
                time.sleep(3)
                print(f"Form submitted successfully for {name} ({netid})!")
                
                # Click "Submit another form" to reset the form
                try:
                    submit_another_button = driver.find_element(By.XPATH, SUBMIT_ANOTHER_FORM_XPATH)
                    submit_another_button.click()
                    time.sleep(2)
                    print("Ready for next submission.")
                except Exception as e:
                    print(f"Could not click 'Submit another form': {e}")
                    # Navigate back to form manually if button not found
                    driver.get(FORM_URL)
                    time.sleep(2)
            else:
                print(f"Form filled but not submitted for {name} ({netid}) (review mode)")
                time.sleep(5)  # Brief pause for review
            
            return True
        except Exception as e:
            print(f"Error filling form: {e}")
            return False


@app.post("/api/submit", response_model=SubmissionResponse, status_code=200)
async def submit_form(form_data: FormSubmission):
    """
    Submit a Google Form with the provided data.
    
    First request will require manual login to Google in the browser window.
    Subsequent requests will reuse the same browser session (no re-login needed).
    """
    try:
        # Fill form synchronously since we use a lock anyway
        success = fill_google_form(
            form_data.name,
            form_data.netid,
            form_data.attack_case,
            form_data.reason,
            form_data.submit
        )
        
        if success:
            return SubmissionResponse(
                status="success",
                message="Form processed successfully." if form_data.submit else "Form filled but not submitted.",
                data={
                    "name": form_data.name,
                    "netid": form_data.netid,
                    "attack_case": form_data.attack_case,
                    "submit": form_data.submit
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to fill form")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Google Forms Submission API"
    }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Google Forms Submission API",
        "version": "1.0.0",
        "login_status": "logged_in" if browser_driver is not None else "not_logged_in",
        "endpoints": {
            "POST /api/submit": "Submit a form with student information",
            "GET /api/health": "Health check",
            "POST /api/close_browser": "Close the browser session",
            "GET /docs": "Interactive API documentation",
            "GET /redoc": "Alternative API documentation"
        }
    }


@app.post("/api/close_browser")
async def close_browser():
    """Close the persistent browser session"""
    global browser_driver
    
    with browser_lock:
        if browser_driver is not None:
            try:
                browser_driver.quit()
                browser_driver = None
                return {"status": "success", "message": "Browser session closed"}
            except Exception as e:
                return {"status": "error", "message": f"Failed to close browser: {str(e)}"}
        else:
            return {"status": "info", "message": "No active browser session"}


if __name__ == "__main__":
    print("Starting Google Forms Submission API Server with FastAPI...")
    print("API Documentation available at:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nAPI Endpoints:")
    print("  POST /api/submit - Submit a form")
    print("  GET  /api/health - Health check")
    print("\nExample usage:")
    print('  curl -X POST http://localhost:8000/api/submit \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"name": "Steven Li", "netid": "sl36325", "attack_case": "test1.r2py", "reason": "Test reason", "submit": false}\'')
    print("\nServer running on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
