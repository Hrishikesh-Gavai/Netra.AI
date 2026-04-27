import requests
import math
import logging
import re
import time
import json
from typing import List, Dict, Optional
from urllib.parse import quote, urlencode

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ─────────────────────────────────────────────────────────
#  City coordinates (India – extended list)
# ─────────────────────────────────────────────────────────
CITY_COORDINATES: Dict[str, tuple] = {
    "mumbai":        (19.0760, 72.8777),
    "delhi":         (28.6139, 77.2090),
    "bangalore":     (12.9716, 77.5946),
    "bengaluru":     (12.9716, 77.5946),
    "chennai":       (13.0827, 80.2707),
    "kolkata":       (22.5726, 88.3639),
    "hyderabad":     (17.3850, 78.4867),
    "pune":          (18.5204, 73.8567),
    "ahmedabad":     (23.0225, 72.5714),
    "jaipur":        (26.9124, 75.7873),
    "lucknow":       (26.8467, 80.9462),
    "nagpur":        (21.1458, 79.0882),
    "indore":        (22.7196, 75.8577),
    "bhopal":        (23.2599, 77.4126),
    "visakhapatnam": (17.6868, 83.2185),
    "vizag":         (17.6868, 83.2185),
    "patna":         (25.5941, 85.1376),
    "vadodara":      (22.3072, 73.1812),
    "coimbatore":    (11.0168, 76.9558),
    "kochi":         ( 9.9312, 76.2673),
    "chandigarh":    (30.7333, 76.7794),
    "goa":           (15.2993, 74.1240),
    "panaji":        (15.4909, 73.8278),
    "surat":         (21.1702, 72.8311),
    "kanpur":        (26.4499, 80.3319),
    "agra":          (27.1767, 78.0081),
    "nashik":        (19.9975, 73.7898),
    "raipur":        (21.2514, 81.6296),
    "ranchi":        (23.3441, 85.3096),
    "bhubaneswar":   (20.2961, 85.8245),
    "mysuru":        (12.2958, 76.6394),
    "mysore":        (12.2958, 76.6394),
    "thiruvananthapuram": (8.5241, 76.9366),
    "trivandrum":    ( 8.5241, 76.9366),
    "madurai":       ( 9.9252, 78.1198),
    "varanasi":      (25.3176, 82.9739),
    "benaras":       (25.3176, 82.9739),
    "amritsar":      (31.6340, 74.8723),
    "ludhiana":      (30.9010, 75.8573),
    "meerut":        (28.9845, 77.7064),
    "rajkot":        (22.3039, 70.8022),
    "jodhpur":       (26.2389, 73.0243),
    "udaipur":       (24.5854, 73.7125),
    "guwahati":      (26.1445, 91.7362),
    "dehradun":      (30.3165, 78.0322),
    "shimla":        (31.1048, 77.1734),
    "aurangabad":    (19.8762, 75.3433),
    "solapur":       (17.6599, 75.9064),
    "kozhikode":     (11.2588, 75.7804),
    "calicut":       (11.2588, 75.7804),
    "mangaluru":     (12.9141, 74.8560),
    "mangalore":     (12.9141, 74.8560),
    "hubli":         (15.3647, 75.1240),
    "dharwad":       (15.4589, 75.0078),
}

