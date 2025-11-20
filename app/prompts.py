from __future__ import annotations

import json
from typing import Any, Dict, List


PRODUCTS = '''PRODUCT DATABASE

| ProductName | PriceTier | ApproxCost | AvgRating | KeyReviewSnippet | ProductCategory | TargetProblem | TargetIntensity | TargetUserProfile | KeyActiveIngredient |
|---|---|---|---|---|---|---|---|---|---|
| Cetaphil Gentle Skin Cleanser | Budget | $13.99 | 4.6/5 | "best face wash for all skin types, according to dermatologists" [1] | Cleanser | Dryness | N/A | Sensitive\_Skin, Dry\_Skin | N/A |
| La Roche-Posay Toleriane Hydrating Gentle Cleanser | Mid-Range | $15.99 | 4.6/5 | "gentle, effective cleansers... great for maintaining the skin's natural barrier" [2, 3] | Cleanser | Dryness | N/A | Sensitive\_Skin, Dry\_Skin | Ceramide-3 |
| iS Clinical Cleansing Complex | Premium | $48.00 | 4.7/5 | "Best For Sensitive Skin" | Cleanser | Acne | N/A | Sensitive\_Skin, Acne\_Prone | Salicylic Acid (trace) |
| CeraVe Acne Control Cleanser | Budget | $14.99 | 4.6/5 | "Formulated to clear acne, reduce blackheads" [4, 5, 6] | Cleanser | Acne, Oily | Mild / Moderate | Oily\_Skin, Acne\_Prone | Salicylic Acid 2% |
| La Roche-Posay Effaclar Medicated Gel Cleanser | Mid-Range | $16.99 | 4.6/5 | "uses salicylic acid and lipo-hydroxy acid to remove gunk and dead skin" | Cleanser | Acne, Oily | Mild / Moderate | Oily\_Skin, Acne\_Prone | Salicylic Acid 2% |
| CeraVe Foaming Facial Cleanser | Budget | $15.99 | 4.7/5 | "Best Overall" [7, 8], "for Normal to Oily Skin" [6] | Cleanser | Oily | N/A | Oily\_Skin, Normal\_Skin | Niacinamide |
| The Inkey List Bio-Active Ceramide Repairing Moisturizer | Budget | $22.00 | 4.5/5 | "Best moisturizer with ceramides" [4, 9, 10, 5] | Moisturizer | Dryness | Mild / Moderate | Dry\_Skin, Sensitive\_Skin | Ceramides |
| First Aid Beauty Ultra Repair Cream | Mid-Range | $38.00 | 4.6/5 | "instantly relieves dry, distressed skin and eczema" | Moisturizer | Dryness, Eczema | Mild / Moderate / Severe | Dry\_Skin, Sensitive\_Skin | Colloidal Oatmeal |
| SkinCeuticals Triple Lipid Restore 2:4:2 | Premium | $155.00 | 4.7/5 | "Best Moisturizer for Sensitive, Oily Skin" [11, 12], "restores the skin's protective barrier" [4, 9] | Moisturizer | Dryness, Wrinkles | Mild / Moderate / Severe | Dry\_Skin, Sensitive\_Skin, Mature\_Skin | Ceramides, Cholesterol |
| Neutrogena Hydro Boost Water Gel | Budget | $19.99 | 4.5/5 | "Best budget moisturiser for oily skin" [13, 14], "Best Drugstore Moisturizer" [15, 16] | Moisturizer | Oily, Dehydrated | Mild / Moderate | Oily\_Skin, Acne\_Prone | Hyaluronic Acid |
| La Roche-Posay Toleriane Double Repair (Matte) | Mid-Range | $20.99 | 4.5/5 | "Best Overall Moisturizer... effectively hydrates... without a greasy residue" [15, 16] | Moisturizer | Oily, Dehydrated | Mild / Moderate | Oily\_Skin, Normal\_Skin | Niacinamide |
| Kiehl's Ultra Facial Cream | Mid-Range | $39.00 | 4.6/5 | "Best Moisturizer for Combination Skin" [17, 15, 16] | Moisturizer | Dryness | Mild / Moderate | Normal\_Skin, Combination\_Skin | Squalane |
| CeraVe Hydrating Mineral Tinted Sunscreen SPF 30 | Budget | $13.99 | 4.3/5 | "CeraVe Hydrating Mineral Face Sunscreen SPF 30 - Tinted" [18, 19, 20, 21] | Sunscreen | Hyperpigmentation, Redness | N/A | Sensitive\_Skin, Dry\_Skin | Zinc Oxide, Iron Oxides |
| EltaMD UV Clear Tinted SPF 46 | Mid-Range | $45.00 | 4.5/5 | "formulated to calm and protect skin prone to acne and rosacea" [22, 23, 19, 24, 25, 21, 26, 27, 28, 29, 30] | Sunscreen | Hyperpigmentation, Redness, Acne | N/A | Sensitive\_Skin, Acne\_Prone, Rosacea | Zinc Oxide, Niacinamide |
| Isdin Eryfotona Actinica Mineral SPF 50+ | Premium | $73.00 | 4.6/5 | "Best Fast Absorbing" [22, 26], "Ultralight Tinted Mineral Sunscreen" [19, 21] | Sunscreen | Hyperpigmentation, Wrinkles | N/A | Sensitive\_Skin, Mature\_Skin | Zinc Oxide |
| Supergoop\! Unseen Sunscreen SPF 50 | Mid-Range | $38.00 | 4.6/5 | "silky-smooth, almost primer-like finish... gel-like formula goes on clear" [31, 32, 33] | Sunscreen | N/A | N/A | Normal\_Skin, Oily\_Skin | Chemical Filters |
| SkinCeuticals Physical Fusion UV Defense SPF 50 | Premium | $45.00 | 4.5/5 | "premium-feeling all-mineral sunscreen" [34, 33], "Tinted" [19, 21] | Sunscreen | Hyperpigmentation | N/A | Sensitive\_Skin, All\_Profiles | Zinc Oxide, Titanium Dioxide |
| EltaMD UV Clear Tinted SPF 46 (for Moles / Nevi) | Mid-Range | $45.00 | 4.5/5 | "Refer to Dermatologist for monitoring.[9] Daily photoprotection is essential to minimize risk." [35, 36] | Sunscreen | Moles / Nevi | N/A (Referral) | All\_Profiles, High\_Risk | Zinc Oxide, Iron Oxides |
| The Ordinary Salicylic Acid 2% Solution | Budget | $6.50 | 4.4/5 | "Best Budget" [32, 37, 38, 39] | Serum | Acne, Oily | Mild / Moderate | Oily\_Skin, Resilient\_Skin | Salicylic Acid 2% |
| Paula's Choice 2% BHA Liquid Exfoliant | Mid-Range | $35.00 | 4.6/5 | "liquid gold... shrunk the appearance of my pores" | Serum | Acne, Oily | Mild / Moderate | Oily\_Skin, Resilient\_Skin | Salicylic Acid 2% |
| Differin Adapalene Gel 0.1% | Budget | $14.99 | 4.5/5 | "Clears acne with the power of Rx... Restores skin tone" [40, 41, 42, 43, 7, 44, 45, 12, 46, 47, 48, 49, 50, 51, 52, 53] | Serum | Acne, Hyperpigmentation | Mild / Moderate | Oily\_Skin, Resilient\_Skin, Acne\_Prone | Adapalene 0.1% |
| The Ordinary Niacinamide 10% + Zinc 1% | Budget | $6.00 | 4.2/5 | "reduce the signs of congestion and visible sebum activity" [54, 2, 55, 27, 56, 57, 58, 59, 60, 29, 6, 61] | Serum | Redness/PIE, Oily | Mild / Moderate | Sensitive\_Skin, Oily\_Skin | Niacinamide 10% |
| Naturium Azelaic Topical Acid 10% | Mid-Range | $20.00 | 4.4/5 | "incorporates niacinamide and vitamin C... reducing redness" | Serum | Redness/PIE, Acne, Hyperpigmentation | Mild / Moderate | Sensitive\_Skin, Rosacea | Azelaic Acid 10% |
| Paula's Choice 10% Azelaic Acid Booster | Premium | $39.00 | 4.5/5 | "Best azelaic acid booster" [62, 14, 48, 63, 64], "shoppers love the... multitasking properties" [65] | Serum | Redness/PIE, Acne, Hyperpigmentation | Mild / Moderate | Sensitive\_Skin, Rosacea | Azelaic Acid 10% |
| CeraVe Resurfacing Retinol Serum | Budget | $21.99 | 4.6/5 | "Best Retinol Cream For Acne" [18, 23, 17, 66, 67, 59, 68] | Serum | Wrinkles, Hyperpigmentation, PIE | Mild (Beginner) | Beginner\_Retinol, Resilient\_Skin | Retinol |
| La Roche-Posay Retinol B3 Serum | Mid-Range | $44.99 | 4.5/5 | "Reduces Fine Lines... Goes on smooth without a tacky feeling" | Serum | Wrinkles, Hyperpigmentation | Mild / Moderate (Beginner) | Beginner\_Retinol, Sensitive\_Skin | Retinol (Pure + Gradual) |
| Kiehl's Retinol Skin-Renewing Daily Micro-Dose Serum | Premium | $65.00 | 4.6/5 | "Best for sensitive skin" , "Best for Dry Skin" [69, 70] | Serum | Wrinkles | Mild / Moderate (Beginner) | Beginner\_Retinol, Sensitive\_Skin | Retinol 0.1% |
| Paula's Choice Clinical 1% Retinol Treatment | Mid-Range | $61.75 | 4.5/5 | "Best Retinol Cream Overall" [23, 68], "Best for wrinkles" | Serum | Wrinkles, Hyperpigmentation | Moderate (Experienced) | Experienced\_Retinol, Resilient\_Skin | Retinol 1% |
| SkinCeuticals Retinol 1.0 | Premium | $90.00 | 4.4/5 | "Best Retinol Night Cream" [23, 71, 68] | Serum | Wrinkles, Hyperpigmentation | Moderate / Severe (Experienced) | Experienced\_Retinol, Resilient\_Skin | Retinol 1.0% |
| Naturium Vitamin C Complex Serum | Budget | $21.00 | 4.5/5 | "Best Value Vitamin C Serum" [72, 1, 73], "affordable" | Serum | Hyperpigmentation, Dullness, Wrinkles | Mild | Resilient\_Skin, All\_Profiles | L-Ascorbic Acid |
| The INKEY List Tranexamic Acid Serum | Budget | $15.99 | 4.3/5 | "budget-friendly... popular for beginners" [74, 58] | Serum | Hyperpigmentation, Melasma | Mild / Moderate | Sensitive\_Skin, PIH\_Prone | Tranexamic Acid 2% |
| SkinCeuticals C E Ferulic | Premium | $185.00 | 4.5/5 | "firms skin and brightens... see the results\!" | Serum | Hyperpigmentation, Wrinkles, Freckles | Mild / Moderate | Resilient\_Skin, Dry\_Skin, Mature\_Skin | L-Ascorbic Acid 15% |
| The Ordinary Hyaluronic Acid 2% + B5 | Budget | $9.90 | 4.5/5 | "Best Budget" [13, 15, 75], "Best for Beginners" [75, 76] | Serum | Dryness, Dehydrated | Mild / Moderate | All\_Profiles | Hyaluronic Acid |
| CeraVe Hydrating Hyaluronic Acid Serum | Mid-Range | $19.99 | 4.4/5 | "Best Drugstore" [75, 76], "help support the skin's barrier" | Serum | Dryness, Dehydrated | Mild / Moderate | All\_Profiles | Hyaluronic Acid, Ceramides |
| The Inkey List Caffeine Eye Cream | Budget | $7.95 | 4.1/5 | "Best budget eye cream" | Eye Cream | Puffiness | Mild / Moderate | All\_Profiles | Caffeine |
| CeraVe Eye Repair Cream | Mid-Range | $14.00 | 4.3/5 | "Best Drugstore Eye Cream" | Eye Cream | Puffiness, Dark Circles | Mild / Moderate | All\_Profiles | Niacinamide, Ceramides |
| Charlotte Tilbury Cryo-Recovery Eye Serum | Premium | $37.60 | 4.0/5 | "Best eye serum for puffiness" | Eye Cream | Puffiness | Mild / Moderate | All\_Profiles | Caffeine |
| Neutrogena Rapid Wrinkle Repair Eye Cream | Budget | $21.00 | 4.4/5 | "Best Drugstore" , "Hyaluronic acid plumps" [77] | Eye Cream | Wrinkles | Mild / Moderate | Resilient\_Skin | Retinol |
| RoC Retinol Correxion Eye Cream | Budget | $21.99 | 4.6/5 | "Visibly Reduces: Dark Circles, Puffiness, Fine Lines" | Eye Cream | Wrinkles, Dark Circles | Mild / Moderate | Resilient\_Skin | Retinol |
| La Roche-Posay Redermic R Retinol Eye Cream | Mid-Range | $49.99 | 4.4/5 | "Best Retinol Eye Cream Overall" , "Gentle on skin, despite that it contains retinol" | Eye Cream | Wrinkles | Mild / Moderate | Resilient\_Skin, Sensitive\_Skin | Retinol |
| Medik8 Crystal Retinal Ceramide Eye | Premium | $42.00 | 4.5/5 | "Best eye cream overall" | Eye Cream | Wrinkles, Dark Circles | Mild / Moderate | All\_Profiles | Retinaldehyde |
| CeraVe Renewing Vitamin C Eye Cream | Budget | $15.00 | 4.3/5 | "Eye cream with vitamin C" [31, 78, 71] | Eye Cream | Dark Circles (Pigment) | Mild / Moderate | All\_Profiles | Vitamin C |
| Summer Fridays Light Aura Vitamin C + Peptide Eye Cream | Mid-Range | $44.00 | 4.3/5 | "brightened, smoothed, and hydrated under-eyes" [79, 70] | Eye Cream | Dark Circles (Pigment) | Mild / Moderate | All\_Profiles | Vitamin C, Peptides |
| Tatcha The Brightening Eye Cream | Premium | $64.00 | 4.3/5 | "Best eye cream for dark circles" , "truly helps brighten the skin" | Eye Cream | Dark Circles (Pigment) | Mild / Moderate | All\_Profiles | Vitamin C |
'''
ROUTINE_SYSTEM_PROMPT = """You are a skincare planner. Build safe, evidence-aligned AM/Midday/PM routines.
NEVER invent products. Use only items from the provided Product DB.
Return VALID JSON only. Follow the output schema exactly."""


