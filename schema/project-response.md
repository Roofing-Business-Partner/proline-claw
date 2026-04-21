# ProLine — Project Response Schema

Source: Anonymized example based on a live `find/project` query.

---

## Full Response

```json
{
  "project_name": "Jamie Rivera",
  "project_number": "10056",
  "project_id": "1770000000001x100000000000000000",
  "stage": "APPT SCHEDULED",
  "stage_id": "1690000000002x300000000000000000",
  "address1": "123 Example Street",
  "address2": "",
  "city": "Tampa",
  "state": "FL",
  "zip": "33601",
  "custom_field_1": "",
  "custom_field_2": "",
  "custom_field_3": "",
  "custom_field_4": "",
  "custom_field_5": "",
  "custom_field_6": "",
  "custom_field_7": "",
  "assigned_to_id": "1690000000000x200000000000000000",
  "assigned_to_email": "pat@examplecoroofing.com",
  "assigned_to_proline": "5559876543",
  "assigned_to_name": "Pat Smith",
  "notes": "",
  "contact_id": "1770000000000x100000000000000000",
  "contact_display": "Jamie Rivera",
  "contact_fname": "Jamie",
  "contact_lname": "Rivera",
  "contact_phone": "5551234567",
  "contact_email": "jamie.rivera@example.com",
  "other_contact_1_id": "",
  "other_contact_1_display": "",
  "other_contact_1_fname": "",
  "other_contact_1_lname": "",
  "other_contact_1_phone": "",
  "other_contact_1_email": "",
  "other_contact_2_id": "",
  "other_contact_2_display": "",
  "other_contact_2_fname": "",
  "other_contact_2_lname": "",
  "other_contact_2_phone": "",
  "other_contact_2_email": "",
  "status": "Inspection",
  "category": "",
  "type": "",
  "services": [],
  "tags": [],
  "quoted_value": 0,
  "approved_value": 0,
  "accounts_receivable": 0,
  "gross_revenue": 0,
  "net_revenue": 0,
  "gross_profit": 0,
  "gross_margin": 0,
  "merchant_fees": 0,
  "refunds": 0,
  "chargebacks": 0,
  "contact_lead_source": ""
}
```

## Field Reference

| Field | Type | Notes |
|-------|------|-------|
| project_id | string | ProLine unique ID |
| project_number | string | Sequential job number |
| stage | string | Stage label in ProLine |
| stage_id | string | Stage unique ID (use this for writes, not the string) |
| status | string | High-level status group |
| assigned_to_id | string | Rep's ProLine user ID |
| custom_field_1–7 | string | Configured per company |
| quoted_value | number | Estimate sent |
| approved_value | number | Signed contract value |
| accounts_receivable | number | Outstanding balance |
| gross_revenue | number | Total collected |
| net_revenue | number | After fees/refunds |
| gross_profit | number | Revenue minus cost |
| gross_margin | number | Profit % |
| merchant_fees | number | Processing fees |
| refunds | number | Refund total |
| chargebacks | number | Chargeback total |
| contact_display | string | Full name as stored — may have splitting issues |
| other_contact_1/2 | object | Secondary contacts on project |

---

**Note:** IDs shown above are illustrative placeholders. Your tenant's IDs will have the same shape (`<13digits>x<18digits>`) but different values. Run `scripts/onboard.py` to discover yours.
