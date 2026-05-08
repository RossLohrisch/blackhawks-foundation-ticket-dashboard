# Data Dictionary — Initial Draft

Source file: `data/foundation_2026-05-04-1601.csv`

| Column | Current interpretation | Needs confirmation? |
|---|---|---|
| `SEASON_YEAR` | Ticket season year. | Low |
| `POSTAL_CODE` | Customer/account ZIP code. | Medium — confirm billing ZIP vs account address ZIP vs ticket holder ZIP. |
| `PRODUCT_TYPE` | Ticket product/category, e.g. Full Season, Half Season, Group, Single Game. | Low |
| `TOTAL_SEATS` | Total seats/tickets for the ZIP + product + season bucket. For season products, likely ticketed seat-events across games, not unique physical seats. | High |
| `TOTAL_ACCOUNTS` | Number of distinct customer/accounts in the ZIP + product + season bucket. | Medium |
| `SEATS_PER_ACCOUNT` | Derived field: `TOTAL_SEATS / TOTAL_ACCOUNTS`. | Depends on definitions above. |

## Open clarification

Does `TOTAL_SEATS` count ticketed seat-events across all games in the package/season? For example, should ~1,500 seats across ~14 Full Season accounts be interpreted as roughly 35–37 season seats multiplied across the home-game schedule?