ROUTINE_USER_PROMPT = """## INPUTS
### A) Skin Analysis JSON
{SKIN_ANALYSIS_JSON}

### B) Intake JSON (any field may be missing or "unsure")
{FORM_JSON}

### C) Product DB (FULL; only use these items)
{PRODUCT_TABLE}

## RULES (APPLY SILENTLY)
1) Sequencing (barrier-first):
   - AM: Cleanser → (optional single Active) → Moisturizer → Sunscreen (mandatory).
   - Midday (optional): quick refresh like SPF reapply/oil control/hydration if relevant.
   - PM: Cleanser → (optional single Active) → Moisturizer.
2) Safety overrides:
   - pregnancy=yes/prefer_not_to_say/unsure → avoid retinoids (retinol/adapalene) and hydroquinone; prefer azelaic/vitamin C/tranexamic when treating pigment.
   - rx_topical=yes → omit all Active steps (support-only).
   - If analysis suggests severe red flags (e.g., severe acne/rosacea, suspicious moles) → no OTC actives; surface a referral warning and choose gentle cleanser/moisturizer/sunscreen only.
3) Sensitivity & Fitzpatrick:
   - sensitivity=high → prefer "fragrance_free"/"sensitive_ok"; avoid strong acids/retinoids; mineral sunscreen is preferred.
   - fitzpatrick=III–IV or V–VI or notable pigmentation → consider gentle pigment actives (azelaic/tranexamic/vitamin C) and prefer tinted/mineral SPF when available.
4) Priorities from analysis:
   - Infer top 1–2 concerns by severity (pigmentation, acne, oily_shine, dryness, redness, wrinkles).
   - Choose ONE compatible Active path overall (AM or PM). Do not stack multiple potent actives in both AM and PM.
5) Product selection policy:
   - Use only items from Product DB. Prefer budget and mid; include premium only if helpful.
   - Respect allergies if provided (e.g., avoid non–fragrance-free when fragrance allergy is declared and the tag exists).
   - Prefer "non_comedogenic" in oily/acne contexts; "mineral" and/or "tinted" for pigment/sensitive contexts.
6) Instruction clarity:
   - For each step: short "how", "frequency", "timing". Include SPF reminders (15 min before sun; reapply every 2 hours outdoors).
7) Output:
   - Return a single JSON object matching the schema below. If a step is unsafe/disabled, simply omit it. If midday is not relevant, omit "midday".

---
Return JSON only.
"""


