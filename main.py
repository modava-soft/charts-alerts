# -*- coding: utf-8 -*-
# Modu Bazler v6.0 – نسخه‌ی کامل با انتخاب تایم‌فریم، Binance/KuCoin، آلارم‌ها و نمودارها
# سازگار با Railway – توکن‌ها و چت‌آیدی‌ها از متغیرهای محیطی

import os, json, time, threading, datetime as dt
import requests, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import telebot
from telebot import types

# =========================
# مسیرها و کانفیگ
# =========================

BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
CHARTS_DIR = os.path.join(DATA_DIR, "charts")
PDF_DIR    = os.path.join(DATA_DIR, "pdf")

for d in [DATA_DIR, CHARTS_DIR, PDF_DIR]:
    os.makedirs(d, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, "config_v6_0.json")

DEFAULT_CONFIG = {
    "symbols_15m": [
        "BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","ADAUSDT","SOLUSDT","DOGEUSDT","DOTUSDT","MATICUSDT","LTCUSDT",
        "TRXUSDT","AVAXUSDT","LINKUSDT","ATOMUSDT","XMRUSDT","ETCUSDT","XLMUSDT","FILUSDT","APTUSDT","NEARUSDT",
        "OPUSDT","ARBUSDT","SUIUSDT","PEPEUSDT","TONUSDT","UNIUSDT","AAVEUSDT","INJUSDT","RNDRUSDT","FTMUSDT",
        "NEOUSDT","GALAUSDT","SEIUSDT","TIAUSDT","PYTHUSDT","JTOUSDT","WIFUSDT","JUPUSDT","STRKUSDT","BLURUSDT",
        "RUNEUSDT","RAYUSDT","LDOUSDT","COMPUSDT","CRVUSDT","MKRUSDT","SNXUSDT","GMXUSDT","DYDXUSDT","ENSUSDT"
    ],
    "symbols_1h": [
        "BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","ADAUSDT",
        "SOLUSDT","DOGEUSDT","DOTUSDT","MATICUSDT","LTCUSDT",
        "TRXUSDT","AVAXUSDT","LINKUSDT","ATOMUSDT","XMRUSDT",
        "ETCUSDT","XLMUSDT","FILUSDT","APTUSDT","NEARUSDT"
    ],
    "symbols_4h": [
        "BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","ADAUSDT",
        "SOLUSDT","DOGEUSDT","DOTUSDT","MATICUSDT","LTCUSDT",
        "TRXUSDT","AVAXUSDT","LINKUSDT","ATOMUSDT","XMRUSDT",
        "ETCUSDT","XLMUSDT","FILUSDT","APTUSDT","NEARUSDT"
    ],
    "symbols_1d": [
        "BTCUSDT","ETHUSDT","BNBUSDT","XRPUSDT","ADAUSDT",
        "SOLUSDT","DOGEUSDT","DOTUSDT","MATICUSDT","LTCUSDT",
        "TRXUSDT","AVAXUSDT","LINKUSDT","ATOMUSDT","XMRUSDT",
        "ETCUSDT","XLMUSDT","FILUSDT","APTUSDT","NEARUSDT"
    ],

    # lookback بر اساس روز/دوره، max_bars برای نمایش
    "lookback_15m": 3,
    "lookback_1h": 5,
    "lookback_4h": 15,
    "lookback_1d": 180,
    "max_bars": 300,

    # آلارم‌ها
    "alarm_wma_direction": True,
    "alarm_cross_sma20": False,
    "alarm_cross_sma100": False,
    "alarm_cross_sma200": False,
    "alarm_sma20_direction": False,
    "alarm_sma100_direction": False,
    "alarm_sma200_direction": False,

    # PDF
    "make_pdf_1h": True,
    "make_pdf_1d": True,

    # Combined 15m
    "make_combined_15m": True,

    # چت‌آیدی‌ها – اگر از Railway ست شده باشند، اینجا کپی می‌شوند
    "chat_id_main": None,   # ربات اصلی (1h)
    "chat_id_15m": None,
    "chat_id_1h": None,
    "chat_id_4h": None,
    "chat_id_1d": None,

    # verbose
    "verbose_15m": True,
    "verbose_1h": True,
    "verbose_4h": True,
    "verbose_1d": True,

    # SmartLock
    "lock_timeout_sec": 600,
    "cycle_min_duration_sec": 5,

    # تایم‌فریم فعال (برای اجرای فوری از ربات اصلی)
    "active_interval": "15m"
}

def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        debug_mark(None, None, 101, "save_config")

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        cfg = DEFAULT_CONFIG.copy()
        # مقداردهی اولیه چت‌آیدی‌ها از Railway
        cfg["chat_id_main"] = os.getenv("CHAT_ID_MAIN")
        cfg["chat_id_15m"]  = os.getenv("CHAT_ID_15M")
        cfg["chat_id_1h"]   = os.getenv("CHAT_ID_1H")
        cfg["chat_id_4h"]   = os.getenv("CHAT_ID_4H")
        cfg["chat_id_1d"]   = os.getenv("CHAT_ID_1D")
        save_config(cfg)
        return cfg
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        debug_mark(None, None, 102, "load_config")
        return DEFAULT_CONFIG.copy()

