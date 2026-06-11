# Nepal Import Review Draft — Grid-Connected PV Inverter

*For SunBridge Trading, to share with the Nepal import agent. Checked against NEPQA-2025 §1.4. Draft for review.*

## 1. Important: the two documents describe different products

**Verdict:** DIFFERENT_PRODUCT

Records do not share any model number and/or differ in phase. Their specifications are not comparable.

| Field | SUN-3K-G06P3-EU-AM2 (three-phase) | CE-1P3001G-230-EU (single-phase) |
| --- | --- | --- |
| Document type | Certificate of Conformity | Test Report |
| Phase | three | single |
| DC voltage class | 1100V | 60V |

These two documents share a factory but are different product lines. They cannot be treated as one filing. Each is scored separately against NEPQA below.

**Extracted facts, for reference — these are different products, not a conflict comparison:**

| Field | Value (A) | Value (B) | Sources |
| --- | --- | --- | --- |
| ac_output_voltage | 230/400V | 230V | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| certificate_or_report_number | PCS-24-1022 | GZES230100125901 | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| ip_rating | IP65 | IP67 | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| issue_date | 2024-03-26 | 2023-02-01 | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| manufacturer_address | No. 26 South YongJiang Road, Daqi, Beilun, NingBo, China | No. 1828 Fuqing South RD. Panhuo ST. Yinzhou District Ningbo Zhejiang 315000 China | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| manufacturer_name | NingBo Deye Inverter Technology Co., Ltd. | Zhejiang CHISAGE New Energy Technology Co., Ltd | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| output_frequency | 50/60 Hz | 50Hz | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| power_factor | 0.8 leading~0.8 lagging | ＞0.99 | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| rated_power | 3kW, 4kW, 5kW, 6kW, 7kW, 8kW, 9kW, 10kW, 12kW, 15kW | 300W to 2000W | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| standards | IEC 62116:2014 and IEC 61727:2004 | IEC/EN 62109-1:2010 | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |
| test_lab | SGS-CSTC Standards Technical Services Co., Ltd. Guangzhou Branch | SGS-CSTC Standards Technical Services Co., Ltd. Guangzhou Branch | 188_1115.pdf / DSS_GZES230100125901_combined-1.pdf |

## NEPQA §1.4 document scorecard — SUN-3K-G06P3-EU-AM2 (three-phase)

Models: SUN-3K-G06P3-EU-AM2, SUN-4K-G06P3-EU-AM2, SUN-5K-G06P3-EU-AM2, SUN-6K-G06P3-EU-AM2, SUN-7K-G06P3-EU-AM2, SUN-8K-G06P3-EU-AM2, SUN-9K-G06P3-EU-AM2, SUN-10K-G06P3-EU-AM2, SUN-12K-G06P3-EU-AM2, SUN-15K-G06P3-EU-AM2, SUN-3K-G06P3-EU-AM2-P1, SUN-4K-G06P3-EU-AM2-P1, SUN-5K-G06P3-EU-AM2-P1, SUN-6K-G06P3-EU-AM2-P1, SUN-7K-G06P3-EU-AM2-P1, SUN-8K-G06P3-EU-AM2-P1, SUN-9K-G06P3-EU-AM2-P1, SUN-10K-G06P3-EU-AM2-P1, SUN-12K-G06P3-EU-AM2-P1, SUN-15K-G06P3-EU-AM2-P1

- **MET** — DOC-1: Test certificate to IEC 61727:2004 (utility interface characteristics), from an IECEE/IECRE-listed body
- **MET** — DOC-2: Test certificate to IEC 62116:2014 (islanding prevention test procedure), from an IECEE/IECRE-listed body
- **MISSING** — DOC-3: Test certificate to IEC 62891:2020 (MPPT efficiency of grid-connected inverters), from an IECEE/IECRE-listed body
- **MISSING** — DOC-4: Test certificate to IEC 62109-1:2010 AND IEC 62109-2:2011 (safety: general + inverter-particular), from an IECEE/IECRE-listed body
- **ASK_FACTORY** — DOC-5: Importer-manufacturer agreement, signed and stamped, stating the PV inverter warranty period
- **ASK_FACTORY** — DOC-6: Catalogue and technical datasheet of the PV inverter

## NEPQA §1.4 technical scorecard — SUN-3K-G06P3-EU-AM2 (three-phase)

- **MET** — TECH-1: Rated AC output voltage: 3-phase 400V (L-L) ±10%, or 1-phase 230V (L-N) ±10%
  - extracted: 230/400V (quote: "Nominal grid voltage (V) 3L/N/PE 230/400V")
- **MET** — TECH-2: Output frequency 50Hz ± 2.5%
  - extracted: 50/60 Hz (quote: "Nominal grid frequency (Hz) 50/60")
