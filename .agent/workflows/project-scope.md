---
description: Project scope rules — focus only on OS module, not detention, fuel, etc.
---

# Project Scope Rules

This project is focused **exclusively on the OS (Offence Sheet) module** upgrade.

## DO NOT touch or modify:
- Detention module (`detention.py`, detention models, DR forms)
- Fuel module (`fuel.py`, fuel models, fuel forms)
- Warehouse module (`warehouse.py`, warehouse models, warehouse forms)
- MHB module (`mhb.py`, MHB models, MHB forms)
- Revenue module (`revenue.py`, revenue models, revenue forms)
- Any other module unrelated to the OS (Offence Sheet) workflow

## Focus areas:
- **SDO (Superintending/Search & Detection Officer)** Offence Case Registration
- **Adjudication** of Offence cases
- **Authentication & User Management** for SDO and Adjudication modules
- **Baggage** forms (as part of the SDO workflow)
- **Reports, Queries, Dashboard** related to the OS module
- **App-level config** (icons, logos, Tauri config, deployment)
