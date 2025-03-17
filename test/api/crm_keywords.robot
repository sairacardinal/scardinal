*** Settings ***
Library    RequestsLibrary
Library    Collections
Library    FakerLibrary
Library    String
Library    XML  # For parsing HTML
Library    crm_keywords.py  # Import our custom Python helper for HTML parsing

*** Variables ***
${LOGIN_ENDPOINT}           /login
${LOGOUT_ENDPOINT}          /logout
${REGISTER_ENDPOINT}        /register
${CUSTOMERS_ENDPOINT}       /customers
${ADD_CUSTOMER_ENDPOINT}    /add
${ADD_ORDER_ENDPOINT}       /add_order
${EDIT_ORDER_ENDPOINT}      /edit_order/1
${DELETE_ORDER_ENDPOINT}    /delete_order/1
${EXPORT_CSV_ENDPOINT}      /export/csv
${EXPORT_PDF_ENDPOINT}      /export/pdf

*** Keywords ***

The API is available
    Create Session    crm    ${BASE_URL}

The database is cleaned
    Log    Cleaning database before test run

The user is created
    ${username}=    FakerLibrary.Username
    ${password}=    FakerLibrary.Password
    Set Suite Variable    ${TEST_USERNAME}    ${username}
    Set Suite Variable    ${TEST_PASSWORD}    ${password}

    ${data}=    Create Dictionary    username=${username}    password=${password}
    ${response}=    POST On Session    crm    ${REGISTER_ENDPOINT}    data=${data}
    Log    Test user created successfully

The user logs in with valid credentials
    ${data}=    Create Dictionary    username=${TEST_USERNAME}    password=${TEST_PASSWORD}
    ${response}=    POST On Session    crm    ${LOGIN_ENDPOINT}    data=${data}

    # Extract status code
    ${status_code}=    Convert To String    ${response.status_code}

    # Store response and status code for later use
    Set Suite Variable    ${LOGIN_RESPONSE}    ${response}
    Set Suite Variable    ${LOGIN_STATUS_CODE}    ${status_code}

    # Debugging log
    Log    Login Response Object: ${response}
    Log    Login Status Code: ${LOGIN_STATUS_CODE}

The response status code should be 200
    # Log the response status code before validation
    Log    Login Response Status Code: ${LOGIN_STATUS_CODE}

    # Validate the response code
    Should Be Equal As Strings    ${LOGIN_STATUS_CODE}    200

#The test customer is created
#    # After login, create test data
#    A test customer is created
#    Extract all customer IDs using BeautifulSoup
#    A test order is created

The customer data should be ready
    ${name}=        FakerLibrary.Name
    ${email}=       FakerLibrary.Email
    ${phone}=       FakerLibrary.PhoneNumber
    ${company}=     FakerLibrary.Company
    Set Suite Variable    ${TEST_CUSTOMER_NAME}    ${name}
    Set Suite Variable    ${TEST_CUSTOMER_EMAIL}   ${email}

    ${data}=    Create Dictionary    name=${name}    email=${email}    phone=${phone}    company=${company}
    Set Suite Variable    ${data}
    
The customer data is created
    ${response}=    POST On Session    crm    ${ADD_CUSTOMER_ENDPOINT}    data=${data}
    Set Test Variable    ${TEST_CUSTOMER_RESPONSE}    ${response}

All customer IDs
    ${response}=    GET On Session    crm    ${CUSTOMERS_ENDPOINT}
    Should Contain    ${response.text}    <table class="table table-bordered">  # Ensure Customers table exists

    ${customer_ids}=    Get Customer IDs From HTML    ${response.text}
    Log    Extracted Customer IDs: ${customer_ids}
    Set Suite Variable    ${EXTRACTED_CUSTOMER_IDS}    ${customer_ids}

    # Select the last customer_id in the list
    ${last_customer_id}=    Get From List    ${customer_ids}    -1
    Set Suite Variable    ${TEST_CUSTOMER_ID}    ${last_customer_id}
    Log    Retrieved Last Customer ID from /customers: ${last_customer_id}
    
The order data should be ready
    ${product}=    FakerLibrary.Word
    ${amount}=     FakerLibrary.Random Number
    Set Suite Variable    ${TEST_ORDER_PRODUCT}    ${product}

    ${data}=    Create Dictionary    customer_id=${TEST_CUSTOMER_ID}    product=${product}    amount=${amount}    status="Pending"
    Set Suite Variable    ${data}

The order data is created
    ${response}=    POST On Session    crm    ${ADD_ORDER_ENDPOINT}    data=${data}
    Set Test Variable    ${TEST_ORDER_RESPONSE}    ${response}

The test data should be ready
    Log    Test data setup completed after login

The user logs out
    ${response}=    GET On Session    crm    ${LOGOUT_ENDPOINT}
    Set Test Variable    ${LOGOUT_RESPONSE}    ${response}

The user requests customer data in CSV format
    ${response}=    GET On Session    crm    ${EXPORT_CSV_ENDPOINT}
    Set Test Variable    ${EXPORT_CSV_RESPONSE}    ${response}

The response should be in CSV format
    Should Contain    ${EXPORT_CSV_RESPONSE.text}    Name,Email,Phone,Company

The user requests customer data in PDF format
    ${response}=    GET On Session    crm    ${EXPORT_PDF_ENDPOINT}
    Set Test Variable    ${EXPORT_PDF_RESPONSE}    ${response}

The response should be in PDF format
    Should Be Equal As Strings    ${EXPORT_PDF_RESPONSE.headers["Content-Type"]}    application/pdf
