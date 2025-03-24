*** Settings ***
Documentation     UI Tests for CRM Web App using Selenium and Faker
Library           SeleniumLibrary
Library           FakerLibrary
Library           OperatingSystem
Library           Process

Suite Setup       Scenario: Register a new user and log in
Suite Teardown    Close browser

*** Variables ***
${BROWSER}        Chrome
${URL}            http://127.0.0.1:5000
${HOME}           /Users/sairacardinal
${DOWNLOAD_DIR}   ${HOME}/Downloads
${PDF_READER}     acrobat.exe

*** Keywords ***
# Feature: User Management
Scenario: Register a new user and log in
    ${username}=     FakerLibrary.User Name
    ${password}=     FakerLibrary.Password

    Open Browser    ${URL}    ${BROWSER}
    Maximize Browser Window
    Wait Until Page Contains Element    id=heading-login

    Go To    ${URL}/register
    Wait Until Page Contains Element    id=heading-register
    Input Text    id=input-username    ${username}
    Input Text    id=input-password    ${password}
    Click Button  id=btn-register
    Wait Until Page Contains     Login

    Go To    ${URL}/login
    Wait Until Page Contains Element    id=heading-login
    Input Text    id=input-username    ${username}
    Input Text    id=input-password    ${password}
    Click Button  id=btn-login
    Wait Until Page Contains     Welcome

Close browser
    Click Link    id=nav-logout
    Handle Alert
    Wait Until Page Contains Element    id=heading-login

*** Test Cases ***
# Feature: Customer Management
Scenario: Add a new customer with fake data
    ${name}=      FakerLibrary.Name
    ${email}=     FakerLibrary.Email
    ${phone}=     FakerLibrary.Phone Number
    ${company}=   FakerLibrary.Company

    Click Link    id=btn-add-customer
    Input Text    id=input-name     ${name}
    Input Text    id=input-email    ${email}
    Input Text    id=input-phone    ${phone}
    Input Text    id=input-company    ${company}
    Click Button  id=btn-submit-customer
    Wait Until Page Contains    Welcome

# Feature: Order Management
Scenario: Add a new order with fake data
    ${product}=   FakerLibrary.Word
    ${amount}=  FakerLibrary.Random Int    min=1    max=10

    Scroll Element Into View    id=btn-add-order
    Click Link    id=btn-add-order
    Input Text    id=input-product    ${product}
    Input Text    id=input-amount     ${amount}
    Click Button  id=btn-submit-order
    Wait Until Page Contains    Welcome

# Feature: Data Export
Scenario: Export customers as CSV via UI
    ${options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Set Variable     ${DOWNLOAD_DIR}    ${HOME}/Downloads
    Call Method    ${options}    add_experimental_option    prefs    {"download.default_directory": "${DOWNLOAD_DIR}"}
    Go To    ${URL}/export/csv
    ${file}=    Set Variable    ${DOWNLOAD_DIR}${/}customers.csv
    Wait Until Keyword Succeeds    10x    1s    File Should Exist    ${file}
    Remove File    ${file}

Scenario: Export customers as PDF via UI
    ${options}=    Evaluate    sys.modules['selenium.webdriver'].ChromeOptions()    sys, selenium.webdriver
    Set Variable     ${DOWNLOAD_DIR}    ${HOME}/Downloads
    Call Method    ${options}    add_experimental_option    prefs    {"download.default_directory": "${DOWNLOAD_DIR}"}
    Go To    ${URL}/export/pdf
    ${file}=    Set Variable    ${DOWNLOAD_DIR}${/}customers.pdf
    Wait Until Keyword Succeeds    10x    1s    File Should Exist    ${file}
    # Close PDF reader if it's open
    Run Process    taskkill    /im    ${PDF_READER}    /f    shell=True    stderr=STDOUT
    Sleep    2s
    Remove File    ${file}
