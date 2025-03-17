*** Settings ***
Documentation   API Tests for CRM Web App using Robot Framework with Faker
Library         RequestsLibrary
Resource        crm_keywords.robot    # Importing Keywords from a Separate File

Suite Setup     User successfully logs in
#Suite Teardown  User logs out successfully

*** Variables ***
${BASE_URL}    http://127.0.0.1:5000  # Update this with your Flask app URL

*** Keywords ***
# Feature: User Authentication
User successfully logs in
    Given The API is available
    And The database is cleaned
    When The user is created
    Then The user logs in with valid credentials
    And The response status code should be 200

#User logs out successfully
#    Given User successfully logs in
#    When The user logs out
#    Then The response status code should be 200
#    And The response should contain "Logged out successfully"

*** Test Cases ***
# Feature: Customer Management
Scenario: Add a new customer
    Given The customer data should be ready
    When The customer data is created
    Then The response status code should be 200

#Scenario: Edit an existing customer
#    Given All customer IDs
#    When The user updates the customer email
#    Then The response status code should be 200
#
#Scenario: Delete a customer
#    Given The user logs in with valid credentials
#    And A customer exists
#    When The user deletes the customer
    Then The response status code should be 200

# Feature: Order Management
Scenario: Add a new order
    Given All customer IDs
    And The order data should be ready
    When The order data is created
    Then The response status code should be 200

#Scenario: Edit an existing order
#    Given The user logs in with valid credentials
#    And An order exists
#    When The user updates the order status
#    Then The response status code should be 200
#
#Scenario: Delete an order
#    Given The user logs in with valid credentials
#    And An order exists
#    When The user deletes the order
#    Then The response status code should be 200

# Feature: Data Export
Scenario: Export customers as CSV
    Given The user logs in with valid credentials
    When The user requests customer data in CSV format
    Then The response status code should be 200
    And The response should be in CSV format

Scenario: Export customers as PDF
    Given The user logs in with valid credentials
    When The user requests customer data in PDF format
    Then The response status code should be 200
    And The response should be in PDF format
