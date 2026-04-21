# ProLine — Contact Response Schema

Source: Anonymized example based on a live query.

---

## Full Response

```json
{
  "contact_id": "1770000000000x100000000000000000",
  "first_name": "Jamie",
  "last_name": "Rivera",
  "phone": "5551234567",
  "email": "jamie.rivera@example.com",
  "address1": "123 Example Street",
  "address2": "",
  "city": "Tampa",
  "state": "FL",
  "zip": "33601",
  "assigned_to_id": "1690000000000x200000000000000000",
  "assigned_to_name": "Pat Smith",
  "assigned_to_proline": "5559876543",
  "assigned_to_email": "pat@examplecoroofing.com",
  "external_id": "",
  "notes": "",
  "custom_field_1": "",
  "custom_field_2": "",
  "custom_field_3": "",
  "custom_date_1": null,
  "custom_date_2": null,
  "custom_date_3": null,
  "lead_source": ""
}
```

## Field Reference

| Field | Type | Notes |
|-------|------|-------|
| contact_id | string | ProLine unique ID |
| first_name | string | May be mangled if `contact_name` was used on create — always prefer `contact_fname` |
| last_name | string | Same caveat |
| phone | string | Digits only, no formatting |
| email | string | |
| address1/2 | string | Street address |
| city / state / zip | string | |
| assigned_to_id | string | ProLine user ID of assigned rep |
| external_id | string | Your system's reference ID |
| custom_field_1–3 | string | Company-configured text fields |
| custom_date_1–3 | date\|null | Company-configured date fields |
| lead_source | string | Acquisition source |

---

**Note:** IDs shown above are illustrative placeholders. Your tenant's IDs will have the same shape (`<13digits>x<18digits>`) but different values. See `docs/stage-ids.md` for discovering yours.