def reset_config():
    cfg = DEFAULT_CONFIG.copy()
    cfg["chat_id_main"] = os.getenv("CHAT_ID_MAIN")
    cfg["chat_id_15m"]  = os.getenv("CHAT_ID_15M")
    cfg["chat_id_1h"]   = os.getenv("CHAT_ID_1H")
    cfg["chat_id_4h"]   = os.getenv("CHAT_ID_4H")
    cfg["chat_id_1d"]   = os.getenv("CHAT_ID_1D")
    save_config(cfg)
    return cfg

def now_utc():
    return dt.datetime.now(dt.timezone.utc)

def now_utc_str():
    return now_utc().strftime("%Y-%m-%d %H:%M:%S")

# =========================
# توکن‌ها و ربات‌ها (Railway)
# =========================

TOKEN_MAIN = (os.getenv("TOKEN_MAIN") or os.getenv("TOKEN_1H") or "").strip()
TOKEN_15M  = (os.getenv("TOKEN_15M") or "").strip()
TOKEN_4H   = (os.getenv("TOKEN_4H") or "").strip()
TOKEN_1D   = (os.getenv("TOKEN_1D") or "").strip()
ADMIN_CHAT = (os.getenv("ADMIN_CHAT_ID") or "").strip()

def debug_mark(bot, chat_id, code: int, where: str):
    msg = f"TEST#{code} @ {where}"
    try:
        if bot and chat_id:
            bot.send_message(int(chat_id), msg)
        elif ADMIN_CHAT and bot:
            bot.send_message(int(ADMIN_CHAT), msg)
    except:
        pass

def create_bot(token: str):
    if not token or not isinstance(token, str):
        return None
    if ":" not in token:
        return None
    try:
        return telebot.TeleBot(token, parse_mode="HTML")
    except Exception:
        debug_mark(None, None, 103, "create_bot")
        return None

bot_main = create_bot(TOKEN_MAIN)  # ربات اصلی – منو و کنترل
bot_15m  = create_bot(TOKEN_15M)
bot_4h   = create_bot(TOKEN_4H)
bot_1d   = create_bot(TOKEN_1D)

if bot_main is None:
    raise ValueError("TOKEN_MAIN/TOKEN_1H تنظیم نشده یا اشتباه است؛ ربات اصلی نمی‌تواند ساخته شود.")

LAST_ALARMS = {
    "15m": [],
    "1h": [],
    "4h": [],
    "1d": []
}

# =========================
# SmartLock
# =========================

class SmartLock:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_acquire = None

    def acquire(self, blocking=False):
        cfg = load_config()
        timeout = cfg.get("lock_timeout_sec", 600)
        if self.lock.locked() and self.last_acquire:
            elapsed = (now_utc() - self.last_acquire).total_seconds()
            if elapsed > timeout:
                try:
                    self.lock.release()
                    debug_mark(bot_main, cfg.get("chat_id_main"), 1901, "SmartLock_force_release")
                except:
                    pass
        ok = self.lock.acquire(blocking=blocking)
        if ok:
            self.last_acquire = now_utc()
        return ok

    def release(self):
        if self.lock.locked():
            try:
                self.lock.release()
            except:
                pass

CYCLE_LOCKS = {
    "15m": SmartLock(),
    "1h": SmartLock(),
    "4h": SmartLock(),
    "1d": SmartLock()
}

# =========================
# راهنما
# =========================

HELP_TEXT = """
Modu Bazler v6.0 – نسخه‌ی کامل با انتخاب تایم‌فریم

📌 ربات‌ها:
- ربات اصلی (TOKEN_MAIN/TOKEN_1H): منوی مدیریت و انتخاب تایم‌فریم
- ربات 15m: اجرای سیکل ۱۵دقیقه‌ای
- ربات 4h: اجرای سیکل ۴ساعته
- ربات 1d: اجرای سیکل روزانه

✅ ثبت چت هر ربات:
- در هر ربات دستور /start را بفرست تا chat_id ثبت شود.
- اگر در Railway متغیر CHAT_ID_* ست شده باشد، به‌صورت خودکار استفاده می‌شود.

🧭 منوی ربات اصلی:
- انتخاب تایم‌فریم فعال (15m / 1h / 4h / 1d)
- اجرای فوری تایم‌فریم فعال
- اجرای فوری 15m / 1h / 4h / 1d
- مدیریت نمادهای هر تایم‌فریم
- تنظیم آلارم‌ها
- گزارش آلارم‌ها
- وضعیت سیستم
- تنظیمات پیشرفته
- اجرای چرخه‌ها (همه تایم‌فریم‌ها)
- ریست برنامه
- راهنما / رفرش منو

🔊 حالت پردازش (verbose):
- ON → پیام‌های پردازش + نمودار همه‌ی نمادها
- OFF → فقط نمودار نمادهای دارای آلارم

📄 PDF:
- برای سیکل‌های 1h و 1d در صورت فعال بودن، یک فایل PDF از همه‌ی نمودارها ساخته و ارسال می‌شود.

⏱ زمان‌بندی خودکار (قابل تنظیم در Scheduler):
- 15m: هر ۱۵ دقیقه
- 1h: هر ساعت
- 4h: هر ۴ ساعت
- 1d: هر روز
"""

# =========================
# منوی اصلی ربات
# =========================

