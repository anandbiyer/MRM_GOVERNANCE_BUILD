# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: ..\functional\reports.spec.ts >> FS-25 REG-16 REG-17 D14 D17 S13 the seeded example discloses its dates everywhere; decisions sit in the changes section
- Location: functional\reports.spec.ts:124:5

# Error details

```
Error: D17: generated_at is no longer shaped to 09:00 on the illustrative date

expect(received).toBe(expected) // Object.is equality

Expected: false
Received: true
```

# Page snapshot

```yaml
- generic [ref=e2]:
  - banner [ref=e3]:
    - generic [ref=e4]:
      - generic [ref=e5]: MRM Governance MIS
      - generic [ref=e6]: Model risk inventory, validation & monitoring
    - generic [ref=e7]:
      - generic [ref=e8]: checking…
      - combobox "Act as user and role" [ref=e9]:
        - option "Admin — Priya Raman (U-001)"
        - option "Platform Administrator — Daniel Okafor (U-002)"
        - option "Model Owner — Helen Carter (U-003)"
        - option "Model Owner — Marcus Lee (U-007)"
        - option "Validator — Sarah Patel (U-014)"
        - option "Validator — Tomasz Nowak (U-016)"
        - option "Model Developer — Aisha Khan (U-021)"
        - option "Data Owner — Carlos Mendes (U-031)"
        - option "Executive — Robert Diaz (U-040)"
        - option "MRC Member — Robert Diaz (U-040)"
        - option "Auditor — Grace Liu (U-041)" [selected]
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
          - generic [ref=e31]: Control
          - heading "Model Risk Report" [level=1] [ref=e32]
          - paragraph [ref=e33]: A point-in-time report for senior management and the MRC, built from the governance records. Every figure equals the Command Center on the same business date.
        - paragraph [ref=e35]: You can read and download reports. Generating one needs the report:generate permission (Admin, MRC Member or Validator).
        - generic [ref=e36]:
          - heading "Earlier reports" [level=3] [ref=e37]
          - table [ref=e39]:
            - rowgroup [ref=e40]:
              - row [ref=e41]:
                - columnheader "Report" [ref=e42]
                - columnheader "Business date" [ref=e43]
                - columnheader "Generated" [ref=e44]
                - columnheader "By" [ref=e45]
                - columnheader [ref=e46]
            - rowgroup [ref=e47]:
              - row [ref=e48]:
                - cell "MRR-20260930-002" [ref=e49]
                - cell "9/30/2026" [ref=e50]
                - cell "10/16/2026, 12:49:55 AM" [ref=e51]
                - cell "U-014" [ref=e52]
                - cell [ref=e53]:
                  - button "Open" [ref=e54] [cursor=pointer]
                  - button "PDF" [ref=e55] [cursor=pointer]
              - row [ref=e56]:
                - cell "MRR-20260930-001" [ref=e57]
                - cell "9/30/2026" [ref=e58]
                - cell "10/16/2026, 12:49:54 AM" [ref=e59]
                - cell "U-014" [ref=e60]
                - cell [ref=e61]:
                  - button "Open" [ref=e62] [cursor=pointer]
                  - button "PDF" [ref=e63] [cursor=pointer]
              - row [ref=e64]:
                - 'cell "MRR-20260831-001 Seeded example Seeded example: figures computed from current seed data on 2026-09-30, dated 2026-08-31 for illustration." [ref=e65]':
                  - text: MRR-20260831-001
                  - generic [ref=e66]: Seeded example
                  - generic [ref=e67]: "Seeded example: figures computed from current seed data on 2026-09-30, dated 2026-08-31 for illustration."
                - cell "8/31/2026" [ref=e68]
                - cell "8/31/2026, 5:00:00 AM" [ref=e69]
                - cell "system" [ref=e70]
                - cell [ref=e71]:
                  - button "Showing" [active] [ref=e72] [cursor=pointer]
                  - button "PDF" [ref=e73] [cursor=pointer]
        - generic [ref=e74]:
          - generic [ref=e75]:
            - heading "SR 26-2 / OCC Bulletin 2026-13 Seeded example" [level=3] [ref=e76]:
              - text: SR 26-2 / OCC Bulletin 2026-13
              - generic [ref=e77]: Seeded example
            - paragraph [ref=e78]:
              - text: Business date 8/31/2026 · MRR-20260831-001 · generated by system at 8/31/2026, 5:00:00 AMContent hash
              - generic [ref=e79]: ec6a0b326d224566…
              - text: Figures reconciled with the
              - link "Command Center" [ref=e80] [cursor=pointer]:
                - /url: /
              - text: "at generation, 8/31/2026, 5:00:00 AM.Seeded example: figures computed from current seed data on 2026-09-30, dated 2026-08-31 for illustration. Its comparison baseline was shaped so the next report has changes to show."
            - button "Download PDF" [ref=e81] [cursor=pointer]
          - generic [ref=e82]:
            - heading "Inventory — 256 models" [level=4] [ref=e83]
            - table [ref=e85]:
              - rowgroup [ref=e86]:
                - row [ref=e87]:
                  - columnheader "Risk tier" [ref=e88]
                  - columnheader "Models" [ref=e89]
                  - columnheader "Share" [ref=e90]
              - rowgroup [ref=e91]:
                - row [ref=e92]:
                  - cell "High" [ref=e93]
                  - cell "89" [ref=e94]
                  - cell "35%" [ref=e95]
                - row [ref=e96]:
                  - cell "Medium" [ref=e97]
                  - cell "106" [ref=e98]
                  - cell "41%" [ref=e99]
                - row [ref=e100]:
                  - cell "Low" [ref=e101]
                  - cell "61" [ref=e102]
                  - cell "24%" [ref=e103]
            - table [ref=e105]:
              - rowgroup [ref=e106]:
                - row [ref=e107]:
                  - columnheader "Stage (as displayed)" [ref=e108]
                  - columnheader "Models" [ref=e109]
                  - columnheader "Share" [ref=e110]
              - rowgroup [ref=e111]:
                - row [ref=e112]:
                  - cell "Initiation" [ref=e113]
                  - cell "6" [ref=e114]
                  - cell "2%" [ref=e115]
                - row [ref=e116]:
                  - cell "Development" [ref=e117]
                  - cell "14" [ref=e118]
                  - cell "5%" [ref=e119]
                - row [ref=e120]:
                  - cell "Validation" [ref=e121]
                  - cell "18" [ref=e122]
                  - cell "7%" [ref=e123]
                - row [ref=e124]:
                  - cell "Implementation" [ref=e125]
                  - cell "11" [ref=e126]
                  - cell "4%" [ref=e127]
                - row [ref=e128]:
                  - cell "Monitoring" [ref=e129]
                  - cell "148" [ref=e130]
                  - cell "58%" [ref=e131]
                - row [ref=e132]:
                  - cell "Revalidation" [ref=e133]
                  - cell "31" [ref=e134]
                  - cell "12%" [ref=e135]
                - row [ref=e136]:
                  - cell "Reg/Audit" [ref=e137]
                  - cell "14" [ref=e138]
                  - cell "5%" [ref=e139]
                - row [ref=e140]:
                  - cell "Retirement" [ref=e141]
                  - cell "14" [ref=e142]
                  - cell "5%" [ref=e143]
            - paragraph [ref=e144]: "Stage is the column the Command Center displays: a model in Monitoring inside its revalidation lead time is shown in Revalidation."
          - generic [ref=e145]:
            - heading "Validation" [level=4] [ref=e146]
            - table [ref=e148]:
              - rowgroup [ref=e149]:
                - row [ref=e150]:
                  - columnheader "Revalidation status" [ref=e151]
                  - columnheader "Models" [ref=e152]
                  - columnheader "Share" [ref=e153]
              - rowgroup [ref=e154]:
                - row [ref=e155]:
                  - cell "Overdue" [ref=e156]
                  - cell "8" [ref=e157]
                  - cell "4%" [ref=e158]
                - row [ref=e159]:
                  - cell "Due Soon" [ref=e160]
                  - cell "15" [ref=e161]
                  - cell "8%" [ref=e162]
                - row [ref=e163]:
                  - cell "Scheduled" [ref=e164]
                  - cell "170" [ref=e165]
                  - cell "88%" [ref=e166]
            - heading "Overdue (8), highest tier first" [level=5] [ref=e167]
            - table [ref=e169]:
              - rowgroup [ref=e170]:
                - row [ref=e171]:
                  - columnheader "model id" [ref=e172]
                  - columnheader "model name" [ref=e173]
                  - columnheader "tier" [ref=e174]
                  - columnheader "owner id" [ref=e175]
                  - columnheader "days overdue" [ref=e176]
              - rowgroup [ref=e177]:
                - row [ref=e178]:
                  - cell "M-0015" [ref=e179]
                  - cell "Retail LGD Model" [ref=e180]
                  - cell "High" [ref=e181]
                  - cell "U-103" [ref=e182]
                  - cell "24" [ref=e183]
                - row [ref=e184]:
                  - cell "M-0042" [ref=e185]
                  - cell "ALM Interest Rate Risk" [ref=e186]
                  - cell "High" [ref=e187]
                  - cell "U-115" [ref=e188]
                  - cell "52" [ref=e189]
                - row [ref=e190]:
                  - cell "M-0188" [ref=e191]
                  - cell "Branch Expense Model v2" [ref=e192]
                  - cell "High" [ref=e193]
                  - cell "U-201" [ref=e194]
                  - cell "87" [ref=e195]
                - row [ref=e196]:
                  - cell "M-0050" [ref=e197]
                  - cell "Wealth Lending PD Model" [ref=e198]
                  - cell "Medium" [ref=e199]
                  - cell "U-205" [ref=e200]
                  - cell "35" [ref=e201]
                - row [ref=e202]:
                  - cell "M-0074" [ref=e203]
                  - cell "Credit Card Scorecard Model" [ref=e204]
                  - cell "Medium" [ref=e205]
                  - cell "U-204" [ref=e206]
                  - cell "28" [ref=e207]
                - row [ref=e208]:
                  - cell "M-0110" [ref=e209]
                  - cell "HELOC Scorecard Model" [ref=e210]
                  - cell "Medium" [ref=e211]
                  - cell "U-206" [ref=e212]
                  - cell "56" [ref=e213]
                - row [ref=e214]:
                  - cell "M-0223" [ref=e215]
                  - cell "Securities Portfolio Liquidity Model v2" [ref=e216]
                  - cell "Medium" [ref=e217]
                  - cell "U-003" [ref=e218]
                  - cell "7" [ref=e219]
                - row [ref=e220]:
                  - cell "M-0219" [ref=e221]
                  - cell "Credit Card EAD Model v3" [ref=e222]
                  - cell "Low" [ref=e223]
                  - cell "U-007" [ref=e224]
                  - cell "6" [ref=e225]
          - generic [ref=e226]:
            - heading "Findings" [level=4] [ref=e227]
            - table [ref=e229]:
              - rowgroup [ref=e230]:
                - row [ref=e231]:
                  - columnheader "Open by severity" [ref=e232]
                  - columnheader "Models" [ref=e233]
                  - columnheader "Share" [ref=e234]
              - rowgroup [ref=e235]:
                - row [ref=e236]:
                  - cell "Critical" [ref=e237]
                  - cell "21" [ref=e238]
                  - cell "14%" [ref=e239]
                - row [ref=e240]:
                  - cell "Medium" [ref=e241]
                  - cell "94" [ref=e242]
                  - cell "64%" [ref=e243]
                - row [ref=e244]:
                  - cell "Low" [ref=e245]
                  - cell "33" [ref=e246]
                  - cell "22%" [ref=e247]
            - table [ref=e249]:
              - rowgroup [ref=e250]:
                - row [ref=e251]:
                  - columnheader "Overdue by severity" [ref=e252]
                  - columnheader "Models" [ref=e253]
                  - columnheader "Share" [ref=e254]
              - rowgroup [ref=e255]:
                - row [ref=e256]:
                  - cell "Critical" [ref=e257]
                  - cell "12" [ref=e258]
                  - cell "14%" [ref=e259]
                - row [ref=e260]:
                  - cell "Medium" [ref=e261]
                  - cell "53" [ref=e262]
                  - cell "62%" [ref=e263]
                - row [ref=e264]:
                  - cell "Low" [ref=e265]
                  - cell "20" [ref=e266]
                  - cell "24%" [ref=e267]
            - heading "Critical and overdue (12)" [level=5] [ref=e268]
            - table [ref=e270]:
              - rowgroup [ref=e271]:
                - row [ref=e272]:
                  - columnheader "finding id" [ref=e273]
                  - columnheader "model id" [ref=e274]
                  - columnheader "title" [ref=e275]
                  - columnheader "days overdue" [ref=e276]
              - rowgroup [ref=e277]:
                - row [ref=e278]:
                  - cell "F-0066" [ref=e279]
                  - cell "M-0074" [ref=e280]
                  - cell "Production code differs from the validated version" [ref=e281]
                  - cell "306" [ref=e282]
                - row [ref=e283]:
                  - cell "F-0085" [ref=e284]
                  - cell "M-0104" [ref=e285]
                  - cell "Rank-ordering weakened in the latest period" [ref=e286]
                  - cell "260" [ref=e287]
                - row [ref=e288]:
                  - cell "F-0159" [ref=e289]
                  - cell "M-0198" [ref=e290]
                  - cell "Source extract does not reconcile to the ledger" [ref=e291]
                  - cell "220" [ref=e292]
                - row [ref=e293]:
                  - cell "F-0026" [ref=e294]
                  - cell "M-0020" [ref=e295]
                  - cell "Rank-ordering weakened in the latest period" [ref=e296]
                  - cell "210" [ref=e297]
                - row [ref=e298]:
                  - cell "F-0072" [ref=e299]
                  - cell "M-0084" [ref=e300]
                  - cell "Production code differs from the validated version" [ref=e301]
                  - cell "172" [ref=e302]
                - row [ref=e303]:
                  - cell "F-0136" [ref=e304]
                  - cell "M-0171" [ref=e305]
                  - cell "Source extract does not reconcile to the ledger" [ref=e306]
                  - cell "163" [ref=e307]
                - row [ref=e308]:
                  - cell "F-0193" [ref=e309]
                  - cell "M-0244" [ref=e310]
                  - cell "Production code differs from the validated version" [ref=e311]
                  - cell "115" [ref=e312]
                - row [ref=e313]:
                  - cell "F-0029" [ref=e314]
                  - cell "M-0021" [ref=e315]
                  - cell "Rank-ordering weakened in the latest period" [ref=e316]
                  - cell "110" [ref=e317]
                - row [ref=e318]:
                  - cell "F-0189" [ref=e319]
                  - cell "M-0242" [ref=e320]
                  - cell "Assumption log incomplete" [ref=e321]
                  - cell "73" [ref=e322]
                - row [ref=e323]:
                  - cell "F-0001" [ref=e324]
                  - cell "M-0012" [ref=e325]
                  - cell "CRE obligor data gap" [ref=e326]
                  - cell "40" [ref=e327]
                - row [ref=e328]:
                  - cell "F-0104" [ref=e329]
                  - cell "M-0125" [ref=e330]
                  - cell "Source extract does not reconcile to the ledger" [ref=e331]
                  - cell "32" [ref=e332]
                - row [ref=e333]:
                  - cell "F-0004" [ref=e334]
                  - cell "M-0015" [ref=e335]
                  - cell "Collateral valuation lag" [ref=e336]
                  - cell "12" [ref=e337]
          - generic [ref=e338]:
            - heading "Approvals" [level=4] [ref=e339]
            - heading "Conditional with open conditions (24)" [level=5] [ref=e340]
            - table [ref=e342]:
              - rowgroup [ref=e343]:
                - row [ref=e344]:
                  - columnheader "model id" [ref=e345]
                  - columnheader "model name" [ref=e346]
                  - columnheader "open conditions" [ref=e347]
                  - columnheader "latest decision" [ref=e348]
              - rowgroup [ref=e349]:
                - row [ref=e350]:
                  - cell "M-0001" [ref=e351]
                  - cell "Loan Volume Balance Model" [ref=e352]
                  - cell "1" [ref=e353]
                  - cell "Conditional" [ref=e354]
                - row [ref=e355]:
                  - cell "M-0012" [ref=e356]
                  - cell "Wholesale PD Model" [ref=e357]
                  - cell "1" [ref=e358]
                  - cell "Conditional" [ref=e359]
                - row [ref=e360]:
                  - cell "M-0015" [ref=e361]
                  - cell "Retail LGD Model" [ref=e362]
                  - cell "1" [ref=e363]
                  - cell "Conditional" [ref=e364]
                - row [ref=e365]:
                  - cell "M-0022" [ref=e366]
                  - cell "Residential Mortgage LGD Model" [ref=e367]
                  - cell "1" [ref=e368]
                  - cell "Conditional" [ref=e369]
                - row [ref=e370]:
                  - cell "M-0038" [ref=e371]
                  - cell "IFRS 9 Stage Allocation" [ref=e372]
                  - cell "1" [ref=e373]
                  - cell "Conditional" [ref=e374]
                - row [ref=e375]:
                  - cell "M-0045" [ref=e376]
                  - cell "Wholesale Funding Liquidity Model" [ref=e377]
                  - cell "1" [ref=e378]
                  - cell "Conditional" [ref=e379]
                - row [ref=e380]:
                  - cell "M-0051" [ref=e381]
                  - cell "Branch Climate Model" [ref=e382]
                  - cell "1" [ref=e383]
                  - cell "Conditional" [ref=e384]
                - row [ref=e385]:
                  - cell "M-0059" [ref=e386]
                  - cell "Securities Portfolio Prepayment Model v2" [ref=e387]
                  - cell "1" [ref=e388]
                  - cell "Conditional" [ref=e389]
                - row [ref=e390]:
                  - cell "M-0065" [ref=e391]
                  - cell "Securities Reserve allocation Model" [ref=e392]
                  - cell "1" [ref=e393]
                  - cell "Conditional" [ref=e394]
                - row [ref=e395]:
                  - cell "M-0071" [ref=e396]
                  - cell "CCAR PPNR Model" [ref=e397]
                  - cell "1" [ref=e398]
                  - cell "Conditional" [ref=e399]
                - row [ref=e400]:
                  - cell "M-0075" [ref=e401]
                  - cell "Treasury ALM/IRR Model v2" [ref=e402]
                  - cell "1" [ref=e403]
                  - cell "Conditional" [ref=e404]
                - row [ref=e405]:
                  - cell "M-0086" [ref=e406]
                  - cell "Credit Card LGD Model v2" [ref=e407]
                  - cell "1" [ref=e408]
                  - cell "Conditional" [ref=e409]
                - row [ref=e410]:
                  - cell "M-0093" [ref=e411]
                  - cell "Trading Book RWA Model v2" [ref=e412]
                  - cell "1" [ref=e413]
                  - cell "Conditional" [ref=e414]
                - row [ref=e415]:
                  - cell "M-0132" [ref=e416]
                  - cell "Treasury Prepayment Model v4" [ref=e417]
                  - cell "1" [ref=e418]
                  - cell "Conditional" [ref=e419]
                - row [ref=e420]:
                  - cell "M-0134" [ref=e421]
                  - cell "Student Lending EAD Model v2" [ref=e422]
                  - cell "1" [ref=e423]
                  - cell "Conditional" [ref=e424]
                - row [ref=e425]:
                  - cell "M-0166" [ref=e426]
                  - cell "Deposit Volume Volume Model v3" [ref=e427]
                  - cell "1" [ref=e428]
                  - cell "Conditional" [ref=e429]
                - row [ref=e430]:
                  - cell "M-0183" [ref=e431]
                  - cell "Credit Card PD Model v4" [ref=e432]
                  - cell "1" [ref=e433]
                  - cell "Conditional" [ref=e434]
                - row [ref=e435]:
                  - cell "M-0193" [ref=e436]
                  - cell "Wholesale Funding Liquidity Model v3" [ref=e437]
                  - cell "1" [ref=e438]
                  - cell "Conditional" [ref=e439]
                - row [ref=e440]:
                  - cell "M-0201" [ref=e441]
                  - cell "Operating Expense Revenue Model v2" [ref=e442]
                  - cell "1" [ref=e443]
                  - cell "Conditional" [ref=e444]
                - row [ref=e445]:
                  - cell "M-0205" [ref=e446]
                  - cell "CRE Reserve allocation Model v4" [ref=e447]
                  - cell "1" [ref=e448]
                  - cell "Conditional" [ref=e449]
                - row [ref=e450]:
                  - cell "M-0214" [ref=e451]
                  - cell "Fee Income Expense Model v4" [ref=e452]
                  - cell "1" [ref=e453]
                  - cell "Conditional" [ref=e454]
                - row [ref=e455]:
                  - cell "M-0232" [ref=e456]
                  - cell "Non-maturity Deposit Funds transfer pricing Model v2" [ref=e457]
                  - cell "1" [ref=e458]
                  - cell "Conditional" [ref=e459]
                - row [ref=e460]:
                  - cell "M-0237" [ref=e461]
                  - cell "CRE Office Collections Model" [ref=e462]
                  - cell "1" [ref=e463]
                  - cell "Conditional" [ref=e464]
                - row [ref=e465]:
                  - cell "M-0247" [ref=e466]
                  - cell "Securities CECL Model" [ref=e467]
                  - cell "1" [ref=e468]
                  - cell "Conditional" [ref=e469]
          - generic [ref=e470]:
            - heading "Governance score — portfolio 92.9" [level=4] [ref=e471]
            - table [ref=e473]:
              - rowgroup [ref=e474]:
                - row [ref=e475]:
                  - columnheader "Score band" [ref=e476]
                  - columnheader "Models" [ref=e477]
                  - columnheader "Share" [ref=e478]
              - rowgroup [ref=e479]:
                - row [ref=e480]:
                  - cell "Below 60" [ref=e481]
                  - cell "2" [ref=e482]
                  - cell "1%" [ref=e483]
                - row [ref=e484]:
                  - cell "60 – 80" [ref=e485]
                  - cell "16" [ref=e486]
                  - cell "7%" [ref=e487]
                - row [ref=e488]:
                  - cell "80 and above" [ref=e489]
                  - cell "224" [ref=e490]
                  - cell "93%" [ref=e491]
            - heading "Lowest scoring" [level=5] [ref=e492]
            - table [ref=e494]:
              - rowgroup [ref=e495]:
                - row [ref=e496]:
                  - columnheader "model id" [ref=e497]
                  - columnheader "model name" [ref=e498]
                  - columnheader "score" [ref=e499]
                  - columnheader "weakest component" [ref=e500]
              - rowgroup [ref=e501]:
                - row [ref=e502]:
                  - cell "M-0125" [ref=e503]
                  - cell "CRE Loss Model v2" [ref=e504]
                  - cell "20" [ref=e505]
                  - cell "documentation" [ref=e506]
                - row [ref=e507]:
                  - cell "M-0085" [ref=e508]
                  - cell "Behavioral Scorecard v2" [ref=e509]
                  - cell "58.3" [ref=e510]
                  - cell "documentation" [ref=e511]
                - row [ref=e512]:
                  - cell "M-0110" [ref=e513]
                  - cell "HELOC Scorecard Model" [ref=e514]
                  - cell "64.7" [ref=e515]
                  - cell "validation_currency" [ref=e516]
                - row [ref=e517]:
                  - cell "M-0050" [ref=e518]
                  - cell "Wealth Lending PD Model" [ref=e519]
                  - cell "65.3" [ref=e520]
                  - cell "validation_currency" [ref=e521]
                - row [ref=e522]:
                  - cell "M-0042" [ref=e523]
                  - cell "ALM Interest Rate Risk" [ref=e524]
                  - cell "65.9" [ref=e525]
                  - cell "validation_currency" [ref=e526]
                - row [ref=e527]:
                  - cell "M-0188" [ref=e528]
                  - cell "Branch Expense Model v2" [ref=e529]
                  - cell "65.9" [ref=e530]
                  - cell "validation_currency" [ref=e531]
                - row [ref=e532]:
                  - cell "M-0076" [ref=e533]
                  - cell "CCAR Loss Forecasting" [ref=e534]
                  - cell "67.6" [ref=e535]
                  - cell "issue_remediation" [ref=e536]
                - row [ref=e537]:
                  - cell "M-0015" [ref=e538]
                  - cell "Retail LGD Model" [ref=e539]
                  - cell "70" [ref=e540]
                  - cell "validation_currency" [ref=e541]
                - row [ref=e542]:
                  - cell "M-0055" [ref=e543]
                  - cell "Revenue Forecasting Model" [ref=e544]
                  - cell "70.6" [ref=e545]
                  - cell "mrc_compliance" [ref=e546]
                - row [ref=e547]:
                  - cell "M-0074" [ref=e548]
                  - cell "Credit Card Scorecard Model" [ref=e549]
                  - cell "72.2" [ref=e550]
                  - cell "validation_currency" [ref=e551]
          - generic [ref=e552]:
            - heading "Documentation — 63.6% complete" [level=4] [ref=e553]
            - table [ref=e555]:
              - rowgroup [ref=e556]:
                - row [ref=e557]:
                  - columnheader "model id" [ref=e558]
                  - columnheader "model name" [ref=e559]
                  - columnheader "lifecycle phase" [ref=e560]
                  - columnheader "missing" [ref=e561]
              - rowgroup [ref=e562]:
                - row [ref=e563]:
                  - cell "M-0001" [ref=e564]
                  - cell "Loan Volume Balance Model" [ref=e565]
                  - cell "Monitoring" [ref=e566]
                  - cell "Validation Report" [ref=e567]
                - row [ref=e568]:
                  - cell "M-0002" [ref=e569]
                  - cell "Card Reserve allocation Model" [ref=e570]
                  - cell "Implementation" [ref=e571]
                  - cell "Terms of Reference,Model Approval/MRC Paper" [ref=e572]
                - row [ref=e573]:
                  - cell "M-0005" [ref=e574]
                  - cell "Basel II IRB Floor Model" [ref=e575]
                  - cell "Retirement" [ref=e576]
                  - cell "Model Development Document" [ref=e577]
                - row [ref=e578]:
                  - cell "M-0008" [ref=e579]
                  - cell "Legacy ALCO NII Model" [ref=e580]
                  - cell "Retirement" [ref=e581]
                  - cell "Model Development Document,Model Approval/MRC Paper" [ref=e582]
                - row [ref=e583]:
                  - cell "M-0011" [ref=e584]
                  - cell "Trading Book Capital Model" [ref=e585]
                  - cell "Monitoring" [ref=e586]
                  - cell "Validation Report" [ref=e587]
                - row [ref=e588]:
                  - cell "M-0016" [ref=e589]
                  - cell "Securities Portfolio Funds transfer pricing Model" [ref=e590]
                  - cell "Monitoring" [ref=e591]
                  - cell "Monitoring Plan" [ref=e592]
                - row [ref=e593]:
                  - cell "M-0021" [ref=e594]
                  - cell "Consumer Capital Model" [ref=e595]
                  - cell "Monitoring" [ref=e596]
                  - cell "Terms of Reference" [ref=e597]
                - row [ref=e598]:
                  - cell "M-0022" [ref=e599]
                  - cell "Residential Mortgage LGD Model" [ref=e600]
                  - cell "Monitoring" [ref=e601]
                  - cell "Terms of Reference,Validation Report" [ref=e602]
                - row [ref=e603]:
                  - cell "M-0026" [ref=e604]
                  - cell "Treasury Liquidity Model" [ref=e605]
                  - cell "Monitoring" [ref=e606]
                  - cell "Monitoring Plan" [ref=e607]
                - row [ref=e608]:
                  - cell "M-0029" [ref=e609]
                  - cell "Mortgage ALM/IRR Model" [ref=e610]
                  - cell "Monitoring" [ref=e611]
                  - cell "Validation Report" [ref=e612]
                - row [ref=e613]:
                  - cell "M-0034" [ref=e614]
                  - cell "Treasury ALM/IRR Model" [ref=e615]
                  - cell "Monitoring" [ref=e616]
                  - cell "Terms of Reference,Validation Report" [ref=e617]
                - row [ref=e618]:
                  - cell "M-0036" [ref=e619]
                  - cell "Non-maturity Deposit Liquidity Model" [ref=e620]
                  - cell "Monitoring" [ref=e621]
                  - cell "Validation Report" [ref=e622]
                - row [ref=e623]:
                  - cell "M-0039" [ref=e624]
                  - cell "Branch Volume Model" [ref=e625]
                  - cell "Monitoring" [ref=e626]
                  - cell "Validation Report" [ref=e627]
                - row [ref=e628]:
                  - cell "M-0045" [ref=e629]
                  - cell "Wholesale Funding Liquidity Model" [ref=e630]
                  - cell "Monitoring" [ref=e631]
                  - cell "Terms of Reference" [ref=e632]
                - row [ref=e633]:
                  - cell "M-0047" [ref=e634]
                  - cell "Credit Card EAD Model" [ref=e635]
                  - cell "Monitoring" [ref=e636]
                  - cell "Model Development Document" [ref=e637]
                - row [ref=e638]:
                  - cell "M-0049" [ref=e639]
                  - cell "Credit Card LGD Model" [ref=e640]
                  - cell "Monitoring" [ref=e641]
                  - cell "Model Approval/MRC Paper" [ref=e642]
                - row [ref=e643]:
                  - cell "M-0050" [ref=e644]
                  - cell "Wealth Lending PD Model" [ref=e645]
                  - cell "Monitoring" [ref=e646]
                  - cell "Terms of Reference" [ref=e647]
                - row [ref=e648]:
                  - cell "M-0052" [ref=e649]
                  - cell "CRE Reserve allocation Model" [ref=e650]
                  - cell "Monitoring" [ref=e651]
                  - cell "Monitoring Plan" [ref=e652]
                - row [ref=e653]:
                  - cell "M-0055" [ref=e654]
                  - cell "Revenue Forecasting Model" [ref=e655]
                  - cell "Monitoring" [ref=e656]
                  - cell "Model Development Document,Model Approval/MRC Paper" [ref=e657]
                - row [ref=e658]:
                  - cell "M-0056" [ref=e659]
                  - cell "Student Lending PD Model v2" [ref=e660]
                  - cell "Monitoring" [ref=e661]
                  - cell "Validation Report" [ref=e662]
                - row [ref=e663]:
                  - cell "M-0059" [ref=e664]
                  - cell "Securities Portfolio Prepayment Model v2" [ref=e665]
                  - cell "Reg/Audit" [ref=e666]
                  - cell "Model Development Document" [ref=e667]
                - row [ref=e668]:
                  - cell "M-0072" [ref=e669]
                  - cell "Commercial & Industrial EAD Model" [ref=e670]
                  - cell "Monitoring" [ref=e671]
                  - cell "Model Approval/MRC Paper" [ref=e672]
                - row [ref=e673]:
                  - cell "M-0075" [ref=e674]
                  - cell "Treasury ALM/IRR Model v2" [ref=e675]
                  - cell "Monitoring" [ref=e676]
                  - cell "Terms of Reference" [ref=e677]
                - row [ref=e678]:
                  - cell "M-0081" [ref=e679]
                  - cell "Dealer Floorplan Rating Model" [ref=e680]
                  - cell "Monitoring" [ref=e681]
                  - cell "Model Development Document" [ref=e682]
                - row [ref=e683]:
                  - cell "M-0085" [ref=e684]
                  - cell "Behavioral Scorecard v2" [ref=e685]
                  - cell "Development" [ref=e686]
                  - cell "Terms of Reference" [ref=e687]
                - row [ref=e688]:
                  - cell "M-0086" [ref=e689]
                  - cell "Credit Card LGD Model v2" [ref=e690]
                  - cell "Monitoring" [ref=e691]
                  - cell "Model Approval/MRC Paper" [ref=e692]
                - row [ref=e693]:
                  - cell "M-0087" [ref=e694]
                  - cell "Treasury Deposit Model v2" [ref=e695]
                  - cell "Monitoring" [ref=e696]
                  - cell "Validation Report" [ref=e697]
                - row [ref=e698]:
                  - cell "M-0088" [ref=e699]
                  - cell "Net Interest Income Volume Model" [ref=e700]
                  - cell "Monitoring" [ref=e701]
                  - cell "Monitoring Plan" [ref=e702]
                - row [ref=e703]:
                  - cell "M-0090" [ref=e704]
                  - cell "Securities Q-factor Model" [ref=e705]
                  - cell "Monitoring" [ref=e706]
                  - cell "Model Development Document" [ref=e707]
                - row [ref=e708]:
                  - cell "M-0094" [ref=e709]
                  - cell "Residential Mortgage Rating Model" [ref=e710]
                  - cell "Monitoring" [ref=e711]
                  - cell "Monitoring Plan" [ref=e712]
                - row [ref=e713]:
                  - cell "M-0104" [ref=e714]
                  - cell "Small Business EAD Model" [ref=e715]
                  - cell "Monitoring" [ref=e716]
                  - cell "Terms of Reference,Model Development Document" [ref=e717]
                - row [ref=e718]:
                  - cell "M-0107" [ref=e719]
                  - cell "Dealer Floorplan Collections Model" [ref=e720]
                  - cell "Monitoring" [ref=e721]
                  - cell "Terms of Reference" [ref=e722]
                - row [ref=e723]:
                  - cell "M-0108" [ref=e724]
                  - cell "Deposit Volume Climate Model" [ref=e725]
                  - cell "Monitoring" [ref=e726]
                  - cell "Validation Report" [ref=e727]
                - row [ref=e728]:
                  - cell "M-0109" [ref=e729]
                  - cell "CRE Q-factor Model" [ref=e730]
                  - cell "Monitoring" [ref=e731]
                  - cell "Model Development Document" [ref=e732]
                - row [ref=e733]:
                  - cell "M-0110" [ref=e734]
                  - cell "HELOC Scorecard Model" [ref=e735]
                  - cell "Monitoring" [ref=e736]
                  - cell "Validation Report" [ref=e737]
                - row [ref=e738]:
                  - cell "M-0112" [ref=e739]
                  - cell "Small Business Rating Model" [ref=e740]
                  - cell "Reg/Audit" [ref=e741]
                  - cell "Validation Report,Model Approval/MRC Paper" [ref=e742]
                - row [ref=e743]:
                  - cell "M-0114" [ref=e744]
                  - cell "Commercial & Industrial Scorecard Model" [ref=e745]
                  - cell "Monitoring" [ref=e746]
                  - cell "Model Approval/MRC Paper" [ref=e747]
                - row [ref=e748]:
                  - cell "M-0117" [ref=e749]
                  - cell "Trading Book Scenario Model" [ref=e750]
                  - cell "Reg/Audit" [ref=e751]
                  - cell "Model Approval/MRC Paper,Monitoring Plan" [ref=e752]
                - row [ref=e753]:
                  - cell "M-0121" [ref=e754]
                  - cell "Card CECL Model" [ref=e755]
                  - cell "Implementation" [ref=e756]
                  - cell "Monitoring Plan" [ref=e757]
                - row [ref=e758]:
                  - cell "M-0122" [ref=e759]
                  - cell "Net Interest Income Volume Model v2" [ref=e760]
                  - cell "Implementation" [ref=e761]
                  - cell "Terms of Reference" [ref=e762]
                - row [ref=e763]:
                  - cell "M-0123" [ref=e764]
                  - cell "Student Lending PD Model v3" [ref=e765]
                  - cell "Monitoring" [ref=e766]
                  - cell "Validation Report" [ref=e767]
                - row [ref=e768]:
                  - cell "M-0125" [ref=e769]
                  - cell "CRE Loss Model v2" [ref=e770]
                  - cell "Validation" [ref=e771]
                  - cell "Terms of Reference,Model Development Document" [ref=e772]
                - row [ref=e773]:
                  - cell "M-0127" [ref=e774]
                  - cell "Commercial & Industrial LGD Model v2" [ref=e775]
                  - cell "Monitoring" [ref=e776]
                  - cell "Validation Report" [ref=e777]
                - row [ref=e778]:
                  - cell "M-0131" [ref=e779]
                  - cell "Wholesale Funding Deposit Model" [ref=e780]
                  - cell "Validation" [ref=e781]
                  - cell "Model Development Document" [ref=e782]
                - row [ref=e783]:
                  - cell "M-0137" [ref=e784]
                  - cell "Residential Mortgage PD Model" [ref=e785]
                  - cell "Monitoring" [ref=e786]
                  - cell "Terms of Reference" [ref=e787]
                - row [ref=e788]:
                  - cell "M-0139" [ref=e789]
                  - cell "Card IFRS 9 Model" [ref=e790]
                  - cell "Monitoring" [ref=e791]
                  - cell "Model Approval/MRC Paper" [ref=e792]
                - row [ref=e793]:
                  - cell "M-0140" [ref=e794]
                  - cell "Consumer IFRS 9 Model v2" [ref=e795]
                  - cell "Validation" [ref=e796]
                  - cell "Model Development Document" [ref=e797]
                - row [ref=e798]:
                  - cell "M-0143" [ref=e799]
                  - cell "Dealer Floorplan Rating Model v2" [ref=e800]
                  - cell "Monitoring" [ref=e801]
                  - cell "Validation Report" [ref=e802]
                - row [ref=e803]:
                  - cell "M-0147" [ref=e804]
                  - cell "Treasury Liquidity Model v2" [ref=e805]
                  - cell "Monitoring" [ref=e806]
                  - cell "Monitoring Plan" [ref=e807]
                - row [ref=e808]:
                  - cell "M-0148" [ref=e809]
                  - cell "HELOC PD Model" [ref=e810]
                  - cell "Monitoring" [ref=e811]
                  - cell "Terms of Reference" [ref=e812]
                - row [ref=e813]:
                  - cell "M-0152" [ref=e814]
                  - cell "HELOC Scorecard Model v2" [ref=e815]
                  - cell "Monitoring" [ref=e816]
                  - cell "Model Development Document" [ref=e817]
                - row [ref=e818]:
                  - cell "M-0153" [ref=e819]
                  - cell "Student Lending Rating Model" [ref=e820]
                  - cell "Reg/Audit" [ref=e821]
                  - cell "Monitoring Plan" [ref=e822]
                - row [ref=e823]:
                  - cell "M-0155" [ref=e824]
                  - cell "Deposit Volume Volume Model v2" [ref=e825]
                  - cell "Monitoring" [ref=e826]
                  - cell "Model Development Document,Model Approval/MRC Paper" [ref=e827]
                - row [ref=e828]:
                  - cell "M-0157" [ref=e829]
                  - cell "Wealth Lending PD Model v2" [ref=e830]
                  - cell "Monitoring" [ref=e831]
                  - cell "Validation Report" [ref=e832]
                - row [ref=e833]:
                  - cell "M-0167" [ref=e834]
                  - cell "Consumer RWA Model v2" [ref=e835]
                  - cell "Implementation" [ref=e836]
                  - cell "Terms of Reference,Model Approval/MRC Paper" [ref=e837]
                - row [ref=e838]:
                  - cell "M-0170" [ref=e839]
                  - cell "Operating Expense Climate Model v3" [ref=e840]
                  - cell "Monitoring" [ref=e841]
                  - cell "Model Development Document" [ref=e842]
                - row [ref=e843]:
                  - cell "M-0173" [ref=e844]
                  - cell "Credit Card PD Model v3" [ref=e845]
                  - cell "Reg/Audit" [ref=e846]
                  - cell "Monitoring Plan" [ref=e847]
                - row [ref=e848]:
                  - cell "M-0175" [ref=e849]
                  - cell "Loan Volume Climate Model" [ref=e850]
                  - cell "Monitoring" [ref=e851]
                  - cell "Terms of Reference,Model Development Document" [ref=e852]
                - row [ref=e853]:
                  - cell "M-0176" [ref=e854]
                  - cell "Loan Volume Balance Model v2" [ref=e855]
                  - cell "Implementation" [ref=e856]
                  - cell "Model Approval/MRC Paper" [ref=e857]
                - row [ref=e858]:
                  - cell "M-0178" [ref=e859]
                  - cell "Enterprise Scenario Model v2" [ref=e860]
                  - cell "Implementation" [ref=e861]
                  - cell "Validation Report" [ref=e862]
                - row [ref=e863]:
                  - cell "M-0179" [ref=e864]
                  - cell "Auto Loan Scorecard Model" [ref=e865]
                  - cell "Monitoring" [ref=e866]
                  - cell "Terms of Reference" [ref=e867]
                - row [ref=e868]:
                  - cell "M-0185" [ref=e869]
                  - cell "Card Q-factor Model v2" [ref=e870]
                  - cell "Reg/Audit" [ref=e871]
                  - cell "Model Approval/MRC Paper" [ref=e872]
                - row [ref=e873]:
                  - cell "M-0186" [ref=e874]
                  - cell "Treasury ALM/IRR Model v3" [ref=e875]
                  - cell "Validation" [ref=e876]
                  - cell "Terms of Reference" [ref=e877]
                - row [ref=e878]:
                  - cell "M-0187" [ref=e879]
                  - cell "Operational Scenario Model v2" [ref=e880]
                  - cell "Monitoring" [ref=e881]
                  - cell "Validation Report" [ref=e882]
                - row [ref=e883]:
                  - cell "M-0194" [ref=e884]
                  - cell "Student Lending EAD Model v3" [ref=e885]
                  - cell "Monitoring" [ref=e886]
                  - cell "Terms of Reference,Validation Report,Monitoring Plan" [ref=e887]
                - row [ref=e888]:
                  - cell "M-0199" [ref=e889]
                  - cell "Small Business PD Model" [ref=e890]
                  - cell "Monitoring" [ref=e891]
                  - cell "Model Development Document" [ref=e892]
                - row [ref=e893]:
                  - cell "M-0201" [ref=e894]
                  - cell "Operating Expense Revenue Model v2" [ref=e895]
                  - cell "Monitoring" [ref=e896]
                  - cell "Model Approval/MRC Paper" [ref=e897]
                - row [ref=e898]:
                  - cell "M-0204" [ref=e899]
                  - cell "Commercial & Industrial LGD Model v3" [ref=e900]
                  - cell "Monitoring" [ref=e901]
                  - cell "Model Approval/MRC Paper" [ref=e902]
                - row [ref=e903]:
                  - cell "M-0207" [ref=e904]
                  - cell "Commercial & Industrial EAD Model v2" [ref=e905]
                  - cell "Retirement" [ref=e906]
                  - cell "Model Development Document,Validation Report" [ref=e907]
                - row [ref=e908]:
                  - cell "M-0208" [ref=e909]
                  - cell "Loan Volume Revenue Model" [ref=e910]
                  - cell "Monitoring" [ref=e911]
                  - cell "Validation Report" [ref=e912]
                - row [ref=e913]:
                  - cell "M-0211" [ref=e914]
                  - cell "CRE Scenario Model v2" [ref=e915]
                  - cell "Monitoring" [ref=e916]
                  - cell "Terms of Reference" [ref=e917]
                - row [ref=e918]:
                  - cell "M-0213" [ref=e919]
                  - cell "Deposit Volume Climate Model v3" [ref=e920]
                  - cell "Retirement" [ref=e921]
                  - cell "Validation Report" [ref=e922]
                - row [ref=e923]:
                  - cell "M-0218" [ref=e924]
                  - cell "CRE Office Rating Model v3" [ref=e925]
                  - cell "Monitoring" [ref=e926]
                  - cell "Terms of Reference" [ref=e927]
                - row [ref=e928]:
                  - cell "M-0219" [ref=e929]
                  - cell "Credit Card EAD Model v3" [ref=e930]
                  - cell "Monitoring" [ref=e931]
                  - cell "Terms of Reference" [ref=e932]
                - row [ref=e933]:
                  - cell "M-0220" [ref=e934]
                  - cell "CRE PPNR Model" [ref=e935]
                  - cell "Reg/Audit" [ref=e936]
                  - cell "Monitoring Plan" [ref=e937]
                - row [ref=e938]:
                  - cell "M-0221" [ref=e939]
                  - cell "Small Business PD Model v2" [ref=e940]
                  - cell "Reg/Audit" [ref=e941]
                  - cell "Validation Report" [ref=e942]
                - row [ref=e943]:
                  - cell "M-0222" [ref=e944]
                  - cell "Commercial & Industrial PD Model" [ref=e945]
                  - cell "Monitoring" [ref=e946]
                  - cell "Terms of Reference" [ref=e947]
                - row [ref=e948]:
                  - cell "M-0225" [ref=e949]
                  - cell "Securities Portfolio ALM/IRR Model v3" [ref=e950]
                  - cell "Monitoring" [ref=e951]
                  - cell "Monitoring Plan" [ref=e952]
                - row [ref=e953]:
                  - cell "M-0226" [ref=e954]
                  - cell "Enterprise Capital Model v3" [ref=e955]
                  - cell "Monitoring" [ref=e956]
                  - cell "Model Approval/MRC Paper" [ref=e957]
                - row [ref=e958]:
                  - cell "M-0227" [ref=e959]
                  - cell "Consumer Q-factor Model v2" [ref=e960]
                  - cell "Retirement" [ref=e961]
                  - cell "Monitoring Plan" [ref=e962]
                - row [ref=e963]:
                  - cell "M-0229" [ref=e964]
                  - cell "Commercial & Industrial LGD Model v4" [ref=e965]
                  - cell "Monitoring" [ref=e966]
                  - cell "Terms of Reference,Validation Report" [ref=e967]
                - row [ref=e968]:
                  - cell "M-0230" [ref=e969]
                  - cell "Dealer Floorplan Collections Model v2" [ref=e970]
                  - cell "Retirement" [ref=e971]
                  - cell "Model Development Document" [ref=e972]
                - row [ref=e973]:
                  - cell "M-0234" [ref=e974]
                  - cell "Loan Volume Balance Model v3" [ref=e975]
                  - cell "Monitoring" [ref=e976]
                  - cell "Validation Report,Model Approval/MRC Paper" [ref=e977]
                - row [ref=e978]:
                  - cell "M-0235" [ref=e979]
                  - cell "Fee Income Revenue Model v3" [ref=e980]
                  - cell "Monitoring" [ref=e981]
                  - cell "Validation Report" [ref=e982]
                - row [ref=e983]:
                  - cell "M-0237" [ref=e984]
                  - cell "CRE Office Collections Model" [ref=e985]
                  - cell "Monitoring" [ref=e986]
                  - cell "Model Development Document" [ref=e987]
                - row [ref=e988]:
                  - cell "M-0243" [ref=e989]
                  - cell "Treasury Prepayment Model v5" [ref=e990]
                  - cell "Monitoring" [ref=e991]
                  - cell "Terms of Reference" [ref=e992]
                - row [ref=e993]:
                  - cell "M-0244" [ref=e994]
                  - cell "Credit Card PD Model v5" [ref=e995]
                  - cell "Monitoring" [ref=e996]
                  - cell "Terms of Reference,Model Approval/MRC Paper" [ref=e997]
                - row [ref=e998]:
                  - cell "M-0247" [ref=e999]
                  - cell "Securities CECL Model" [ref=e1000]
                  - cell "Monitoring" [ref=e1001]
                  - cell "Model Development Document" [ref=e1002]
                - row [ref=e1003]:
                  - cell "M-0250" [ref=e1004]
                  - cell "Residential Mortgage Collections Model" [ref=e1005]
                  - cell "Monitoring" [ref=e1006]
                  - cell "Model Development Document,Monitoring Plan" [ref=e1007]
                - row [ref=e1008]:
                  - cell "M-0253" [ref=e1009]
                  - cell "CRE CECL Model" [ref=e1010]
                  - cell "Monitoring" [ref=e1011]
                  - cell "Validation Report" [ref=e1012]
                - row [ref=e1013]:
                  - cell "M-0254" [ref=e1014]
                  - cell "Operating Expense Expense Model v2" [ref=e1015]
                  - cell "Monitoring" [ref=e1016]
                  - cell "Terms of Reference" [ref=e1017]
                - row [ref=e1018]:
                  - cell "M-0256" [ref=e1019]
                  - cell "Enterprise RWA Model v2" [ref=e1020]
                  - cell "Monitoring" [ref=e1021]
                  - cell "Model Development Document" [ref=e1022]
          - generic [ref=e1023]:
            - heading "Changes since the previous report" [level=4] [ref=e1024]
            - paragraph [ref=e1025]: This is the first report, so there is nothing to compare against.
```