- **NOT_STATED** — TECH-3: MPPT input efficiency ≥ 95%
- **NOT_STATED** — TECH-4: Inverter efficiency ≥ 95% (≤5kVA) / ≥ 97% (>5kVA), transformerless
- **NOT_STATED** — TECH-5: Euro efficiency ≥ 94% (≤5kVA) / ≥ 96% (>5kVA), transformerless; efficiency-vs-output curve provided
- **NOT_STATED** — TECH-6: Inverter efficiency ≥ 90% for transformer topology
- **NOT_STATED** — TECH-7: No-load loss < 0.5% of rated power (transformerless)
- **NOT_STATED** — TECH-8: No-load loss < 1.5% of rated power (transformer topology)
- **NOT_STATED** — TECH-9: Total harmonic distortion (THD) < 5% at full load
- **MET** — TECH-10: Power factor > 0.99 at nominal power; adjustable 0.8 leading to 0.8 lagging
  - extracted: 0.8 leading~0.8 lagging (quote: "Output power factor 0.8 leading~0.8 lagging")
- **MET** — TECH-11: Ingress protection ≥ IP65 per IEC 60529
  - extracted: IP65 (quote: "Protection degree IP65")
- **NOT_STATED** — TECH-12: Built-in meter and data logger with external user interface
- **NOT_STATED** — TECH-13: Internal protection: DC reverse polarity, grid fault, lightning on feeder
- **NOT_STATED** — TECH-14: Fully automatic operation (wake-up, synchronization, shutdown)
- **NOT_STATED** — TECH-15: Cooling: fan or heat sink to avoid excessive heating
- **NOT_STATED** — TECH-16: PV inverter warranty ≥ 5 years

## Labeling — SUN-3K-G06P3-EU-AM2 (three-phase)

No label artwork or photo provided — pending from factory. What we could pre-fill from the extracted facts:

- LBL-1 (Name of the manufacturer): NingBo Deye Inverter Technology Co., Ltd.
- LBL-2 (Brand, Model and Type): SUN-3K-G06P3-EU-AM2, SUN-4K-G06P3-EU-AM2, SUN-5K-G06P3-EU-AM2, SUN-6K-G06P3-EU-AM2, SUN-7K-G06P3-EU-AM2, SUN-8K-G06P3-EU-AM2, SUN-9K-G06P3-EU-AM2, SUN-10K-G06P3-EU-AM2, SUN-12K-G06P3-EU-AM2, SUN-15K-G06P3-EU-AM2, SUN-3K-G06P3-EU-AM2-P1, SUN-4K-G06P3-EU-AM2-P1, SUN-5K-G06P3-EU-AM2-P1, SUN-6K-G06P3-EU-AM2-P1, SUN-7K-G06P3-EU-AM2-P1, SUN-8K-G06P3-EU-AM2-P1, SUN-9K-G06P3-EU-AM2-P1, SUN-10K-G06P3-EU-AM2-P1, SUN-12K-G06P3-EU-AM2-P1, SUN-15K-G06P3-EU-AM2-P1
- LBL-3 (Rated Power in Watt or VA): 3kW, 4kW, 5kW, 6kW, 7kW, 8kW, 9kW, 10kW, 12kW, 15kW
- LBL-4 (Input and output voltage (V) and frequency (Hz)): 230/400V, 50/60 Hz
- LBL-5 (Maximum Input Voltage): 1100V
- LBL-6 (MPPT Voltage Range): unknown — pending from factory
- LBL-7 (Serial Number): unknown — pending from factory

## Manufacturer and test information — SUN-3K-G06P3-EU-AM2 (three-phase)

- Manufacturer: NingBo Deye Inverter Technology Co., Ltd.
- Manufacturer address: No. 26 South YongJiang Road, Daqi, Beilun, NingBo, China
- Certificate / report number: PCS-24-1022
- Issue date: 2024-03-26
- Test lab / issuing body: SGS-CSTC Standards Technical Services Co., Ltd. Guangzhou Branch

## NEPQA §1.4 document scorecard — CE-1P3001G-230-EU (single-phase)

Models: CE-1P3001G-230-EU, CE-1P5001G-230-EU, CE-1P6001G-230-EU, CE-1P8001G-230-EU, CE-1P10001G-230-EU, CE-1P13001G-230-EU, CE-1P16001G-230-EU, CE-1P18001G-230-EU, CE-1P20001G-230-EU(1)

- **MISSING** — DOC-1: Test certificate to IEC 61727:2004 (utility interface characteristics), from an IECEE/IECRE-listed body
- **MISSING** — DOC-2: Test certificate to IEC 62116:2014 (islanding prevention test procedure), from an IECEE/IECRE-listed body
- **MISSING** — DOC-3: Test certificate to IEC 62891:2020 (MPPT efficiency of grid-connected inverters), from an IECEE/IECRE-listed body
- **MISSING** — DOC-4: Test certificate to IEC 62109-1:2010 AND IEC 62109-2:2011 (safety: general + inverter-particular), from an IECEE/IECRE-listed body
- **ASK_FACTORY** — DOC-5: Importer-manufacturer agreement, signed and stamped, stating the PV inverter warranty period
- **ASK_FACTORY** — DOC-6: Catalogue and technical datasheet of the PV inverter