def send_main_menu(chat_id):
    cfg = load_config()
    active = cfg.get("active_interval", "15m")
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("انتخاب تایم‌فریم فعال", f"تایم‌فریم فعال: {active}")
    kb.row("اجرای فوری تایم‌فریم فعال")
    kb.row("اجرای فوری 15m", "اجرای فوری 1h")
    kb.row("اجرای فوری 4h", "اجرای فوری 1d")
    kb.row("مدیریت نمادهای 15m", "مدیریت نمادهای 1h")
    kb.row("مدیریت نمادهای 4h", "مدیریت نمادهای 1d")
    kb.row("تنظیم آلارم‌ها", "گزارش آلارم‌ها")
    kb.row("وضعیت سیستم", "تنظیمات پیشرفته")
    kb.row("اجرای چرخه‌ها", "ریست برنامه")
    kb.row("راهنما", "رفرش منو")
    try:
        bot_main.send_message(chat_id, "منوی اصلی:", reply_markup=kb)
    except Exception:
        debug_mark(bot_main, chat_id, 201, "send_main_menu")

@bot_main.message_handler(commands=["start"])
def start_main(m):
    cfg = load_config()
    cfg["chat_id_main"] = m.chat.id
    save_config(cfg)
    try:
        bot_main.send_message(m.chat.id, HELP_TEXT)
        send_main_menu(m.chat.id)
    except Exception:
        debug_mark(bot_main, m.chat.id, 202, "start_main")

@bot_main.message_handler(commands=["refresh"])
@bot_main.message_handler(func=lambda m: m.text == "رفرش منو")
def refresh_main(m):
    send_main_menu(m.chat.id)

# =========================
# استارت سایر ربات‌ها
# =========================

if bot_15m:
    @bot_15m.message_handler(commands=["start"])
    def start_15m(m):
        cfg = load_config()
        cfg["chat_id_15m"] = m.chat.id
        save_config(cfg)
        try:
            bot_15m.send_message(m.chat.id, "ربات ۱۵دقیقه‌ای فعال شد.\n" + now_utc_str())
        except Exception:
            debug_mark(bot_15m, m.chat.id, 205, "start_15m")

if bot_4h:
    @bot_4h.message_handler(commands=["start"])
    def start_4h(m):
        cfg = load_config()
        cfg["chat_id_4h"] = m.chat.id
        save_config(cfg)
        try:
            bot_4h.send_message(m.chat.id, "ربات ۴ساعته فعال شد.\n" + now_utc_str())
        except Exception:
            debug_mark(bot_4h, m.chat.id, 203, "start_4h")

if bot_1d:
    @bot_1d.message_handler(commands=["start"])
    def start_1d(m):
        cfg = load_config()
        cfg["chat_id_1d"] = m.chat.id
        save_config(cfg)
        try:
            bot_1d.send_message(m.chat.id, "ربات روزانه فعال شد.\n" + now_utc_str())
        except Exception:
            debug_mark(bot_1d, m.chat.id, 204, "start_1d")

# =========================
# انتخاب تایم‌فریم فعال
# =========================

@bot_main.message_handler(func=lambda m: m.text == "انتخاب تایم‌فریم فعال")
def choose_active_interval(m):
    kb = types.InlineKeyboardMarkup()
    for tf in ["15m","1h","4h","1d"]:
        kb.add(types.InlineKeyboardButton(f"{tf}", callback_data=f"set_active_{tf}"))
    try:
        bot_main.send_message(m.chat.id, "تایم‌فریم فعال را انتخاب کنید:", reply_markup=kb)
    except Exception:
        debug_mark(bot_main, m.chat.id, 210, "choose_active_interval")

@bot_main.callback_query_handler(func=lambda c: c.data.startswith("set_active_"))
def set_active_interval(c):
    cfg = load_config()
    tf = c.data.replace("set_active_", "")
    cfg["active_interval"] = tf
    save_config(cfg)
    try:
        bot_main.answer_callback_query(c.id, f"تایم‌فریم فعال: {tf}")
        send_main_menu(c.message.chat.id)
    except Exception:
        debug_mark(bot_main, c.message.chat.id, 211, "set_active_interval")

# =========================
# ریست برنامه
# =========================

@bot_main.message_handler(func=lambda m: m.text == "ریست برنامه")
def reset_app(m):
    cfg = reset_config()
    cfg["chat_id_main"] = m.chat.id
    save_config(cfg)
    try:
        bot_main.send_message(m.chat.id, "برنامه و تنظیمات کامل ریست شد.")
        send_main_menu(m.chat.id)
    except Exception:
        debug_mark(bot_main, m.chat.id, 206, "reset_app")

# =========================
# مدیریت نمادها
# =========================

def get_symbols(cfg, group):
    return cfg[f"symbols_{group}"]

def set_symbols(cfg, group, symbols):
    cfg[f"symbols_{group}"] = symbols
    save_config(cfg)

def show_symbol_menu(chat_id, group):
    cfg = load_config()
    symbols = get_symbols(cfg, group)
    txt = f"نمادهای فعال در {group}:\n"
    txt += ", ".join(symbols) if symbols else "هیچ نمادی ثبت نشده است."
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(f"افزودن نماد به {group}", f"حذف نماد از {group}")
    kb.row(f"نمایش نمادهای {group}")
    kb.row("بازگشت به منوی اصلی")
    try:
        bot_main.send_message(chat_id, txt, reply_markup=kb)
    except Exception:
        debug_mark(bot_main, chat_id, 301, "show_symbol_menu")

@bot_main.message_handler(func=lambda m: m.text == "مدیریت نمادهای 15m")
def manage_15m(m): show_symbol_menu(m.chat.id, "15m")

