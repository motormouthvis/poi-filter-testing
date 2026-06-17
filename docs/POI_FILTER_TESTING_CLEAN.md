# POI Filter Testing and Results (clean copy)

Use this file as the source of truth. Paste into Google Docs with Paste without formatting (Ctrl+Shift+V), then apply Heading 1 / Heading 2 styles and insert tables from the tab-separated sections if needed.

---

## 1. Hospital (USA) — Django admin preset

### Search fields (per query; not part of static preset)

- Latitude, Longitude — user’s search pin
- Distance (miles) — e.g. 30
- Max results — e.g. 250
- Min confidence — leave empty unless tuning
- Address, City, State, Zipcode, Operating status — empty
- Website — Any

### Business name — include (primary and common)

(empty in both)

### Business name — exclude (same list in primary and common)

veterinary
veterinarian
animal hospital
pet hospital
urgent care
immediate care
express care
walk-in clinic
walk in clinic
minute clinic
convenient care
retail clinic
telehealth
dental
dentist
orthodont
endodont
oral surgery
chiropract
acupuncture
med spa
medspa
plastic surgery
cosmetic surgery
bariatric center
weight loss center
fertility
ivf
dialysis
sleep center
sleep medicine
insomnia
pain management clinic
imaging center
radiology center
mri
ct scan
laboratory
blood draw
plasma
blood donation
surgery center
surgical center
ambulatory surgery
outpatient surgery
endoscopy center
chemotherapy
radiation oncology
cancer center
oncology center
cardiology office
orthopedic clinic
ent clinic
eye clinic
vision center
hearing aid
audiology
physical therapy
rehabilitation
substance abuse
detox
psychiat
mental health clinic
counseling center
hospice
nursing home
skilled nursing
assisted living
memory care
long term care
home health
pharmacy
drugstore
surgical specialists
suite 
healthcare specialist
trauma surgeons
physicians group
physician group

### Basic category

Include: hospital  
Exclude: (empty)

### Category primary

Include:

hospital
emergency_room
medical_center

Exclude: (empty)

### Category alternate

Include:

emergency_room
medical_center

Exclude:

urgent_care
walk_in
walk-in
clinic
doctor
health_clinic
family_practice
primary_care
pediatric_clinic
dentist
dental
orthodont
chiropract
acupuncture
tattoo_and_piercing
dog_park
event_planning
charity_organization
community_services_non_profits
sleep_specialist
cancer_treatment_center
dialysis_center
imaging_center
radiology_center
laboratory
laboratory_testing
outpatient
ambulatory
hospice
nursing
assisted_living
rehab
rehabilitation
mental_health
counseling
therapy
surgical_center

### Taxonomy (primary / alternates — include and exclude)

All four boxes: (empty)

### Query builder (final expression)

name_primary_exclude and name_common_exclude and basic_category_include and category_primary_include and category_alternate_include and category_alternate_exclude

If “Generate Query” renames tokens, keep your app’s official names and preserve this boolean structure.

### Known limitation

Cleveland Clinic Martin South Hospital can appear with empty category_alternate and will be excluded until the DB adds something like acute_hospital_er_capable (cron / external verify). See section 3.

---

## 2. Dedupe (dev)

- Dedupe when normalized address matches OR lat/lon within ~50–100 m and same brand/operator if available.
- Do not merge different street addresses (e.g. main hospital vs freestanding ER elsewhere).
- Do merge same-campus duplicates (e.g. main hospital + Emergency Department at identical address/coords).

---

## 3. Under-tagged hospitals (dev)

New columns (example):

- acute_hospital_er_capable (boolean)
- acute_hospital_source (unknown | overture_tagged | inferred_internal | verified_external | manual_override)
- acute_hospital_updated_at (timestamp)
- acute_hospital_evidence (optional json/text)

Populate: overture tags first; external match preferred; conservative internal rules for empty alternate; filter ORs in this flag.

---

## 4. Benchmark — Grok reference vs Overture (Treasure Coast test pin)

Tab-separated for easy paste into a Google Sheet or Docs table:

Reference	Grok-style name	Overture / filter note	Action
1	HCA Florida Lawnwood Hospital	Match	overture_tagged
2	Cleveland Clinic Indian River Hospital	Match	overture_tagged
3	Florida Coast Medical Center (new)	Missing in snapshot	refresh / external when present
4	HCA Florida St. Lucie Hospital	Match as St Lucie Medical Center (Tiffany address)	overture_tagged
4b	Darwin Square freestanding ER	Separate POI; different address	product choice; not address-dedupe with 4
5	Cleveland Clinic Tradition Hospital	Match; Tradition ED same site → dedupe	dedupe
6	Cleveland Clinic Martin North Hospital	Match	overture_tagged
7	Orlando Health Sebastian River Hospital	Match as Sebastian River Medical Center; branding may differ	overture_tagged
8	Cleveland Clinic Martin South Hospital	In DB; empty alternate → dropped by strict filter	verified_external or inferred_internal

---

## 5. Evaluation (dev)

- Maintain a labeled set (200–500 pins, ≥5 metros): keep / drop for ER-capable acute hospital layer.
- Track precision, recall, FP by token, counts by acute_hospital_source.
- Release with FP regression budget.

---

Document generated from session notes. Google Doc: publish or paste this file if the automated pub fetch is blocked for non-browser clients.
