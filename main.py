import stripe
import httpx
import asyncio
import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

stripe.api_key        = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID       = "price_1T7KE2KFJRX1avMl9z1D8leJ"
SUPABASE_URL          = "https://znzsttdyeigkfwbvocie.supabase.co"
SUPABASE_SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY")

app = FastAPI(title="ARBION OS", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── CONFIGURATION ──────────────────────────────────────────────────────────
TIERS = ["T4", "T5", "T6", "T7", "T8"]

# Τα καλύτερα items για arbitrage βάσει volume και profit consistency
BASE_ITEMS = [
    # High volume — πάντα έχουν deals
    "BAG", "CAPE",
    "MOUNT_HORSE", "MOUNT_OX", "MOUNT_MULE",
    # Resources — τεράστιο volume, σταθερές τιμές
    "PLANKS", "METALBAR", "CLOTH", "LEATHER", "STONEBLOCK",
    # Food — guaranteed arbitrage μεταξύ πόλεων
    "FOOD_BREAD", "FOOD_ROAST", "FOOD_SOUP",
    # Weapons — υψηλό profit margin
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
    # Armor
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
MIN_PROFIT         = 2000
MAX_DEALS_PER_CITY = 50
CHUNK_SIZE         = 50
MAX_PRICE_AGE_H    = 48   # αγνοούμε τιμές παλιότερες από 48 ώρες
PLACEHOLDER_PRICE  = 999999  # Albion placeholder για "δεν υπάρχει listing"

# ── NAME MAPPING ───────────────────────────────────────────────────────────
TIER_NAMES = {
    "T4": "Adept's", "T5": "Expert's",
    "T6": "Master's", "T7": "Grandmaster's", "T8": "Elder's"
}

BASE_NAMES = {
    "BAG": "Bag", "CAPE": "Cape",
    "MOUNT_HORSE": "Riding Horse", "MOUNT_OX": "Transport Ox", "MOUNT_MULE": "Mule",
    "PLANKS": "Planks", "METALBAR": "Metal Bar", "CLOTH": "Cloth",
    "LEATHER": "Leather", "STONEBLOCK": "Stone Block",
    "FOOD_BREAD": "Bread", "FOOD_ROAST": "Roast", "FOOD_SOUP": "Soup",
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


def is_price_fresh(date_str: str) -> bool:
    """Ελέγχει αν η τιμή είναι φρέσκια (< MAX_PRICE_AGE_H ώρες παλιά)"""
    if not date_str:
        return False
    try:
        price_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if price_time.tzinfo is None:
            price_time = price_time.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - price_time
        return age < timedelta(hours=MAX_PRICE_AGE_H)
    except Exception:
        return False


def is_valid_price(price: int) -> bool:
    """Ελέγχει αν η τιμή είναι πραγματική (όχι placeholder ή 0)"""
    return 0 < price < PLACEHOLDER_PRICE


async def fetch_prices_chunk(client: httpx.AsyncClient, item_chunk: list[str]) -> list[dict]:
    """Φέρνει real-time τιμές από το prices API"""
    item_str = ",".join(item_chunk)
    url = (
        f"https://www.albion-online-data.com/api/v2/stats/prices/{item_str}"
        f"?locations={CITY_STR}&qualities=1"
    )
    try:
        resp = await client.get(url, timeout=40.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ARBION] Prices chunk error: {e}")
        return []


async def fetch_history_chunk(client: httpx.AsyncClient, item_chunk: list[str]) -> list[dict]:
    """Φέρνει history για fallback όταν δεν υπάρχουν fresh prices"""
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
        print(f"[ARBION] History chunk error: {e}")
        return []


def get_history_price(history: list[dict]) -> float | None:
    """Weighted average από τις τελευταίες 3 μέρες με volume weighting"""
    if not history:
        return None
    valid = [h for h in history if h.get("item_count", 0) >= 5 and h.get("avg_price", 0) > 0]
    if not valid:
        return None
    recent = valid[-3:] if len(valid) >= 3 else valid
    prices = [h["avg_price"] for h in recent]
    sorted_p = sorted(prices)
    mid = len(sorted_p) // 2
    median = sorted_p[mid]
    # Φιλτράρουμε spikes: τιμές > 2x median ή < 0.5x median
    filtered = [h for h in recent if median * 0.5 <= h["avg_price"] <= median * 2.0]
    if not filtered:
        filtered = recent
    total_weight = sum(h["item_count"] for h in filtered)
    if total_weight == 0:
        return None
    weighted_sum = sum(h["avg_price"] * h["item_count"] for h in filtered)
    return weighted_sum / total_weight


# ── GLOBAL CACHE ───────────────────────────────────────────────────────────
# Αποθηκεύουμε το τελευταίο αποτέλεσμα για να το χρησιμοποιεί το route planner
_last_prices: dict[tuple, float] = {}
_last_deals:  dict[str, list]    = {}


# ── MAIN ENDPOINT ──────────────────────────────────────────────────────────
@app.get("/global-stats")
async def get_arbitrage_deals():
    global _last_prices, _last_deals

    item_chunks = list(chunks(ITEM_LIST, CHUNK_SIZE))
    print(f"[ARBION v4] Scanning {len(ITEM_LIST)} items — {len(item_chunks)} chunks...")

    async with httpx.AsyncClient() as client:
        # Φέρνουμε prices + history παράλληλα
        price_tasks   = [fetch_prices_chunk(client, chunk) for chunk in item_chunks]
        history_tasks = [fetch_history_chunk(client, chunk) for chunk in item_chunks]
        price_results, history_results = await asyncio.gather(
            asyncio.gather(*price_tasks),
            asyncio.gather(*history_tasks)
        )

    # ── Χτίζουμε price index ──
    prices: dict[tuple, float] = {}  # key: (item_id, city)

    # 1. Πρώτα βάζουμε history prices ως base
    for chunk_data in history_results:
        for entry in chunk_data:
            item_id  = entry.get("item_id")
            location = entry.get("location")
            history  = entry.get("data", [])
            quality  = entry.get("quality", 1)
            if not item_id or not location or quality != 1:
                continue
            h_price = get_history_price(history)
            if h_price and h_price > 0:
                prices[(item_id, location)] = h_price

    # 2. Override με real-time prices αν είναι φρέσκιες και valid
    fresh_count = 0
    for chunk_data in price_results:
        for entry in chunk_data:
            item_id    = entry.get("item_id")
            city       = entry.get("city")
            sell_min   = entry.get("sell_price_min", 0)
            sell_date  = entry.get("sell_price_min_date", "")
            if not item_id or not city:
                continue
            if is_valid_price(sell_min) and is_price_fresh(sell_date):
                prices[(item_id, city)] = float(sell_min)
                fresh_count += 1

    print(f"[ARBION v4] {len(prices)} prices total, {fresh_count} real-time overrides")
    _last_prices = prices

    # ── Arbitrage computation ──
    all_results: dict[str, dict] = {}
    all_deals_flat: dict[str, list] = {}

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

                # Confidence score: πόσο αξιόπιστο είναι το deal
                # Βασίζεται στο αν έχουμε real-time τιμές και για τις δύο πόλεις
                buy_rt  = any(e.get("city") == buy_city  and e.get("item_id") == item_id for chunk in price_results for e in chunk)
                sell_rt = any(e.get("city") == sell_city and e.get("item_id") == item_id for chunk in price_results for e in chunk)
                if buy_rt and sell_rt:
                    confidence = "HIGH"
                elif buy_rt or sell_rt:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"

                deal = {
                    "id":         item_id,
                    "human_name": get_human_name(item_id),
                    "buy_at":     buy_city,
                    "sell_at":    sell_city,
                    "buy_price":  int(buy_price),
                    "sell_price": int(sell_price),
                    "profit":     profit,
                    "roi":        roi,
                    "confidence": confidence,
                    "img":        f"https://render.albiononline.com/v1/item/{item_id}.png",
                }
                city_deals.append(deal)
                total_city_profit += profit

        city_deals.sort(key=lambda x: x["profit"], reverse=True)
        all_results[buy_city] = {
            "total": total_city_profit,
            "deals": city_deals[:MAX_DEALS_PER_CITY],
        }
        all_deals_flat[buy_city] = city_deals[:MAX_DEALS_PER_CITY]

    _last_deals = all_deals_flat
    print(f"[ARBION v4] Complete — {sum(len(v['deals']) for v in all_results.values())} total deals")
    return all_results


# ── ROUTE PLANNER (PRO) ────────────────────────────────────────────────────
@app.post("/route-planner")
async def route_planner(request: Request):
    """
    PRO feature: δίνεις silver budget + inventory slots,
    επιστρέφει τον βέλτιστο συνδυασμό items για μέγιστο κέρδος.
    """
    body   = await request.json()
    budget = int(body.get("budget", 0))
    slots  = int(body.get("slots", 1))
    city   = body.get("city", "Martlock")

    if budget <= 0 or slots <= 0:
        raise HTTPException(status_code=400, detail="Invalid budget or slots")

    # Παίρνουμε τα deals από cache
    city_deals = _last_deals.get(city, [])
    if not city_deals:
        raise HTTPException(status_code=503, detail="No market data yet. Try again in a moment.")

    # Φιλτράρουμε deals που χωράνε στο budget
    affordable = [d for d in city_deals if d["buy_price"] <= budget]
    if not affordable:
        return {"route": [], "total_profit": 0, "total_cost": 0, "message": "No deals found within budget"}

    # Knapsack-style: μέγιστο profit με slots constraint
    # Για κάθε slot βρίσκουμε το καλύτερο deal που δεν ξεπερνά το remaining budget
    selected  = []
    remaining = budget
    used_items = set()

    for _ in range(slots):
        best = None
        for deal in affordable:
            if deal["id"] in used_items:
                continue
            if deal["buy_price"] > remaining:
                continue
            if best is None or deal["profit"] > best["profit"]:
                best = deal
        if best is None:
            break
        selected.append(best)
        used_items.add(best["id"])
        remaining -= best["buy_price"]

    total_profit = sum(d["profit"] for d in selected)
    total_cost   = sum(d["buy_price"] for d in selected)
    roi          = round((total_profit / total_cost * 100), 1) if total_cost > 0 else 0

    return {
        "route":        selected,
        "total_profit": total_profit,
        "total_cost":   total_cost,
        "remaining":    remaining,
        "roi":          roi,
        "slots_used":   len(selected),
    }


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
        print(f"[ARBION] User {user_id} → Pro ✓")

    return {"status": "ok"}


# ── HEALTH ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":         "ok",
        "version":        "4.0.0",
        "items_tracked":  len(ITEM_LIST),
        "cities":         CITIES,
        "max_price_age":  f"{MAX_PRICE_AGE_H}h",
        "cached_prices":  len(_last_prices),
        "cached_deals":   sum(len(v) for v in _last_deals.values()),
    }