@bot_main.message_handler(func=lambda m: m.text == "مدیریت نمادهای 1h")
def manage_1h(m): show_symbol_menu(m.chat.id, "1h")

@bot_main.message_handler(func=lambda m: m.text == "مدیریت نمادهای 4h")
def manage_4h(m): show_symbol_menu(m.chat.id, "4h")

@bot_main.message_handler(func=lambda m: m.text == "مدیریت نمادهای 1d")
def manage_1d(m): show_symbol_menu(m.chat.id, "1d")

def add_symbol_step(m, group):
    symbol = m.text.strip().upper()
    cfg = load_config()
    symbols = get_symbols(cfg, group)
    if symbol not in symbols:
        symbols.append(symbol)
        set_symbols(cfg, group, symbols)
        try:
            bot_main.send_message(m.chat.id, f"{symbol} به لیست {group} اضافه شد.")
        except Exception:
            debug_mark(bot_main, m.chat.id, 302, "add_symbol_step")
    else:
        try:
            bot_main.send_message(m.chat.id, f"{symbol} قبلاً در لیست {group} وجود دارد.")
        except Exception:
            debug_mark(bot_main, m.chat.id, 303, "add_symbol_step_exists")
    show_symbol_menu(m.chat.id, group)

@bot_main.message_handler(func=lambda m: m.text.startswith("افزودن نماد به "))
def add_symbol_any(m):
    group = m.text.split()[-1]
    msg = bot_main.send_message(m.chat.id, "نماد را وارد کنید:")
    bot_main.register_next_step_handler(msg, lambda mm: add_symbol_step(mm, group))

def remove_symbol_step(m, group):
    symbol = m.text.strip().upper()
    cfg = load_config()
    symbols = get_symbols(cfg, group)
    if symbol in symbols:
        symbols.remove(symbol)
        set_symbols(cfg, group, symbols)
        try:
            bot_main.send_message(m.chat.id, f"{symbol} از لیست {group} حذف شد.")
        except Exception:
            debug_mark(bot_main, m.chat.id, 304, "remove_symbol_step")
    else:
        try:
            bot_main.send_message(m.chat.id, f"{symbol} در لیست {group} وجود ندارد.")
        except Exception:
            debug_mark(bot_main, m.chat.id, 305, "remove_symbol_step_not_found")
    show_symbol_menu(m.chat.id, group)

@bot_main.message_handler(func=lambda m: m.text.startswith("حذف نماد از "))
def remove_symbol_any(m):
    group = m.text.split()[-1]
    msg = bot_main.send_message(m.chat.id, "نماد مورد نظر را وارد کنید:")
    bot_main.register_next_step_handler(msg, lambda mm: remove_symbol_step(mm, group))

@bot_main.message_handler(func=lambda m: m.text.startswith("نمایش نمادهای "))
def show_symbols_any(m):
    group = m.text.split()[-1]
    cfg = load_config()
    symbols = get_symbols(cfg, group)
    txt = f"نمادهای {group}:\n"
    txt += ", ".join(symbols) if symbols else "هیچ نمادی ثبت نشده است."
    try:
        bot_main.send_message(m.chat.id, txt)
    except Exception:
        debug_mark(bot_main, m.chat.id, 306, "show_symbols_any")

# =========================
# تنظیم آلارم‌ها
# =========================

@bot_main.message_handler(func=lambda m: m.text == "تنظیم آلارم‌ها")
def alarms_menu(m):
    cfg = load_config()
    kb = types.InlineKeyboardMarkup()
    for key in [
        "alarm_wma_direction",
        "alarm_cross_sma20",
        "alarm_cross_sma100",
        "alarm_cross_sma200",
        "alarm_sma20_direction",
        "alarm_sma100_direction",
        "alarm_sma200_direction"
    ]:
        kb.add(types.InlineKeyboardButton(
            f"{key} ({'ON' if cfg.get(key) else 'OFF'})",
            callback_data=f"alarm_{key}"
        ))
    try:
        bot_main.send_message(m.chat.id, "آلارم‌ها را تنظیم کنید:", reply_markup=kb)
    except Exception:
        debug_mark(bot_main, m.chat.id, 401, "alarms_menu")

@bot_main.callback_query_handler(func=lambda c: c.data.startswith("alarm_"))
def toggle_alarm(c):
    cfg = load_config()
    key = c.data.replace("alarm_", "")
    cfg[key] = not cfg.get(key)
    save_config(cfg)
    try:
        bot_main.answer_callback_query(c.id, f"{key} -> {'ON' if cfg[key] else 'OFF'}")
        alarms_menu(c.message)
    except Exception:
        debug_mark(bot_main, c.message.chat.id, 402, "toggle_alarm")

# =========================
# گزارش آلارم‌ها
# =========================

@bot_main.message_handler(func=lambda m: m.text == "گزارش آلارم‌ها")
def alarms_report(m):
    txt = ""
    for group in ["15m","1h","4h","1d"]:
        if LAST_ALARMS[group]:
            txt += f"آلارم‌های {group}:\n"
            for item in LAST_ALARMS[group]:
                txt += f"{item['symbol']} ({item['interval']}):\n"
                for a in item["alarms"]:
                    txt += f" - {a}\n"
                txt += f"زمان: {item['time']}\n\n"
    if not txt:
        txt = "هیچ آلارمی ثبت نشده است."
    try:
        bot_main.send_message(m.chat.id, txt)
    except Exception:
        debug_mark(bot_main, m.chat.id, 501, "alarms_report")

