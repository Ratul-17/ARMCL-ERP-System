"""
generate_route_data.py
Generates full March 2026 delivery dataset with GPS coordinates for all clients.
Run once: python3 generate_route_data.py
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid

random.seed(42)
np.random.seed(42)

# ── Depot ─────────────────────────────────────────────────────────────────────
DEPOT = {"name": "ARMCL-01 Dhour", "lat": 23.8490, "lng": 90.3580}

# ── Address → GPS coordinate map (all real Dhaka-area coordinates) ─────────────
ADDRESS_COORDS = {
    "Nayadingi,Saturia,Manikganj":              (23.8640, 90.0120),
    "Almanda Roya, Plot- 09, Road- 125 & 127, Block- CSE(D), Gulshan, Dhaka.": (23.7934, 90.4130),
    "Dhanmondi":                                (23.7461, 90.3742),
    "Dhanmondi, Dhaka":                         (23.7472, 90.3760),
    "Shanta shalmoli Dhanmondi project":        (23.7650, 90.3590),
    "Shanta shalmoli Dhanmondi Dhaka":          (23.7650, 90.3590),
    "Bosila, Dhaka.":                           (23.7198, 90.3503),
    "Bocila":                                   (23.7198, 90.3503),
    "Shamlapur Western city, bosila":           (23.7180, 90.3480),
    "40 fit bosila Mohammadpur":                (23.7220, 90.3540),
    "Khagan, Ashulia":                          (23.8810, 90.2820),
    "Uttara":                                   (23.8759, 90.3795),
    "Uttara 1":                                 (23.8720, 90.3780),
    "Uttata 10":                                (23.8800, 90.3820),
    "Uttara,House  12 . Road 07. Sector  04 . Uttara": (23.8760, 90.3790),
    "House 23,Road 27,Sector 07,Uttara":        (23.8780, 90.3810),
    "Vabnartek, Ranabola, Uttara":              (23.8700, 90.3760),
    "Rupayan City Uttara, Uttara, Dhaka.":      (23.8750, 90.3800),
    "Pagar, Tongi, Gazipur .":                  (23.8950, 90.4060),
    "Tongi":                                    (23.8940, 90.4050),
    "RDDL Gul Mahal, Mirpur":                   (23.8220, 90.3650),
    "Mirpur":                                   (23.8060, 90.3600),
    "Mirpur-06":                                (23.8100, 90.3550),
    "Khalsi,mirpur":                            (23.8180, 90.3620),
    "Chowdhuri Mansion, Plot-22, Block-E, Extention Pallabi, Mirpur, Dhaka": (23.8350, 90.3580),
    "Turag":                                    (23.8490, 90.3620),
    "Deyabari":                                 (23.8510, 90.3560),
    "Dieabari":                                 (23.8510, 90.3560),
    "Nolvog, Dieabari":                         (23.8520, 90.3540),
    "Ashulia":                                  (23.9100, 90.2650),
    "Aragon, Aahulia, Dhaka.":                  (23.9080, 90.2700),
    "Vorari, Tetuljora, Savar, Dhaka.":         (23.8600, 90.2700),
    "Savar":                                    (23.8560, 90.2660),
    "Zirobo, Ashulia":                          (23.9000, 90.2750),
    "Dag.RS 228, |L#73, East Norshinghapur, Zirabo, Ashulia, Savar, Dhaka-1341.": (23.9010, 90.2740),
    "Nikunja-1, Khilkhet, Dhaka.":              (23.8340, 90.4210),
    "Nikunja-1, Dhaka.":                        (23.8340, 90.4210),
    "Nikunjo 1, Dhaka":                         (23.8340, 90.4200),
    "Khilkhet":                                 (23.8330, 90.4220),
    "ECB Chattar, Dhaka Cantarment":            (23.7980, 90.3920),
    "Starpath Business Centre, Plot: 02, Lake Circus, Kalabagan, Dhaka.": (23.7500, 90.3810),
    "Kola Bagan":                               (23.7500, 90.3800),
    "Panthapath, Danmondi":                     (23.7530, 90.3870),
    "Asad Gate":                                (23.7540, 90.3740),
    "Farmget ":                                 (23.8550, 90.3570),
    "Bulbul Heights, 78 Park Road, Baridhara, Dhaka.": (23.7980, 90.4290),
    "Baridhara":                                (23.7980, 90.4280),
    "Banani, Dhaka":                            (23.7936, 90.4035),
    "Banani, ":                                 (23.7936, 90.4035),
    "Banani ":                                  (23.7936, 90.4035),
    "Mahakhali":                                (23.7890, 90.4020),
    "Mohakhali":                                (23.7890, 90.4020),
    "Ranavola":                                 (23.8700, 90.3750),
    "Manikgonj":                                (23.8640, 90.0120),
    "Shamoly":                                  (23.7720, 90.3680),
    "Kawla":                                    (23.8600, 90.3900),
    "Bashundhara":                              (23.8140, 90.4350),
    "Rayer Bazar":                              (23.7480, 90.3620),
    "Hilton Tower, 156/1, Sultanganj, Rayer Bazar, Dhaka (Behind Mukti Cinema Hall).": (23.7470, 90.3610),
    "Satrasta,tejgaon":                         (23.7710, 90.4000),
    "Tejgaon":                                  (23.7700, 90.3980),
    "Dokkin Khan":                              (23.8900, 90.4180),
    "Vashantek":                                (23.8280, 90.3540),
    "Kalampur":                                 (23.9200, 90.3800),
    "Dhamrai":                                  (23.8970, 90.1990),
    "Kamarpara":                                (23.9050, 90.3960),
    "Gulshan":                                  (23.7925, 90.4130),
    "Niketon":                                  (23.7870, 90.4050),
    "Uttarkhan":                                (23.9050, 90.4050),
    "Hazaribag":                                (23.7280, 90.3660),
    "Birulia":                                  (23.8620, 90.3380),
    "Tati Bazar":                               (23.7180, 90.4140),
    "300 feet":                                 (23.8240, 90.3640),
    "Gabtoli":                                  (23.7910, 90.3340),
    "GLG Rahim Rishad Platinum Palace, House: 1, Road: 14/B, Sector: 4, Uttara, Dhaka.": (23.8760, 90.3800),
    "Akij Foundation Madrasha Keraniganj":      (23.6820, 90.3570),
    "Ashkona, airport Dhaka":                   (23.8440, 90.3970),
    "Rupayan City Uttara":                      (23.8750, 90.3800),
}

# ── Client → (address, lat, lng) mapping ──────────────────────────────────────
CLIENT_LOCATIONS = {
    "AKIJ-MONOWARA TRUST(Akij venture)":        ("Nayadingi,Saturia,Manikganj",          23.8640, 90.0120),
    "Asset Developments & Holdings Limited":    ("Gulshan, Dhaka",                         23.7934, 90.4130),
    "Green Land":                               ("Dhanmondi",                              23.7461, 90.3742),
    "Homelink Real Estate Ltd. (Project-14)":   ("Bosila, Dhaka.",                         23.7198, 90.3503),
    "M/S. S. LOVLU ENTERPRISE":                 ("Khagan, Ashulia",                        23.8810, 90.2820),
    "Md. Hafizur Rahman":                       ("Uttara",                                  23.8759, 90.3795),
    "PARADISE WASHING PLANT LTD":               ("Pagar, Tongi, Gazipur",                  23.8950, 90.4060),
    "Rising Design & Development Ltd.":         ("Mirpur",                                  23.8220, 90.3650),
    "Shanta Holdings Ltd":                      ("Shanta shalmoli Dhanmondi project",       23.7650, 90.3590),
    "Sofiullah Developments Ltd.":              ("Turag",                                   23.8490, 90.3620),
    "Ayesha Clothing co.Ltd":                   ("Ashulia",                                 23.9100, 90.2650),
    "G Six Packaging & Accessories Ltd.":       ("Zirobo, Ashulia",                         23.9000, 90.2750),
    "Md. Nasir Ullah":                          ("Nikunja-1, Khilkhet, Dhaka.",             23.8340, 90.4210),
    "Oasis Enterprise":                         ("ECB Chattar, Dhaka Cantonment",           23.7980, 90.3920),
    "Radisson Creations LTD":                   ("Tongi",                                   23.8940, 90.4050),
    "Rupayan Housing Estate Ltd.(Project: Rupayan City Uttara)": ("Uttara", 23.8750, 90.3800),
    "STI Builders (Tower 36)":                  ("Uttara",                                  23.8700, 90.3800),
    "Arif Ashraf":                              ("Uttara",                                  23.8720, 90.3785),
    "GLG Assets Ltd":                           ("Uttara, Sector 4",                        23.8760, 90.3800),
    "Joney Enterprise":                         ("Satrasta, Tejgaon",                       23.7710, 90.4000),
    "Md. Maidul Islam":                         ("Uttara",                                   23.8730, 90.3790),
    "Nortex Textile Mills Ltd":                 ("Nikunja-1, Dhaka",                        23.8340, 90.4200),
    "Shin Shin Apparels Ltd":                   ("Zirabo, Ashulia",                          23.9010, 90.2740),
    "Starpath Holdings Limited":                ("Kalabagan, Dhaka",                        23.7500, 90.3810),
    "SWADESH ABASON":                           ("Dieabari",                                23.8510, 90.3560),
    "Austral Properties Ltd.":                  ("Pallabi, Mirpur, Dhaka",                  23.8350, 90.3580),
    "Brothers Community Alliance Ltd.":         ("Bosila",                                  23.7180, 90.3480),
    "Creative Builders Ltd":                    ("Panthapath, Dhanmondi",                   23.7530, 90.3870),
    "Green Dot Limited":                        ("Ashulia",                                  23.9080, 90.2700),
    " Rangs Properties Ltd.":                   ("Farmgate",                                23.8550, 90.3570),
    "Rising Property Development":              ("Mirpur",                                  23.8100, 90.3600),
    "MD.Abdul Mannan":                          ("Uttara",                                   23.8755, 90.3800),
    "Bandhon Nibash":                           ("Dieabari",                                23.8515, 90.3550),
    "BYD Builders Ltd.":                        ("Mirpur",                                  23.8180, 90.3620),
    "Manama Developments Ltd":                  ("Baridhara, Dhaka",                        23.7980, 90.4280),
    "Mohammad Riaz":                            ("Uttara",                                   23.8765, 90.3810),
    "P2P Engineering & construction Ltd":       ("Khagan, Ashulia",                         23.8800, 90.2830),
    "Mutual Living Limited(Project: Mutual 765)": ("Dhanmondi",                             23.7450, 90.3730),
    "Akij Plastics Ltd.":                       ("Tongi, Gazipur",                          23.8950, 90.4050),
    "Akij Textile Mills Ltd. (RMC)":            ("Ashulia",                                  23.9090, 90.2660),
    "Anisha Enterprise":                        ("Mirpur",                                  23.8220, 90.3620),
    "Md Bellal Hossain":                        ("Uttara",                                   23.8745, 90.3785),
    "Bochila City Developers Ltd":              ("Bosila",                                  23.7200, 90.3510),
    "Dehsar Works":                             ("Gabtoli",                                 23.7910, 90.3340),
    "MD Osman Ali Construction Ltd.":           ("Uttara",                                   23.8770, 90.3800),
    "Vertex Wear Ltd":                          ("Ashulia",                                  23.9120, 90.2680),
    "Signature 11 ltd (Shanta)":                ("Dhanmondi",                               23.7655, 90.3600),
    "Suvastu Properties Ltd(Project: Shaptarshi))": ("Bashundhara",                         23.8140, 90.4350),
    "A- Z Bangladesh":                          ("Ashulia",                                  23.9100, 90.2700),
    "Akij Bekars Ltd":                          ("Ashulia",                                  23.9080, 90.2650),
    "Bangladesh Specialized Hospital Ltd.":     ("Shyamoli, Dhaka",                         23.7720, 90.3680),
    "Monzzor Hossain  Mamun":                   ("Uttara",                                   23.8760, 90.3800),
    "Osman Ali":                                ("Uttara",                                   23.8755, 90.3795),
    "Prince Business Center":                   ("Banani, Dhaka",                           23.7936, 90.4035),
    "Shanto-Mariam University of Creative Technology": ("Uttara",                           23.8790, 90.3820),
    "Sunvista Properties":                      ("Uttara",                                   23.8740, 90.3785),
    "Urban Design":                             ("Uttara, Sector 10",                       23.8800, 90.3820),
    "Amin Mohammad":                            ("Uttara",                                   23.8750, 90.3800),
    "Goutom Kumer Sarker":                      ("Tejgaon",                                 23.7700, 90.3980),
    "Hossain builders(Shopnochoa tower)":       ("Mirpur",                                  23.8100, 90.3580),
    "Hilton Tower":                             ("Rayer Bazar, Dhaka",                      23.7470, 90.3610),
    "Md Alamgir Hossain":                       ("Dieabari",                                23.8520, 90.3555),
    "Next Spaces Limited":                      ("Bashundhara",                             23.8150, 90.4350),
    "Debonair Felt and Geotextile ltd":         ("Kamarpara, Gazipur",                      23.9050, 90.3960),
    "Mahamud Hasan":                            ("Uttara",                                   23.8760, 90.3790),
    "Nabid Petroleum Co.Limited":               ("Kawla",                                   23.8600, 90.3900),
    "Priyoprangon":                             ("Mirpur",                                  23.8200, 90.3630),
    "Ventura Properties ":                      ("Bashundhara",                             23.8140, 90.4360),
    "Aries Securities Limited":                 ("Gulshan",                                 23.7930, 90.4120),
    "Bondhon Nibash":                           ("Dieabari",                                23.8515, 90.3555),
    "Bright Home Builders Ltd.":                ("Mirpur",                                  23.8070, 90.3590),
    "CONCEPT ENGINEERING& DEVELOPMENT LTD.":    ("Gabtoli",                                 23.7900, 90.3330),
    "Ashiyan Lands Development Ltd.":           ("Uttarkhan",                               23.9050, 90.4050),
    "Nafiz Enterprise":                         ("Uttara",                                   23.8745, 90.3780),
    "Papiya Khan":                              ("Dhanmondi",                               23.7480, 90.3750),
    "Space Ten Ltd":                            ("Baridhara",                               23.7985, 90.4285),
    "Deshar Works Ltd":                         ("Gabtoli",                                 23.7910, 90.3340),
    "Jahangir Alom":                            ("Ashulia",                                  23.9095, 90.2660),
    "Abdul Hasan":                              ("Mirpur",                                  23.8150, 90.3610),
    "Dihan Shah Properties":                    ("Uttara",                                   23.8740, 90.3800),
    "Dream House":                              ("Dianmondi",                               23.7460, 90.3750),
    "Ebrahim & Brothers ":                      ("Tongi",                                   23.8945, 90.4055),
    "NDE Infra Real Estate Ltd.":               ("Bosila",                                  23.7195, 90.3495),
    "Rising  Design Ltd":                       ("Mirpur",                                  23.8210, 90.3640),
    "Shonar Bangla Tower":                      ("Khilkhet",                                23.8335, 90.4215),
    "Toma Holding Ltd":                         ("Tejgaon",                                 23.7715, 90.3985),
    "Arkay Knit Dyeing Mills Ltd":              ("Ashulia",                                  23.9110, 90.2680),
    "Proyash":                                  ("Mirpur",                                  23.8090, 90.3570),
    "Fair Way":                                 ("Uttara",                                   23.8760, 90.3800),
    "MA Jobber":                                ("Ashulia",                                  23.9085, 90.2660),
    "Nassa Holding Ltd":                        ("Gulshan",                                 23.7920, 90.4125),
    "South Breeze Housing Ltd":                 ("Dhanmondi",                               23.7455, 90.3738),
    "Beximco Engineering Ltd.":                 ("Ashulia",                                  23.9100, 90.2670),
    "MIRSAIGE":                                 ("Mirpur",                                  23.8200, 90.3630),
    "Orchid and Textile Tower":                 ("Ashulia",                                  23.9095, 90.2645),
    "Siddikur Rahman":                          ("Dianmondi",                               23.7462, 90.3735),
    "Md Abdur Rahim":                           ("Tongi",                                   23.8940, 90.4045),
    "Nandan Kanon Housing Ltd.":                ("Ashulia",                                  23.9105, 90.2655),
    "Accurate Assets Holdings Limited":         ("Uttara",                                   23.8755, 90.3810),
    "Asset Development Ltd":                    ("Gulshan",                                 23.7928, 90.4128),
    "Md Irfan Khan":                            ("Uttara",                                   23.8748, 90.3788),
    "Orchid & Development Ltd":                 ("Ashulia",                                  23.9090, 90.2648),
    "Anik Trading":                             ("Tongi",                                   23.8948, 90.4058),
    "JFA Enterprise Ltd":                       ("Mirpur",                                  23.8215, 90.3645),
    "Md. Alamgir Hossain":                      ("Dieabari",                                23.8525, 90.3558),
    "Jahangir Hossain":                         ("Ashulia",                                  23.9088, 90.2668),
    "Umayer Trading Cor. Ltd":                  ("Tongi",                                   23.8942, 90.4048),
    "Universal Medical Collage":                ("Uttara",                                   23.8752, 90.3796),
    "Valven Homes Ltd":                         ("Bashundhara",                             23.8145, 90.4355),
    "Rising Design Ltd":                        ("Mirpur",                                  23.8218, 90.3648),
    "MS Construction Ltd":                      ("Mirpur",                                  23.8205, 90.3635),
    "M/S SR Trading":                           ("Ashulia",                                  23.9098, 90.2658),
    "Orchid & Textile Ltd":                     ("Ashulia",                                  23.9092, 90.2652),
    "ST Enterprise":                            ("Tongi",                                   23.8946, 90.4052),
    "Humayun Rashid Real Estate Ltd":           ("Bashundhara",                             23.8148, 90.4348),
    "M/S Lavlu Enterprise":                     ("Khagan, Ashulia",                         23.8805, 90.2815),
}

PSI_GRADES = [3000, 3500, 4000, 4000, 4000, 4350, 4500, 5000, 5800, 6000]
PLANTS     = ["Schwing Stetter Plant", "Fujian Xinda Plant"]

def gen_qty():
    return round(random.choice([
        random.uniform(3.0, 15.0),
        random.uniform(15.0, 50.0),
        random.uniform(50.0, 120.0),
    ]), 2)

def make_record(d, client, pump=None):
    addr, lat, lng = CLIENT_LOCATIONS[client]
    # small jitter so same client on different days slightly varies
    lat += random.uniform(-0.0005, 0.0005)
    lng += random.uniform(-0.0005, 0.0005)
    qty  = gen_qty()
    psi  = random.choice(PSI_GRADES)
    unit = random.choice(PLANTS)
    if pump is None:
        pump = "Yes" if random.random() > 0.45 else "No"
    return {
        "date":            d.strftime("%Y-%m-%d"),
        "unit":            unit,
        "client_name":     client,
        "project_address": addr,
        "lat":             round(lat, 6),
        "lng":             round(lng, 6),
        "psi":             psi,
        "qty_m3":          qty,
        "qty_cft":         round(qty * 35.315, 2),
        "pump_status":     pump,
    }

# ── Generate full March 2026 ───────────────────────────────────────────────────
clients = list(CLIENT_LOCATIONS.keys())
records = []

for day in range(1, 32):
    d = datetime(2026, 3, day)
    # 8-18 deliveries per day, weighted to clients near Dhaka
    n_deliveries = random.randint(10, 22)
    day_clients  = random.sample(clients, min(n_deliveries, len(clients)))
    for client in day_clients:
        records.append(make_record(d, client))

df = pd.DataFrame(records)
df = df.sort_values(["date", "unit", "client_name"]).reset_index(drop=True)

out_path = "route_data_march2026.csv"
df.to_csv(out_path, index=False)
print(f"✅ Generated {len(df)} records across 31 days → {out_path}")
print(df.groupby("date")["qty_m3"].agg(["count","sum"]).rename(columns={"count":"deliveries","sum":"total_m3"}).to_string())

if __name__ == "__main__":
    pass
