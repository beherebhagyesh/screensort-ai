import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('packet_data.json', encoding='utf-8'))

# ── 1. FIX WEIGHTS ───────────────────────────────────────────────────────────
fixes = {
    1: 25,   # Biryani Stick
    2: 25,   # Pasta
    3: 15,   # Wonder Car
    18: 20,  # Amaize
}
for d in data:
    if d['packet_num'] in fixes:
        d['net_weight_g'] = fixes[d['packet_num']]
        print(f"Fixed P{d['packet_num']} weight -> {fixes[d['packet_num']]}g")

# ── 2. FIX P1 product name (it was "Stick / Pasta" — actually Biryani Stick) ─
for d in data:
    if d['packet_num'] == 1:
        d['product_name_english'] = 'Biryani Stick Snack Pellets'
        d['product_name_local'] = 'बिर्याणी स्टिक'
        d['variant_flavor'] = 'Chatpata Masala'
        d['pack_primary_color'] = 'Yellow'
        d['pack_secondary_color'] = 'Orange'

# ── 3. INSERT LADKI BAHIN (4th Surya product, between P2 and P3) ─────────────
# Get Surya template from P2 (same manufacturer, same nutrition)
p2 = next(d for d in data if d['packet_num'] == 2)

ladki_bahin = copy.deepcopy(p2)
ladki_bahin.update({
    'packet_num': 2.5,           # temp — will renumber below
    'product_name_english': 'Ladki Bahin',
    'product_name_local': 'लाडकी बहीण',
    'tagline_or_slogan': 'Inspired by the Maharashtra Ladki Bahin Yojana scheme',
    'variant_flavor': 'Masala',
    'product_type': 'Papad / Snack Pellet',
    'net_weight_g': 15,
    'mrp_inr': 5.0,
    'pack_primary_color': 'Hot Pink / Magenta',
    'pack_secondary_color': 'Purple',
    'pack_accent_colors': 'Yellow, Green',
    'front_imagery': 'Cartoon girl character, coins, gift items, Free Gift Inside sticker',
    'design_style': 'Vibrant/Playful, scheme-branded',
    'font_style': 'Bold Devanagari, Yellow on Pink',
    'pack_format': 'Pillow bag',
    'pack_appeal_score': 7,
    'shelf_visibility_score': 8,
    'target_audience': 'Women, girls, families — scheme brand recognition',
    'usp_differentiator': 'Leverages Maharashtra govt Ladki Bahin Yojana name — high recall with women shoppers. Free gift inside.',
    'claims_on_pack': 'Free Gift Inside',
    'competitive_notes': 'Brand piggybacks on popular Maharashtra govt welfare scheme for women — very clever regional positioning. Likely strong pull with women customers.',
    'image_files': ['IMG20260312213024.jpg', 'IMG20260312213033.jpg',
                    'IMG20260312213059.jpg', 'IMG20260312213106.jpg'],
})
# Remove pasta-specific fields
ladki_bahin['batch_no'] = None
ladki_bahin['date_of_mfg'] = None

print(f"Inserted Ladki Bahin (15g)")

# ── 4. INSERT into list between P2 and P3 ────────────────────────────────────
new_data = []
for d in data:
    new_data.append(d)
    if d['packet_num'] == 2:
        new_data.append(ladki_bahin)

# ── 5. RENUMBER sequentially ─────────────────────────────────────────────────
for i, d in enumerate(new_data, 1):
    d['packet_num'] = i

print(f"Total packets after patch: {len(new_data)}")

json.dump(new_data, open('packet_data.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print("Saved packet_data.json")