# =========================
# وضعیت سیستم و تنظیمات پیشرفته
# =========================

@bot_main.message_handler(func=lambda m: m.text == "وضعیت سیستم")
def system_status(m):
    cfg = load_config()
    txt = "وضعیت سیستم:\n"
    txt += f"نمادهای 15m: {len(cfg['symbols_15m'])}\n"
    txt += f"نمادهای 1h: {len(cfg['symbols_1h'])}\n"
    txt += f"نمادهای 4h: {len(cfg['symbols_4h'])}\n"
    txt += f"نمادهای 1d: {len(cfg['symbols_1d'])}\n"
    txt += f"PDF 1h: {'ON' if cfg['make_pdf_1h'] else 'OFF'}\n"
    txt += f"PDF 1d: {'ON' if cfg['make_pdf_1d'] else 'OFF'}\n"
    txt += f"Combined 15m: {'ON' if cfg.get('make_combined_15m', True) else 'OFF'}\n"
    txt += f"verbose 15m: {'ON' if cfg['verbose_15m'] else 'OFF'}\n"
    txt += f"verbose 1h: {'ON' if cfg['verbose_1h'] else 'OFF'}\n"
    txt += f"verbose 4h: {'ON' if cfg['verbose_4h'] else 'OFF'}\n"
    txt += f"verbose 1d: {'ON' if cfg['verbose_1d'] else 'OFF'}\n"
    txt += f"active_interval: {cfg.get('active_interval','15m')}\n"
    txt += f"lock_timeout_sec: {cfg.get('lock_timeout_sec', 600)}\n"
    txt += f"cycle_min_duration_sec: {cfg.get('cycle_min_duration_sec', 5)}\n"
    try:
        bot_main.send_message(m.chat.id, txt)
    except Exception:
        debug_mark(bot_main, m.chat.id, 601, "system_status")

@bot_main.message_handler(func=lambda m: m.text == "تنظیمات پیشرفته")
def advanced_settings(m):
    cfg = load_config()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"PDF 1h ({'ON' if cfg['make_pdf_1h'] else 'OFF'})", callback_data="adv_pdf_1h"))
    kb.add(types.InlineKeyboardButton(f"PDF 1d ({'ON' if cfg['make_pdf_1d'] else 'OFF'})", callback_data="adv_pdf_1d"))
    kb.add(types.InlineKeyboardButton(f"Combined 15m ({'ON' if cfg.get('make_combined_15m', True) else 'OFF'})", callback_data="adv_combined_15m"))
    kb.add(types.InlineKeyboardButton(f"verbose 15m ({'ON' if cfg['verbose_15m'] else 'OFF'})", callback_data="adv_verbose_15m"))
    kb.add(types.InlineKeyboardButton(f"verbose 1h ({'ON' if cfg['verbose_1h'] else 'OFF'})", callback_data="adv_verbose_1h"))
    kb.add(types.InlineKeyboardButton(f"verbose 4h ({'ON' if cfg['verbose_4h'] else 'OFF'})", callback_data="adv_verbose_4h"))
    kb.add(types.InlineKeyboardButton(f"verbose 1d ({'ON' if cfg['verbose_1d'] else 'OFF'})", callback_data="adv_verbose_1d"))
    kb.add(types.InlineKeyboardButton("ریست کامل برنامه", callback_data="adv_reset_app"))
    try:
        bot_main.send_message(m.chat.id, "تنظیمات پیشرفته:", reply_markup=kb)
    except Exception:
        debug_mark(bot_main, m.chat.id, 602, "advanced_settings")

@bot_main.callback_query_handler(func=lambda c: c.data.startswith("adv_"))
def advanced_settings_handler(c):
    cfg = load_config()
    if c.data == "adv_pdf_1h":
        cfg["make_pdf_1h"] = not cfg["make_pdf_1h"]
    elif c.data == "adv_pdf_1d":
        cfg["make_pdf_1d"] = not cfg["make_pdf_1d"]
    elif c.data == "adv_combined_15m":
        cfg["make_combined_15m"] = not cfg.get("make_combined_15m", True)
    elif c.data == "adv_verbose_15m":
        cfg["verbose_15m"] = not cfg["verbose_15m"]
    elif c.data == "adv_verbose_1h":
        cfg["verbose_1h"] = not cfg["verbose_1h"]
    elif c.data == "adv_verbose_4h":
        cfg["verbose_4h"] = not cfg["verbose_4h"]
    elif c.data == "adv_verbose_1d":
        cfg["verbose_1d"] = not cfg["verbose_1d"]
    elif c.data == "adv_reset_app":
        cfg = reset_config()
    save_config(cfg)
    try:
        bot_main.answer_callback_query(c.id, "تنظیمات اعمال شد.")
        advanced_settings(c.message)
    except Exception:
        debug_mark(bot_main, c.message.chat.id, 603, "advanced_settings_handler")

# =========================
# راهنما
# =========================

@bot_main.message_handler(func=lambda m: m.text == "راهنما")
def help_menu(m):
    try:
        bot_main.send_message(m.chat.id, HELP_TEXT)
    except Exception:
        debug_mark(bot_main, m.chat.id, 701, "help_menu")

# =========================
# دیتا، اندیکاتورها، نمودار
# =========================

def _binance_interval(i: str) -> str:
    return {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}[i]

def _kucoin_interval(i: str) -> str:
    return {"15m": "15min", "1h": "1hour", "4h": "4hour", "1d": "1day"}[i]