## NEPQA §1.4 technical scorecard — CE-1P3001G-230-EU (single-phase)

- **MET** — TECH-1: Rated AC output voltage: 3-phase 400V (L-L) ±10%, or 1-phase 230V (L-N) ±10%
  - extracted: 230V (quote: "Rated grid voltage 230V")
- **MET** — TECH-2: Output frequency 50Hz ± 2.5%
  - extracted: 50Hz (quote: "Rated grid frequency 50Hz")
- **NOT_STATED** — TECH-3: MPPT input efficiency ≥ 95%
- **NOT_STATED** — TECH-4: Inverter efficiency ≥ 95% (≤5kVA) / ≥ 97% (>5kVA), transformerless
- **NOT_STATED** — TECH-5: Euro efficiency ≥ 94% (≤5kVA) / ≥ 96% (>5kVA), transformerless; efficiency-vs-output curve provided
- **NOT_STATED** — TECH-6: Inverter efficiency ≥ 90% for transformer topology
- **NOT_STATED** — TECH-7: No-load loss < 0.5% of rated power (transformerless)
- **NOT_STATED** — TECH-8: No-load loss < 1.5% of rated power (transformer topology)
- **NOT_STATED** — TECH-9: Total harmonic distortion (THD) < 5% at full load
- **MET** — TECH-10: Power factor > 0.99 at nominal power; adjustable 0.8 leading to 0.8 lagging
  - extracted: ＞0.99 (quote: "Power factor ＞0.99")
- **MET** — TECH-11: Ingress protection ≥ IP65 per IEC 60529
  - extracted: IP67 (quote: "IP protection class.....................................................: IP 67")
- **NOT_STATED** — TECH-12: Built-in meter and data logger with external user interface
- **NOT_STATED** — TECH-13: Internal protection: DC reverse polarity, grid fault, lightning on feeder
- **NOT_STATED** — TECH-14: Fully automatic operation (wake-up, synchronization, shutdown)
- **NOT_STATED** — TECH-15: Cooling: fan or heat sink to avoid excessive heating
- **NOT_STATED** — TECH-16: PV inverter warranty ≥ 5 years

## Labeling — CE-1P3001G-230-EU (single-phase)

No label artwork or photo provided — pending from factory. What we could pre-fill from the extracted facts:

- LBL-1 (Name of the manufacturer): Zhejiang CHISAGE New Energy Technology Co., Ltd
- LBL-2 (Brand, Model and Type): CE-1P3001G-230-EU, CE-1P5001G-230-EU, CE-1P6001G-230-EU, CE-1P8001G-230-EU, CE-1P10001G-230-EU, CE-1P13001G-230-EU, CE-1P16001G-230-EU, CE-1P18001G-230-EU, CE-1P20001G-230-EU(1)
- LBL-3 (Rated Power in Watt or VA): 300W to 2000W
- LBL-4 (Input and output voltage (V) and frequency (Hz)): 230V, 50Hz
- LBL-5 (Maximum Input Voltage): 60V
- LBL-6 (MPPT Voltage Range): unknown — pending from factory
- LBL-7 (Serial Number): unknown — pending from factory

## Manufacturer and test information — CE-1P3001G-230-EU (single-phase)

- Manufacturer: Zhejiang CHISAGE New Energy Technology Co., Ltd
- Manufacturer address: No. 1828 Fuqing South RD. Panhuo ST. Yinzhou District Ningbo Zhejiang 315000 China
- Certificate / report number: GZES230100125901
- Issue date: 2023-02-01
- Test lab / issuing body: SGS-CSTC Standards Technical Services Co., Ltd. Guangzhou Branch

## To clarify with the factory

- Catalogue and technical datasheet of the PV inverter
- Importer-manufacturer agreement, signed and stamped, stating the PV inverter warranty period
- Test certificate to IEC 61727:2004 (utility interface characteristics), from an IECEE/IECRE-listed body
- Test certificate to IEC 62109-1:2010 AND IEC 62109-2:2011 (safety: general + inverter-particular), from an IECEE/IECRE-listed body
- Test certificate to IEC 62116:2014 (islanding prevention test procedure), from an IECEE/IECRE-listed body
- Test certificate to IEC 62891:2020 (MPPT efficiency of grid-connected inverters), from an IECEE/IECRE-listed body

---
*Statuses — documents: MET = standard found; MISSING = required standard not present; ASK_FACTORY = cannot be shown by this document type. Technical: MET/FAIL = checked against the extracted value; NOT_STATED = not in this document, await test reports.*