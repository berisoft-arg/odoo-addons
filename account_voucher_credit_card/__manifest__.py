
{
    "name": "Account Voucher Credit Card",
    "summary": "",
    "version": "15.0.0.1.0",
    "category": "Account",
    "website": "",
    "author": "",
    "license": "AGPL-3",
    "depends": [
        'account',
        'account_payment_fix',
        ],
    "data": [
        'data/account_payment_method_data.xml',
        'security/ir.model.access.csv',
        'views/account_journal_views.xml',
        'views/account_payment_views.xml',
        'views/res_card_views.xml',
        'views/installments_card_views.xml',        
        ],
    "installable": True,
}