def fetch_ohlc(symbol: str, interval: str, lookback_days: int, max_bars: int) -> pd.DataFrame:
    limit = max(500, max_bars)
    # Binance
    try:
        url = "https://api.binance.com/api/v3/klines"
        r = requests.get(url, params={
            "symbol": symbol,
            "interval": _binance_interval(interval),
            "limit": limit
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        rows = [[int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])] for k in data]
        df = pd.DataFrame(rows, columns=["t","o","h","l","c","v"])
        df["t"] = pd.to_datetime(df["t"], unit="ms", utc=True)
        df.set_index("t", inplace=True)
        return df
    except Exception:
        debug_mark(bot_main, ADMIN_CHAT or None, 801, "fetch_ohlc_binance")
    # KuCoin fallback
    try:
        sym = symbol.replace("USDT", "-USDT")
        end = int(now_utc().timestamp())
        start = end - 60 * 60 * (limit + 10)
        url = "https://api.kucoin.com/api/v1/market/candles"
        r = requests.get(url, params={
            "symbol": sym,
            "type": _kucoin_interval(interval),
            "startAt": start,
            "endAt": end
        }, timeout=10)
        r.raise_for_status()
        data = r.json()["data"]
        rows = [[int(k[0]), float(k[1]), float(k[3]), float(k[4]), float(k[2]), float(k[5])] for k in data]
        df = pd.DataFrame(rows, columns=["t","o","h","l","c","v"])
        df["t"] = pd.to_datetime(df["t"], unit="s", utc=True)
        df.sort_values("t", inplace=True)
        df.set_index("t", inplace=True)
        return df
    except Exception:
        debug_mark(bot_main, ADMIN_CHAT or None, 802, "fetch_ohlc_kucoin")
        return pd.DataFrame()

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df
    try:
        df["SMA20"]  = df["c"].rolling(20).mean()
        df["SMA100"] = df["c"].rolling(100).mean()
        df["SMA200"] = df["c"].rolling(200).mean()
        df["WMA20"] = df["c"].rolling(20).apply(lambda x: np.average(x, weights=np.arange(1, len(x)+1)), raw=True)
        df["WMA20_slope"] = df["WMA20"].diff()
        delta = df["c"].diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        roll_gain = pd.Series(gain, index=df.index).rolling(14).mean()
        roll_loss = pd.Series(loss, index=df.index).rolling(14).mean()
        rs = roll_gain / (roll_loss + 1e-9)
        df["RSI14"] = 100 - (100 / (1 + rs))
        ema12 = df["c"].ewm(span=12, adjust=False).mean()
        ema26 = df["c"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    except Exception:
        debug_mark(bot_main, ADMIN_CHAT or None, 803, "compute_indicators")
    return df

def create_plotly_chart(symbol: str, interval: str, lookback_days: int, max_bars: int, png_name: str):
    df = fetch_ohlc(symbol, interval, lookback_days, max_bars)
    if df.empty:
        df = pd.DataFrame(columns=["o","h","l","c","v"])
        df.index = pd.to_datetime([])
    else:
        df = df.tail(max_bars)[["o","h","l","c","v"]]
    df = compute_indicators(df)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.6,0.2,0.2], vertical_spacing=0.03)
    try:
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["o"], high=df["h"], low=df["l"], close=df["c"],
            name="Price"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"],  mode="lines",
                                 name="SMA20",  line=dict(color="blue")),   row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA100"], mode="lines",
                                 name="SMA100", line=dict(color="orange")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], mode="lines",
                                 name="SMA200", line=dict(color="purple")), row=1, col=1)

        wma   = df["WMA20"]
        slope = df["WMA20_slope"]
        wma_up   = wma.where(slope >= 0)
        wma_down = wma.where(slope < 0)

        fig.add_trace(go.Scatter(x=df.index, y=wma_up,   mode="lines",
                                 name="WMA20 Up",
                                 line=dict(color="green", width=2, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=wma_down, mode="lines",
                                 name="WMA20 Down",
                                 line=dict(color="red",   width=2, dash="dot")), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["RSI14"], mode="lines",
                                 name="RSI14", line=dict(color="brown")), row=2, col=1)
        fig.add_hline(y=70, line=dict(color="red", dash="dash"), row=2, col=1)
        fig.add_hline(y=30, line=dict(color="green", dash="dash"), row=2, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],        mode="lines",
                                 name="MACD",   line=dict(color="black")),   row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], mode="lines",
                                 name="Signal", line=dict(color="magenta")), row=3, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"],
                             name="Hist", marker_color="gray"), row=3, col=1)

        fig.update_layout(
            title=f"{symbol} – {interval}",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=1000
        )
        fig.update_yaxes(side="right", showgrid=True)
    except Exception:
        debug_mark(bot_main, ADMIN_CHAT or None, 804, "create_plotly_chart_build")

    png_path = os.path.join(CHARTS_DIR, png_name)
    try:
        # حجم مناسب برای تلگرام و Railway
        fig.write_image(png_path, width=1200, height=800, scale=1)
    except Exception:
        debug_mark(bot_main, ADMIN_CHAT or None, 805, "create_plotly_chart_write")

    return {
        "symbol": symbol,
        "interval": interval,
        "png_path": png_path,
        "created_at": now_utc_str(),
        "wma": df["WMA20"].tolist() if "WMA20" in df.columns else [],
        "wma_slope": df["WMA20_slope"].tolist() if "WMA20_slope" in df.columns else [],
        "sma20": df["SMA20"].tolist() if "SMA20" in df.columns else [],
        "sma100": df["SMA100"].tolist() if "SMA100" in df.columns else [],
        "sma200": df["SMA200"].tolist() if "SMA200" in df.columns else []
    }