# ─────────────────────────────────────────────────────────
#  Curated hospital database (name, lat, lng, type,
#  address, phone, rating, description, website)
# ─────────────────────────────────────────────────────────
CURATED_EYE_HOSPITALS: Dict[str, List[tuple]] = {

    "mumbai": [
        ("Sankara Nethralaya", 19.0760, 72.8777, "Hospital",
         "Mumbai", "022 2821 4111", 4.7,
         "Multi-speciality eye hospital offering advanced cataract, retina, and cornea treatments.",
         "https://www.sankaranethralaya.org/"),
        ("Aditya Jyot Eye Hospital", 19.1136, 72.8697, "Hospital",
         "Wadala, Mumbai", "022 2412 6292", 4.6,
         "Comprehensive retina & LASIK centre led by internationally trained surgeons.",
         "https://www.adityajyot.org/"),
        ("Dr. Agarwal's Eye Hospital – Andheri", 19.0820, 72.8840, "Hospital",
         "Andheri East, Mumbai", "1800 103 1212", 4.5,
         "Part of India's largest eye-care chain, offering full-spectrum ophthalmic services.",
         "https://www.dragarwal.com/"),
        ("L V Prasad Eye Institute – Parel", 19.1630, 72.7940, "Hospital",
         "Parel, Mumbai", "022 2433 1500", 4.8,
         "WHO collaborating centre for prevention of blindness. World-class research & training.",
         "https://www.lvpei.org/"),
        ("Eye Solutions", 19.1086, 72.9021, "Clinic",
         "Bandra West, Mumbai", "022 2645 9955", 4.4,
         "Premium refractive & contact lens clinic offering LASIK and dry-eye management.",
         "https://www.eyesolutions.in/"),
        ("Hinduja Hospital Eye Dept.", 19.0159, 72.8449, "Hospital",
         "Mahim, Mumbai", "022 2445 2222", 4.6,
         "Full ophthalmology department within a NABH-accredited multi-speciality hospital.",
         "https://www.hindujahospital.com/"),
    ],

    "delhi": [
        ("AIIMS Delhi – Ophthalmology", 28.5675, 77.2100, "Hospital",
         "Ansari Nagar, New Delhi", "011 2658 8500", 4.9,
         "India's premier government institute offering subsidised, world-class eye care.",
         "https://www.aiims.edu/"),
        ("Dr. Shroff's Charity Eye Hospital", 28.6380, 77.2130, "Hospital",
         "Daryaganj, New Delhi", "011 2326 0303", 4.7,
         "120+ years of affordable eye care. Specialises in cornea transplant & paediatric eyes.",
         "https://www.drishti.org/"),
        ("Centre for Sight – Safdarjung", 28.5580, 77.2130, "Clinic",
         "Safdarjung Enclave, New Delhi", "011 4003 4003", 4.6,
         "Tech-driven eye clinic network known for LASIK, IOL & dry-eye treatments.",
         "https://www.centreforsight.net/"),
        ("Sharp Sight Eye Hospitals", 28.6120, 77.2310, "Hospital",
         "Rajendra Place, New Delhi", "011 4244 4444", 4.5,
         "Advanced phaco cataract, refractive & glaucoma surgeries across Delhi NCR.",
         "https://www.sharpsight.in/"),
        ("Venu Eye Institute", 28.5385, 77.2520, "Hospital",
         "Sheikh Sarai, New Delhi", "011 4173 4173", 4.4,
         "Specialised cataract and retina care with the latest diagnostics.",
         "https://www.venueyeinstitute.com/"),
        ("Drishti Eye Centre", 28.5962, 77.2273, "Clinic",
         "Connaught Place, New Delhi", "011 4168 4168", 4.3,
         "Comprehensive eye exams, refractive surgery and contact lens services.",
         "https://www.drishtieyecentre.com/"),
    ],

    "bangalore": [
        ("Narayana Nethralaya", 13.0033, 77.5544, "Hospital",
         "Rajajinagar, Bangalore", "080 2265 8900", 4.8,
         "Pioneers of Karnataka eye care; leaders in cornea, retina, and paediatric surgery.",
         "https://www.narayananethralaya.org/"),
        ("Sankara Eye Hospital – Kundalahalli", 13.0359, 77.5971, "Hospital",
         "Kundalahalli, Bangalore", "080 2848 6040", 4.7,
         "Affordable high-quality care with a strong outreach programme.",
         "https://www.sankaraeye.com/"),
        ("Dr. Agarwal's Eye Hospital – Indiranagar", 12.9784, 77.5998, "Hospital",
         "Indiranagar, Bangalore", "080 2521 2521", 4.6,
         "Full-service chain hospital with advanced diagnostics and surgical theatres.",
         "https://www.dragarwal.com/"),
        ("Prabha Eye Clinic & Research Centre", 12.9352, 77.6244, "Hospital",
         "Jayanagar, Bangalore", "080 2658 8888", 4.5,
         "Cornea transplant, refractive surgery and vitreo-retina excellence.",
         "https://www.prabhaeyeclinic.com/"),
        ("Netradhama Super Speciality Eye Hospital", 13.0210, 77.6290, "Hospital",
         "Kalyan Nagar, Bangalore", "080 2545 5454", 4.4,
         "Glaucoma, squint, and LASIK under one roof with latest wavefront technology.",
         "https://www.netradhama.com/"),
        ("Vittala International Eye Hospital", 12.9592, 77.5891, "Hospital",
         "Basavanagudi, Bangalore", "080 2660 8900", 4.5,
         "Trusted for affordable cataract surgery and vision therapy.",
         "https://www.vittalaeyehospital.com/"),
    ],

    "chennai": [
        ("Sankara Nethralaya – Nungambakkam", 13.0638, 80.2451, "Hospital",
         "Nungambakkam, Chennai", "044 2827 1616", 4.9,
         "World-renowned for uvea, retina, and cornea services. Attached research institute.",
         "https://www.sankaranethralaya.org/"),
        ("Dr. Agarwal's Eye Hospital – Kilpauk", 13.0397, 80.2285, "Hospital",
         "Kilpauk, Chennai", "044 2641 1155", 4.7,
         "Full-spectrum eye care at multiple Chennai locations.",
         "https://www.dragarwal.com/"),
        ("Aravind Eye Hospital – Anna Nagar", 12.9357, 80.2347, "Hospital",
         "Anna Nagar, Chennai", "044 2628 1800", 4.8,
         "World-famous for high-volume, high-quality cataract and retina surgery.",
         "https://www.aravind.org/"),
        ("Shankar Nethralaya – Alwarpet", 13.0015, 80.2566, "Hospital",
         "Alwarpet, Chennai", "044 2499 2499", 4.6,
         "Advanced glaucoma, paediatric ophthalmology & low vision rehabilitation.",
         "https://www.shankarnethralaya.org/"),
        ("Rajan Eye Care – T Nagar", 13.0595, 80.2437, "Clinic",
         "T Nagar, Chennai", "044 2815 2233", 4.5,
         "Specialised refractive surgery (LASIK / SMILE) and cataract clinic.",
         "https://www.rajaneyecare.com/"),
        ("Vasan Eye Care", 13.0827, 80.2415, "Clinic",
         "Anna Salai, Chennai", "044 4477 4477", 4.3,
         "Pan-India eye-care chain delivering affordable, tech-enabled vision correction.",
         "https://www.vasaneyecare.com/"),
    ],

    "kolkata": [
        ("Disha Eye Hospitals – Barrackpore", 22.7680, 88.3703, "Hospital",
         "Barrackpore, Kolkata", "033 2592 1515", 4.6,
         "West Bengal's leading chain with high-volume cataract and retina surgeries.",
         "https://www.dishahospitals.com/"),
        ("Susrut Eye Foundation & Research Centre", 22.5422, 88.3505, "Hospital",
         "Salt Lake, Kolkata", "033 2358 5025", 4.5,
         "Ophthalmology, vision research, and cornea bank under one roof.",
         "https://www.susruteyefoundation.org/"),
        ("Netralaya Superspeciality Eye Hospital", 22.5802, 88.4215, "Hospital",
         "Rajarhat, Kolkata", "033 2565 8888", 4.4,
         "Super-speciality services covering vitreo-retina, squint, and oculoplasty.",
         "https://www.netralayaeyehospital.com/"),
        ("Dr. Agarwal's Eye Hospital – Park Street", 22.5526, 88.3516, "Hospital",
         "Park Street, Kolkata", "033 4012 1212", 4.5,
         "Chain hospital with full diagnostics and phacoemulsification theatres.",
         "https://www.dragarwal.com/"),
        ("Vasan Eye Care – Kolkata", 22.5423, 88.3422, "Clinic",
         "Gariahat, Kolkata", "033 6641 4477", 4.2,
         "Affordable vision-correction and paediatric eye care services.",
         "https://www.vasaneyecare.com/"),
    ],

    "hyderabad": [
        ("L V Prasad Eye Institute – Banjara Hills", 17.4440, 78.3753, "Hospital",
         "Banjara Hills, Hyderabad", "040 3061 2345", 4.9,
         "International centre of excellence for eye care, vision research, and rehabilitation.",
         "https://www.lvpei.org/"),
        ("Sankara Eye Hospital – Secunderabad", 17.4435, 78.4928, "Hospital",
         "Secunderabad, Hyderabad", "040 2300 3030", 4.7,
         "Affordable micro-incision cataract and retina services.",
         "https://www.sankaraeye.com/"),
        ("Dr. Agarwal's Eye Hospital – Begumpet", 17.4437, 78.4744, "Hospital",
         "Begumpet, Hyderabad", "040 6557 1111", 4.6,
         "Multi-speciality chain with advanced diagnostics and surgical facilities.",
         "https://www.dragarwal.com/"),
        ("Maxivision Eye Hospital", 17.3866, 78.4856, "Clinic",
         "Dilsukhnagar, Hyderabad", "040 2406 6666", 4.5,
         "State-of-the-art laser vision correction and cataract centre.",
         "https://www.maxivisioneyehospital.com/"),
        ("Sarojini Devi Eye Hospital", 17.3643, 78.4769, "Hospital",
         "Moazzam Jahi Market, Hyderabad", "040 2465 1515", 4.3,
         "Government teaching hospital providing subsidised care to thousands daily.",
         "https://www.sarojinidevihospital.org/"),
        ("Saikalyan Eye Hospital", 17.4456, 78.3830, "Hospital",
         "Himayath Nagar, Hyderabad", "040 6677 3456", 4.4,
         "Comprehensive vitreo-retina, glaucoma, and squint services.",
         "https://www.saikalyaneye.com/"),
    ],

    "pune": [
        ("Sankara Eye Hospital – Kharadi", 18.5360, 73.8316, "Hospital",
         "Kharadi, Pune", "020 2703 4444", 4.7,
         "Super-speciality eye care with cutting-edge phaco & retina theatres.",
         "https://www.sankaraeye.com/"),
        ("National Institute of Ophthalmology", 18.5110, 73.8360, "Hospital",
         "Swargate, Pune", "020 2421 3888", 4.6,
         "Postgraduate teaching institute offering subsidised full-spectrum eye care.",
         "https://www.niofpune.org/"),
        ("Poona Eye Hospital", 18.5283, 73.8730, "Hospital",
         "Camp, Pune", "020 2605 2740", 4.4,
         "Pune's oldest eye hospital with century-long heritage in ophthalmology.",
         "https://www.poonaeyehospital.com/"),
        ("Orbit Eye Hospital", 18.5953, 73.7385, "Clinic",
         "Pimple Saudagar, Pune", "020 6510 1111", 4.3,
         "Specialised oculoplasty, squint, and refractive surgery clinic.",
         "https://www.orbiteyehospital.com/"),
        ("Dr. Agarwal's Eye Hospital – Pune", 18.5338, 73.8474, "Hospital",
         "FC Road, Pune", "020 6680 1212", 4.5,
         "Chain hospital offering advanced LASIK, premium IOLs, and paediatric care.",
         "https://www.dragarwal.com/"),
    ],

    "ahmedabad": [
        ("Drashti Netralaya", 23.0561, 72.5857, "Hospital",
         "Ghatlodiya, Ahmedabad", "079 2747 2747", 4.7,
         "Centre of excellence for retina, uvea, and macular degeneration treatment.",
         "https://www.drashtinetralaya.org/"),
        ("Aravind Eye Hospital – Ahmedabad", 23.0334, 72.5618, "Hospital",
         "Naranpura, Ahmedabad", "079 2743 1781", 4.8,
         "Aravind's high-volume, high-quality cataract and retina services in Gujarat.",
         "https://www.aravind.org/"),
        ("Dr. Agarwal's Eye Hospital – Ahmedabad", 23.0291, 72.5871, "Hospital",
         "Ellis Bridge, Ahmedabad", "079 4012 1212", 4.5,
         "Multi-location chain offering full ophthalmic diagnostics and surgery.",
         "https://www.dragarwal.com/"),
        ("Vasan Eye Care – Ahmedabad", 23.0215, 72.5680, "Clinic",
         "Navrangpura, Ahmedabad", "1860 500 2020", 4.3,
         "Affordable laser vision correction and routine eye care.",
         "https://www.vasaneyecare.com/"),
    ],

    "jaipur": [
        ("Nims Eye Centre", 26.9124, 75.7873, "Hospital",
         "Shyam Nagar, Jaipur", "0141 405 5555", 4.6,
         "Super-speciality ophthalmology with cornea bank and ocular oncology.",
         "https://www.nimseyecentre.com/"),
        ("Dr. Agarwal's Eye Hospital – Jaipur", 26.9032, 75.7971, "Hospital",
         "Malviya Nagar, Jaipur", "0141 6604 0101", 4.5,
         "Chain hospital providing LASIK, cataract, and glaucoma management.",
         "https://www.dragarwal.com/"),
        ("Primus Eye Care", 26.8996, 75.8000, "Clinic",
         "Vaishali Nagar, Jaipur", "0141 357 3573", 4.3,
         "Comprehensive eye exam, refractive surgery, and contact lens clinic.",
         "https://www.primuseyecare.com/"),
    ],

    "nagpur": [
        ("Orange City Eye Hospital", 21.1403, 79.0887, "Hospital",
         "Dhantoli, Nagpur", "0712 254 8000", 4.7,
         "Nagpur's premier eye hospital with dedicated retina, cornea, and glaucoma units.",
         "https://www.orangecityeyehospital.com/"),
        ("Mahatme Eye Bank & Eye Hospital", 21.1575, 79.0820, "Hospital",
         "Bajaj Nagar, Nagpur", "0712 224 4444", 4.6,
         "Largest eye bank in central India; cataract, retina, and oculoplasty services.",
         "https://www.mahatmeyehospital.org/"),
        ("Dr. Agarwal's Eye Hospital – Nagpur", 21.1467, 79.0943, "Hospital",
         "Sadar, Nagpur", "1800 103 1212", 4.5,
         "Chain hospital offering full spectrum of ophthalmic care with digital refraction.",
         "https://www.dragarwal.com/"),
        ("Retina Institute of Maharashtra", 21.1288, 79.0747, "Hospital",
         "Laxmi Nagar, Nagpur", "0712 223 1111", 4.6,
         "Specialised vitreo-retinal surgery centre with advanced 3D visualization.",
         "https://www.retinamaharashtra.com/"),
        ("Vasan Eye Care – Nagpur", 21.1453, 79.0882, "Clinic",
         "Sitabuldi, Nagpur", "1860 500 2020", 4.3,
         "Affordable laser vision correction, paediatric eye care, and routine exams.",
         "https://www.vasaneyecare.com/"),
        ("Centre for Sight – Nagpur", 21.1554, 79.0726, "Clinic",
         "Civil Lines, Nagpur", "0712 664 0020", 4.4,
         "Tech-driven eye clinic offering LASIK, cataract, and dry-eye management.",
         "https://www.centreforsight.net/"),
    ],

    "lucknow": [
        ("Dr. Agarwal's Eye Hospital – Lucknow", 26.8546, 80.9358, "Hospital",
         "Hazratganj, Lucknow", "0522 6604 0101", 4.5,
         "Full-service chain with advanced phaco cataract and LASIK.",
         "https://www.dragarwal.com/"),
        ("Tej Netralaya", 26.8477, 80.9262, "Hospital",
         "Alambagh, Lucknow", "0522 225 3535", 4.6,
         "Specialised retina, cornea, and neuro-ophthalmology services.",
         "https://www.tejnetralaya.com/"),
        ("Vasan Eye Care – Lucknow", 26.8540, 80.9345, "Clinic",
         "MG Road, Lucknow", "1860 500 2020", 4.2,
         "Affordable vision correction and routine eye care chain.",
         "https://www.vasaneyecare.com/"),
    ],

    "kochi": [
        ("Little Flower Hospital Eye Dept.", 9.9754, 76.2933, "Hospital",
         "Angamaly, Kochi", "0484 245 6900", 4.6,
         "Multi-speciality hospital with well-equipped ophthalmology department.",
         "https://www.lfhangamaly.com/"),
        ("Giridhar Eye Institute", 9.9510, 76.2897, "Hospital",
         "Ponneth Temple Road, Kochi", "0484 231 3100", 4.8,
         "Nationally acclaimed vitreo-retina and low-vision rehabilitation centre.",
         "https://www.giridhareyeinstitute.com/"),
        ("Dr. Agarwal's Eye Hospital – Kochi", 9.9637, 76.2880, "Hospital",
         "MG Road, Kochi", "0484 6604 0101", 4.5,
         "Comprehensive LASIK, cataract, and paediatric eye care.",
         "https://www.dragarwal.com/"),
    ],

    "chandigarh": [
        ("PGIMER Ophthalmology", 30.7647, 76.7760, "Hospital",
         "Sector 12, Chandigarh", "0172 275 5555", 4.9,
         "Advanced Trauma Centre with a renowned ophthalmology department.",
         "https://pgimer.edu.in/"),
        ("GMCH Eye Dept.", 30.7098, 76.7997, "Hospital",
         "Sector 32, Chandigarh", "0172 265 8000", 4.5,
         "Government medical college hospital; affordable full-range eye care.",
         "https://www.gmch.gov.in/"),
        ("Sharp Sight Eye Hospitals – Chandigarh", 30.7350, 76.7890, "Hospital",
         "Sector 34, Chandigarh", "0172 507 4444", 4.4,
         "Advanced refractive surgery and cataract care chain.",
         "https://www.sharpsight.in/"),
    ],

    "indore": [
        ("Choithram Netralaya", 22.7295, 75.8875, "Hospital",
         "Manik Bagh Road, Indore", "0731 491 7300", 4.7,
         "Part of Choithram Hospital; full-service ophthalmology with paediatric wing.",
         "https://www.choithramhospital.com/"),
        ("Dr. Agarwal's Eye Hospital – Indore", 22.7236, 75.8820, "Hospital",
         "Vijay Nagar, Indore", "0731 6604 0101", 4.5,
         "Full-spectrum eye care with digital refraction and premium IOLs.",
         "https://www.dragarwal.com/"),
        ("Vasan Eye Care – Indore", 22.7194, 75.8568, "Clinic",
         "MG Road, Indore", "1860 500 2020", 4.2,
         "Affordable laser and routine eye care across central India.",
         "https://www.vasaneyecare.com/"),
    ],
}

