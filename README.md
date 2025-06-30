# SurgeX-PDU-DxP-Client

Python control module using the DxP protocol for SurgeX switched PDU's

## Currently Supported Features

- `turn_on_outlet`
- `turn_off_outlet`
- `get_outlet_state`

## Example

```python
pdu_client = SurgeX_DxPClient(
    "192.168.1.254",
    model="SA-82-AR",
    username="admin",
    password="secret",
)

pdu_client.turn_off_outlet(0)
```

## Known Issues

- If `get_outlet_state` is called with incorrect credentials, it will always return False (de-energized), regardless of the outlet state.

## Disclaimer

Not affilated with SurgeX, AMETEK, or any manufacturer.