def detect_alarms(cfg: dict, info: dict, group: str):
    alarms = []
    wma    = info["wma"]
    slope  = info["wma_slope"]
    sma20  = info["sma20"]
    sma100 = info["sma100"]
    sma200 = info["sma200"]
    if len(wma) < 3:
        return alarms

    if cfg.get("alarm_wma_direction", True):
        if slope[-2] < 0 and slope[-1] > 0:
            alarms.append("WMA20 جهت رو به بالا گرفت")
        if slope[-2] > 0 and slope[-1] < 0:
            alarms.append("WMA20 جهت رو به پایین گرفت")

    def cross(a, b):
        if len(a) < 2 or len(b) < 2:
            return False
        return (a[-2] - b[-2]) * (a[-1] - b[-1]) < 0

    if cfg.get("alarm_cross_sma20", False) and cross(wma, sma20):
        alarms.append("برخورد WMA20 با SMA20")
    if cfg.get("alarm_cross_sma100", False) and cross(wma, sma100):
        alarms.append("برخورد WMA20 با SMA100")
    if cfg.get("alarm_cross_sma200", False) and cross(wma, sma200):
        alarms.append("برخورد WMA20 با SMA200")

    def dir_change(arr, name):
        if len(arr) < 3:
            return
        d1 = arr[-1] - arr[-2]
        d2 = arr[-2] - arr[-3]
        if d2 < 0 and d1 > 0:
            alarms.append(f"{name} جهت رو به بالا گرفت")
        if d2 > 0 and d1 < 0:
            alarms.append(f"{name} جهت رو به پایین گرفت")

    if cfg.get("alarm_sma20_direction", False):
        dir_change(sma20, "SMA20")
    if cfg.get("alarm_sma100_direction", False):
        dir_change(sma100, "SMA100")
    if cfg.get("alarm_sma200_direction", False):
        dir_change(sma200, "SMA200")

    if alarms:
        LAST_ALARMS[group] = [{
            "symbol": info["symbol"],
            "interval": info["interval"],
            "time": info["created_at"],
            "alarms": alarms
        }]
    return alarms

# =========================
# اجرای سیکل‌ها
# =========================

def run_cycle(interval: str, manual: bool = False):
    cfg = load_config()
    lock = CYCLE_LOCKS[interval]
    if not lock.acquire(blocking=False):
        debug_mark(bot_main, cfg.get("chat_id_main"), 901, f"run_cycle_{interval}_lock_busy")
        return

    start_time = now_utc()
    try:
        symbols_key = f"symbols_{interval}"
        symbols = cfg.get(symbols_key, [])
        chat_id = cfg.get(f"chat_id_{interval}") or cfg.get("chat_id_main")
        verbose_key = f"verbose_{interval}"
        verbose = cfg.get(verbose_key, True)

        bot_for_interval = {
            "15m": bot_15m or bot_main,
            "1h": bot_main,
            "4h": bot_4h or bot_main,
            "1d": bot_1d or bot_main
        }[interval]

        if chat_id and bot_for_interval:
            bot_for_interval.send_message(chat_id,
                f"شروع سیکل {interval} برای {len(symbols)} نماد...\n{now_utc_str()}")

        batch = cfg.get("cycle_progress_batch", 5)

        pdf_pages = None
        pdf_path = None
        if interval in ["1h","1d"] and cfg.get(f"make_pdf_{interval}", False):
            pdf_path = os.path.join(PDF_DIR, f"{interval}_cycle_{now_utc_str().replace(' ','_').replace(':','-')}.pdf")
            pdf_pages = PdfPages(pdf_path)

        for idx, sym in enumerate(symbols, start=1):
            info = create_plotly_chart(sym, interval, cfg[f"lookback_{interval}"], cfg["max_bars"], f"{interval}_{sym}.png")
            alarms = detect_alarms(cfg, info, interval)

            if pdf_pages:
                try:
                    img = Image.open(info["png_path"])
                    fig_pdf, ax_pdf = plt.subplots(figsize=(8, 6))
                    ax_pdf.imshow(img)
                    ax_pdf.axis("off")
                    pdf_pages.savefig(fig_pdf)
                    plt.close(fig_pdf)
                except Exception:
                    debug_mark(bot_main, chat_id, 910, f"run_cycle_{interval}_pdf_add")

            if chat_id and bot_for_interval:
                if verbose or alarms:
                    try:
                        with open(info["png_path"], "rb") as img_file:
                            bot_for_interval.send_photo(chat_id, img_file,
                                caption=f"{sym} – {interval}\n{now_utc_str()}")
                    except Exception:
                        debug_mark(bot_for_interval, chat_id, 902, f"run_cycle_{interval}_send_photo")
                if alarms:
                    txt = f"آلارم {interval} برای {sym}:\n" + "\n".join(f"- {a}" for a in alarms)
                    bot_for_interval.send_message(chat_id, txt)

            if idx % batch == 0 and chat_id and bot_for_interval:
                bot_for_interval.send_message(chat_id, f"پیشرفت {interval}: {idx}/{len(symbols)} نماد")

        if pdf_pages:
            try:
                pdf_pages.close()
                if chat_id and bot_for_interval and pdf_path:
                    with open(pdf_path, "rb") as pdf_file:
                        bot_for_interval.send_document(chat_id, pdf_file,
                            caption=f"PDF سیکل {interval}\n{now_utc_str()}")
            except Exception:
                debug_mark(bot_main, chat_id, 911, f"run_cycle_{interval}_pdf_send")

        elapsed = (now_utc() - start_time).total_seconds()
        if elapsed < cfg.get("cycle_min_duration_sec", 5):
            debug_mark(bot_main, chat_id, 903, f"run_cycle_{interval}_too_fast")

        if chat_id and bot_for_interval:
            bot_for_interval.send_message(chat_id,
                f"پایان سیکل {interval}.\nمدت زمان: {int(elapsed)} ثانیه")
    except Exception:
        debug_mark(bot_main, cfg.get("chat_id_main"), 904, f"run_cycle_{interval}_error")
    finally:
        lock.release()

