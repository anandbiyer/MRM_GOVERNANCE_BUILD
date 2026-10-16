# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ..\functional\import.spec.ts >> FS-21 GEN-01 GEN-04 GEN-05 two resets at the same business date give the same counts
- Location: functional\import.spec.ts:122:5

# Error details

```
Error: CR-67: report generation during a reset must be refused with a conflict

expect(received).toBe(expected) // Object.is equality

Expected: "refused"
Received: "report generation during a reset answered 500: Internal Server Error"
```

# Page snapshot

```yaml
- generic [ref=e2]:
  - banner [ref=e3]:
    - generic [ref=e4]:
      - generic [ref=e5]: MRM Governance MIS
      - generic [ref=e6]: Model risk inventory, validation & monitoring
    - generic [ref=e7]:
      - 'generic "database: ok redis: down (TimeoutError) object_store: ok (local folder (development): C:\\Users\\anand\\OneDrive\\Documents\\AI_Projects\\MRM_Governance_Build\\D_Reviews\\DD_functional_test\\20261016\\env\\object_store)" [ref=e8]': system degraded
      - combobox "Act as user and role" [ref=e9]:
        - option "Admin — Priya Raman (U-001)" [selected]
        - option "Platform Administrator — Daniel Okafor (U-002)"
        - option "Model Owner — Helen Carter (U-003)"
        - option "Model Owner — Marcus Lee (U-007)"
        - option "Validator — Sarah Patel (U-014)"
        - option "Validator — Tomasz Nowak (U-016)"
        - option "Model Developer — Aisha Khan (U-021)"
        - option "Data Owner — Carlos Mendes (U-031)"
        - option "Executive — Robert Diaz (U-040)"
        - option "MRC Member — Robert Diaz (U-040)"
        - option "Auditor — Grace Liu (U-041)"
        - option "Executive — James Whitfield (U-042)"
        - option "Monitoring Analyst — Nina Petrova (U-050)"
        - option "Model Owner — Jia Chen (U-101)"
        - option "Validator — Jia Chen (U-101)"
        - option "Model Developer — Rahul Kumar (U-102)"
        - option "Model Owner — Anna Williams (U-103)"
        - option "Model Developer — Thanh Nguyen (U-104)"
        - option "Validator — Maria Garcia (U-105)"
        - option "Model Owner — Daniel Park (U-106)"
        - option "Model Developer — Kavya Sharma (U-107)"
        - option "Validator — Laura Thompson (U-108)"
        - option "Model Owner — Ben Foster (U-109)"
        - option "Model Developer — Joon Lee (U-110)"
        - option "Validator — Carmen Martinez (U-111)"
        - option "Model Owner — Nadia Ahmed (U-112)"
        - option "Model Developer — Yuki Tanaka (U-113)"
        - option "Validator — Patrick O'Brien (U-114)"
        - option "Model Owner — Ruth Stevens (U-115)"
        - option "Model Developer — Hans Muller (U-116)"
        - option "Validator — Emily Wong (U-117)"
        - option "Model Owner — Greta Hoffman (U-118)"
        - option "Model Developer — Andre Costa (U-119)"
        - option "Validator — Tara Raj (U-120)"
        - option "Model Owner — Lena Kim (U-121)"
        - option "Model Developer — Sora Nakamura (U-122)"
        - option "Validator — David Brown (U-123)"
        - option "Model Owner — Megan Taylor (U-124)"
        - option "Model Developer — Wei Zhang (U-125)"
        - option "Validator — Jorge Fernandez (U-126)"
        - option "Model Owner — Fiona Johnson (U-127)"
        - option "Model Developer — Bina Gupta (U-128)"
        - option "Validator — Katya Ivanova (U-129)"
        - option "Model Owner — Viktor Petrov (U-130)"
        - option "Model Developer — Chidi Okafor (U-131)"
        - option "Validator — Amelie Dubois (U-132)"
        - option "Model Owner — Tobias Fischer (U-133)"
        - option "Model Developer — Marco Rossi (U-134)"
        - option "Model Developer — Per Johansson (U-135)"
        - option "Model Owner — Olivia Grant (U-201)"
        - option "Model Owner — Samuel Osei (U-202)"
        - option "Model Owner — Irene Novak (U-203)"
        - option "Model Owner — Hiro Sato (U-204)"
        - option "Model Owner — Claire Dubois (U-205)"
        - option "Model Owner — Mateo Ruiz (U-206)"
        - option "Model Developer — Leah Cohen (U-207)"
        - option "Model Developer — Arjun Mehta (U-208)"
        - option "Model Developer — Sofia Rossi (U-209)"
        - option "Model Developer — Kwame Mensah (U-210)"
        - option "Model Developer — Elena Petrova (U-211)"
        - option "Model Developer — Lucas Martin (U-212)"
        - option "Validator — Priyanka Das (U-213)"
        - option "Validator — Oskar Lindqvist (U-214)"
        - option "Validator — Fatima Al-Sayed (U-215)"
        - option "Validator — George Adeyemi (U-216)"
        - option "Validator — Mei Lin (U-217)"
        - option "Validator — Rafael Souza (U-218)"
      - button "Sign out" [ref=e10] [cursor=pointer]
  - generic [ref=e11]:
    - navigation "Main" [ref=e12]:
      - generic [ref=e13]:
        - generic [ref=e14]: Portfolio
        - link "Command Center" [ref=e15] [cursor=pointer]:
          - /url: /
        - link "Operations Board" [ref=e16] [cursor=pointer]:
          - /url: /operations
        - link "Monitoring" [ref=e17] [cursor=pointer]:
          - /url: /monitoring
        - link "Data Audit" [ref=e18] [cursor=pointer]:
          - /url: /data-audit
      - generic [ref=e19]:
        - generic [ref=e20]: Evidence & data
        - link "Document Centre" [ref=e21] [cursor=pointer]:
          - /url: /documents
        - link "Import Centre" [ref=e22] [cursor=pointer]:
          - /url: /imports
      - generic [ref=e23]:
        - generic [ref=e24]: Control
        - link "Model Risk Report" [ref=e25] [cursor=pointer]:
          - /url: /reports/model-risk
        - link "Audit Trail" [ref=e26] [cursor=pointer]:
          - /url: /audit
        - link "Admin" [ref=e27] [cursor=pointer]:
          - /url: /admin
    - main [ref=e28]:
      - generic [ref=e29]:
        - generic [ref=e30]:
          - generic [ref=e31]: Portfolio
          - heading "Command Center" [level=1] [ref=e32]
          - paragraph [ref=e33]: Model risk across the portfolio as of 9/30/2026. Every figure is calculated from the governance records and opens the matching models.
        - paragraph [ref=e34]:
          - text: These figures are what the
          - link "Model Risk Report" [ref=e35] [cursor=pointer]:
            - /url: /reports/model-risk
          - text: states for the same business date.
        - generic [ref=e36]:
          - link "Total models 256 242 active" [ref=e37] [cursor=pointer]:
            - generic [ref=e38]: Total models
            - generic [ref=e39]: "256"
            - generic [ref=e40]: 242 active
          - link "In production 193 75% of the inventory" [ref=e41] [cursor=pointer]:
            - generic [ref=e42]: In production
            - generic [ref=e43]: "193"
            - generic [ref=e44]: 75% of the inventory
          - link "High risk 89 effective tier High" [ref=e45] [cursor=pointer]:
            - generic [ref=e46]: High risk
            - generic [ref=e47]: "89"
            - generic [ref=e48]: effective tier High
          - link "Revalidation queue 31 8 overdue" [ref=e49] [cursor=pointer]:
            - generic [ref=e50]: Revalidation queue
            - generic [ref=e51]: "31"
            - link "8 overdue" [ref=e53]:
              - /url: /operations?revalidation_status=Overdue
          - link "Models with open findings 80 148 open findings · 61 overdue" [ref=e54] [cursor=pointer]:
            - generic [ref=e55]: Models with open findings
            - generic [ref=e56]: "80"
            - generic [ref=e57]:
              - text: 148 open findings ·
              - link "61 overdue" [ref=e58]:
                - /url: /operations?flag=overdue_findings
          - link "Document completeness 63.6% 92 models with gaps" [ref=e59] [cursor=pointer]:
            - generic [ref=e60]: Document completeness
            - generic [ref=e61]: 63.6%
            - generic [ref=e62]: 92 models with gaps
          - link "Open MRC conditions 24 models" [ref=e63] [cursor=pointer]:
            - generic [ref=e64]: Open MRC conditions
            - generic [ref=e65]: "24"
            - generic [ref=e66]: models
          - generic [ref=e67]:
            - generic [ref=e68]: Portfolio score
            - generic [ref=e69]: "92.9"
            - generic [ref=e70]: average of 242 scored models
        - generic [ref=e71]:
          - generic [ref=e72]:
            - heading "Risk tier" [level=4] [ref=e73]
            - list [ref=e74]:
              - listitem [ref=e75]:
                - button "High 89 · 34.8%" [ref=e76] [cursor=pointer]:
                  - generic [ref=e77]: High
                  - generic [ref=e80]:
                    - text: "89"
                    - generic [ref=e81]: · 34.8%
              - listitem [ref=e82]:
                - button "Medium 106 · 41.4%" [ref=e83] [cursor=pointer]:
                  - generic [ref=e84]: Medium
                  - generic [ref=e87]:
                    - text: "106"
                    - generic [ref=e88]: · 41.4%
              - listitem [ref=e89]:
                - button "Low 61 · 23.8%" [ref=e90] [cursor=pointer]:
                  - generic [ref=e91]: Low
                  - generic [ref=e94]:
                    - text: "61"
                    - generic [ref=e95]: · 23.8%
          - generic [ref=e96]:
            - heading "Model type" [level=4] [ref=e97]
            - list [ref=e98]:
              - listitem [ref=e99]:
                - button "Credit Risk 78 · 30.5%" [ref=e100] [cursor=pointer]:
                  - generic [ref=e101]: Credit Risk
                  - generic [ref=e104]:
                    - text: "78"
                    - generic [ref=e105]: · 30.5%
              - listitem [ref=e106]:
                - button "Provisioning 42 · 16.4%" [ref=e107] [cursor=pointer]:
                  - generic [ref=e108]: Provisioning
                  - generic [ref=e111]:
                    - text: "42"
                    - generic [ref=e112]: · 16.4%
              - listitem [ref=e113]:
                - button "Balance Sheet 48 · 18.8%" [ref=e114] [cursor=pointer]:
                  - generic [ref=e115]: Balance Sheet
                  - generic [ref=e118]:
                    - text: "48"
                    - generic [ref=e119]: · 18.8%
              - listitem [ref=e120]:
                - button "Forecasting 52 · 20.3%" [ref=e121] [cursor=pointer]:
                  - generic [ref=e122]: Forecasting
                  - generic [ref=e125]:
                    - text: "52"
                    - generic [ref=e126]: · 20.3%
              - listitem [ref=e127]:
                - button "CCAR/Stress Testing 36 · 14.1%" [ref=e128] [cursor=pointer]:
                  - generic [ref=e129]: CCAR/Stress Testing
                  - generic [ref=e132]:
                    - text: "36"
                    - generic [ref=e133]: · 14.1%
          - generic [ref=e134]:
            - heading "Lifecycle stage Revalidation is derived from due dates" [level=4] [ref=e135]:
              - text: Lifecycle stage
              - generic [ref=e136]: Revalidation is derived from due dates
            - list [ref=e137]:
              - listitem [ref=e138]:
                - button "Initiation 6 · 2.3%" [ref=e139] [cursor=pointer]:
                  - generic [ref=e140]: Initiation
                  - generic [ref=e143]:
                    - text: "6"
                    - generic [ref=e144]: · 2.3%
              - listitem [ref=e145]:
                - button "Development 14 · 5.5%" [ref=e146] [cursor=pointer]:
                  - generic [ref=e147]: Development
                  - generic [ref=e150]:
                    - text: "14"
                    - generic [ref=e151]: · 5.5%
              - listitem [ref=e152]:
                - button "Validation 18 · 7%" [ref=e153] [cursor=pointer]:
                  - generic [ref=e154]: Validation
                  - generic [ref=e157]:
                    - text: "18"
                    - generic [ref=e158]: · 7%
              - listitem [ref=e159]:
                - button "Implementation 11 · 4.3%" [ref=e160] [cursor=pointer]:
                  - generic [ref=e161]: Implementation
                  - generic [ref=e164]:
                    - text: "11"
                    - generic [ref=e165]: · 4.3%
              - listitem [ref=e166]:
                - button "Monitoring 148 · 57.8%" [ref=e167] [cursor=pointer]:
                  - generic [ref=e168]: Monitoring
                  - generic [ref=e171]:
                    - text: "148"
                    - generic [ref=e172]: · 57.8%
              - listitem [ref=e173]:
                - button "Revalidation 31 · 12.1%" [ref=e174] [cursor=pointer]:
                  - generic [ref=e175]: Revalidation
                  - generic [ref=e178]:
                    - text: "31"
                    - generic [ref=e179]: · 12.1%
              - listitem [ref=e180]:
                - button "Reg/Audit 14 · 5.5%" [ref=e181] [cursor=pointer]:
                  - generic [ref=e182]: Reg/Audit
                  - generic [ref=e185]:
                    - text: "14"
                    - generic [ref=e186]: · 5.5%
              - listitem [ref=e187]:
                - button "Retirement 14 · 5.5%" [ref=e188] [cursor=pointer]:
                  - generic [ref=e189]: Retirement
                  - generic [ref=e192]:
                    - text: "14"
                    - generic [ref=e193]: · 5.5%
          - generic [ref=e194]:
            - heading "Revalidation status models with a due date" [level=4] [ref=e195]:
              - text: Revalidation status
              - generic [ref=e196]: models with a due date
            - list [ref=e197]:
              - listitem [ref=e198]:
                - button "Overdue 8 · 4.1%" [ref=e199] [cursor=pointer]:
                  - generic [ref=e200]: Overdue
                  - generic [ref=e203]:
                    - text: "8"
                    - generic [ref=e204]: · 4.1%
              - listitem [ref=e205]:
                - button "Due Soon 15 · 7.8%" [ref=e206] [cursor=pointer]:
                  - generic [ref=e207]: Due Soon
                  - generic [ref=e210]:
                    - text: "15"
                    - generic [ref=e211]: · 7.8%
              - listitem [ref=e212]:
                - button "Scheduled 170 · 88.1%" [ref=e213] [cursor=pointer]:
                  - generic [ref=e214]: Scheduled
                  - generic [ref=e217]:
                    - text: "170"
                    - generic [ref=e218]: · 88.1%
          - generic [ref=e219]:
            - heading "Open findings by severity open findings; opens the models holding them" [level=4] [ref=e220]:
              - text: Open findings by severity
              - generic [ref=e221]: open findings; opens the models holding them
            - list [ref=e222]:
              - listitem [ref=e223]:
                - button "Critical 21 · 14.2%" [ref=e224] [cursor=pointer]:
                  - generic [ref=e225]: Critical
                  - generic [ref=e228]:
                    - text: "21"
                    - generic [ref=e229]: · 14.2%
              - listitem [ref=e230]:
                - button "Medium 94 · 63.5%" [ref=e231] [cursor=pointer]:
                  - generic [ref=e232]: Medium
                  - generic [ref=e235]:
                    - text: "94"
                    - generic [ref=e236]: · 63.5%
              - listitem [ref=e237]:
                - button "Low 33 · 22.3%" [ref=e238] [cursor=pointer]:
                  - generic [ref=e239]: Low
                  - generic [ref=e242]:
                    - text: "33"
                    - generic [ref=e243]: · 22.3%
          - generic [ref=e244]:
            - heading "Governance score scored models" [level=4] [ref=e245]:
              - text: Governance score
              - generic [ref=e246]: scored models
            - list [ref=e247]:
              - listitem [ref=e248]:
                - button "Below 60 2 · 0.8%" [ref=e249] [cursor=pointer]:
                  - generic [ref=e250]: Below 60
                  - generic [ref=e253]:
                    - text: "2"
                    - generic [ref=e254]: · 0.8%
              - listitem [ref=e255]:
                - button "60 – 80 16 · 6.6%" [ref=e256] [cursor=pointer]:
                  - generic [ref=e257]: 60 – 80
                  - generic [ref=e260]:
                    - text: "16"
                    - generic [ref=e261]: · 6.6%
              - listitem [ref=e262]:
                - button "80 and above 224 · 92.6%" [ref=e263] [cursor=pointer]:
                  - generic [ref=e264]: 80 and above
                  - generic [ref=e267]:
                    - text: "224"
                    - generic [ref=e268]: · 92.6%
        - generic [ref=e269]:
          - generic [ref=e270]:
            - heading "Governance insights 10 of 67 · generated from current data" [level=4] [ref=e271]:
              - text: Governance insights
              - generic [ref=e272]: 10 of 67 · generated from current data
            - list [ref=e273]:
              - listitem [ref=e274]:
                - generic [ref=e275]: Critical
                - generic [ref=e276]:
                  - 'link "M-0078 CCAR Capital Adequacy: Validator U-101 cannot validate model M-0078 because U-101 is also the model owner." [ref=e277] [cursor=pointer]':
                    - /url: /models/M-0078
                  - generic [ref=e278]: "Source: model M-0078"
              - listitem [ref=e279]:
                - generic [ref=e280]: Critical
                - generic [ref=e281]:
                  - link "Critical finding F-0001 on M-0012 (CRE obligor data gap) is 40 days past due." [ref=e282] [cursor=pointer]:
                    - /url: /models/M-0012
                  - generic [ref=e283]: "Source: finding F-0001"
              - listitem [ref=e284]:
                - generic [ref=e285]: Critical
                - generic [ref=e286]:
                  - link "Critical finding F-0004 on M-0015 (Collateral valuation lag) is 12 days past due." [ref=e287] [cursor=pointer]:
                    - /url: /models/M-0015
                  - generic [ref=e288]: "Source: finding F-0004"
              - listitem [ref=e289]:
                - generic [ref=e290]: Critical
                - generic [ref=e291]:
                  - link "Critical finding F-0029 on M-0021 (Rank-ordering weakened in the latest period) is 110 days past due." [ref=e292] [cursor=pointer]:
                    - /url: /models/M-0021
                  - generic [ref=e293]: "Source: finding F-0029"
              - listitem [ref=e294]:
                - generic [ref=e295]: Critical
                - generic [ref=e296]:
                  - link "Critical finding F-0085 on M-0104 (Rank-ordering weakened in the latest period) is 260 days past due." [ref=e297] [cursor=pointer]:
                    - /url: /models/M-0104
                  - generic [ref=e298]: "Source: finding F-0085"
              - listitem [ref=e299]:
                - generic [ref=e300]: Critical
                - generic [ref=e301]:
                  - link "Critical finding F-0189 on M-0242 (Assumption log incomplete) is 73 days past due." [ref=e302] [cursor=pointer]:
                    - /url: /models/M-0242
                  - generic [ref=e303]: "Source: finding F-0189"
              - listitem [ref=e304]:
                - generic [ref=e305]: Critical
                - generic [ref=e306]:
                  - link "Critical finding F-0193 on M-0244 (Production code differs from the validated version) is 115 days past due." [ref=e307] [cursor=pointer]:
                    - /url: /models/M-0244
                  - generic [ref=e308]: "Source: finding F-0193"
              - listitem [ref=e309]:
                - generic [ref=e310]: Critical
                - generic [ref=e311]:
                  - link "High-tier M-0015 Retail LGD Model is 24 days overdue for revalidation." [ref=e312] [cursor=pointer]:
                    - /url: /models/M-0015
                  - generic [ref=e313]: "Source: model M-0015"
              - listitem [ref=e314]:
                - generic [ref=e315]: Critical
                - generic [ref=e316]:
                  - link "High-tier M-0042 ALM Interest Rate Risk is 52 days overdue for revalidation." [ref=e317] [cursor=pointer]:
                    - /url: /models/M-0042
                  - generic [ref=e318]: "Source: model M-0042"
              - listitem [ref=e319]:
                - generic [ref=e320]: Critical
                - generic [ref=e321]:
                  - link "High-tier M-0188 Branch Expense Model v2 is 87 days overdue for revalidation." [ref=e322] [cursor=pointer]:
                    - /url: /models/M-0188
                  - generic [ref=e323]: "Source: model M-0188"
            - paragraph [ref=e324]:
              - link "1 segregation-of-duties breach(es)" [ref=e325] [cursor=pointer]:
                - /url: /operations?flag=sod_breach
          - generic [ref=e326]:
            - heading "Revalidation timeline 31 models in the Revalidation column" [level=4] [ref=e327]:
              - text: Revalidation timeline
              - generic [ref=e328]: 31 models in the Revalidation column
            - table [ref=e330]:
              - rowgroup [ref=e331]:
                - row [ref=e332]:
                  - columnheader "Model" [ref=e333]
                  - columnheader "Tier" [ref=e334]
                  - columnheader "Owner" [ref=e335]
                  - columnheader "Last validation" [ref=e336]
                  - columnheader "Due" [ref=e337]
                  - columnheader "Days" [ref=e338]
                  - columnheader "Outcome" [ref=e339]
                  - columnheader "Status" [ref=e340]
              - rowgroup [ref=e341]:
                - row [ref=e342]:
                  - cell [ref=e343]:
                    - link "M-0188" [ref=e344] [cursor=pointer]:
                      - /url: /models/M-0188
                    - text: Branch Expense Model v2
                  - cell "High" [ref=e345]
                  - cell "U-201" [ref=e347]
                  - cell "7/5/2024" [ref=e348]
                  - cell "7/5/2026" [ref=e349]
                  - cell "87d overdue" [ref=e350]
                  - cell "Approved" [ref=e352]
                  - cell "Overdue" [ref=e354]
                - row [ref=e356]:
                  - cell [ref=e357]:
                    - link "M-0110" [ref=e358] [cursor=pointer]:
                      - /url: /models/M-0110
                    - text: HELOC Scorecard Model
                  - cell "Medium" [ref=e359]
                  - cell "U-206" [ref=e361]
                  - cell "8/5/2025" [ref=e362]
                  - cell "8/5/2026" [ref=e363]
                  - cell "56d overdue" [ref=e364]
                  - cell "Approved" [ref=e366]
                  - cell "Overdue" [ref=e368]
                - row [ref=e370]:
                  - cell [ref=e371]:
                    - link "M-0042" [ref=e372] [cursor=pointer]:
                      - /url: /models/M-0042
                    - text: ALM Interest Rate Risk
                  - cell "High" [ref=e373]
                  - cell "U-115" [ref=e375]
                  - cell "8/9/2025" [ref=e376]
                  - cell "8/9/2026" [ref=e377]
                  - cell "52d overdue" [ref=e378]
                  - cell "Approved" [ref=e380]
                  - cell "Overdue" [ref=e382]
                - row [ref=e384]:
                  - cell [ref=e385]:
                    - link "M-0050" [ref=e386] [cursor=pointer]:
                      - /url: /models/M-0050
                    - text: Wealth Lending PD Model
                  - cell "Medium" [ref=e387]
                  - cell "U-205" [ref=e389]
                  - cell "8/26/2024" [ref=e390]
                  - cell "8/26/2026" [ref=e391]
                  - cell "35d overdue" [ref=e392]
                  - cell "Approved" [ref=e394]
                  - cell "Overdue" [ref=e396]
                - row [ref=e398]:
                  - cell [ref=e399]:
                    - link "M-0074" [ref=e400] [cursor=pointer]:
                      - /url: /models/M-0074
                    - text: Credit Card Scorecard Model
                  - cell "Medium" [ref=e401]
                  - cell "U-204" [ref=e403]
                  - cell "9/2/2024" [ref=e404]
                  - cell "9/2/2026" [ref=e405]
                  - cell "28d overdue" [ref=e406]
                  - cell "Approved" [ref=e408]
                  - cell "Overdue" [ref=e410]
                - row [ref=e412]:
                  - cell [ref=e413]:
                    - link "M-0015" [ref=e414] [cursor=pointer]:
                      - /url: /models/M-0015
                    - text: Retail LGD Model
                  - cell "High" [ref=e415]
                  - cell "U-103" [ref=e417]
                  - cell "9/6/2025" [ref=e418]
                  - cell "9/6/2026" [ref=e419]
                  - cell "24d overdue" [ref=e420]
                  - cell "Conditional" [ref=e422]
                  - cell "Overdue" [ref=e424]
                - row [ref=e426]:
                  - cell [ref=e427]:
                    - link "M-0223" [ref=e428] [cursor=pointer]:
                      - /url: /models/M-0223
                    - text: Securities Portfolio Liquidity Model v2
                  - cell "Medium" [ref=e429]
                  - cell "U-003" [ref=e431]
                  - cell "3/23/2026" [ref=e432]
                  - cell "9/23/2026" [ref=e433]
                  - cell "7d overdue" [ref=e434]
                  - cell "Approved" [ref=e436]
                  - cell "Overdue" [ref=e438]
                - row [ref=e440]:
                  - cell [ref=e441]:
                    - link "M-0219" [ref=e442] [cursor=pointer]:
                      - /url: /models/M-0219
                    - text: Credit Card EAD Model v3
                  - cell "Low" [ref=e443]
                  - cell "U-007" [ref=e445]
                  - cell "9/24/2025" [ref=e446]
                  - cell "9/24/2026" [ref=e447]
                  - cell "6d overdue" [ref=e448]
                  - cell "Conditional" [ref=e450]
                  - cell "Overdue" [ref=e452]
                - row [ref=e454]:
                  - cell [ref=e455]:
                    - link "M-0103" [ref=e456] [cursor=pointer]:
                      - /url: /models/M-0103
                    - text: Operational Scenario Model
                  - cell "Medium" [ref=e457]
                  - cell "U-201" [ref=e459]
                  - cell "9/30/2024" [ref=e460]
                  - cell "9/30/2026" [ref=e461]
                  - cell "0d" [ref=e462]
                  - cell "Approved" [ref=e464]
                  - cell "Due Soon" [ref=e466]
                - row [ref=e468]:
                  - cell [ref=e469]:
                    - link "M-0204" [ref=e470] [cursor=pointer]:
                      - /url: /models/M-0204
                    - text: Commercial & Industrial LGD Model v3
                  - cell "Medium" [ref=e471]
                  - cell "U-205" [ref=e473]
                  - cell "9/30/2025" [ref=e474]
                  - cell "9/30/2026" [ref=e475]
                  - cell "0d" [ref=e476]
                  - cell "Approved" [ref=e478]
                  - cell "Due Soon" [ref=e480]
                - row [ref=e482]:
                  - cell [ref=e483]:
                    - link "M-0036" [ref=e484] [cursor=pointer]:
                      - /url: /models/M-0036
                    - text: Non-maturity Deposit Liquidity Model
                  - cell "Low" [ref=e485]
                  - cell "U-003" [ref=e487]
                  - cell "10/5/2025" [ref=e488]
                  - cell "10/5/2026" [ref=e489]
                  - cell "5d" [ref=e490]
                  - cell "Approved" [ref=e492]
                  - cell "Due Soon" [ref=e494]
                - row [ref=e496]:
                  - cell [ref=e497]:
                    - link "M-0098" [ref=e498] [cursor=pointer]:
                      - /url: /models/M-0098
                    - text: Non-maturity Deposit Prepayment Model v2
                  - cell "Medium" [ref=e499]
                  - cell "U-201" [ref=e501]
                  - cell "10/6/2025" [ref=e502]
                  - cell "10/6/2026" [ref=e503]
                  - cell "6d" [ref=e504]
                  - cell "Approved" [ref=e506]
                  - cell "Due Soon" [ref=e508]
                - row [ref=e510]:
                  - cell [ref=e511]:
                    - link "M-0133" [ref=e512] [cursor=pointer]:
                      - /url: /models/M-0133
                    - text: Student Lending Collections Model
                  - cell "High" [ref=e513]
                  - cell "U-203" [ref=e515]
                  - cell "10/9/2024" [ref=e516]
                  - cell "10/9/2026" [ref=e517]
                  - cell "9d" [ref=e518]
                  - cell "Approved" [ref=e520]
                  - cell "Due Soon" [ref=e522]
                - row [ref=e524]:
                  - cell [ref=e525]:
                    - link "M-0217" [ref=e526] [cursor=pointer]:
                      - /url: /models/M-0217
                    - text: Commercial IFRS 9 Model v3
                  - cell "Medium" [ref=e527]
                  - cell "U-007" [ref=e529]
                  - cell "10/9/2025" [ref=e530]
                  - cell "10/9/2026" [ref=e531]
                  - cell "9d" [ref=e532]
                  - cell "Approved" [ref=e534]
                  - cell "Due Soon" [ref=e536]
                - row [ref=e538]:
                  - cell [ref=e539]:
                    - link "M-0048" [ref=e540] [cursor=pointer]:
                      - /url: /models/M-0048
                    - text: Liquidity Stress Model
                  - cell "High" [ref=e541]
                  - cell "U-118" [ref=e543]
                  - cell "4/17/2026" [ref=e544]
                  - cell "10/17/2026" [ref=e545]
                  - cell "17d" [ref=e546]
                  - cell "Approved" [ref=e548]
                  - cell "Due Soon" [ref=e550]
                - row [ref=e552]:
                  - cell [ref=e553]:
                    - link "M-0236" [ref=e554] [cursor=pointer]:
                      - /url: /models/M-0236
                    - text: HELOC Rating Model v2
                  - cell "Low" [ref=e555]
                  - cell "U-201" [ref=e557]
                  - cell "10/17/2025" [ref=e558]
                  - cell "10/17/2026" [ref=e559]
                  - cell "17d" [ref=e560]
                  - cell "Approved" [ref=e562]
                  - cell "Due Soon" [ref=e564]
                - row [ref=e566]:
                  - cell [ref=e567]:
                    - link "M-0214" [ref=e568] [cursor=pointer]:
                      - /url: /models/M-0214
                    - text: Fee Income Expense Model v4
                  - cell "Medium" [ref=e569]
                  - cell "U-007" [ref=e571]
                  - cell "10/22/2025" [ref=e572]
                  - cell "10/22/2026" [ref=e573]
                  - cell "22d" [ref=e574]
                  - cell "Conditional" [ref=e576]
                  - cell "Due Soon" [ref=e578]
                - row [ref=e580]:
                  - cell [ref=e581]:
                    - link "M-0107" [ref=e582] [cursor=pointer]:
                      - /url: /models/M-0107
                    - text: Dealer Floorplan Collections Model
                  - cell "Medium" [ref=e583]
                  - cell "U-203" [ref=e585]
                  - cell "10/23/2024" [ref=e586]
                  - cell "10/23/2026" [ref=e587]
                  - cell "23d" [ref=e588]
                  - cell "Approved" [ref=e590]
                  - cell "Due Soon" [ref=e592]
                - row [ref=e594]:
                  - cell [ref=e595]:
                    - link "M-0253" [ref=e596] [cursor=pointer]:
                      - /url: /models/M-0253
                    - text: CRE CECL Model
                  - cell "High" [ref=e597]
                  - cell "U-204" [ref=e599]
                  - cell "10/23/2025" [ref=e600]
                  - cell "10/23/2026" [ref=e601]
                  - cell "23d" [ref=e602]
                  - cell "Approved" [ref=e604]
                  - cell "Due Soon" [ref=e606]
                - row [ref=e608]:
                  - cell [ref=e609]:
                    - link "M-0255" [ref=e610] [cursor=pointer]:
                      - /url: /models/M-0255
                    - text: Securities CECL Model v2
                  - cell "High" [ref=e611]
                  - cell "U-201" [ref=e613]
                  - cell "4/23/2026" [ref=e614]
                  - cell "10/23/2026" [ref=e615]
                  - cell "23d" [ref=e616]
                  - cell "Approved" [ref=e618]
                  - cell "Due Soon" [ref=e620]
                - row [ref=e622]:
                  - cell [ref=e623]:
                    - link "M-0170" [ref=e624] [cursor=pointer]:
                      - /url: /models/M-0170
                    - text: Operating Expense Climate Model v3
                  - cell "Medium" [ref=e625]
                  - cell "U-204" [ref=e627]
                  - cell "10/24/2025" [ref=e628]
                  - cell "10/24/2026" [ref=e629]
                  - cell "24d" [ref=e630]
                  - cell "Approved" [ref=e632]
                  - cell "Due Soon" [ref=e634]
                - row [ref=e636]:
                  - cell [ref=e637]:
                    - link "M-0062" [ref=e638] [cursor=pointer]:
                      - /url: /models/M-0062
                    - text: Fee Income Revenue Model v2
                  - cell "High" [ref=e639]
                  - cell "U-204" [ref=e641]
                  - cell "10/28/2025" [ref=e642]
                  - cell "10/28/2026" [ref=e643]
                  - cell "28d" [ref=e644]
                  - cell "Approved" [ref=e646]
                  - cell "Due Soon" [ref=e648]
                - row [ref=e650]:
                  - cell [ref=e651]:
                    - link "M-0138" [ref=e652] [cursor=pointer]:
                      - /url: /models/M-0138
                    - text: Branch Climate Model v2
                  - cell "Medium" [ref=e653]
                  - cell "U-203" [ref=e655]
                  - cell "10/29/2025" [ref=e656]
                  - cell "10/29/2026" [ref=e657]
                  - cell "29d" [ref=e658]
                  - cell "Approved" [ref=e660]
                  - cell "Due Soon" [ref=e662]
                - row [ref=e664]:
                  - cell [ref=e665]:
                    - link "M-0007" [ref=e666] [cursor=pointer]:
                      - /url: /models/M-0007
                    - text: Small Business Scorecard Model
                  - cell "High" [ref=e667]
                  - cell "U-203" [ref=e669]
                  - cell "11/9/2025" [ref=e670]
                  - cell "11/9/2026" [ref=e671]
                  - cell "40d" [ref=e672]
                  - cell "Approved" [ref=e674]
                  - cell "Scheduled" [ref=e676]
                - row [ref=e678]:
                  - cell [ref=e679]:
                    - link "M-0070" [ref=e680] [cursor=pointer]:
                      - /url: /models/M-0070
                    - text: HELOC EAD Model
                  - cell "Low" [ref=e681]
                  - cell "U-201" [ref=e683]
                  - cell "11/11/2024" [ref=e684]
                  - cell "11/11/2026" [ref=e685]
                  - cell "42d" [ref=e686]
                  - cell "Approved" [ref=e688]
                  - cell "Scheduled" [ref=e690]
                - row [ref=e692]:
                  - cell [ref=e693]:
                    - link "M-0102" [ref=e694] [cursor=pointer]:
                      - /url: /models/M-0102
                    - text: Commercial IFRS 9 Model
                  - cell "Medium" [ref=e695]
                  - cell "U-003" [ref=e697]
                  - cell "11/14/2025" [ref=e698]
                  - cell "11/14/2026" [ref=e699]
                  - cell "45d" [ref=e700]
                  - cell "Approved" [ref=e702]
                  - cell "Scheduled" [ref=e704]
                - row [ref=e706]:
                  - cell [ref=e707]:
                    - link "M-0029" [ref=e708] [cursor=pointer]:
                      - /url: /models/M-0029
                    - text: Mortgage ALM/IRR Model
                  - cell "High" [ref=e709]
                  - cell "U-007" [ref=e711]
                  - cell "11/17/2025" [ref=e712]
                  - cell "11/17/2026" [ref=e713]
                  - cell "48d" [ref=e714]
                  - cell "Approved" [ref=e716]
                  - cell "Scheduled" [ref=e718]
                - row [ref=e720]:
                  - cell [ref=e721]:
                    - link "M-0228" [ref=e722] [cursor=pointer]:
                      - /url: /models/M-0228
                    - text: Operating Expense Volume Model
                  - cell "High" [ref=e723]
                  - cell "U-201" [ref=e725]
                  - cell "11/19/2025" [ref=e726]
                  - cell "11/19/2026" [ref=e727]
                  - cell "50d" [ref=e728]
                  - cell "Approved" [ref=e730]
                  - cell "Scheduled" [ref=e732]
                - row [ref=e734]:
                  - cell [ref=e735]:
                    - link "M-0116" [ref=e736] [cursor=pointer]:
                      - /url: /models/M-0116
                    - text: Operating Expense Climate Model
                  - cell "Medium" [ref=e737]
                  - cell "U-007" [ref=e739]
                  - cell "11/20/2025" [ref=e740]
                  - cell "11/20/2026" [ref=e741]
                  - cell "51d" [ref=e742]
                  - cell "Approved" [ref=e744]
                  - cell "Scheduled" [ref=e746]
                - row [ref=e748]:
                  - cell [ref=e749]:
                    - link "M-0134" [ref=e750] [cursor=pointer]:
                      - /url: /models/M-0134
                    - text: Student Lending EAD Model v2
                  - cell "High" [ref=e751]
                  - cell "U-201" [ref=e753]
                  - cell "11/20/2025" [ref=e754]
                  - cell "11/20/2026" [ref=e755]
                  - cell "51d" [ref=e756]
                  - cell "Conditional" [ref=e758]
                  - cell "Scheduled" [ref=e760]
                - row [ref=e762]:
                  - cell [ref=e763]:
                    - link "M-0106" [ref=e764] [cursor=pointer]:
                      - /url: /models/M-0106
                    - text: Wholesale Funding Prepayment Model
                  - cell "Low" [ref=e765]
                  - cell "U-003" [ref=e767]
                  - cell "11/28/2025" [ref=e768]
                  - cell "11/28/2026" [ref=e769]
                  - cell "59d" [ref=e770]
                  - cell "Approved" [ref=e772]
                  - cell "Scheduled" [ref=e774]
        - generic [ref=e776]:
          - generic [ref=e777]:
            - generic [ref=e778]: Monitoring breaches & completion
            - text: Monitoring runs, KPI results and breaches arrive with Model Monitoring (Phase 6).
          - generic [ref=e779]:
            - generic [ref=e780]: Data-quality health
            - text: CDE and data-quality health arrive with Data Audit (Phase 7).
```