# Test source

```ts
  87  |     // --- REG-16: an Executive may read but not generate ---------------------------------------
  88  |     await signInAs(page, "Executive");
  89  |     await openScreen(page, "Model Risk Report");
  90  |     await expect(page.getByRole("button", { name: "Generate report" }),
  91  |       "SEC-02: a read-only role is offered no write action").toHaveCount(0);
  92  |     const refused = await page.request.post("/api/reports/model-risk", {
  93  |       headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem("mrm.token"))}` },
  94  |     });
  95  |     expect(refused.status(), "and the API refuses it too, not just the UI").toBe(403);
  96  |     // A refusal is only proven when nothing was stored and nothing was audited either (REG-16).
  97  |     expect(dbCount("model_risk_report"), "REG-16: the refused generation stored nothing")
  98  |       .toBe(before + 2);
  99  |     expect(dbCount("audit_event", "entity = 'model_risk_report' AND action = 'generate'"),
  100 |       "REG-16: and wrote no audit event").toBe(auditBefore + 2);
  101 | 
  102 |     // --- REG-17: a read role reopens a stored report and downloads the PDF --------------------
  103 |     await page.getByRole("button", { name: "Open" }).first().click();
  104 |     await expect(page.getByText(/Content hash/)).toBeVisible({ timeout: 20_000 });
  105 |     const download = page.waitForEvent("download");
  106 |     await page.getByRole("button", { name: "Download PDF" }).click();
  107 |     expect((await download).suggestedFilename()).toMatch(/^MRR-[\d-]+\.pdf$/);
  108 |     await checkpoint(page, "FS-25_executive_reopened");
  109 | 
  110 |     // --- REG-17: and so can an Auditor, whom the criterion names explicitly -------------------
  111 |     await signInAs(page, "Auditor");
  112 |     await openScreen(page, "Model Risk Report");
  113 |     await expect(page.getByRole("button", { name: "PDF" }).first()).toBeVisible();
  114 |     const auditorDownload = page.waitForEvent("download");
  115 |     await page.getByRole("button", { name: "PDF" }).first().click();
  116 |     expect((await auditorDownload).suggestedFilename()).toMatch(/\.pdf$/);
  117 |     await checkpoint(page, "FS-25_auditor_download");
  118 |   });
  119 | 
  120 | // FS-25 (continued) — what changed after the 2026-10-08 Gate 1 run: D14's seeded-example disclosure on
  121 | // every surface, the PDF's reconciliation line (G1.31), and S13's "decisions since the previous report"
  122 | // moving into the changes section, out of the content hash (G1.29). A second test under the same ID so
  123 | // `-g "FS-25"` still runs the whole scenario. Runs after the first half, which stores generated reports.
  124 | test("FS-25 REG-16 REG-17 D14 D17 S13 the seeded example discloses its dates everywhere; decisions sit in the changes section",
  125 |   async ({ page }) => {
  126 |     test.setTimeout(120_000);
  127 |     const token = async () => page.evaluate(() => localStorage.getItem("mrm.token"));
  128 |     const pdfOf = async (reportId: string) => {
  129 |       const resp = await page.request.get(`/api/reports/model-risk/${reportId}/pdf`,
  130 |         { headers: { Authorization: `Bearer ${await token()}` } });
  131 |       expect(resp.status(), `PDF of ${reportId}`).toBe(200);
  132 |       return pdfText(await resp.body());
  133 |     };
  134 |     type Header = { report_id: string; business_date: string; figures_as_of: string | null;
  135 |       is_seeded: boolean; seeded_label: string | null; generated_at: string; content_hash: string };
  136 |     type Detail = Header & { sections: Record<string, Record<string, unknown>> };
  137 | 
  138 |     // --- D14 on the list, as a read role -----------------------------------------------------
  139 |     await signInAs(page, "Auditor");
  140 |     const list = (await apiAs(page, "/api/reports/model-risk")).body as Header[];
  141 |     const seeded = list.filter((r) => r.is_seeded);
  142 |     expect(seeded.length, "a reset seeds exactly one example report (S11)").toBe(1);
  143 |     const ex = seeded[0];
  144 |     const generated = list.filter((r) => !r.is_seeded);
  145 |     expect(generated.length, "the first half of FS-25 stored generated reports").toBeGreaterThan(0);
  146 |     // D14 (clarified 2026-10-15): "<generation date>" is the business date the figures were computed
  147 |     // for — app.clock.today() at the reset — and the example keeps its earlier business date.
  148 |     const businessDate = generated[0].business_date;
  149 |     expect(ex.figures_as_of, "D14: the seeded figures are as of today's business date").toBe(businessDate);
  150 |     expect(ex.business_date < businessDate, "D14 option (b): the example keeps an earlier date").toBe(true);
  151 |     const label = `Seeded example: figures computed from current seed data on ${ex.figures_as_of}, ` +
  152 |       `dated ${ex.business_date} for illustration.`;
  153 |     expect(ex.seeded_label, "D14: the API words the disclosure exactly").toBe(label);
  154 |     for (const r of generated) {
  155 |       expect(r.seeded_label, `${r.report_id} is not seeded and carries no label`).toBeNull();
  156 |       expect(r.figures_as_of, "D14: a generated report's figures are as of its own business date")
  157 |         .toBe(r.business_date);
  158 |     }
  159 | 
  160 |     await openScreen(page, "Model Risk Report");
  161 |     const exRow = page.locator("tr", { hasText: ex.report_id });
  162 |     await expect(exRow, "D14: the list carries the pill").toContainText("Seeded example");
  163 |     await expect(exRow, "D14: and the full label").toContainText(label);
  164 |     await checkpoint(page, "FS-25_d14_list");
  165 | 
  166 |     // --- D14 on the reopened report ----------------------------------------------------------
  167 |     await exRow.getByRole("button", { name: "Open" }).click();
  168 |     const head = page.locator("section.panel", { has: page.getByText(/Content hash/) }).first();
  169 |     await expect(head).toContainText(ex.report_id, { timeout: 20_000 });
  170 |     await expect(head, "D14: the reopened report carries the label").toContainText(label);
  171 |     await expect(head, "S12: the reconciliation is stated in the past tense, about this report")
  172 |       .toContainText("Figures reconciled with the Command Center at generation");
  173 |     // --- D17 (G1.34): the seeded example's generation time is real, not shaped ---------------
  174 |     //
  175 |     // Until G1.34 the seed shaped `generated_at` to 09:00 on the illustrative business date, so the
  176 |     // reconciliation line said "at generation, 2026-08-31 09:00" one line above "figures computed …
  177 |     // on 2026-09-30" (TR-83). D17 (a): it is the real time the example was computed. The only
  178 |     // independent record of *when* that was is the reset lock (G1.32), whose window opens when the
  179 |     // reset starts and closes after the seeded example is written — so the example's time must fall
  180 |     // inside the last reset's window, and the screen must show that same instant.
  181 |     const resetStatus = (await apiAs(page, "/api/admin/reset/status")).body as {
  182 |       acquired_at: string | null; released_at: string | null; last_outcome: string | null };
  183 |     expect(resetStatus.last_outcome, "the last reset completed").toBe("Completed");
  184 |     const exAt = Date.parse(ex.generated_at);
  185 |     expect(Number.isNaN(exAt), `D17: generated_at parses (${ex.generated_at})`).toBe(false);
  186 |     expect(ex.generated_at.startsWith(`${ex.business_date}T09:00`),
> 187 |       "D17: generated_at is no longer shaped to 09:00 on the illustrative date").toBe(false);
      |                                                                                  ^ Error: D17: generated_at is no longer shaped to 09:00 on the illustrative date
  188 |     // `generated_at` has one-second granularity (`func.now()` on SQLite), the lock's times do not.
  189 |     const windowStart = Math.floor(Date.parse(resetStatus.acquired_at ?? "") / 1000) * 1000;
  190 |     const windowEnd = Date.parse(resetStatus.released_at ?? "");
  191 |     expect(exAt >= windowStart && exAt <= windowEnd,
  192 |       `D17: the example was computed during the last reset (${resetStatus.acquired_at} … ` +
  193 |       `${resetStatus.released_at}), not at ${ex.generated_at}`).toBe(true);
  194 |     for (const r of generated) {
  195 |       expect(Date.parse(r.generated_at) >= exAt,
  196 |         `${r.report_id} was generated after the example it diffs against`).toBe(true);
  197 |     }
  198 |     const exShown = await page.evaluate((v) => new Date(v).toLocaleString(), ex.generated_at);
  199 |     await expect(head, "D17: the reconciliation line shows the example's real generation time")
  200 |       .toContainText(`Figures reconciled with the Command Center at generation, ${exShown}.`);
  201 |     await checkpoint(page, "FS-25_d14_reopened");
  202 | 
  203 |     // --- D14: the PDF counts as a surface ----------------------------------------------------
  204 |     const reconciled = "Figures reconciled with the Command Center at generation,";
  205 |     const exPdf = await pdfOf(ex.report_id);
  206 |     expect(containsIgnoringSpace(exPdf, label), "D14: the seeded PDF carries the label").toBe(true);
  207 |     expect(containsIgnoringSpace(exPdf, reconciled), "D14: every PDF carries the reconciliation line")
  208 |       .toBe(true);
  209 |     // D17 on the copy that leaves the system: the PDF prints `generated_at` as "YYYY-MM-DD HH:MM:SS",
  210 |     // and it is the same real instant the API reports — never the shaped 09:00 on the example's date.
  211 |     const exPdfAt = ex.generated_at.slice(0, 19).replace("T", " ");
  212 |     expect(containsIgnoringSpace(exPdf, `${reconciled} ${exPdfAt}`),
  213 |       `D17: the seeded PDF's reconciliation line reads ${exPdfAt}`).toBe(true);
  214 |     expect(containsIgnoringSpace(exPdf, `${ex.business_date} 09:00`),
  215 |       "D17: the shaped 09:00 timestamp is gone from the PDF").toBe(false);
  216 |     const genPdf = await pdfOf(generated[0].report_id);
  217 |     expect(containsIgnoringSpace(genPdf, reconciled),
  218 |       "D14: a generated report's PDF carries the reconciliation line too").toBe(true);
  219 |     expect(containsIgnoringSpace(genPdf, "Seeded example"),
  220 |       "a generated report's PDF is not labelled as an example").toBe(false);
  221 | 
  222 |     // --- S13: a decision recorded between generations, through the UI ------------------------
  223 |     await signInAs(page, "MRC Member");
  224 |     const generate = async (): Promise<Detail> => {
  225 |       await openScreen(page, "Model Risk Report");
  226 |       const respP = page.waitForResponse((r) => r.url().endsWith("/api/reports/model-risk")
  227 |         && r.request().method() === "POST");
  228 |       await page.getByRole("button", { name: "Generate report" }).click();
  229 |       const resp = await respP;
  230 |       expect(resp.ok(), `generate: ${resp.status()}`).toBe(true);
  231 |       const body = await resp.json() as Detail;
  232 |       await expect(page.locator("section.panel", { has: page.getByText(/Content hash/) }).first())
  233 |         .toContainText(body.report_id, { timeout: 20_000 });
  234 |       return body;
  235 |     };
  236 |     await generate();
  237 | 
  238 |     const approvalIds = () => dbQuery("SELECT approval_id FROM approval").map((r) => String(r.approval_id));
  239 |     const before = new Set(approvalIds());
  240 |     const auditBefore = dbCount("audit_event", "entity = 'approval'");
  241 |     await page.goto("/models/M-0030");
  242 |     await page.getByRole("tab", { name: /^Approvals/ }).click();
  243 |     await page.getByRole("button", { name: "Record decision" }).click();
  244 |     const field = (name: string) => page.locator(
  245 |       `xpath=//form[contains(@class,"action-form")]//label[normalize-space(text())="${name}"]`)
  246 |       .locator("input, select, textarea");
  247 |     await field("Decision date").fill("2026-09-29");
  248 |     await field("Forum").selectOption({ index: 1 });
  249 |     await field("Decision type").selectOption({ index: 1 });
  250 |     await field("Decision").selectOption("Approved");
  251 |     await page.getByRole("button", { name: "Save decision" }).click();
  252 |     await expect.poll(() => approvalIds().length, { timeout: 15_000 }).toBe(before.size + 1);
  253 |     const newId = approvalIds().find((id) => !before.has(id)) ?? "";
  254 |     expect(dbCount("audit_event", "entity = 'approval'"), "AUD-01: the decision is audited once")
  255 |       .toBe(auditBefore + 1);
  256 | 
  257 |     const seesIt = await generate();
  258 |     const changes = page.locator("section.panel",
  259 |       { has: page.getByText(/^Changes since the previous report/) }).first();
  260 |     const decisionsRow = changes.locator("tr", { hasText: "Approval decisions recorded" });
  261 |     await expect(decisionsRow, "S13: the decision is listed in the changes section").toContainText(newId);
  262 |     const recorded = (seesIt.sections.changes_since.decisions_recorded as { approval_id: string }[])
  263 |       .map((d) => d.approval_id);
  264 |     expect(recorded, "S13: exactly the decision recorded since the previous report").toEqual([newId]);
  265 |     expect(Object.keys(seesIt.sections.approvals),
  266 |       "S13: nothing derived from the predecessor remains in Approvals").not.toContain("decisions_since_previous");
  267 |     await checkpoint(page, "FS-25_s13_changes");
  268 | 
  269 |     const afterIt = await generate();
  270 |     expect(afterIt.sections.changes_since.decisions_recorded, "nothing recorded in between").toEqual([]);
  271 |     expect(afterIt.content_hash,
  272 |       "REG-16 (CR-52, S13): same data, same business date, same hash — whatever the predecessor saw")
  273 |       .toBe(seesIt.content_hash);
  274 |   });
  275 | 
```