# =========================
# اجرای فوری از منو
# =========================

@bot_main.message_handler(func=lambda m: m.text == "اجرای فوری تایم‌فریم فعال")
def run_now_active(m):
    cfg = load_config()
    tf = cfg.get("active_interval", "15m")
    try:
        bot_main.send_message(m.chat.id, f"اجرای فوری سیکل {tf} آغاز شد...")
    except Exception:
        debug_mark(bot_main, m.chat.id, 905, "run_now_active_msg")
    threading.Thread(target=run_cycle, args=(tf,), kwargs={"manual": True}, daemon=True).start()

@bot_main.message_handler(func=lambda m: m.text == "اجرای فوری 15m")
def run_now_15m(m):
    try:
        bot_main.send_message(m.chat.id, "اجرای فوری سیکل 15m آغاز شد...")
    except Exception:
        debug_mark(bot_main, m.chat.id, 906, "run_now_15m_msg")
    threading.Thread(target=run_cycle, args=("15m",), kwargs={"manual": True}, daemon=True).start()

@bot_main.message_handler(func=lambda m: m.text == "اجرای فوری 1h")
def run_now_1h(m):
    try:
        bot_main.send_message(m.chat.id, "اجرای فوری سیکل 1h آغاز شد...")
    except Exception:
        debug_mark(bot_main, m.chat.id, 907, "run_now_1h_msg")
    threading.Thread(target=run_cycle, args=("1h",), kwargs={"manual": True}, daemon=True).start()

@bot_main.message_handler(func=lambda m: m.text == "اجرای فوری 4h")
def run_now_4h(m):
    try:
        bot_main.send_message(m.chat.id, "اجرای فوری سیکل 4h آغاز شد...")
    except Exception:
        debug_mark(bot_main, m.chat.id, 908, "run_now_4h_msg")
    threading.Thread(target=run_cycle, args=("4h",), kwargs={"manual": True}, daemon=True).start()

@bot_main.message_handler(func=lambda m: m.text == "اجرای فوری 1d")
def run_now_1d(m):
    try:
        bot_main.send_message(m.chat.id, "اجرای فوری سیکل 1d آغاز شد...")
    except Exception:
        debug_mark(bot_main, m.chat.id, 909, "run_now_1d_msg")
    threading.Thread(target=run_cycle, args=("1d",), kwargs={"manual": True}, daemon=True).start()

@bot_main.message_handler(func=lambda m: m.text == "اجرای چرخه‌ها")
def run_all_cycles(m):
    try:
        bot_main.send_message(m.chat.id, "اجرای چرخه‌ها (15m, 1h, 4h, 1d) آغاز شد...")
    except Exception:
        debug_mark(bot_main, m.chat.id, 912, "run_all_cycles_msg")
    for tf in ["15m","1h","4h","1d"]:
        threading.Thread(target=run_cycle, args=(tf,), kwargs={"manual": True}, daemon=True).start()

# =========================
# Schedulerها (در صورت نیاز)
# =========================

def scheduler_15m():
    while True:
        try:
            run_cycle("15m", manual=False)
        except Exception:
            debug_mark(bot_main, None, 920, "scheduler_15m_error")
        time.sleep(15 * 60)

def scheduler_1h():
    while True:
        try:
            run_cycle("1h", manual=False)
        except Exception:
            debug_mark(bot_main, None, 921, "scheduler_1h_error")
        time.sleep(60 * 60)

def scheduler_4h():
    while True:
        try:
            run_cycle("4h", manual=False)
        except Exception:
            debug_mark(bot_main, None, 922, "scheduler_4h_error")
        time.sleep(4 * 60 * 60)

def scheduler_1d():
    while True:
        try:
            run_cycle("1d", manual=False)
        except Exception:
            debug_mark(bot_main, None, 923, "scheduler_1d_error")
        time.sleep(24 * 60 * 60)

# =========================
# main
# =========================

def main():
    # اگر خواستی Schedulerها فعال باشند، این‌ها را باز کن:
    # threading.Thread(target=scheduler_15m, daemon=True).start()
    # threading.Thread(target=scheduler_1h, daemon=True).start()
    # threading.Thread(target=scheduler_4h, daemon=True).start()
    # threading.Thread(target=scheduler_1d, daemon=True).start()

    try:
        bot_main.infinity_polling()
    except Exception:
        debug_mark(bot_main, None, 930, "main_polling_error")

if __name__ == "__main__":
    main()