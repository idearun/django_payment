# Pasargad Payment
This a sample project for using pasargad payment gateway from python.
This project is API baseda and uses django rest framework, but you can use it's main functions for other types of projects, like using django templates.

## Getting Started
You should embed the pasargad app into your own project.
* Add 'pasargad' to your insalled apps in your project settings
* Add these settings to your project settings:
```
PAYMENT = {
    'TERMINAL_CODE': '',
    'MERCHANT_CODE': '',
    'PRIVATE_KEY_ADDRESS': '',
    'GIVE_PROCESS_URL': True,
    'PAYMENT_PROCESS_ADDRESS': '',
    'PASARGAD_REDIRECT_URL': '',
}
```

* Install packages from requirement.txt to in your project env
* Add the pasargad's url to your project urls
* Run Migration

## How does it work
This app provides you three main functions for payment:

### Request
You can send the payment amout (in IRR) to this endpoint. This endpoint will create a empty payment record for the authenticated user, and returns you a transaction code, and a payment process url if you'e set so.
The payment process url is used when you're running the payment from a mobile app. You have to run the payment process in a web app, and redirect the user to that web app so they will be redirected to the bank gateway.

### Process
This endpoint takes the transaction code provided in previous step, and returns payment data. You should post the data to the gateway address (also provided in the response data) so user can do the payment process.

### Confirm
This endpoint takes the 'tref' code provided by the bank (in redirect url) and finalizes the payment.

## Notes
In order to use this app, you should convert your privateKey.xml to .pem format. You can do it in [this](http://www.platanus.cz/blog/converting-rsa-xml-key-to-pem) address.

## Authors
* [**Hasan Noori**](https://github.com/xishma)

## Licence
This project is licensed under the MIT License.

## Contribute
You can help us to:
* Add an script to convert xml to pem
* Add other gateways for other banks
* Add django templates and forms to do the payment
* ...