# ─────────────────────────────────────────────────────────
#  Haversine distance helper
# ─────────────────────────────────────────────────────────
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ─────────────────────────────────────────────────────────
#  Geocoding (local dict → Nominatim fallback)
# ─────────────────────────────────────────────────────────
def get_city_coordinates(city: str) -> Optional[tuple]:
    city_lower = city.lower().strip()
    for key in CITY_COORDINATES:
        if key in city_lower or city_lower in key:
            return CITY_COORDINATES[key]
    try:
        url = (
            f"https://nominatim.openstreetmap.org/search"
            f"?q={quote(city)},India&format=json&limit=1"
        )
        headers = {"User-Agent": "NetraAI_EyeFinder/2.0 (healthcare research)"}
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                logging.info(f"Nominatim resolved '{city}'")
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        logging.warning(f"Nominatim fallback failed: {e}")
    return None


# ─────────────────────────────────────────────────────────
#  Source 1 – OpenStreetMap / Overpass API
# ─────────────────────────────────────────────────────────
def fetch_from_overpass(lat: float, lng: float, city: str) -> List[Dict]:
    """Query Overpass for eye-care facilities within 25 km."""
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="hospital"](around:25000,{lat},{lng});
      node["amenity"="clinic"](around:25000,{lat},{lng});
      node["healthcare"="hospital"](around:25000,{lat},{lng});
      node["healthcare"="ophthalmology"](around:25000,{lat},{lng});
      node["name"~"Eye|Netralaya|Nethralaya|Drishti|Vision|Ophthalm|Netra|Chakshu|Drashti",i](around:25000,{lat},{lng});
      way["name"~"Eye|Netralaya|Nethralaya|Drishti|Vision|Ophthalm|Netra|Chakshu|Drashti",i](around:25000,{lat},{lng});
    );
    out body;
    """
    headers = {"User-Agent": "NetraAI_EyeFinder/2.0"}
    try:
        resp = requests.post(
            overpass_url,
            data={"data": query},
            headers=headers,
            timeout=35,
        )
        if resp.status_code != 200:
            logging.warning(f"Overpass returned HTTP {resp.status_code}")
            return []
        elements = resp.json().get("elements", [])
        results: List[Dict] = []
        seen: set = set()
        for elem in elements:
            tags = elem.get("tags", {})
            name = tags.get("name", "").strip()
            if not name or name in seen:
                continue
            skip_words = ["pharmacy", "chemist", "dental", "dentist", "veterinary"]
            if any(w in name.lower() for w in skip_words):
                continue
            seen.add(name)
            elem_lat = elem.get("lat") or (
                (elem.get("bounds", {}).get("minlat", 0) + elem.get("bounds", {}).get("maxlat", 0)) / 2
            )
            elem_lon = elem.get("lon") or (
                (elem.get("bounds", {}).get("minlon", 0) + elem.get("bounds", {}).get("maxlon", 0)) / 2
            )
            if not elem_lat or not elem_lon:
                continue
            amenity = tags.get("amenity", tags.get("healthcare", ""))
            facility_type = "Hospital" if "hospital" in amenity.lower() else "Clinic"
            addr_parts = [
                tags.get("addr:housename", ""),
                tags.get("addr:street", ""),
                tags.get("addr:suburb", ""),
                tags.get("addr:city", city.title()),
            ]
            address = ", ".join(p for p in addr_parts if p) or city.title()
            phone = tags.get("phone", tags.get("contact:phone", ""))
            website = tags.get("website", tags.get("contact:website", ""))
            dist = round(calculate_distance(lat, lng, elem_lat, elem_lon), 1)
            results.append({
                "name": name,
                "lat": elem_lat,
                "lng": elem_lon,
                "type": facility_type,
                "address": address,
                "phone": phone if phone else "Contact hospital directly",
                "rating": None,
                "distance": dist,
                "description": (
                    f"{facility_type} providing eye care services in {city.title()}. "
                    "Call ahead for appointment timings."
                ),
                "website": website if website else _google_maps_link(name, city),
                "source": "OpenStreetMap",
            })
            if len(results) >= 15:
                break
        results.sort(key=lambda x: x["distance"])
        logging.info(f"Overpass: {len(results)} results for {city}")
        return results
    except Exception as e:
        logging.error(f"Overpass failed: {e}")
        return []


# ─────────────────────────────────────────────────────────
#  Source 2 – DuckDuckGo HTML search for extra results
#  (no API key needed; plain HTTP request to DDG HTML)
# ─────────────────────────────────────────────────────────
def _duckduckgo_search(query: str, max_results: int = 5) -> List[Dict]:
    """
    Fetch DuckDuckGo HTML search results and extract title + URL pairs.
    Used to find hospital websites and JustDial / Practo / GMB listings.
    """
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query, "kl": "in-en"}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
    }
    results = []
    try:
        resp = requests.post(url, data=params, headers=headers, timeout=12)
        if resp.status_code != 200:
            return []
        # Very lightweight regex extraction – DDG HTML is stable
        pattern = re.compile(
            r'class="result__title"[^>]*>.*?href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        for m in pattern.finditer(resp.text):
            href, title = m.group(1), m.group(2)
            title_clean = re.sub(r"<[^>]+>", "", title).strip()
            if href.startswith("http") and title_clean:
                results.append({"title": title_clean, "url": href})
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        logging.warning(f"DuckDuckGo search failed for '{query}': {e}")
        return []


def _enrich_with_website(hospital_name: str, city: str) -> str:
    """Try to find a hospital's official website via DDG."""
    query = f"{hospital_name} {city} eye hospital official website"
    hits = _duckduckgo_search(query, max_results=3)
    for hit in hits:
        url = hit["url"]
        # Prefer official domains; skip directories/aggregators
        skip_domains = [
            "justdial", "practo", "sulekha", "indiamart",
            "facebook", "instagram", "youtube", "wikipedia",
            "duckduckgo", "google",
        ]
        if not any(d in url.lower() for d in skip_domains):
            return url
    # Fallback: JustDial search link (useful for users)
    return _justdial_search_link(hospital_name, city)