product_links = {
    "Cetaphil Gentle Skin Cleanser": "https://www.cetaphil.in/products/cleansers/gentle-skin-cleanser/8906005274105.html",
    "La Roche-Posay Toleriane Hydrating Gentle Cleanser": "https://www.laroche-posay.us/our-products/face/face-wash/toleriane-hydrating-gentle-facial-cleanser-tolerianehydratinggentlefacialcleanser.html",
    "iS Clinical Cleansing Complex": "https://www.isclinical.com/products/cleansing-complex",
    "CeraVe Acne Control Cleanser": "https://www.cerave.com/skincare/cleansers/acne-salicylic-acid-cleanser",
    "La Roche-Posay Effaclar Medicated Gel Cleanser": "https://www.laroche-posay.us/our-products/face/face-wash/effaclar-medicated-gel-cleanser-3337872411083.html",  # (can also use Target: https://www.target.com/p/la-roche-posay-effaclar-acne-face-cleanser-medicated-gel-face-cleanser-with-salicylic-acid-for-acne-prone-skin-6-76-fl-oz/-/A-76552803)
    "CeraVe Foaming Facial Cleanser": "https://www.cerave.com/skincare/cleansers/foaming-facial-cleanser",
    "The Inkey List Bio-Active Ceramide Repairing Moisturizer": "https://eu.theinkeylist.com/products/bio-active-ceramide-moisturizer",
    "First Aid Beauty Ultra Repair Cream": "https://www.firstaidbeauty.com/products/ultra-repair-cream-intense-hydration",
    "SkinCeuticals Triple Lipid Restore 2:4:2": "https://www.dermstore.com/skinceuticals-triple-lipid-restore-2-4-2/11289199.html",
    "Neutrogena Hydro Boost Water Gel": "https://www.neutrogena.com/products/skincare/neutrogena-hydro-boost-water-gel-with-hyaluronic-acid/6811047.html",
    "La Roche-Posay Toleriane Double Repair (Matte)": "https://www.laroche-posay.us/our-products/face/face-moisturizer/toleriane-double-repair-matte-face-moisturizer-spf-30-for-oily-skin-3337875782999.html",
    "Kiehl's Ultra Facial Cream": "https://go.shopmy.us/p-7740940",
    "CeraVe Hydrating Mineral Tinted Sunscreen SPF 30": "https://go.shopmy.us/p-20673810",
    "EltaMD UV Clear Tinted SPF 46": "https://go.shopmy.us/p-20673792",
    "Isdin Eryfotona Actinica Mineral SPF 50+": "https://go.shopmy.us/p-20673789",
    "Supergoop! Unseen Sunscreen SPF 50": "https://supergoop.com/products/unseen-sunscreen-spf-50",
    "SkinCeuticals Physical Fusion UV Defense SPF 50": "https://go.shopmy.us/p-20673803",
    "EltaMD UV Clear Tinted SPF 46 (for Moles / Nevi)": "https://go.shopmy.us/p-20673792",
    "The Ordinary Salicylic Acid 2% Solution": "https://www.sephora.in/product/the-ordinary-salicylic-acid-2-solution-v-30ml",
    "Paula's Choice 2% BHA Liquid Exfoliant": "https://go.shopmy.us/p-1210792",
    "Differin Adapalene Gel 0.1%": "https://www.target.com/p/differin-acne-retinoid-treatment-gel-adapalene-0-1-15g/-/A-51346324",
    "The Ordinary Niacinamide 10% + Zinc 1%": "https://www.amazon.com/dp/B0BSD1M53T",
    "Naturium Azelaic Topical Acid 10%": "https://www.naturium.com/products/azelaic-topical-acid-10",
    "Paula's Choice 10% Azelaic Acid Booster": "https://go.shopmy.us/p-7432177",
    "CeraVe Resurfacing Retinol Serum": "https://myshlf.us/p-70344",
    "La Roche-Posay Retinol B3 Serum": "https://www.laroche-posay.us/our-products/face/face-serum/retinol-b3-pure-retinol-serum-3337875694469.html",
    "Kiehl's Retinol Skin-Renewing Daily Micro-Dose Serum": "https://www.kiehls.com/skincare/face-serums/micro-dose-anti-aging-retinol-serum-with-ceramides-and-peptide/WW0154KIE.html",
    "Paula's Choice Clinical 1% Retinol Treatment": "https://www.paulaschoice.com/clinical-1pct-retinol-treatment/801.html",
    "SkinCeuticals Retinol 1.0": "https://www.skinceuticals.com/skincare/retinol-creams/retinol-1.0/S70.html",
    "Naturium Vitamin C Complex Serum": "https://go.shopmy.us/p-52901",
    "The INKEY List Tranexamic Acid Serum": "https://eu.theinkeylist.com/products/tranexamic-acid-serum",
    "SkinCeuticals C E Ferulic": "https://www.skinceuticals.com/c-e-ferulic-with-15-l-ascorbic-acid/S17.html",
    "The Ordinary Hyaluronic Acid 2% + B5": "https://theordinary.com/en-in/hyaluronic-acid-2-b5-serum-with-ceramides-100637.html",
    "CeraVe Hydrating Hyaluronic Acid Serum": "https://www.cerave.com/skincare/facial-serums/hydrating-hyaluronic-acid-serum",
    "The Inkey List Caffeine Eye Cream": "https://uk.theinkeylist.com/products/caffeine-eye-cream",
    "CeraVe Eye Repair Cream": "https://www.cerave.com/skincare/moisturizers/eye-repair-cream",
    "Charlotte Tilbury Cryo-Recovery Eye Serum": "https://www.johnlewis.com/charlotte-tilbury-cryo-recovery-eye-serum-15ml/p5723788",
    "Neutrogena Rapid Wrinkle Repair Eye Cream": "https://www.neutrogena.com/products/skincare/neutrogena-rapid-wrinkle-repair-retinol-eye-cream/6802123",
    "RoC Retinol Correxion Eye Cream": "https://www.rocskincare.com/products/retinol-correxion-line-smoothing-eye-cream",
    "La Roche-Posay Redermic R Retinol Eye Cream": "https://www.dermstore.com/la-roche-posay-redermic-r-eyes-retinol-eye-cream/11130283.html",
    "Medik8 Crystal Retinal Ceramide Eye": "https://www.medik8.com/products/crystal-retinal-ceramide-eye-3",
    "CeraVe Renewing Vitamin C Eye Cream": "https://www.cerave.com/skincare/moisturizers/facial-moisturizers/skin-renewing-vitamin-c-eye-cream",
    "Summer Fridays Light Aura Vitamin C + Peptide Eye Cream": "https://summerfridays.com/products/light-aura-vitamin-c-peptide-eye-cream",
    "Tatcha The Brightening Eye Cream": "https://www.spacenk.com/uk/skincare/eye-care/eye-creams/the-brightening-eye-cream-MUK200032906.html"
}



def _json_block(payload: Dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, ensure_ascii=False, indent=2)


def build_routine_prompt_messages(analysis: Dict[str, Any], intake: Dict[str, Any]) -> List[Dict[str, str]]:
    user_prompt = (
        ROUTINE_USER_PROMPT
        .replace("{SKIN_ANALYSIS_JSON}", _json_block(analysis))
        .replace("{FORM_JSON}", _json_block(intake))
        .replace("{PRODUCT_TABLE}", PRODUCTS)
    )
    return [
        {"role": "system", "content": ROUTINE_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