# Test source

```ts
  125 |   // the first reset could finish and the retry then collided with its own first attempt (H-12).
  126 |   test.setTimeout(900_000);
  127 |   await signInAs(page, "Admin");
  128 |   // `documents` is part of the snapshot because FT-04 lost all 1,116 of them on a single reset and
  129 |   // nothing here noticed: the counts were equal both times, so determinism alone passes on an empty
  130 |   // Document Centre. The absolute assertion below is what catches it.
  131 |   const snapshot = () => ({
  132 |     models: dbCount("model"), users: dbCount("app_user"), validations: dbCount("validation"),
  133 |     findings: dbCount("finding"), approvals: dbCount("approval"), policy: dbCount("policy_setting"),
  134 |     documents: dbCount("document"),
  135 |   });
  136 |   // A reset deletes and reloads `app_user`, so the acting token stops working part way through and
  137 |   // even signing in again fails for a moment. The token is therefore re-read when it is refused
  138 |   // rather than captured once (part of harness defect H-10; the product side is plan BL.1).
  139 |   const asAdmin = async (): Promise<Record<string, string>> => {
  140 |     const resp = await page.request.post("/api/auth/login", { data: { user_id: "U-001", role: "Admin" } });
  141 |     if (!resp.ok()) return {};
  142 |     return { Authorization: `Bearer ${(await resp.json()).access_token}` };
  143 |   };
  144 | 
  145 |   // A reset that has not finished, read straight from the test database rather than from the API:
  146 |   // mid-reset `app_user` is empty for a moment, so nothing can be asked over HTTP. Since G1.32 the
  147 |   // only answer to "is a reset running?" is the `reset_lock` row (`reset_service.reset_in_progress`).
  148 |   // The old batch-status inference (H-21) is what the product itself stopped using: both batches
  149 |   // are terminal while the seeded example report is written, so the probe could stop early.
  150 |   const resetInFlight = () => dbCount("reset_lock", "holder IS NOT NULL");
  151 | 
  152 |   /**
  153 |    * GEN-04: a second reset, while one is running, is refused with a conflict naming the batch in
  154 |    * flight — and no second job is submitted.
  155 |    *
  156 |    * The criterion was tagged on this scenario but never asserted, so the tag was a false coverage
  157 |    * signal: two *sequential* resets prove determinism, not the guard. 401 and 403 are retried
  158 |    * rather than failed, because the reset deletes `app_user` and for a second or two there is
  159 |    * nobody to authenticate as (plan BL.1) — an unanswered question, not a wrong answer.
  160 |    */
  161 |   const probeConcurrentReset = async () => {
  162 |     const batchesBefore = dbCount("import_batch", "source IN ('reset','seed')");
  163 |     let verdict = "the reset finished before a second one could be attempted";
  164 |     const deadline = Date.now() + 20_000;
  165 |     while (Date.now() < deadline) {
  166 |       if (resetInFlight() === 0) break;
  167 |       const resp = await page.request.post("/api/admin/reset", { headers: await asAdmin() });
  168 |       const text = await resp.text();
  169 |       if (resp.status() === 409) {
  170 |         expect(text, "the refusal names the batch in flight").toMatch(/batch B-\d{8}-\d{3}/);
  171 |         verdict = "refused";
  172 |         break;
  173 |       }
  174 |       if (resp.status() === 202) {
  175 |         verdict = `a second reset was accepted while one was running: ${text}`;
  176 |         break;
  177 |       }
  178 |       if (resp.status() >= 500) {
  179 |         // TR-70 (G1.32): a refused second reset met SQLite's write lock and answered 500. GEN-04
  180 |         // says conflict; a 500 is a wrong answer, not an unanswered question.
  181 |         verdict = `a second reset during a running one answered ${resp.status()}: ${text}`;
  182 |         break;
  183 |       }
  184 |       await page.waitForTimeout(300);  // 401/403: mid-delete, ask again
  185 |     }
  186 |     expect(verdict, "GEN-04: a concurrent reset must be refused with a conflict").toBe("refused");
  187 |     expect(dbCount("import_batch", "source IN ('reset','seed')"),
  188 |       "GEN-04: the refused reset must not have created a batch").toBe(batchesBefore);
  189 |   };
  190 | 
  191 |   /**
  192 |    * CR-67 (G1.34): generating the model risk report while the reset lock is held is refused with a
  193 |    * conflict. A report generated then would be stored for good over a half-loaded portfolio and, as
  194 |    * the newest, become the predecessor the next report diffs against. Admin holds REPORT_GENERATE,
  195 |    * so the permission check passes and the answer is the lock's. "Nothing stored" is read twice: no
  196 |    * `generate` audit event (the audit trail survives a reset), and once the reset is idle the only
  197 |    * stored report is the seeded example (checked in `reset()` below). Same retry rules as GEN-04.
  198 |    */
  199 |   const probeReportDuringReset = async () => {
  200 |     const generateEvents = () =>
  201 |       dbCount("audit_event", "entity = 'model_risk_report' AND action = 'generate'");
  202 |     const auditBefore = generateEvents();
  203 |     let verdict = "the reset finished before a report could be attempted";
  204 |     const deadline = Date.now() + 20_000;
  205 |     while (Date.now() < deadline) {
  206 |       if (resetInFlight() === 0) break;
  207 |       const resp = await page.request.post("/api/reports/model-risk", { headers: await asAdmin() });
  208 |       const text = await resp.text();
  209 |       if (resp.status() === 409) {
  210 |         expect(text, "CR-67: the refusal says a reset is running").toMatch(/reset is running/i);
  211 |         verdict = "refused";
  212 |         break;
  213 |       }
  214 |       if (resp.ok()) {
  215 |         verdict = `a report was generated while a reset was running: ${text.slice(0, 200)}`;
  216 |         break;
  217 |       }
  218 |       if (resp.status() >= 500) {
  219 |         verdict = `report generation during a reset answered ${resp.status()}: ${text.slice(0, 200)}`;
  220 |         break;
  221 |       }
  222 |       await page.waitForTimeout(300);  // 401/403: mid-delete, ask again (BL.1)
  223 |     }
  224 |     expect(verdict, "CR-67: report generation during a reset must be refused with a conflict")
> 225 |       .toBe("refused");
      |        ^ Error: CR-67: report generation during a reset must be refused with a conflict
  226 |     expect(generateEvents(), "CR-67: the refused generation wrote no audit event").toBe(auditBefore);
  227 |   };
  228 | 
  229 |   const reset = async (probe: "reset" | "report" | false = false) => {
  230 |     const resp = await page.request.post("/api/admin/reset", { headers: await asAdmin() });
  231 |     expect(resp.status(), await resp.text()).toBe(202);
  232 |     if (probe === "reset") await probeConcurrentReset();
  233 |     if (probe === "report") await probeReportDuringReset();
  234 | 
  235 |     // Wait for the *reset*, not for the batch the caller is handed. A reset creates two batches —
  236 |     // the seed import and then one for the 1116 evidence files — so the id in the response reports
  237 |     // Completed while the reset is still writing. Polling it was harness defect H-10: the next
  238 |     // reset collided with the one still running. `/api/admin/reset/status` covers the whole
  239 |     // operation, which is why G0.18 added it.
  240 |     await expect
  241 |       .poll(async () => {
  242 |         const status = await page.request.get("/api/admin/reset/status", { headers: await asAdmin() });
  243 |         if (!status.ok()) return "unavailable";   // mid-reset there is briefly no one to authenticate as
  244 |         return (await status.json()).in_progress ? "running" : "idle";
  245 |       }, { timeout: 300_000, intervals: [2000], message: "the reset never finished" })
  246 |       .toBe("idle");
  247 | 
  248 |     // And it finished rather than failed: a reset that ends in Failed must not be read as a
  249 |     // successful one, which the old `/Completed|Failed/` poll allowed before asserting counts.
  250 |     const batches = await page.request.get("/api/imports/batches", { headers: await asAdmin() });
  251 |     const seedBatches = ((await batches.json()) as { source: string; status: string }[])
  252 |       .filter((b) => b.source === "reset" || b.source === "seed");
  253 |     expect(seedBatches.length, "the reset produced its batches").toBeGreaterThan(0);
  254 |     for (const b of seedBatches) {
  255 |       expect(b.status, `reset batch ${JSON.stringify(b)}`).not.toBe("Failed");
  256 |     }
  257 |     // GEN-05 (G1.32): the signal reports how the reset ended, and it ended Completed. Read once the
  258 |     // lock is free, so "finished" is only reported when a further reset would be accepted.
  259 |     const final = await page.request.get("/api/admin/reset/status", { headers: await asAdmin() });
  260 |     const body = await final.json() as { in_progress: boolean; last_outcome: string | null };
  261 |     expect(body.in_progress, "GEN-05: idle means the lock is free").toBe(false);
  262 |     expect(body.last_outcome, `GEN-05: the reset ended ${JSON.stringify(body)}`).toBe("Completed");
  263 |     expect(dbCount("reset_lock", "holder IS NOT NULL"), "GEN-05: the lock is released").toBe(0);
  264 |     // The reset's last write is the seeded example report (G1.26); it must exist once idle.
  265 |     expect(dbCount("model_risk_report", "is_seeded = 1"),
  266 |       "GEN-05: idle only after the seeded example is written").toBe(1);
  267 |     // A reset clears the report history and seeds one example, so anything else stored here was
  268 |     // generated during the reset — which CR-67 forbids.
  269 |     expect(dbCount("model_risk_report"), "CR-67: no report was stored during the reset").toBe(1);
  270 |   };
  271 | 
  272 |   await reset("reset");   // the first reset carries the GEN-04 concurrency probe
  273 |   const first = snapshot();
  274 |   await reset("report");  // the second carries CR-67's report-during-reset probe (G1.34)
  275 |   const second = snapshot();
  276 |   // The Command Center has been open since sign-in and still shows what it fetched *before* the
  277 |   // first reset — 260 models, because FS-03 and FS-04 added four. Reload, so the saved evidence is
  278 |   // the post-reset state and not a stale tile, and check the screen agrees with the database.
  279 |   await page.reload();
  280 |   await expect(page.locator(".tile", { hasText: "Total models" }).first(),
  281 |     "CC-01 after a reset: the tile equals the stored model count")
  282 |     .toContainText(String(second.models), { timeout: 15_000 });
  283 |   await checkpoint(page, "FS-21_after_two_resets");
  284 |   expect(second, "GEN-01: a reset at the same business date is deterministic").toEqual(first);
  285 |   expect(first.models).toBe(256);
  286 |   // Pinned on purpose: GEN-01's claim is the *documented* distribution, so this number has to be
  287 |   // edited deliberately when the bootstrap gains a setting rather than read from the database it is
  288 |   // checking. Gate 1 added `regulatory_framework` and its companion, taking it from 70 to 72
  289 |   // (harness defect H-20; `functional-scenarios.md` line 2 carries the same figure).
  290 |   expect(first.policy).toBe(72);
  291 |   expect(first.documents, "FT-04: a reset must reload the evidence, not just delete it")
  292 |     .toBeGreaterThan(1000);
  293 | });
  294 | 
  295 | 
  296 | test.fixme("FS-30 MON-01 MON-02 MON-03 monitoring plan, metrics, results and breach", async () => {
  297 |   // Not built (Phase 6).
  298 | });
  299 | 
  300 | test.fixme("FS-31 REG-01 REG-14 inventory classes, vendor models, challenges, dependencies",
  301 |   async () => {
  302 |     // Not built (Phase 2A, deferred D12). The report half of this scenario moved to FS-25.
  303 |   });
  304 | 
  305 | test.fixme("FS-32 CDE and DQ results load and appear on Data Audit", async () => {
  306 |   // Not built (Phase 7); criteria set §76B does not exist yet (decision D8 unrecorded).
  307 | });
  308 | 
```