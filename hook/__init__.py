from  odoo import api , SUPERUSER_ID

# __init__.py
def test_pre_init_hook(cr):
    # print("Pre-init hook method is called")
    # cr.execute("UPDATE res_partner SET mobile='03359899671' WHERE mobile IS NULL")
    # print("Pre-init hook done with SQL query.")

    env = api.Environment(cr,SUPERUSER_ID,{})
    env['res.partner'].hello_hook()