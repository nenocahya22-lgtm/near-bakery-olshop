import urllib.parse
import datetime

def wa_link(phone_international: str, message: str) -> str:
    """
    Build a WhatsApp link using wa.me.
    Expected phone format: digits only, international without '+'.
    """
    phone = str(phone_international).strip()
    if phone.startswith("0"):
        # keep as-is; user may provide local-leading format
        pass
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    text = urllib.parse.quote(message)
    return f"https://wa.me/{phone}?text={text}"

def order_to_message(order_id: int, customer_name: str, total_amount: float) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"🛍️ Pesanan baru masuk (Online Orders)\n"
        f"ID Order: #{order_id}\n"
        f"Nama: {customer_name}\n"
        f"Total: {total_amount}\n"
        f"Waktu: {ts}\n\n"
        f"Silakan cek detail order di dashboard: OnlineOrders"
    )
