import httpx
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ARBION OS", version="2.4.0")

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

CITIES = ["Martlock", "Lymhurst", "Fort Sterling", "Bridgewatch", "Thetford", "Caerleon"]
MARKET_TAX = 0.06
MIN_PROFIT = 1500
MAX_DEALS_PER_CITY = 30
CHUNK_SIZE = 50  # items per API request — safe for Albion API URL limits

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
CITY_STR = ",".join(CITIES)


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


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
        tasks = [fetch_chunk(client, chunk) for chunk in item_chunks]
        results = await asyncio.gather(*tasks)

    # Build price index
    prices: dict[str, dict[str, float]] = {}
    for chunk_data in results:
        for entry in chunk_data:
            item_id = entry.get("item_id")
            location = entry.get("location")
            history = entry.get("data", [])
            if not item_id or not location or not history:
                continue
            recent = next(
                (h for h in reversed(history) if h.get("avg_price", 0) > 0),
                None
            )
            if not recent:
                continue
            if item_id not in prices:
                prices[item_id] = {}
            prices[item_id][location] = float(recent["avg_price"])

    print(f"[ARBION] Price index ready: {len(prices)} items with live data")

    # Compute arbitrage
    all_results: dict[str, dict] = {}
    for buy_city in CITIES:
        city_deals = []
        total_city_profit = 0

        for item_id in ITEM_LIST:
            item_prices = prices.get(item_id)
            if not item_prices or buy_city not in item_prices:
                continue
            buy_price = item_prices[buy_city]
            if buy_price <= 0:
                continue

            for sell_city in CITIES:
                if sell_city == buy_city:
                    continue
                sell_price = item_prices.get(sell_city, 0)
                if sell_price <= 0:
                    continue

                net_sell = sell_price * (1 - MARKET_TAX)
                profit = int(net_sell - buy_price)
                if profit < MIN_PROFIT:
                    continue

                roi = round((profit / buy_price) * 100, 2)
                city_deals.append({
                    "id": item_id,
                    "human_name": get_human_name(item_id),
                    "buy_at": buy_city,
                    "sell_at": sell_city,
                    "buy_price": int(buy_price),
                    "sell_price": int(sell_price),
                    "profit": profit,
                    "roi": roi,
                    "img": f"https://render.albiononline.com/v1/item/{item_id}.png",
                })
                total_city_profit += profit

        city_deals.sort(key=lambda x: x["profit"], reverse=True)
        all_results[buy_city] = {
            "total": total_city_profit,
            "deals": city_deals[:MAX_DEALS_PER_CITY],
        }

    print(f"[ARBION] Complete. {len(all_results)} cities processed.")
    return all_results


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.4.0",
        "items_tracked": len(ITEM_LIST),
        "chunk_size": CHUNK_SIZE,
        "cities": CITIES,
    }