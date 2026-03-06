import stripe
import httpx
import asyncio
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

stripe.api_key        = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID       = "price_1T7KE2KFJRX1avMl9z1D8leJ"
SUPABASE_URL          = "https://znzsttdyeigkfwbvocie.supabase.co"
SUPABASE_SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY")

app = FastAPI(title="ARBION OS", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── CONFIGURATION ──────────────────────────────────────────────────────────
TIERS = ["T4", "T5", "T6", "T7", "T8"]

BASE_ITEMS = [
    "BAG", "CAPE",
    "MOUNT_HORSE", "MOUNT_OX", "MOUNT_MULE",
    "MAIN_ARCANESTAFF", "2H_ARCANESTAFF",
    "MAIN_CURSESTAFF", "2H_CURSESTAFF",
    "MAIN_FIRESTAFF", "2H_FIRESTAFF",
    "MAIN_FROSTSTAFF", "2H_FROSTSTAFF",
    "MAIN_HOLYSTAFF", "2H_HOLYSTAFF",
    "MAIN_NATURESTAFF", "2H_NATURESTAFF",
    "MAIN_SWORD", "2H_CLAYMORE",
    "MAIN_AXE", "2H_AXE",
    "MAIN_HAMMER", "2H_POLEHAMMER",
    "MAIN_SPEAR", "2H_HALBERD",
    "MAIN_BOW", "2H_BOW",
    "MAIN_CROSSBOW", "2H_CROSSBOW",
    "MAIN_DAGGER", "2H_DAGGERPAIR",
    "2H_QUARTERSTAFF", "2H_CLAWSSPELL",
    "OFF_SHIELD", "OFF_TORCH",
    "ARMOR_PLATE_SET1", "ARMOR_PLATE_SET2", "ARMOR_PLATE_SET3",
    "ARMOR_LEATHER_SET1", "ARMOR_LEATHER_SET2", "ARMOR_LEATHER_SET3",
    "ARMOR_CLOTH_SET1", "ARMOR_CLOTH_SET2", "ARMOR_CLOTH_SET3",
    "HEAD_PLATE_SET1", "HEAD_PLATE_SET2", "HEAD_PLATE_SET3",
    "HEAD_LEATHER_SET1", "HEAD_LEATHER_SET2", "HEAD_LEATHER_SET3",
    "HEAD_CLOTH_SET1", "HEAD_CLOTH_SET2", "HEAD_CLOTH_SET3",
    "SHOES_PLATE_SET1", "SHOES_PLATE_SET2", "SHOES_PLATE_SET3",
    "SHOES_LEATHER_SET1", "SHOES_LEATHER_SET2", "SHOES_LEATHER_SET3",
    "SHOES_CLOTH_SET1", "SHOES_CLOTH_SET2", "SHOES_CLOTH_SET3",
]

CITIES             = ["Martlock", "Lymhurst", "Fort Sterling", "Bridgewatch", "Thetford", "Caerleon"]
MARKET_TAX         = 0.06
MIN_PROFIT         = 1500
MAX_DEALS_PER_CITY = 30
CHUNK_SIZE         = 50


MIN_ITEM_COUNT     = 10   
LOOKBACK_DAYS      = 3   
MAX_PRICE_RATIO    = 2.5  

# ── NAME MAPPING ───────────────────────────────────────────────────────────
TIER_NAMES = {
    "T4": "Adept's", "T5": "Expert's",
    "T6": "Master's", "T7": "Grandmaster's", "T8": "Elder's"
}

BASE_NAMES = {
    "BAG": "Bag", "CAPE": "Cape",
    "MOUNT_HORSE": "Riding Horse", "MOUNT_OX": "Transport Ox", "MOUNT_MULE": "Mule",
    "MAIN_ARCANESTAFF": "Arcane Staff", "2H_ARCANESTAFF": "Great Arcane Staff",
    "MAIN_CURSESTAFF": "Cursed Staff", "2H_CURSESTAFF": "Great Cursed Staff",
    "MAIN_FIRESTAFF": "Fire Staff", "2H_FIRESTAFF": "Great Fire Staff",
    "MAIN_FROSTSTAFF": "Frost Staff", "2H_FROSTSTAFF": "Great Frost Staff",
    "MAIN_HOLYSTAFF": "Holy Staff", "2H_HOLYSTAFF": "Great Holy Staff",
    "MAIN_NATURESTAFF": "Nature Staff", "2H_NATURESTAFF": "Great Nature Staff",
    "MAIN_SWORD": "Sword", "2H_CLAYMORE": "Claymore",
    "MAIN_AXE": "Axe", "2H_AXE": "Great Axe",
    "MAIN_HAMMER": "Hammer", "2H_POLEHAMMER": "Polehammer",
    "MAIN_SPEAR": "Spear", "2H_HALBERD": "Halberd",
    "MAIN_BOW": "Bow", "2H_BOW": "Warbow",
    "MAIN_CROSSBOW": "Crossbow", "2H_CROSSBOW": "Heavy Crossbow",
    "MAIN_DAGGER": "Dagger", "2H_DAGGERPAIR": "Dagger Pair",
    "2H_QUARTERSTAFF": "Quarterstaff", "2H_CLAWSSPELL": "Claws",
    "OFF_SHIELD": "Shield", "OFF_TORCH": "Torch",
    "ARMOR_PLATE_SET1": "Soldier Armor", "ARMOR_PLATE_SET2": "Knight Armor", "ARMOR_PLATE_SET3": "Guardian Armor",
    "ARMOR_LEATHER_SET1": "Mercenary Jacket", "ARMOR_LEATHER_SET2": "Hunter Jacket", "ARMOR_LEATHER_SET3": "Assassin Jacket",
    "ARMOR_CLOTH_SET1": "Scholar Robe", "ARMOR_CLOTH_SET2": "Mage Robe", "ARMOR_CLOTH_SET3": "Cultist Robe",
    "HEAD_PLATE_SET1": "Soldier Helmet", "HEAD_PLATE_SET2": "Knight Helmet", "HEAD_PLATE_SET3": "Guardian Helmet",
    "HEAD_LEATHER_SET1": "Mercenary Hood", "HEAD_LEATHER_SET2": "Hunter Hood", "HEAD_LEATHER_SET3": "Assassin Hood",
    "HEAD_CLOTH_SET1": "Scholar Cowl", "HEAD_CLOTH_SET2": "Mage Cowl", "HEAD_CLOTH_SET3": "Cultist Cowl",
    "SHOES_PLATE_SET1": "Soldier Boots", "SHOES_PLATE_SET2": "Knight Boots", "SHOES_PLATE_SET3": "Guardian Boots",
    "SHOES_LEATHER_SET1": "Mercenary Shoes", "SHOES_LEATHER_SET2": "Hunter Shoes", "SHOES_LEATHER_SET3": "Assassin Shoes",
    "SHOES_CLOTH_SET1": "Scholar Sandals", "SHOES_CLOTH_SET2": "Mage Sandals", "SHOES_CLOTH_SET3": "Cultist Sandals",
}

ENCHANT_LABELS = {"": "", "@1": ".1", "@2": ".2", "@3": ".3"}


def get_human_name(item_id: str) -> str:
    parts = item_id.split("@")
    base_id = parts[0]
    enchant_suffix = f"@{parts[1]}" if len(parts) > 1 else ""
    tier = base_id[:2]
    base = base_id[3:]
    tier_prefix = TIER_NAMES.get(tier, tier)
    core_name = BASE_NAMES.get(base, base.replace("_", " ").title())
    enc_label = ENCHANT_LABELS.get(enchant_suffix, "")
    return f"{tier_prefix} {core_name}{enc_label}"


def generate_item_list() -> list[str]:
    items = []
    for tier in TIERS:
        for base in BASE_ITEMS:
            items.append(f"{tier}_{base}")
            if tier in ("T4", "T5", "T6", "T7", "T8"):
                items.append(f"{tier}_{base}@1")
            if tier in ("T5", "T6", "T7", "T8"):
                items.append(f"{tier}_{base}@2")
            if tier in ("T6", "T7", "T8"):
                items.append(f"{tier}_{base}@3")
    return items


ITEM_LIST = generate_item_list()
CITY_STR  = ",".join(CITIES)


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ── SMART PRICE CALCULATION ────────────────────────────────────────────────
def calculate_smart_price(history: list[dict]) -> float | None:
    """
    Υπολογίζει αξιόπιστη τιμή από το history:
    1. Φιλτράρει εγγραφές με item_count < MIN_ITEM_COUNT (αναξιόπιστες)
    2. Παίρνει τις τελευταίες LOOKBACK_DAYS μέρες
    3. Ελέγχει για spikes (τιμές > MAX_PRICE_RATIO * median)
    4. Επιστρέφει weighted average (βαρύτερες οι πιο πρόσφατες μέρες)
    """
    if not history:
        return None

    
    valid = [h for h in history if h.get("item_count", 0) >= MIN_ITEM_COUNT and h.get("avg_price", 0) > 0]
    if not valid:
        return None

    
    recent = valid[-LOOKBACK_DAYS:] if len(valid) >= LOOKBACK_DAYS else valid
    if not recent:
        return None

    prices = [h["avg_price"] for h in recent]

    sorted_prices = sorted(prices)
    mid = len(sorted_prices) // 2
    median = sorted_prices[mid] if len(sorted_prices) % 2 != 0 else (sorted_prices[mid-1] + sorted_prices[mid]) / 2

    filtered = [h for h in recent if h["avg_price"] <= median * MAX_PRICE_RATIO and h["avg_price"] >= median / MAX_PRICE_RATIO]
    if not filtered:
        filtered = recent  

   
    total_weight = 0
    weighted_sum = 0
    for idx, h in enumerate(filtered):
        weight = (idx + 1) * h["item_count"]  
        weighted_sum += h["avg_price"] * weight
        total_weight += weight

    if total_weight == 0:
        return None

    return weighted_sum / total_weight


async def fetch_chunk(client: httpx.AsyncClient, item_chunk: list[str]) -> list[dict]:
    item_str = ",".join(item_chunk)
    url = (
        f"https://www.albion-online-data.com/api/v2/stats/history/{item_str}"
        f"?locations={CITY_STR}&time-scale=24"
    )
    try:
        resp = await client.get(url, timeout=40.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ARBION] Chunk error: {e}")
        return []


# ── MAIN ENDPOINT ──────────────────────────────────────────────────────────
@app.get("/global-stats")
async def get_arbitrage_deals():
    item_chunks = list(chunks(ITEM_LIST, CHUNK_SIZE))
    print(f"[ARBION] Scanning {len(ITEM_LIST)} items in {len(item_chunks)} concurrent chunks...")

    async with httpx.AsyncClient() as client:
        tasks   = [fetch_chunk(client, chunk) for chunk in item_chunks]
        results = await asyncio.gather(*tasks)

    prices: dict[tuple, float] = {}

    for chunk_data in results:
        for entry in chunk_data:
            item_id  = entry.get("item_id")
            location = entry.get("location")
            history  = entry.get("data", [])
            quality  = entry.get("quality", 1)

            if not item_id or not location or not history:
                continue

            if quality != 1:
                continue

            smart_price = calculate_smart_price(history)
            if smart_price and smart_price > 0:
                prices[(item_id, location)] = smart_price

    print(f"[ARBION] Price index ready: {len(prices)} item-location pairs")

    # Compute arbitrage
    all_results: dict[str, dict] = {}
    for buy_city in CITIES:
        city_deals        = []
        total_city_profit = 0

        for item_id in ITEM_LIST:
            buy_price = prices.get((item_id, buy_city))
            if not buy_price or buy_price <= 0:
                continue

            for sell_city in CITIES:
                if sell_city == buy_city:
                    continue
                sell_price = prices.get((item_id, sell_city))
                if not sell_price or sell_price <= 0:
                    continue

                net_sell = sell_price * (1 - MARKET_TAX)
                profit   = int(net_sell - buy_price)
                if profit < MIN_PROFIT:
                    continue

                roi = round((profit / buy_price) * 100, 2)
                city_deals.append({
                    "id":         item_id,
                    "human_name": get_human_name(item_id),
                    "buy_at":     buy_city,
                    "sell_at":    sell_city,
                    "buy_price":  int(buy_price),
                    "sell_price": int(sell_price),
                    "profit":     profit,
                    "roi":        roi,
                    "img":        f"https://render.albiononline.com/v1/item/{item_id}.png",
                })
                total_city_profit += profit

        city_deals.sort(key=lambda x: x["profit"], reverse=True)
        all_results[buy_city] = {
            "total": total_city_profit,
            "deals": city_deals[:MAX_DEALS_PER_CITY],
        }

    print(f"[ARBION] Complete. {len(all_results)} cities processed.")
    return all_results


# ── STRIPE CHECKOUT ────────────────────────────────────────────────────────
@app.post("/create-checkout")
async def create_checkout(request: Request):
    body    = await request.json()
    user_id = body.get("user_id")
    email   = body.get("email")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=email,
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url="https://arbi0n.netlify.app?payment=success",
        cancel_url="https://arbi0n.netlify.app?payment=cancelled",
        metadata={"user_id": user_id},
    )
    return {"url": session.url}


# ── STRIPE WEBHOOK ─────────────────────────────────────────────────────────
@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        sb.table("profiles").update({"is_pro": True}).eq("id", user_id).execute()
        print(f"[ARBION] User {user_id} upgraded to Pro ✓")

    return {"status": "ok"}


# ── HEALTH ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":        "ok",
        "version":       "3.0.0",
        "items_tracked": len(ITEM_LIST),
        "chunk_size":    CHUNK_SIZE,
        "cities":        CITIES,
        "min_item_count": MIN_ITEM_COUNT,
        "lookback_days":  LOOKBACK_DAYS,
        "max_price_ratio": MAX_PRICE_RATIO,
    }