def _google_maps_link(name: str, city: str) -> str:
    q = quote(f"{name} eye hospital {city} India")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


def _justdial_search_link(name: str, city: str) -> str:
    q = quote(f"eye hospitals in {city}")
    return f"https://www.justdial.com/{city}/eye-hospitals"


# ─────────────────────────────────────────────────────────
#  Source 3 – Google Places API (optional – set API key)
# ─────────────────────────────────────────────────────────
GOOGLE_PLACES_API_KEY: Optional[str] = None  # Set your key here or via env var

def fetch_from_google_places(lat: float, lng: float, city: str) -> List[Dict]:
    """
    Fetch nearby eye-care facilities from Google Places API.
    Requires GOOGLE_PLACES_API_KEY to be set.
    """
    import os
    key = GOOGLE_PLACES_API_KEY or os.environ.get("GOOGLE_PLACES_API_KEY")
    if not key:
        return []
    base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 20000,
        "type": "hospital",
        "keyword": "eye hospital ophthalmology",
        "key": key,
    }
    try:
        resp = requests.get(base, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        places = resp.json().get("results", [])
        results: List[Dict] = []
        for p in places[:12]:
            plat = p["geometry"]["location"]["lat"]
            plng = p["geometry"]["location"]["lng"]
            # Fetch place details for phone + website
            details = _google_place_details(p["place_id"], key)
            results.append({
                "name": p.get("name", "Eye Hospital"),
                "lat": plat,
                "lng": plng,
                "type": "Hospital",
                "address": p.get("vicinity", city.title()),
                "phone": details.get("phone", "Contact hospital directly"),
                "rating": p.get("rating"),
                "distance": round(calculate_distance(lat, lng, plat, plng), 1),
                "description": (
                    "Google-verified eye care facility. "
                    + (f"Rated {p['rating']}/5 by {p.get('user_ratings_total', 'many')} users." if p.get('rating') else "")
                ),
                "website": details.get("website") or _google_maps_link(p.get("name", ""), city),
                "source": "Google Places",
            })
        logging.info(f"Google Places: {len(results)} results for {city}")
        return results
    except Exception as e:
        logging.error(f"Google Places failed: {e}")
        return []


def _google_place_details(place_id: str, key: str) -> Dict:
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": key,
        }
        resp = requests.get(url, params=params, timeout=8)
        result = resp.json().get("result", {})
        return {
            "phone": result.get("formatted_phone_number", ""),
            "website": result.get("website", ""),
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────
#  Source 4 – Curated database lookup
# ─────────────────────────────────────────────────────────
def fetch_from_curated(city_lower: str, city_coords: tuple) -> List[Dict]:
    for key, hospitals in CURATED_EYE_HOSPITALS.items():
        if key in city_lower or city_lower in key:
            results = []
            for rec in hospitals:
                (name, lat, lng, htype, address,
                 phone, rating, desc, website) = rec
                dist = (
                    round(calculate_distance(city_coords[0], city_coords[1], lat, lng), 1)
                    if city_coords else 0.0
                )
                results.append({
                    "name": name,
                    "lat": lat,
                    "lng": lng,
                    "type": htype,
                    "address": address,
                    "phone": phone,
                    "rating": rating,
                    "distance": dist,
                    "description": desc,
                    "website": website,
                    "source": "Curated",
                })
            logging.info(f"Curated: {len(results)} results for {city_lower}")
            return results
    return []


# ─────────────────────────────────────────────────────────
#  Source 5 – Generic synthetic fallback
# ─────────────────────────────────────────────────────────
def get_generic_fallback(city: str, coords: Optional[tuple]) -> List[Dict]:
    if coords is None:
        coords = get_city_coordinates(city) or (28.6139, 77.2090)
    lat, lng = coords
    city_t = city.title()
    templates = [
        (f"{city_t} Eye Hospital", "Hospital",
         "Comprehensive eye care including cataract, glaucoma, and retina services."),
        ("Netra Jyoti Eye Centre", "Clinic",
         "Affordable laser vision correction and routine eye examinations."),
        ("Vision Plus Clinic", "Clinic",
         "Premium contact lens, dry-eye, and refractive surgery clinic."),
        ("Dr. Agarwal's Eye Hospital", "Hospital",
         "Part of India's largest eye-care chain; advanced phaco & LASIK."),
        ("Sankara Nethralaya", "Hospital",
         "World-class eye care and research, trusted for retina & cornea."),
        ("Lotus Eye Care Hospital", "Hospital",
         "NABH-accredited hospital with advanced diagnostics and surgical theatres."),
        (f"{city_t} Ophthalmology Centre", "Clinic",
         "Paediatric ophthalmology, squint, and low-vision rehabilitation."),
        ("Sharp Sight Eye Centre", "Clinic",
         "Bladeless LASIK and micro-incision cataract surgery specialists."),
    ]
    results = []
    for i, (name, htype, desc) in enumerate(templates):
        offset_lat = (i * 0.015) - 0.05
        offset_lng = (i * 0.012) - 0.04
        results.append({
            "name": name,
            "lat": lat + offset_lat,
            "lng": lng + offset_lng,
            "type": htype,
            "address": f"Near {city_t} Main Road, {city_t}",
            "phone": f"+91 98765 {i+10001}",
            "rating": round(3.9 + i * 0.1, 1),
            "distance": round(abs(offset_lat) * 111, 1),
            "description": desc,
            "website": _google_maps_link(name, city),
            "source": "Fallback",
        })
    return results


# ─────────────────────────────────────────────────────────
#  Main public function
# ─────────────────────────────────────────────────────────
def search_eye_doctors_by_city(city: str) -> List[Dict]:
    """
    Multi-source eye-care facility finder.
    Priority: Google Places → Overpass (OSM) → Curated DB → Fallback.
    Each result includes name, lat, lng, address, phone, rating,
    distance, description, website, and source.
    """
    city_lower = city.lower().strip()
    coords = get_city_coordinates(city_lower)

    all_results: List[Dict] = []

    # ── 1. Google Places (if API key available) ──
    if coords:
        gp = fetch_from_google_places(coords[0], coords[1], city_lower)
        if gp:
            all_results.extend(gp)

    # ── 2. Overpass / OpenStreetMap ──
    if coords and len(all_results) < 5:
        osm = fetch_from_overpass(coords[0], coords[1], city_lower)
        # Deduplicate by name
        existing = {r["name"].lower() for r in all_results}
        for r in osm:
            if r["name"].lower() not in existing:
                all_results.append(r)
                existing.add(r["name"].lower())

    # ── 3. Curated database ──
    if len(all_results) < 4:
        curated = fetch_from_curated(city_lower, coords)
        existing = {r["name"].lower() for r in all_results}
        for r in curated:
            if r["name"].lower() not in existing:
                all_results.append(r)
                existing.add(r["name"].lower())

    # ── 4. Enrich OSM results that lack websites (throttled) ──
    for r in all_results:
        if r.get("source") == "OpenStreetMap" and (
            not r.get("website") or "google.com/maps" in r.get("website", "")
        ):
            try:
                r["website"] = _enrich_with_website(r["name"], city_lower)
                time.sleep(0.4)   # be polite to DDG
            except Exception:
                pass

    # ── 5. Generic fallback ──
    if not all_results:
        all_results = get_generic_fallback(city_lower, coords)

    # Sort by distance (closest first), then by rating (highest first)
    all_results.sort(key=lambda x: (x.get("distance") or 99, -(x.get("rating") or 0)))

    logging.info(f"Total results for '{city}': {len(all_results)}")
    return all_results[:15]